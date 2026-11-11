#!/usr/bin/env python3
"""Samler metadata, tale og skærmtekst til én række pr. opslag.

Brug:
    python3 saml.py --data data --ud ud --transskription large-v3 large-v3-turbo

Resultat i <ud>/:
    videoer.csv     én række pr. opslag pr. platform, med tal og nøgletal
    opslag.json     samme rækker plus fuld tale, skærmtekst og kommentarer
    indhold.md      læsevenlig gennemgang i tidsrækkefølge, til kodning af tema og tone
    transskriptioner/<dato>_<nøgle>.md   én fil pr. opslag med tale, linje for linje med tid

Et opslag, der ligger på både TikTok og Instagram, får samme indhold_id, så det
tælles som ét stykke indhold med to sæt tal.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from zoneinfo import ZoneInfo

from faelles import find_medier, varighed

TIDSZONE = ZoneInfo("Europe/Copenhagen")
# Højst så mange af de 64 punkter må afvige, før to billeder regnes for forskellige.
BILLED_GRAENSE = 6
DREJNINGER = ("", "transpose=1,", "transpose=1,transpose=1,", "transpose=2,")
UGEDAGE = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"]


def laes(fil: Path, standard=None):
    return json.loads(fil.read_text()) if fil.exists() else standard


def tal(vaerdi) -> int | None:
    try:
        return int(vaerdi)
    except (TypeError, ValueError):
        return None


def tidsfelter(tid: datetime) -> dict:
    lokal = tid.astimezone(TIDSZONE)
    return {
        "tid_utc": tid.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "dato": lokal.strftime("%Y-%m-%d"),
        "klokkeslaet": lokal.strftime("%H:%M"),
        "ugedag": UGEDAGE[lokal.weekday()],
    }


def hent_tale(data: Path, noegle: str, mapper: list[str]) -> dict:
    for mappe in mapper:
        fund = laes(data / "transskription" / mappe / f"{noegle}.json")
        if fund is not None:
            return {**fund, "kilde": mappe}
    return {}


def hent_skaermtekst(data: Path, noegle: str) -> dict:
    fund = laes(data / "skaermtekst" / f"{noegle}.json")
    if not fund:
        return {"laest": fund is not None, "fast": [], "skiftende": []}
    billeder = max(len(fund["billeder"]), 1)
    fast, skiftende = [], []
    for linje in fund["unikke"]:
        # Tekst, der står i mindst en tredjedel af billederne, er en titel eller et
        # mærkat. Resten er undertekster eller noget, kameraet fangede i forbifarten.
        staar = linje["antal"] >= 2 and linje["antal"] / billeder >= 1 / 3
        (fast if staar else skiftende).append(linje["tekst"])
    return {"laest": True, "fast": fast, "skiftende": skiftende}


def tiktok_raekker(data: Path, profil: str) -> list[dict]:
    raekker = []
    for post in laes(data / "liste.json", []):
        vid = post["id"]
        d = laes(data / "detalje" / f"{vid}.json")
        if not d:
            continue
        stats = {**d.get("stats", {}), **d.get("statsV2", {})}
        musik = d.get("music") or {}
        maerkater = [
            tekst.strip()
            for m in d.get("stickersOnItem") or []
            for tekst in m.get("stickerText") or []
            if tekst.strip()
        ]
        billedopslag = bool(d.get("imagePost"))
        raekker.append(
            {
                "noegle": f"tt_{vid}",
                "platform": "tiktok",
                "id": vid,
                "url": f"https://www.tiktok.com/@{profil}/video/{vid}",
                **tidsfelter(datetime.fromtimestamp(int(d["createTime"]), timezone.utc)),
                "type": "billede" if billedopslag else "video",
                "varighed_s": None if billedopslag else tal((d.get("video") or {}).get("duration")),
                "beskrivelse": (d.get("desc") or "").strip(),
                "hashtags": [t["hashtagName"] for t in d.get("textExtra") or [] if t.get("hashtagName")],
                "visninger": tal(stats.get("playCount")),
                "likes": tal(stats.get("diggCount")),
                "kommentarer": tal(stats.get("commentCount")),
                "delinger": tal(stats.get("shareCount")),
                "gemt": tal(stats.get("collectCount")),
                "reposts": tal(stats.get("repostCount")),
                "egen_lyd": bool(musik.get("original")),
                "lyd_titel": "" if musik.get("original") else (musik.get("title") or ""),
                "maerkater": maerkater,
                "kommentar_tekster": [
                    k["tekst"] for k in laes(data / "kommentarer" / f"{vid}.json", [])
                ],
            }
        )
    return raekker


def instagram_raekker(data: Path, medier: dict) -> list[dict]:
    raekker = []
    typer = {"Video": "video", "Image": "billede", "Sidecar": "karrusel"}
    for post in laes(data / "instagram" / "posts.json", []):
        kode = post["shortCode"]
        medie = medier.get(f"ig_{kode}")
        laengde = post.get("videoDuration")
        if laengde is None and medie and medie.video:
            laengde = varighed(medie.video)
        musik = post.get("musicInfo") or {}
        raekker.append(
            {
                "noegle": f"ig_{kode}",
                "platform": "instagram",
                "id": kode,
                "url": post.get("url") or f"https://www.instagram.com/p/{kode}/",
                **tidsfelter(datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00"))),
                "type": typer.get(post.get("type"), post.get("type")),
                "varighed_s": round(laengde) if laengde else None,
                "beskrivelse": (post.get("caption") or "").strip(),
                "hashtags": post.get("hashtags") or [],
                "visninger": tal(post.get("videoPlayCount")),
                "likes": tal(post.get("likesCount")),
                "kommentarer": tal(post.get("commentsCount")),
                "delinger": None,
                "gemt": None,
                "reposts": None,
                "egen_lyd": bool(musik.get("uses_original_audio")),
                "lyd_titel": "" if musik.get("uses_original_audio") else (musik.get("song_name") or ""),
                "maerkater": [],
                "kommentar_tekster": [
                    k.get("text") for k in post.get("latestComments") or [] if k.get("text")
                ],
            }
        )
    return raekker


def ord(tekst: str) -> list[str]:
    return re.findall(r"\w+", tekst.lower())


def billedaftryk(fil: Path, drejning: str = "") -> int | None:
    """64-bit aftryk af et billede (lysere/mørkere end nabopunktet i et 9x8-gitter).
    Samme billede giver næsten samme aftryk, selv om platformen har komprimeret det om."""
    ud = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(fil), "-frames:v", "1",
            "-vf", f"{drejning}scale=9:8:flags=area,format=gray", "-f", "rawvideo", "-",
        ],
        capture_output=True,
    )
    punkter = ud.stdout
    if ud.returncode != 0 or len(punkter) != 72:
        return None
    aftryk = 0
    for raekke in range(8):
        for kolonne in range(8):
            venstre = punkter[raekke * 9 + kolonne]
            aftryk = (aftryk << 1) | (venstre > punkter[raekke * 9 + kolonne + 1])
    return aftryk


def par_billeder(raekker: list[dict], medier: dict) -> None:
    """Billedopslag har hverken længde eller tale, så de pares på selve billedet.
    Samme billede lagt op to gange på én platform får også samme indhold_id."""
    opslag = []
    for r in raekker:
        medie = medier.get(r["noegle"])
        if r["type"] == "video" or not medie or not medie.billeder:
            continue
        # Samme billede bliver nogle gange lagt op igen drejet en kvart omgang.
        aftryk = [billedaftryk(medie.billeder[0], drejning) for drejning in DREJNINGER]
        if None not in aftryk:
            opslag.append((r, aftryk))
    opslag.sort(key=lambda par: par[0]["tid_utc"])
    for nr, (r, aftryk) in enumerate(opslag):
        for tidligere, tidligere_aftryk in opslag[:nr]:
            dage = abs(
                (datetime.fromisoformat(r["tid_utc"]) - datetime.fromisoformat(tidligere["tid_utc"])).days
            )
            forskel = min(bin(a ^ tidligere_aftryk[0]).count("1") for a in aftryk)
            if dage > 7 or forskel > BILLED_GRAENSE:
                continue
            r["indhold_id"] = tidligere["indhold_id"]
            if r["platform"] != tidligere["platform"] and not r["par"] and not tidligere["par"]:
                r["par"], tidligere["par"] = tidligere["noegle"], r["noegle"]
                r["par_lighed"] = tidligere["par_lighed"] = round(1 - forskel / 64, 2)
            break


def par_sammen(raekker: list[dict], medier: dict) -> None:
    """Giver krydspostede opslag samme indhold_id. Kravet er samme længde, datoer
    tæt på hinanden og, hvor begge har tale, at ordene ligner hinanden."""
    tiktok = [r for r in raekker if r["platform"] == "tiktok"]
    brugt: set[str] = set()
    for r in raekker:
        r["indhold_id"] = r["noegle"]
        r["par"] = ""
        r["par_lighed"] = None
    par_billeder(raekker, medier)
    for ig in (r for r in raekker if r["platform"] == "instagram" and r["type"] == "video"):
        bedste, bedste_lighed = None, 0.0
        for tt in tiktok:
            if tt["noegle"] in brugt or tt["type"] != "video":
                continue
            dage = abs(
                (datetime.fromisoformat(ig["tid_utc"]) - datetime.fromisoformat(tt["tid_utc"])).days
            )
            if dage > 7 or ig["varighed_s"] is None or tt["varighed_s"] is None:
                continue
            if abs(ig["varighed_s"] - tt["varighed_s"]) > 2:
                continue
            a, b = ord(ig["tale"]), ord(tt["tale"])
            if a and b:
                lighed = SequenceMatcher(None, a, b).ratio()
            elif not a and not b:
                # Uden tale er længde og dato det eneste holdepunkt, så kun samme dag tæller.
                lighed = 0.5 if dage == 0 else 0.0
            else:
                lighed = 0.0
            if lighed > bedste_lighed:
                bedste, bedste_lighed = tt, lighed
        if bedste and bedste_lighed >= 0.5:
            brugt.add(bedste["noegle"])
            ig["indhold_id"] = bedste["noegle"]
            ig["par"], bedste["par"] = bedste["noegle"], ig["noegle"]
            ig["par_lighed"] = bedste["par_lighed"] = round(bedste_lighed, 2)


def andel(taeller, naevner) -> float | None:
    if taeller is None or not naevner:
        return None
    return round(100 * taeller / naevner, 2)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default="data")
    p.add_argument("--ud", default="ud")
    p.add_argument("--profil", default="viktor.dagoe")
    p.add_argument(
        "--transskription",
        nargs="+",
        default=["large-v3", "large-v3-turbo"],
        help="mapper under <data>/transskription i prioriteret rækkefølge",
    )
    a = p.parse_args()

    data, ud = Path(a.data), Path(a.ud)
    ud.mkdir(parents=True, exist_ok=True)
    medier = {m.noegle: m for m in find_medier(data)}

    raekker = tiktok_raekker(data, a.profil) + instagram_raekker(data, medier)
    for r in raekker:
        tale = hent_tale(data, r["noegle"], a.transskription)
        r["tale"] = tale.get("tekst", "")
        r["tale_sprog"] = tale.get("sprog", "")
        r["tale_sikkerhed"] = tale.get("sikkerhed")
        r["tale_kilde"] = tale.get("kilde", "")
        r["tale_segmenter"] = tale.get("segmenter", [])
        r["har_lydspor"] = tale.get("lyd")
        r["antal_ord"] = len(ord(r["tale"]))
        talt = tale.get("varighed_med_tale")
        r["ord_pr_min"] = round(60 * r["antal_ord"] / talt) if talt and r["antal_ord"] else None
        skaerm = hent_skaermtekst(data, r["noegle"])
        r["skaerm_laest"] = skaerm["laest"]
        r["skaerm_fast"] = skaerm["fast"]
        r["skaerm_skiftende"] = skaerm["skiftende"]
        r["likes_pr_100"] = andel(r["likes"], r["visninger"])
        r["kommentarer_pr_100"] = andel(r["kommentarer"], r["visninger"])
        r["delinger_pr_100"] = andel(r["delinger"], r["visninger"])
        r["gemt_pr_100"] = andel(r["gemt"], r["visninger"])
    par_sammen(raekker, medier)
    raekker.sort(key=lambda r: (r["tid_utc"], r["platform"]))

    (ud / "opslag.json").write_text(json.dumps(raekker, ensure_ascii=False, indent=1))

    kolonner = [
        "noegle", "indhold_id", "platform", "dato", "klokkeslaet", "ugedag", "type",
        "varighed_s", "visninger", "likes", "kommentarer", "delinger", "gemt", "reposts",
        "likes_pr_100", "kommentarer_pr_100", "delinger_pr_100", "gemt_pr_100",
        "tale_sprog", "antal_ord", "ord_pr_min", "tale_kilde", "egen_lyd", "lyd_titel",
        "beskrivelse", "hashtags", "maerkater", "skaerm_fast", "par", "url",
    ]
    with (ud / "videoer.csv").open("w", newline="", encoding="utf-8") as f:
        skriver = csv.DictWriter(f, fieldnames=kolonner, extrasaction="ignore")
        skriver.writeheader()
        for r in raekker:
            skriver.writerow(
                {
                    k: " | ".join(v) if isinstance(v := r.get(k), list) else v
                    for k in kolonner
                }
            )

    linjer = ["# Indhold i tidsrækkefølge", ""]
    for r in raekker:
        linjer += [
            f"## {r['dato']} {r['klokkeslaet']} · {r['noegle']} · {r['type']}"
            + (f" · {r['varighed_s']} s" if r["varighed_s"] else ""),
            "",
            f"- Tal: visninger {r['visninger']}, likes {r['likes']}, kommentarer "
            f"{r['kommentarer']}, delinger {r['delinger']}, gemt {r['gemt']}",
        ]
        if r["par"]:
            linjer.append(f"- Samme indhold som {r['par']} (lighed {r['par_lighed']})")
        if r["beskrivelse"]:
            linjer.append(f"- Beskrivelse: {r['beskrivelse']}")
        if r["maerkater"]:
            linjer.append(f"- Tekst lagt på i TikTok: {' | '.join(r['maerkater'])}")
        if r["skaerm_fast"]:
            linjer.append(f"- Fast tekst på skærmen: {' | '.join(r['skaerm_fast'])}")
        if r["skaerm_skiftende"]:
            linjer.append(f"- Skiftende tekst (stikprøve): {' | '.join(r['skaerm_skiftende'])}")
        if not r["egen_lyd"] and r["lyd_titel"]:
            linjer.append(f"- Lånt lyd: {r['lyd_titel']}")
        if r["kommentar_tekster"]:
            linjer.append(f"- Kommentarer: {' | '.join(r['kommentar_tekster'])}")
        if r["tale"]:
            linjer += [
                f"- Tale ({r['tale_sprog']}, {r['antal_ord']} ord, {r['tale_kilde']}, "
                f"sikkerhed {r['tale_sikkerhed']}):",
                "",
                f"> {r['tale']}",
            ]
        elif r["har_lydspor"] is False:
            linjer.append("- Intet lydspor")
        elif r["har_lydspor"]:
            linjer.append("- Lydspor uden genkendt tale")
        else:
            linjer.append("- Tale ikke transskriberet endnu")
        linjer.append("")
    (ud / "indhold.md").write_text("\n".join(linjer))

    tekstmappe = ud / "transskriptioner"
    tekstmappe.mkdir(exist_ok=True)
    for r in raekker:
        if not r["tale_segmenter"]:
            continue
        hoved = [
            f"# {r['dato']} {r['klokkeslaet']} · {r['platform']} · {r['id']}",
            "",
            r["url"],
            "",
            f"Sprog: {r['tale_sprog']} · model: {r['tale_kilde']} · {r['antal_ord']} ord",
            "",
        ]
        krop = [
            f"[{int(s['start'] // 60):02d}:{int(s['start'] % 60):02d}] {s['tekst']}"
            for s in r["tale_segmenter"]
        ]
        (tekstmappe / f"{r['dato']}_{r['noegle']}.md").write_text("\n".join(hoved + krop) + "\n")

    print(f"{len(raekker)} opslag: "
          f"{sum(r['platform'] == 'tiktok' for r in raekker)} TikTok, "
          f"{sum(r['platform'] == 'instagram' for r in raekker)} Instagram, "
          f"{sum(bool(r['par']) for r in raekker) // 2} par")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

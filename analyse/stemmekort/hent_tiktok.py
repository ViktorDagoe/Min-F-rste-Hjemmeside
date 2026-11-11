#!/usr/bin/env python3
"""Henter alle offentlige opslag og metadata fra en TikTok-profil.

Brug:
    python3 hent_tiktok.py --profil viktor.dagoe --data data

Resultat i <data>/:
    liste.json                 profilens liste over opslag, som TikTok viser den lige nu
    video/<id>.mp4|.m4a        video, eller lydsporet hvis opslaget er et billedopslag
    video/<id>.info.json       yt-dlp-metadata pr. opslag
    detalje/<id>.json          TikToks egen post-struktur (tal, tekstklistermærker, lyd)
    kommentarer/<id>.json      kommentarernes tekst, uden andres brugernavne
    billeder/<id>_<n>.jpg      billederne i billedopslag
    hent_rapport.json          hvor mange der kom igennem, og hvilke der fejlede

Kræver: yt-dlp[default,curl-cffi]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from curl_cffi import requests

YT_DLP = [sys.executable, "-m", "yt_dlp", "--no-warnings"]
REHYDRERING = re.compile(
    r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', re.S
)


def hent_liste(profil: str, forsoeg: int) -> list[dict]:
    """TikTok svarer med jævne mellemrum tomt på listekaldet, så det gentages,
    og det længste svar vinder."""
    bedste: list[dict] = []
    for nr in range(1, forsoeg + 1):
        ud = subprocess.run(
            [*YT_DLP, "--flat-playlist", "-J", f"https://www.tiktok.com/@{profil}"],
            capture_output=True,
            text=True,
        )
        try:
            poster = [p for p in json.loads(ud.stdout).get("entries") or [] if p]
        except json.JSONDecodeError:
            poster = []
        print(f"Listekald {nr}/{forsoeg}: {len(poster)} opslag", flush=True)
        if len(poster) > len(bedste):
            bedste = poster
        if poster and ud.returncode == 0:
            break
        time.sleep(4 * 2 ** (nr - 1))
    return bedste


def flet_lister(gammel: list[dict], ny: list[dict]) -> list[dict]:
    """Nye tal vinder, men et opslag, der kun står i den gamle liste, beholdes."""
    samlet = {p["id"]: p for p in gammel}
    samlet.update({p["id"]: p for p in ny})
    return list(samlet.values())


def hent_video(url: str, mappe: Path) -> tuple[bool, str]:
    ud = subprocess.run(
        [
            *YT_DLP,
            "--write-info-json",
            "--no-overwrites",
            "--retries",
            "3",
            "-o",
            str(mappe / "%(id)s.%(ext)s"),
            url,
        ],
        capture_output=True,
        text=True,
    )
    fejl = [linje for linje in ud.stderr.splitlines() if linje.startswith("ERROR")]
    return ud.returncode == 0, (fejl[-1] if fejl else "")


def hent_detalje(profil: str, vid: str) -> dict | None:
    svar = requests.get(
        f"https://www.tiktok.com/@{profil}/video/{vid}",
        impersonate="chrome",
        timeout=30,
    )
    fund = REHYDRERING.search(svar.text)
    if not fund:
        return None
    scope = json.loads(fund.group(1)).get("__DEFAULT_SCOPE__", {})
    return scope.get("webapp.video-detail", {}).get("itemInfo", {}).get("itemStruct")


def gyldig_detalje(profil: str, post: dict) -> dict | None:
    """TikTok leverer af og til en side, hvor alle tal står til nul. Hvis listen
    siger, at opslaget har visninger, tæller sådan et svar som mislykket."""
    detalje = hent_detalje(profil, post["id"])
    if not detalje:
        return None
    visninger = int((detalje.get("stats") or {}).get("playCount") or 0)
    if visninger == 0 and (post.get("view_count") or 0) > 0:
        return None
    return detalje


def hent_billeder(detalje: dict, mappe: Path) -> int:
    antal = 0
    for nr, billede in enumerate((detalje.get("imagePost") or {}).get("images") or [], 1):
        maal = mappe / f"{detalje['id']}_{nr}.jpg"
        if maal.exists():
            antal += 1
            continue
        for url in (billede.get("imageURL") or {}).get("urlList") or []:
            svar = requests.get(url, impersonate="chrome", timeout=30)
            if svar.status_code == 200 and svar.content:
                maal.write_bytes(svar.content)
                antal += 1
                break
    return antal


def hent_kommentarer(profil: str, vid: str) -> list[dict]:
    """Kun tekst, tid, likes og om det er profilens egen kommentar. Andres
    brugernavne gemmes ikke; analysen har ikke brug for dem."""
    ud: list[dict] = []
    markoer = 0
    while True:
        svar = requests.get(
            "https://www.tiktok.com/api/comment/list/",
            params={"aweme_id": vid, "count": "50", "cursor": str(markoer), "aid": "1988"},
            headers={"referer": f"https://www.tiktok.com/@{profil}/video/{vid}"},
            impersonate="chrome",
            timeout=30,
        ).json()
        for k in svar.get("comments") or []:
            ud.append(
                {
                    "tid": k.get("create_time"),
                    "tekst": k.get("text"),
                    "likes": k.get("digg_count"),
                    "svar": k.get("reply_comment_total"),
                    "egen": (k.get("user") or {}).get("unique_id") == profil,
                }
            )
        if not svar.get("has_more") or not svar.get("comments"):
            return ud
        markoer = svar.get("cursor") or markoer + 50


def med_forsoeg(funktion, forsoeg: int):
    resultat = None
    for nr in range(1, forsoeg + 1):
        try:
            resultat = funktion()
        except Exception as fejl:  # netværksfejl skal ikke vælte hele kørslen
            resultat = None
            print(f"  forsøg {nr}: {type(fejl).__name__}: {fejl}", flush=True)
        if resultat:
            return resultat
        time.sleep(4 * 2 ** (nr - 1))
    return resultat


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--profil", required=True, help="TikTok-brugernavn uden @")
    p.add_argument("--data", default="data", help="mappe til hentede filer")
    p.add_argument("--pause", type=float, default=1.5, help="sekunder mellem opslag")
    p.add_argument("--forsoeg", type=int, default=4, help="forsøg pr. kald")
    a = p.parse_args()

    data = Path(a.data)
    video, detalje_mappe, billeder = data / "video", data / "detalje", data / "billeder"
    kommentar_mappe = data / "kommentarer"
    for mappe in (video, detalje_mappe, billeder, kommentar_mappe):
        mappe.mkdir(parents=True, exist_ok=True)

    listefil = data / "liste.json"
    gammel = json.loads(listefil.read_text()) if listefil.exists() else []
    liste = flet_lister(gammel, hent_liste(a.profil, a.forsoeg))
    if not liste:
        print("Ingen liste: TikTok svarede tomt på alle forsøg")
        return 2
    listefil.write_text(json.dumps(liste, ensure_ascii=False, indent=1))
    print(f"Profilen viser {len(liste)} opslag", flush=True)

    uden_medie: dict[str, str] = {}
    uden_detalje: list[str] = []
    billedopslag: dict[str, int] = {}

    for nr, post in enumerate(sorted(liste, key=lambda x: x.get("timestamp") or 0), 1):
        vid = post["id"]
        maerke = f"[{nr}/{len(liste)}] {vid}"

        detaljefil = detalje_mappe / f"{vid}.json"
        if detaljefil.exists():
            detalje = json.loads(detaljefil.read_text())
        else:
            detalje = med_forsoeg(lambda: gyldig_detalje(a.profil, post), a.forsoeg)
            if detalje:
                detaljefil.write_text(json.dumps(detalje, ensure_ascii=False, indent=1))
            time.sleep(a.pause)
        if not detalje:
            uden_detalje.append(vid)
        else:
            if detalje.get("imagePost"):
                billedopslag[vid] = hent_billeder(detalje, billeder)
            kommentarfil = kommentar_mappe / f"{vid}.json"
            if int(detalje.get("stats", {}).get("commentCount") or 0) and not kommentarfil.exists():
                try:
                    kommentarer = hent_kommentarer(a.profil, vid)
                except Exception as fejl:
                    kommentarer = []
                    print(f"{maerke} kommentarer fejlede: {type(fejl).__name__}", flush=True)
                if kommentarer:
                    kommentarfil.write_text(
                        json.dumps(kommentarer, ensure_ascii=False, indent=1)
                    )
                time.sleep(a.pause)

        har_medie = any(
            f.suffix != ".json" and not f.name.endswith(".part")
            for f in video.glob(f"{vid}.*")
        )
        if har_medie and (video / f"{vid}.info.json").exists():
            print(f"{maerke} findes allerede", flush=True)
            continue

        ok, besked = False, ""
        for forsoeg in range(1, a.forsoeg + 1):
            ok, besked = hent_video(post["url"], video)
            if ok or "No video formats found" in besked:
                break
            time.sleep(4 * 2 ** (forsoeg - 1))
        if ok:
            print(f"{maerke} ok", flush=True)
        elif vid in billedopslag and "No video formats found" in besked:
            uden_medie[vid] = "billedopslag uden lyd"
            print(f"{maerke} billedopslag uden lyd", flush=True)
        else:
            uden_medie[vid] = besked
            print(f"{maerke} FEJL: {besked}", flush=True)
        time.sleep(a.pause)

    rapport = {
        "profil": a.profil,
        "listet": len(liste),
        "med_video_eller_lyd": len(liste) - len(uden_medie),
        "uden_video_eller_lyd": uden_medie,
        "billedopslag": billedopslag,
        "uden_detalje": uden_detalje,
    }
    (data / "hent_rapport.json").write_text(
        json.dumps(rapport, ensure_ascii=False, indent=1)
    )
    print(json.dumps(rapport, ensure_ascii=False, indent=1))
    return 0 if not uden_detalje else 1


if __name__ == "__main__":
    raise SystemExit(main())

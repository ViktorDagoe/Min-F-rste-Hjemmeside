#!/usr/bin/env python3
"""Holder hvert citat op mod alle de transskriptioner, der findes af den video.

Brug:
    python3 tjek_citater.py --data data --ud ud

Læser:
    <ud>/citater.json  liste af {"id": ..., "noegle": "tt_<id>", "tekst": "..."}
                       Udeladelser i et citat skrives som […] eller [...].
                       Ord i kantede parenteser, fx [uklart], regnes ikke med.
    <ud>/opslag.json   fra saml.py, bruges til at finde samme video på den anden platform

Kilder pr. citat: hver mappe under <data>/transskription (én pr. model) for videoen
selv og for dens krydspostede tvilling, samt TikToks egne undertekster, hvis de findes.

Resultat:
    <ud>/citattjek.md    pr. citat og kilde: det sted i kilden, der ligner mest, og
                         hvert ord, hvor citatet og kilden er uenige
    <ud>/citattjek.json  samme i maskinlæsbar form

Ingen kilde er facit; det er maskinlyttede udkast. Et citat, som alle kilder er
enige om, er derfor ikke bevist, men et citat, de er uenige om, er usikkert.
Store og små bogstaver og tegnsætning tæller ikke som forskel.
"""

from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

from sammenlign import noegleord, undertekst


def ordene(tekst: str) -> list[str]:
    return re.findall(r"\w[\w'’-]*", tekst)


def dele(citat: str) -> list[str]:
    stykker = re.split(r"\[\s*(?:…|\.\.\.)\s*\]", citat)
    return [re.sub(r"\[[^\]]*\]", " ", s) for s in stykker if ordene(s)]


def bedste_sted(citat: list[str], kilde: list[str]) -> tuple[int, int, float]:
    """Finder det vindue i kilden, der ligner citatet mest."""
    c = noegleord(citat)
    k = noegleord(kilde)
    if not c or not k:
        return 0, 0, 0.0
    blokke = SequenceMatcher(None, c, k, autojunk=False).get_matching_blocks()
    bedst = (0, 0, 0.0)
    for blok in blokke:
        if not blok.size:
            continue
        start = max(0, blok.b - blok.a)
        for slut in range(start + max(1, len(c) - 4), min(len(k), start + len(c) + 4) + 1):
            lighed = SequenceMatcher(None, c, k[start:slut], autojunk=False).ratio()
            if lighed > bedst[2]:
                bedst = (start, slut, lighed)
    return bedst


def forskelle(citat: list[str], kilde: list[str]) -> list[tuple[str, str]]:
    sm = SequenceMatcher(None, noegleord(citat), noegleord(kilde), autojunk=False)
    return [
        (" ".join(citat[a1:a2]), " ".join(kilde[b1:b2]))
        for slags, a1, a2, b1, b2 in sm.get_opcodes()
        if slags != "equal"
    ]


def kilder(data: Path, noegle: str, tvilling: str | None) -> list[tuple[str, str]]:
    ud: list[tuple[str, str]] = []
    for hvem, n in (("", noegle), ("tvilling ", tvilling)):
        if not n:
            continue
        for mappe in sorted((data / "transskription").iterdir()):
            fil = mappe / f"{n}.json"
            if mappe.is_dir() and fil.exists():
                tekst = json.loads(fil.read_text()).get("tekst") or ""
                if tekst.strip():
                    ud.append((f"{hvem}{mappe.name}", tekst))
    for n in (noegle, tvilling):
        if n and n.startswith("tt_"):
            for fil in sorted((data / "undertekster").glob(f"{n[3:]}.*.vtt")):
                ud.append((f"undertekst {fil.suffixes[0].lstrip('.')}", undertekst(fil)))
    return ud


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default="data")
    p.add_argument("--ud", default="ud")
    p.add_argument("--citater", default=None, help="standard: <ud>/citater.json")
    a = p.parse_args()

    data, ud = Path(a.data), Path(a.ud)
    citater = json.loads(Path(a.citater or ud / "citater.json").read_text())
    opslag = {r["noegle"]: r for r in json.loads((ud / "opslag.json").read_text())}

    resultat = []
    linjer = [
        "# Citattjek",
        "",
        "Hvert citat holdt op mod alle maskintransskriptioner af videoen. `citat → kilde` "
        "viser ord, hvor de to er uenige; `∅` betyder, at ordet mangler det ene sted.",
        "",
    ]
    for c in citater:
        noegle = c["noegle"]
        r = opslag.get(noegle)
        if not r:
            raise SystemExit(f"{c['id']}: ukendt nøgle {noegle}")
        linjer += [f"## {c['id']} · {r['dato']} · {noegle}", "", f"> {c['tekst']}", ""]
        post = {"id": c["id"], "noegle": noegle, "dato": r["dato"], "kilder": []}
        for navn, tekst in kilder(data, noegle, r.get("par")):
            kildeord = ordene(tekst)
            uenige: list[tuple[str, str]] = []
            ligheder = []
            for del_ in dele(c["tekst"]):
                citatord = ordene(del_)
                start, slut, lighed = bedste_sted(citatord, kildeord)
                ligheder.append(lighed)
                uenige += forskelle(citatord, kildeord[start:slut])
                if uenige and not uenige[-1][1] and slut < len(kildeord):
                    # Citatets sidste ord faldt uden for vinduet: vis hvad kilden har dér.
                    mangler = len(ordene(uenige[-1][0]))
                    uenige[-1] = (uenige[-1][0], " ".join(kildeord[slut : slut + mangler]))
            lighed = min(ligheder) if ligheder else 0.0
            if lighed < 0.5:
                linjer.append(f"- {navn}: passagen findes ikke i denne kilde")
                post["kilder"].append({"kilde": navn, "fundet": False})
                continue
            tekst_forskel = "; ".join(f"`{x or '∅'}` → `{y or '∅'}`" for x, y in uenige)
            linjer.append(f"- {navn}: {'ens' if not uenige else tekst_forskel}")
            post["kilder"].append(
                {"kilde": navn, "fundet": True, "ens": not uenige, "forskelle": uenige}
            )
        linjer.append("")
        resultat.append(post)

    (ud / "citattjek.md").write_text("\n".join(linjer))
    (ud / "citattjek.json").write_text(json.dumps(resultat, ensure_ascii=False, indent=1))
    fundne = [k for post in resultat for k in post["kilder"] if k["fundet"]]
    print(
        f"{len(resultat)} citater, {len(fundne)} sammenligninger, "
        f"{sum(not k['ens'] for k in fundne)} med mindst én uenighed -> {ud / 'citattjek.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Sammenligner to transskriptioner af de samme videoer, ord for ord.

Brug:
    python3 sammenlign.py --data data --ud ud --a large-v3-turbo --b large-v3

Resultat:
    <ud>/sammenligning.md    pr. video: andel ens ord og teksten med forskellene markeret
    <ud>/sammenligning.json  samme tal i maskinlæsbar form

Ingen af modellerne er facit. Formålet er at finde de ord, de to er uenige om, så et
citat kun bruges, hvor begge har hørt det samme. I teksten står uenighed som
[A-udgaven | B-udgaven]. Findes TikToks egne undertekster i <data>/undertekster,
sammenlignes de også med B.

Store og små bogstaver og tegnsætning tæller ikke som forskel.
"""

from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


def laes(fil: Path) -> dict | None:
    return json.loads(fil.read_text()) if fil.exists() else None


def ordliste(tekst: str) -> list[str]:
    return re.findall(r"[\w'’-]+|[^\w\s]", tekst)


def noegleord(ordene: list[str]) -> list[str]:
    return [o.lower().strip("'’-") for o in ordene]


def er_ord(o: str) -> bool:
    return bool(re.search(r"\w", o))


def sammenlign(a: str, b: str) -> tuple[float, str, list[tuple[str, str]]]:
    """Returnerer andel ens ord, B-teksten med forskelle markeret, og listen af forskelle."""
    oa = [o for o in ordliste(a) if er_ord(o)]
    ob = [o for o in ordliste(b) if er_ord(o)]
    sm = SequenceMatcher(None, noegleord(oa), noegleord(ob), autojunk=False)
    dele: list[str] = []
    forskelle: list[tuple[str, str]] = []
    ens = 0
    for slags, a1, a2, b1, b2 in sm.get_opcodes():
        if slags == "equal":
            ens += a2 - a1
            dele.append(" ".join(ob[b1:b2]))
        else:
            fra, til = " ".join(oa[a1:a2]), " ".join(ob[b1:b2])
            forskelle.append((fra, til))
            dele.append(f"[{fra or '∅'} | {til or '∅'}]")
    andel = 2 * ens / (len(oa) + len(ob)) if oa or ob else 1.0
    return andel, " ".join(dele), forskelle


def undertekst(fil: Path) -> str:
    linjer = [
        linje.strip()
        for linje in fil.read_text().splitlines()
        if linje.strip() and "-->" not in linje and not linje.startswith("WEBVTT")
    ]
    return " ".join(linjer)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default="data")
    p.add_argument("--ud", default="ud")
    p.add_argument("--a", default="large-v3-turbo", help="mappe under <data>/transskription")
    p.add_argument("--b", default="large-v3", help="mappe under <data>/transskription")
    a = p.parse_args()

    data, ud = Path(a.data), Path(a.ud)
    ud.mkdir(parents=True, exist_ok=True)
    mappe_a, mappe_b = data / "transskription" / a.a, data / "transskription" / a.b

    resultater = []
    linjer = [
        f"# Sammenligning: {a.a} (A) mod {a.b} (B)",
        "",
        "Uenighed står som [A | B]. ∅ betyder, at den ene udgave ikke har noget ord dér.",
        "",
    ]
    for fil_b in sorted(mappe_b.glob("*.json")):
        b = laes(fil_b)
        udgave_a = laes(mappe_a / fil_b.name)
        if not b or not udgave_a or not b.get("tekst") or not udgave_a.get("tekst"):
            continue
        noegle = fil_b.stem
        andel, markeret, forskelle = sammenlign(udgave_a["tekst"], b["tekst"])
        post = {
            "noegle": noegle,
            "sprog_a": udgave_a.get("sprog"),
            "sprog_b": b.get("sprog"),
            "ord_b": len([o for o in ordliste(b["tekst"]) if er_ord(o)]),
            "andel_ens": round(andel, 3),
            "forskelle": forskelle,
        }
        linjer += [
            f"## {noegle}",
            "",
            f"- Sprog: A {post['sprog_a']}, B {post['sprog_b']} · {post['ord_b']} ord i B · "
            f"{100 * andel:.0f} % ens · {len(forskelle)} steder med uenighed",
            "",
            f"> {markeret}",
            "",
        ]
        for vtt in sorted((data / "undertekster").glob(f"{noegle.split('_', 1)[1]}.*.vtt")):
            andel_u, markeret_u, forskelle_u = sammenlign(undertekst(vtt), b["tekst"])
            post["andel_ens_undertekst"] = round(andel_u, 3)
            post["forskelle_undertekst"] = forskelle_u
            linjer += [
                f"- Platformens egne undertekster ({vtt.name}) som A: {100 * andel_u:.0f} % ens",
                "",
                f"> {markeret_u}",
                "",
            ]
        resultater.append(post)

    (ud / "sammenligning.md").write_text("\n".join(linjer))
    (ud / "sammenligning.json").write_text(json.dumps(resultater, ensure_ascii=False, indent=1))
    if resultater:
        snit = sum(r["andel_ens"] for r in resultater) / len(resultater)
        print(f"{len(resultater)} videoer sammenlignet, i snit {100 * snit:.0f} % ens ord")
    else:
        print("Ingen videoer findes i begge mapper")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Tegner charts over de rå tal fra opslag.json.

Brug:
    python3 charts.py --ud ud [--koder ud/koder.json]

koder.json er valgfri og har formen {indhold_id: {"titel": ..., "tema": ..., "tone": ...}}.
Uden den tegnes kun de charts, der ikke kræver tema og tone.

Tallene er små (få hundrede visninger pr. video), så hvert chart viser median og
antal i stedet for gennemsnit, og grupper med under tre videoer tegnes ikke.

Kræver: matplotlib
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

BLAA, GRAA, ROED, GROEN = "#2f6fbd", "#9aa0a6", "#c0392b", "#2e8b57"
MIN_GRUPPE = 3

plt.rcParams.update(
    {
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "figure.dpi": 140,
        "savefig.bbox": "tight",
    }
)


def dag(r: dict) -> date:
    return date.fromisoformat(r["dato"])


def maerke(r: dict, koder: dict, laengde: int = 44) -> str:
    titel = (koder.get(r["indhold_id"]) or {}).get("titel") or r["beskrivelse"] or r["tale"]
    titel = " ".join(titel.split())
    if len(titel) > laengde:
        titel = titel[: laengde - 1] + "…"
    return f"{r['dato'][2:]}  {titel}"


def kilde(fig, tekst: str) -> None:
    fig.text(0.01, -0.02, tekst, fontsize=8, color="#555", ha="left", va="top")


def visninger_over_tid(tt: list[dict], ig: list[dict], ud: Path, kildetekst: str) -> None:
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.bar([dag(r) for r in tt], [r["visninger"] for r in tt], width=0.9, color=BLAA, label="TikTok")
    if ig:
        ax.scatter(
            [dag(r) for r in ig], [r["visninger"] for r in ig],
            s=18, color=ROED, zorder=3, label="Instagram (afspilninger)",
        )
    median = statistics.median(r["visninger"] for r in tt)
    ax.axhline(median, color=GRAA, linestyle="--", linewidth=1)
    ax.text(dag(tt[-1]), median, f" median TikTok {median:.0f}", va="bottom", ha="right", fontsize=8, color="#555")
    ax.set_title("Visninger pr. opslag over tid")
    ax.set_xlabel("Dato for opslag")
    ax.set_ylabel("Visninger (antal)")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax.legend(frameon=False, loc="upper right")
    kilde(fig, kildetekst)
    fig.savefig(ud / "01_visninger_over_tid.png")
    plt.close(fig)


def top_og_bund(tt: list[dict], koder: dict, ud: Path, kildetekst: str, antal: int = 10) -> None:
    sorteret = sorted(tt, key=lambda r: r["visninger"])
    bund, top = sorteret[:antal], sorteret[-antal:]
    fig, akser = plt.subplots(1, 2, figsize=(13, 4.6))
    for ax, raekker, farve, titel in (
        (akser[0], top, GROEN, f"De {antal} mest sete (TikTok)"),
        (akser[1], bund[::-1], ROED, f"De {antal} mindst sete (TikTok)"),
    ):
        # Pladser som tal: to opslag med samme mærke må ikke smelte sammen til én søjle.
        ax.barh(range(len(raekker)), [r["visninger"] for r in raekker], color=farve)
        ax.set_yticks(range(len(raekker)), [maerke(r, koder) for r in raekker])
        for nr, r in enumerate(raekker):
            ax.text(r["visninger"], nr, f" {r['visninger']}", va="center", fontsize=8)
        ax.set_title(titel)
        ax.set_xlabel("Visninger (antal)")
        ax.set_xlim(0, max(r["visninger"] for r in tt) * 1.12)
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    kilde(fig, kildetekst)
    fig.savefig(ud / "02_top_og_bund.png")
    plt.close(fig)


def engagement(tt: list[dict], ud: Path, kildetekst: str) -> None:
    fig, akser = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    datoer = [dag(r) for r in tt]
    akser[0].bar(datoer, [r["likes_pr_100"] for r in tt], width=0.9, color=BLAA)
    akser[0].set_title("Likes pr. 100 visninger (TikTok)")
    akser[0].set_ylabel("Likes pr. 100 visninger")
    videre = [(r["delinger"] + r["gemt"]) for r in tt]
    akser[1].bar(datoer, [r["delinger"] for r in tt], width=0.9, color=GROEN, label="Delinger")
    akser[1].bar(datoer, [r["gemt"] for r in tt], width=0.9, bottom=[r["delinger"] for r in tt], color="#e0a030", label="Gemt")
    akser[1].set_title(f"Delinger og gemt pr. opslag (TikTok), i alt {sum(videre)}")
    akser[1].set_ylabel("Antal")
    akser[1].set_xlabel("Dato for opslag")
    akser[1].legend(frameon=False)
    akser[1].xaxis.set_major_locator(mdates.MonthLocator())
    akser[1].xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    fig.tight_layout()
    kilde(fig, kildetekst)
    fig.savefig(ud / "03_engagement.png")
    plt.close(fig)


def frekvens(tt: list[dict], ig: list[dict], ud: Path, kildetekst: str) -> None:
    maaneder = sorted({r["dato"][:7] for r in tt + ig})
    fig, ax = plt.subplots(figsize=(10, 3.6))
    bredde = 0.4
    for forskydning, raekker, farve, navn in ((-bredde / 2, tt, BLAA, "TikTok"), (bredde / 2, ig, ROED, "Instagram")):
        antal = [sum(r["dato"][:7] == m for r in raekker) for m in maaneder]
        pladser = [i + forskydning for i in range(len(maaneder))]
        ax.bar(pladser, antal, width=bredde, color=farve, label=navn)
        for x, n in zip(pladser, antal):
            if n:
                ax.text(x, n, str(n), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(range(len(maaneder)), maaneder, rotation=45, ha="right")
    ax.set_title("Opslag pr. måned")
    ax.set_xlabel("Måned")
    ax.set_ylabel("Opslag (antal)")
    ax.legend(frameon=False)
    kilde(fig, kildetekst)
    fig.savefig(ud / "04_opslag_pr_maaned.png")
    plt.close(fig)


def laengde(tt: list[dict], ud: Path, kildetekst: str) -> None:
    videoer = [r for r in tt if r["varighed_s"]]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.scatter([r["varighed_s"] for r in videoer], [r["visninger"] for r in videoer], s=22, color=BLAA, alpha=0.8)
    ax.set_title("Længde mod visninger (TikTok-videoer)")
    ax.set_xlabel("Længde (sekunder)")
    ax.set_ylabel("Visninger (antal)")
    kilde(fig, kildetekst)
    fig.savefig(ud / "05_laengde_mod_visninger.png")
    plt.close(fig)


def grupper(tt: list[dict], koder: dict, felt: str, ud: Path, filnavn: str, kildetekst: str) -> None:
    samlet: dict[str, list[dict]] = defaultdict(list)
    for r in tt:
        vaerdi = (koder.get(r["indhold_id"]) or {}).get(felt)
        if vaerdi:
            samlet[vaerdi].append(r)
    samlet = {k: v for k, v in samlet.items() if len(v) >= MIN_GRUPPE}
    if not samlet:
        return
    navne = sorted(samlet, key=lambda k: statistics.median(r["visninger"] for r in samlet[k]))
    etiketter = [f"{k} (n={len(samlet[k])})" for k in navne]
    fig, akser = plt.subplots(1, 2, figsize=(12, 0.45 * len(navne) + 2.2))
    akser[0].boxplot(
        [[r["visninger"] for r in samlet[k]] for k in navne],
        vert=False, labels=etiketter, widths=0.6,
        medianprops={"color": ROED}, flierprops={"markersize": 3},
    )
    akser[0].set_title(f"Visninger pr. {felt} (TikTok)")
    akser[0].set_xlabel("Visninger (antal); rød streg = median")
    videre = [
        100 * sum(r["delinger"] + r["gemt"] for r in samlet[k]) / sum(r["visninger"] for r in samlet[k])
        for k in navne
    ]
    # Boxplottet lægger grupperne på plads 1..n, så søjlerne gør det samme.
    akser[1].barh(range(1, len(navne) + 1), videre, color=GROEN)
    akser[1].set_ylim(akser[0].get_ylim())
    for nr, v in enumerate(videre, 1):
        akser[1].text(v, nr, f" {v:.2f}", va="center", fontsize=8)
    akser[1].set_title(f"Delinger + gemt pr. 100 visninger pr. {felt}")
    akser[1].set_xlabel("Delinger + gemt pr. 100 visninger (samlet for gruppen)")
    akser[1].set_yticklabels([])
    for ax in akser:
        ax.grid(axis="y", visible=False)
    fig.tight_layout()
    kilde(fig, kildetekst + f" · grupper under {MIN_GRUPPE} videoer er udeladt")
    fig.savefig(ud / filnavn)
    plt.close(fig)


def platforme(raekker: list[dict], koder: dict, ud: Path, kildetekst: str) -> None:
    par = [
        (r, next(x for x in raekker if x["noegle"] == r["par"]))
        for r in raekker
        if r["platform"] == "tiktok" and r["par"]
    ]
    par = [(tt, ig) for tt, ig in par if tt["visninger"] and ig["visninger"]]
    if len(par) < MIN_GRUPPE:
        return
    par.sort(key=lambda p: p[0]["tid_utc"])
    fig, ax = plt.subplots(figsize=(9, 0.32 * len(par) + 1.8))
    pladser = range(len(par))
    ax.barh([p - 0.2 for p in pladser], [tt["visninger"] for tt, _ in par], height=0.4, color=BLAA, label="TikTok")
    ax.barh([p + 0.2 for p in pladser], [ig["visninger"] for _, ig in par], height=0.4, color=ROED, label="Instagram")
    ax.set_yticks(list(pladser), [maerke(tt, koder) for tt, _ in par], fontsize=8)
    ax.invert_yaxis()
    ax.set_title("Samme video på begge platforme")
    ax.set_xlabel("Visninger på TikTok / afspilninger på Instagram (antal)")
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False)
    kilde(fig, kildetekst)
    fig.savefig(ud / "08_samme_video_to_platforme.png")
    plt.close(fig)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--ud", default="ud")
    p.add_argument("--koder")
    p.add_argument("--aflaest", default=date.today().isoformat(), help="dato tallene blev aflæst")
    a = p.parse_args()

    ud = Path(a.ud)
    charts = ud / "charts"
    charts.mkdir(parents=True, exist_ok=True)
    raekker = json.loads((ud / "opslag.json").read_text())
    koder = json.loads(Path(a.koder).read_text()) if a.koder else {}

    tt = [r for r in raekker if r["platform"] == "tiktok"]
    ig = [r for r in raekker if r["platform"] == "instagram" and r["visninger"]]
    kildetekst = (
        f"Kilde: offentlige tal på TikTok og Instagram, aflæst {a.aflaest} · "
        f"{len(tt)} TikTok-opslag {tt[0]['dato']} til {tt[-1]['dato']}"
    )

    visninger_over_tid(tt, ig, charts, kildetekst)
    top_og_bund(tt, koder, charts, kildetekst)
    engagement(tt, charts, kildetekst)
    frekvens(tt, [r for r in raekker if r["platform"] == "instagram"], charts, kildetekst)
    laengde(tt, charts, kildetekst)
    if koder:
        grupper(tt, koder, "tema", charts, "06_tema.png", kildetekst)
        grupper(tt, koder, "tone", charts, "07_tone.png", kildetekst)
    platforme(raekker, koder, charts, kildetekst)
    print(f"Charts skrevet til {charts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

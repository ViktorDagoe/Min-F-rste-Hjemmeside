#!/usr/bin/env python3
"""Tegner charts over de rå tal fra opslag.json.

Brug:
    python3 charts.py --ud ud [--koder ud/koder.json]

koder.json er valgfri og har formen
{indhold_id: {"titel": ..., "tema": ..., "tone": ..., "ord": ...}}, hvor "ord" siger,
om ordene er egne, eget manuskript eller oplæst. Uden filen tegnes kun de charts,
der ikke kræver kodning.

Tallene er små (få hundrede visninger pr. video), så hvert chart viser median og
antal i stedet for gennemsnit, og grupper med under tre videoer tegnes ikke.

Kræver: matplotlib 3.10 eller nyere
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

BLAA, GRAA, ROED, GROEN, GUL = "#2f6fbd", "#9aa0a6", "#c0392b", "#2e8b57", "#e0a030"
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
    titel = " ".join(titel.split()) or f"({r['type']} uden tekst)"
    if len(titel) > laengde:
        titel = titel[: laengde - 1] + "…"
    return f"{r['dato'][2:]}  {titel}"


MAANEDER = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]


def komma(x: float, decimaler: int) -> str:
    return f"{x:.{decimaler}f}".replace(".", ",")


def kommaakse(akse) -> None:
    akse.set_major_formatter(lambda x, _: f"{x:g}".replace(".", ","))


def kilde(fig, tekst: str) -> None:
    # Først pakkes figuren, så akseteksterne ligger inden for den; så kan kilden
    # stå under uden at ramme dem.
    fig.tight_layout()
    fig.text(0.01, -0.02, tekst, fontsize=8, color="#555", ha="left", va="top")


def maanedsakse(ax) -> None:
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(
        lambda x, _: (d := mdates.num2date(x)) and f"{MAANEDER[d.month - 1]} {d.year}"
    )


def rangkorrelation(x: list[float], y: list[float]) -> float:
    """Spearman: sammenhæng mellem rækkefølgerne, så få høje tal ikke styrer resultatet."""

    def rang(v: list[float]) -> list[float]:
        orden = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(orden):
            j = i
            while j + 1 < len(orden) and v[orden[j + 1]] == v[orden[i]]:
                j += 1
            for k in range(i, j + 1):
                r[orden[k]] = (i + j) / 2 + 1
            i = j + 1
        return r

    rx, ry = rang(x), rang(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    taeller = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    naevner = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return taeller / naevner if naevner else 0.0


def visninger_over_tid(tt: list[dict], ig: list[dict], ud: Path, kildetekst: str) -> None:
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.bar([dag(r) for r in tt], [r["visninger"] for r in tt], width=0.9, color=BLAA, label="TikTok")
    if ig:
        ax.scatter(
            [dag(r) for r in ig], [r["visninger"] for r in ig],
            s=18, color=ROED, zorder=3, label="Instagram (afspilninger)",
        )
    median = statistics.median(r["visninger"] for r in tt)
    ax.axhline(median, color=GRAA, linestyle="--", linewidth=1, label=f"Median TikTok ({median:.0f})")
    ax.set_title("Visninger pr. opslag over tid: TikTok (visninger) og Instagram (afspilninger)")
    ax.set_xlabel("Dato for opslag")
    ax.set_ylabel("Visninger / afspilninger (antal)")
    maanedsakse(ax)
    ax.legend(frameon=False, loc="upper right", ncols=3, fontsize=8)
    kilde(fig, kildetekst)
    fig.savefig(ud / "01_visninger_over_tid.png")
    plt.close(fig)


def top_og_bund(tt: list[dict], koder: dict, ud: Path, kildetekst: str, antal: int = 10) -> None:
    sorteret = sorted(tt, key=lambda r: r["visninger"])
    bund, top = sorteret[:antal], sorteret[-antal:]
    fig, akser = plt.subplots(1, 2, figsize=(13, 4.6))
    for ax, raekker, farve, titel in (
        (akser[0], top, GROEN, f"De {antal} mest sete TikTok-opslag"),
        (akser[1], bund[::-1], ROED, f"De {antal} mindst sete TikTok-opslag"),
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
    kilde(fig, kildetekst)
    fig.savefig(ud / "02_top_og_bund.png")
    plt.close(fig)


def engagement(tt: list[dict], ud: Path, kildetekst: str) -> None:
    fig, akser = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    datoer = [dag(r) for r in tt]
    i_alt = sum(r["visninger"] for r in tt)

    def samlet(felt: str) -> float:
        return 100 * sum(r[felt] for r in tt) / i_alt

    akser[0].bar(datoer, [r["likes_pr_100"] for r in tt], width=0.9, color=BLAA)
    akser[0].set_title(f"Likes pr. 100 visninger pr. TikTok-opslag (alle opslag samlet: {komma(samlet('likes'), 1)})")
    akser[0].set_ylabel("Likes pr. 100 visninger")
    akser[1].bar(datoer, [r["delinger_pr_100"] for r in tt], width=0.9, color=GROEN, label="Delinger")
    akser[1].bar(
        datoer, [r["gemt_pr_100"] for r in tt], width=0.9,
        bottom=[r["delinger_pr_100"] for r in tt], color=GUL, label="Gemt",
    )
    akser[1].set_title(
        "Delinger og gemt pr. 100 visninger pr. TikTok-opslag "
        f"(samlet: {komma(samlet('delinger'), 2)} og {komma(samlet('gemt'), 2)})"
    )
    akser[1].set_ylabel("Pr. 100 visninger")
    kommaakse(akser[1].yaxis)
    akser[1].legend(frameon=False)
    akser[2].bar(datoer, [r["delinger"] for r in tt], width=0.9, color=GROEN, label="Delinger")
    akser[2].bar(datoer, [r["gemt"] for r in tt], width=0.9, bottom=[r["delinger"] for r in tt], color=GUL, label="Gemt")
    akser[2].set_title(
        f"De samme i rå antal: {sum(r['delinger'] for r in tt)} delinger og "
        f"{sum(r['gemt'] for r in tt)} gemt i alt på {len(tt)} opslag"
    )
    akser[2].set_ylabel("Antal")
    akser[2].set_xlabel("Dato for opslag")
    akser[2].legend(frameon=False)
    maanedsakse(akser[2])
    kilde(fig, kildetekst + " · Instagram viser hverken delinger eller gemt offentligt")
    fig.savefig(ud / "03_engagement.png")
    plt.close(fig)


def frekvens(tt: list[dict], ig: list[dict], ud: Path, kildetekst: str) -> None:
    # Hver måned i TikTok-perioden vises, også de tomme, så en pause ligner en pause.
    foerste, sidste = tt[0]["dato"][:7], max(r["dato"][:7] for r in tt + ig)
    aar, maaned = int(foerste[:4]), int(foerste[5:])
    maaneder = []
    while f"{aar}-{maaned:02d}" <= sidste:
        maaneder.append(f"{aar}-{maaned:02d}")
        aar, maaned = (aar + 1, 1) if maaned == 12 else (aar, maaned + 1)
    foer = [r for r in ig if r["dato"][:7] < foerste]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    bredde = 0.4
    for forskydning, raekker, farve, navn in ((-bredde / 2, tt, BLAA, "TikTok"), (bredde / 2, ig, ROED, "Instagram")):
        antal = [sum(r["dato"][:7] == m for r in raekker) for m in maaneder]
        pladser = [i + forskydning for i in range(len(maaneder))]
        ax.bar(pladser, antal, width=bredde, color=farve, label=navn)
        for x, n in zip(pladser, antal):
            ax.text(x, n, str(n), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(
        range(len(maaneder)),
        [f"{MAANEDER[int(m[5:]) - 1]} {m[:4]}" for m in maaneder],
    )
    ax.set_title("Opslag pr. måned på TikTok og Instagram")
    ax.set_xlabel("Måned")
    ax.set_ylabel("Opslag (antal)")
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False)
    note = (
        f" · {len(foer)} ældre Instagram-opslag ({foer[0]['dato'][:4]}–{foer[-1]['dato'][:4]}) er ikke vist"
        if foer else ""
    )
    kilde(fig, kildetekst + note)
    fig.savefig(ud / "04_opslag_pr_maaned.png")
    plt.close(fig)


def laengde(tt: list[dict], ud: Path, kildetekst: str) -> None:
    videoer = [r for r in tt if r["varighed_s"]]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.scatter([r["varighed_s"] for r in videoer], [r["visninger"] for r in videoer], s=22, color=BLAA, alpha=0.8)
    rho = rangkorrelation([r["varighed_s"] for r in videoer], [r["visninger"] for r in videoer])
    ax.set_title(
        f"Længde mod visninger, {len(videoer)} TikTok-videoer\n"
        f"Rangkorrelation (Spearman) {komma(rho, 2)}; 0 = ingen sammenhæng, ±1 = fuld",
        fontsize=10,
    )
    ax.set_xlabel("Længde (sekunder)")
    ax.set_ylabel("Visninger (antal)")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    kilde(fig, kildetekst)
    fig.savefig(ud / "05_laengde_mod_visninger.png")
    plt.close(fig)


def grupper(
    tt: list[dict], koder: dict, felt: str, navn: str, ud: Path, filnavn: str, kildetekst: str
) -> None:
    samlet: dict[str, list[dict]] = defaultdict(list)
    for r in tt:
        vaerdi = (koder.get(r["indhold_id"]) or {}).get(felt)
        if vaerdi:
            samlet[vaerdi].append(r)
    udeladt = sum(len(v) for v in samlet.values() if len(v) < MIN_GRUPPE)
    samlet = {k: v for k, v in samlet.items() if len(v) >= MIN_GRUPPE}
    if not samlet:
        return
    navne = sorted(samlet, key=lambda k: statistics.median(r["visninger"] for r in samlet[k]))
    etiketter = [f"{k} (n={len(samlet[k])})" for k in navne]
    pladser = range(1, len(navne) + 1)
    fig, akser = plt.subplots(1, 2, figsize=(13.5, 0.5 * len(navne) + 2.4))
    akser[0].boxplot(
        [[r["visninger"] for r in samlet[k]] for k in navne],
        orientation="horizontal", widths=0.55, showfliers=False,
        medianprops={"color": ROED, "linewidth": 1.6},
    )
    # Hvert opslag som en prik, så man ser hvor få tal hver kasse hviler på.
    for plads, k in zip(pladser, navne):
        akser[0].scatter(
            [r["visninger"] for r in samlet[k]], [plads] * len(samlet[k]),
            s=10, color=BLAA, alpha=0.6, zorder=3,
        )
    akser[0].set_yticks(list(pladser), etiketter)
    akser[0].set_title(f"Visninger pr. opslag fordelt på {navn} (TikTok)", fontsize=10)
    akser[0].set_xlabel("Visninger (antal). Rød streg = median, prik = ét opslag")
    akser[0].set_xlim(left=0)
    videre = [
        100 * sum(r["delinger"] + r["gemt"] for r in samlet[k]) / sum(r["visninger"] for r in samlet[k])
        for k in navne
    ]
    akser[1].barh(list(pladser), videre, color=GROEN)
    akser[1].set_ylim(akser[0].get_ylim())
    for plads, k, v in zip(pladser, navne, videre):
        i_alt = sum(r["delinger"] + r["gemt"] for r in samlet[k])
        akser[1].text(v, plads, f" {komma(v, 2)}  ({i_alt} i alt)", va="center", fontsize=8)
    akser[1].set_xlim(0, max(videre) * 1.3)
    akser[1].set_title(f"Delinger + gemt pr. 100 visninger fordelt på {navn} (TikTok)", fontsize=10)
    akser[1].set_xlabel("Delinger + gemt pr. 100 visninger (gruppens sum / gruppens visninger)")
    akser[1].set_yticks(list(pladser), [])
    kommaakse(akser[1].xaxis)
    for ax in akser:
        ax.grid(axis="y", visible=False)
    note = f" · {udeladt} opslag i grupper under {MIN_GRUPPE} er udeladt" if udeladt else ""
    kilde(fig, kildetekst + note)
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
    ax.barh([p - 0.2 for p in pladser], [tt["visninger"] for tt, _ in par], height=0.4, color=BLAA, label="TikTok (visninger)")
    ax.barh([p + 0.2 for p in pladser], [ig["visninger"] for _, ig in par], height=0.4, color=ROED, label="Instagram (afspilninger)")
    ax.set_yticks(list(pladser), [maerke(tt, koder) for tt, _ in par], fontsize=8)
    ax.invert_yaxis()
    hoejest = sum(tt["visninger"] > ig["visninger"] for tt, ig in par)
    ax.set_title(
        f"Samme video på begge platforme, {len(par)} par\n"
        f"TikTok har flest i {hoejest}, Instagram i {len(par) - hoejest}",
        fontsize=10,
    )
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

    begge = kildetekst + (
        f" · {len(ig)} Instagram-reels {ig[0]['dato']} til {ig[-1]['dato']}" if ig else ""
    )

    visninger_over_tid(tt, ig, charts, begge)
    top_og_bund(tt, koder, charts, kildetekst)
    engagement(tt, charts, kildetekst)
    frekvens(tt, [r for r in raekker if r["platform"] == "instagram"], charts, begge)
    laengde(tt, charts, kildetekst)
    if koder:
        grupper(tt, koder, "tema", "tema", charts, "06_tema.png", kildetekst)
        grupper(tt, koder, "tone", "tone", charts, "07_tone.png", kildetekst)
    platforme(raekker, koder, charts, begge)
    if koder:
        grupper(tt, koder, "ord", "ordenes kilde", charts, "09_egne_ord.png", kildetekst)
    print(f"Charts skrevet til {charts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

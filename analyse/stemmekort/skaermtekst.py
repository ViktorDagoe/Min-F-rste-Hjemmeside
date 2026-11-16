#!/usr/bin/env python3
"""Læser teksten på skærmen i hver video og i billedopslag.

Brug:
    python3 skaermtekst.py --data data --interval 2

Resultat:
    <data>/skaermtekst/<nøgle>.json   tekstlinjer pr. udtaget billede + samlet liste

Der tages ét billede pr. <interval> sekunder. Undertekster, der skifter hurtigere
end det, bliver derfor kun læst som stikprøve, ikke ord for ord.
Modellen er latinsk, men forveksler jævnligt å med ä/à/á.

Kræver: rapidocr, onnxruntime, ffmpeg
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR

from faelles import find_medier


def udtag_billeder(video: Path, interval: float, mappe: Path) -> list[tuple[float, Path]]:
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y", "-i", str(video),
            "-vf", f"fps=1/{interval}", "-q:v", "3", str(mappe / "%05d.jpg"),
        ],
        capture_output=True,
    )
    # ffmpegs fps-filter lægger billede n midt i sit interval.
    return [
        (round((nr + 0.5) * interval, 1), fil)
        for nr, fil in enumerate(sorted(mappe.glob("*.jpg")))
    ]


def laes(motor: RapidOCR, fil: Path, min_score: float) -> list[dict]:
    svar = motor(str(fil))
    if svar.txts is None or svar.boxes is None:
        return []
    linjer = []
    for tekst, score, boks in zip(svar.txts, svar.scores, svar.boxes):
        if score < min_score or not tekst.strip():
            continue
        linjer.append(
            {
                "tekst": tekst.strip(),
                "score": round(float(score), 2),
                "y": int(min(p[1] for p in boks)),
            }
        )
    return sorted(linjer, key=lambda linje: linje["y"])


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default="data")
    p.add_argument("--interval", type=float, default=2.0, help="sekunder mellem billeder")
    p.add_argument("--min-score", type=float, default=0.8)
    p.add_argument("--traade", type=int, default=1)
    p.add_argument("--kun", nargs="*", help="kun disse nøgler")
    p.add_argument("--platform", choices=["tiktok", "instagram"])
    a = p.parse_args()

    data = Path(a.data)
    ud_mappe = data / "skaermtekst"
    ud_mappe.mkdir(parents=True, exist_ok=True)

    motor = RapidOCR(
        params={
            "Rec.lang_type": LangRec.LATIN,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
            "Rec.model_type": ModelType.MOBILE,
            "Global.log_level": "error",
            "EngineConfig.onnxruntime.intra_op_num_threads": a.traade,
        }
    )

    medier = [
        m for m in find_medier(data)
        if (not a.kun or m.noegle in a.kun) and (not a.platform or m.platform == a.platform)
    ]
    for nr, m in enumerate(medier, 1):
        maal = ud_mappe / f"{m.noegle}.json"
        if maal.exists():
            continue

        billeder: list[dict] = []
        if m.video:
            with tempfile.TemporaryDirectory() as tmp:
                for tid, fil in udtag_billeder(m.video, a.interval, Path(tmp)):
                    linjer = laes(motor, fil, a.min_score)
                    if linjer:
                        billeder.append({"t": tid, "linjer": linjer})
        for billednr, fil in enumerate(m.billeder, 1):
            linjer = laes(motor, fil, a.min_score)
            if linjer:
                billeder.append({"billede": billednr, "linjer": linjer})

        unikke: dict[str, dict] = {}
        for billede in billeder:
            for linje in billede["linjer"]:
                post = unikke.setdefault(
                    linje["tekst"],
                    {"tekst": linje["tekst"], "foerst": billede.get("t"), "antal": 0},
                )
                post["antal"] += 1

        maal.write_text(
            json.dumps(
                {
                    "noegle": m.noegle,
                    "interval": a.interval,
                    "unikke": list(unikke.values()),
                    "billeder": billeder,
                },
                ensure_ascii=False,
                indent=1,
            )
        )
        print(f"[{nr}/{len(medier)}] {m.noegle} {len(unikke)} tekstlinjer", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

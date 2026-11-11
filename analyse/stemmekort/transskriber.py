#!/usr/bin/env python3
"""Tale til tekst for alle hentede videoer, lokalt med faster-whisper.

Brug:
    python3 transskriber.py --data data --model large-v3-turbo
    python3 transskriber.py --data data --model large-v3 --sprog-fra large-v3-turbo --kun tt_123 ig_abc

Resultat:
    <data>/lyd/<nøgle>.wav                          16 kHz mono
    <data>/transskription/<model>/<nøgle>.json      segmenter med tid og sikkerhed

Sprog: Materialet er dansk, engelsk og portugisisk imellem hinanden, og et forkert
sproggæt får Whisper til at oversætte i stedet for at skrive ned. Derfor prøves
hvert sandsynligt sprog, og den udgave, modellen selv er mest sikker på, vinder.
Den tabende udgave gemmes ved siden af, så valget kan efterprøves.

Regneart: int8 giver volapyk på CPU'er uden AVX2, så standarden er float32.

Kræver: faster-whisper, ffmpeg
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

from faelles import find_medier

SPROG = ("da", "en", "pt")
KANDIDAT_GRAENSE = 0.05


def til_wav(kilde: Path, maal: Path) -> bool:
    if maal.exists():
        return True
    ud = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y", "-i", str(kilde),
            "-vn", "-ac", "1", "-ar", "16000", str(maal),
        ],
        capture_output=True,
        text=True,
    )
    return ud.returncode == 0 and maal.exists()


def laes_wav(fil: Path) -> np.ndarray:
    """Læser lyden selv, så resultatet ikke afhænger af hvilken PyAV der er installeret."""
    with wave.open(str(fil), "rb") as w:
        raa = w.readframes(w.getnframes())
    return np.frombuffer(raa, dtype=np.int16).astype(np.float32) / 32768.0


def kandidater(model: WhisperModel, lyd: np.ndarray) -> tuple[list[str], dict[str, float]]:
    _, _, alle = model.detect_language(
        audio=lyd, vad_filter=True, language_detection_segments=4
    )
    gaet = {sprog: round(p, 3) for sprog, p in alle[:5]}
    kendte = sorted(
        ((sprog, p) for sprog, p in alle if sprog in SPROG), key=lambda x: -x[1]
    )
    valgt = [sprog for sprog, p in kendte if p >= KANDIDAT_GRAENSE] or [kendte[0][0]]
    # Et gæt uden for de tre sprog er næsten altid musik eller støj; så prøves alle tre.
    if alle[0][0] not in SPROG:
        valgt = list(SPROG)
    return valgt, gaet


def skriv_ned(model: WhisperModel, lyd: np.ndarray, sprog: str) -> dict:
    segmenter, info = model.transcribe(
        lyd,
        language=sprog,
        beam_size=5,
        vad_filter=True,
        # Uden dette kan en fejl i ét segment gentage sig resten af videoen.
        condition_on_previous_text=False,
    )
    liste = [
        {
            "start": round(s.start, 2),
            "slut": round(s.end, 2),
            "tekst": s.text.strip(),
            "avg_logprob": round(s.avg_logprob, 3),
            "no_speech_prob": round(s.no_speech_prob, 3),
            "compression_ratio": round(s.compression_ratio, 2),
        }
        for s in segmenter
    ]
    laengde = sum(s["slut"] - s["start"] for s in liste)
    sikkerhed = (
        sum(s["avg_logprob"] * (s["slut"] - s["start"]) for s in liste) / laengde
        if laengde
        else None
    )
    return {
        "sprog": sprog,
        "sikkerhed": round(sikkerhed, 3) if sikkerhed is not None else None,
        "varighed": round(info.duration, 2),
        "varighed_med_tale": round(info.duration_after_vad, 2),
        "tekst": " ".join(s["tekst"] for s in liste),
        "segmenter": liste,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default="data")
    p.add_argument("--model", default="large-v3-turbo")
    p.add_argument("--traade", type=int, default=4)
    p.add_argument("--kun", nargs="*", help="kun disse nøgler")
    p.add_argument("--sprog", help="tving ét sprog (fx da) for alle")
    p.add_argument(
        "--sprog-fra",
        help="genbrug det sprog, en tidligere kørsel (mappenavn) valgte pr. video",
    )
    p.add_argument("--beregning", default="float32", help="ctranslate2 compute_type")
    p.add_argument("--ud", help="navn på resultatmappen, hvis ikke modelnavnet")
    a = p.parse_args()

    data = Path(a.data)
    lyd_mappe = data / "lyd"
    ud_mappe = data / "transskription" / (a.ud or a.model.replace("/", "_"))
    lyd_mappe.mkdir(parents=True, exist_ok=True)
    ud_mappe.mkdir(parents=True, exist_ok=True)

    medier = [m for m in find_medier(data) if not a.kun or m.noegle in a.kun]
    model = WhisperModel(
        a.model, device="cpu", compute_type=a.beregning, cpu_threads=a.traade
    )

    for nr, m in enumerate(medier, 1):
        maal = ud_mappe / f"{m.noegle}.json"
        if maal.exists():
            continue
        if not m.lyd:
            maal.write_text(json.dumps({"noegle": m.noegle, "lyd": False}, indent=1))
            print(f"[{nr}/{len(medier)}] {m.noegle} uden lydspor", flush=True)
            continue

        wav = lyd_mappe / f"{m.noegle}.wav"
        if not til_wav(m.lyd, wav):
            print(f"[{nr}/{len(medier)}] {m.noegle} FEJL: kunne ikke læse lyden", flush=True)
            continue
        lyd = laes_wav(wav)

        start = time.time()
        gaet: dict[str, float] = {}
        if a.sprog:
            proev = [a.sprog]
        elif a.sprog_fra and (data / "transskription" / a.sprog_fra / maal.name).exists():
            tidligere = json.loads((data / "transskription" / a.sprog_fra / maal.name).read_text())
            proev = [tidligere["sprog"]] if tidligere.get("sprog") else list(SPROG)
        else:
            proev, gaet = kandidater(model, lyd)

        udgaver = [skriv_ned(model, lyd, sprog) for sprog in proev]
        med_tale = [u for u in udgaver if u["sikkerhed"] is not None]
        bedst = max(med_tale, key=lambda u: u["sikkerhed"]) if med_tale else udgaver[0]

        maal.write_text(
            json.dumps(
                {
                    "noegle": m.noegle,
                    "lyd": True,
                    "model": a.model,
                    "sproggaet": gaet,
                    **bedst,
                    "andre_udgaver": [
                        {k: u[k] for k in ("sprog", "sikkerhed", "tekst")}
                        for u in udgaver
                        if u is not bedst
                    ],
                },
                ensure_ascii=False,
                indent=1,
            )
        )
        print(
            f"[{nr}/{len(medier)}] {m.noegle} {bedst['sprog']} "
            f"(prøvet: {','.join(proev)}) {bedst['varighed']:.0f}s lyd på "
            f"{time.time() - start:.0f}s",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Fælles opslag af hentede medier, så alle trin bruger samme nøgler.

En nøgle er "tt_<id>" for TikTok og "ig_<shortcode>" for Instagram.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Medie:
    noegle: str
    platform: str
    id: str
    video: Path | None
    lyd: Path | None
    billeder: list[Path]


def uden_brugernavne(tekst: str | None) -> str:
    """Fjerner @-omtaler, så andres brugernavne ikke gemmes sammen med en kommentar."""
    return re.sub(r"@[\w.]+", "@…", tekst or "")


def har_stroem(fil: Path, slags: str) -> bool:
    ud = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", slags[0],
            "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(fil),
        ],
        capture_output=True,
        text=True,
    )
    return slags in ud.stdout


def varighed(fil: Path) -> float | None:
    ud = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", str(fil),
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(ud.stdout.strip())
    except ValueError:
        return None


def find_medier(data: Path) -> list[Medie]:
    medier: list[Medie] = []

    listefil = data / "liste.json"
    for post in json.loads(listefil.read_text()) if listefil.exists() else []:
        vid = post["id"]
        filer = [
            f for f in sorted((data / "video").glob(f"{vid}.*"))
            if f.suffix not in (".json", ".part")
        ]
        video = next((f for f in filer if har_stroem(f, "video")), None)
        lyd = next((f for f in filer if har_stroem(f, "audio")), None)
        billeder = sorted((data / "billeder").glob(f"{vid}_*.jpg"))
        medier.append(Medie(f"tt_{vid}", "tiktok", vid, video, lyd, billeder))

    ig = data / "instagram"
    postfil = ig / "posts.json"
    for post in json.loads(postfil.read_text()) if postfil.exists() else []:
        kode = post["shortCode"]
        video = ig / "video" / f"{kode}.mp4"
        video = video if video.exists() else None
        saerskilt = ig / "audio" / f"{kode}.mp4"
        if saerskilt.exists():
            lyd = saerskilt
        elif video and har_stroem(video, "audio"):
            lyd = video
        else:
            lyd = None
        billeder = sorted((ig / "billeder").glob(f"{kode}_*.jpg"))
        medier.append(Medie(f"ig_{kode}", "instagram", kode, video, lyd, billeder))

    return medier

"""Paso 2 — Descargar el video de referencia y transcribirlo."""
from __future__ import annotations

import subprocess
from pathlib import Path

import requests

from .comun import env, log


def descargar(reel: dict, carpeta: Path, indice: int) -> Path | None:
    if not reel.get("video_url"):
        return None
    destino = carpeta / f"ref_{indice:02d}.mp4"
    if destino.exists():
        return destino
    r = requests.get(reel["video_url"], timeout=120, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    destino.write_bytes(r.content)
    return destino


def transcribir(video: Path) -> str:
    """Transcribe con Whisper (OpenAI). Devuelve '' si no hay clave."""
    clave = env("OPENAI_API_KEY")
    if not clave:
        return ""
    audio = video.with_suffix(".mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1", "-b:a", "64k", str(audio)],
                   check=True)
    with open(audio, "rb") as f:
        r = requests.post("https://api.openai.com/v1/audio/transcriptions",
                          headers={"Authorization": f"Bearer {clave}"},
                          files={"file": (audio.name, f, "audio/mpeg")},
                          data={"model": "whisper-1", "language": "es"}, timeout=300)
    r.raise_for_status()
    return r.json().get("text", "")


def procesar_referencias(reels: list[dict], carpeta: Path) -> list[dict]:
    for i, reel in enumerate(reels):
        if reel.get("transcripcion"):
            continue
        try:
            video = descargar(reel, carpeta, i)
            reel["transcripcion"] = transcribir(video) if video else ""
            log(f"  Referencia {i + 1}: {reel['url']} → {len(reel['transcripcion'])} caracteres transcriptos")
        except Exception as e:  # una referencia rota no frena todo el proceso
            log(f"  No pude procesar {reel['url']}: {e}")
            reel["transcripcion"] = ""
    return reels

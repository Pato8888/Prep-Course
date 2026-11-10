"""Paso 4 — Generar la narración (voz en off) con tiempos por palabra para los subtítulos."""
from __future__ import annotations

import base64
import subprocess
from pathlib import Path

import requests

from .comun import env, log

ELEVEN = "https://api.elevenlabs.io/v1/text-to-speech/{voz}/with-timestamps"
PAUSA = 0.25  # segundos de aire entre escenas


def _palabras_desde_caracteres(alineacion: dict) -> list[tuple[str, float, float]]:
    chars = alineacion["characters"]
    ini = alineacion["character_start_times_seconds"]
    fin = alineacion["character_end_times_seconds"]
    palabras, actual, t0, t1 = [], "", None, 0.0
    for c, a, b in zip(chars, ini, fin):
        if c.isspace():
            if actual:
                palabras.append((actual, t0, t1))
            actual, t0 = "", None
            continue
        if t0 is None:
            t0 = a
        actual += c
        t1 = b
    if actual:
        palabras.append((actual, t0, t1))
    return palabras


def _eleven(texto: str, cfg: dict, destino: Path) -> list[tuple[str, float, float]]:
    r = requests.post(
        ELEVEN.format(voz=env("ELEVENLABS_VOICE_ID")),
        headers={"xi-api-key": env("ELEVENLABS_API_KEY")},
        json={"text": texto, "model_id": cfg["voz"]["modelo"],
              "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.35}},
        timeout=180,
    )
    r.raise_for_status()
    datos = r.json()
    mp3 = destino.with_suffix(".mp3")
    mp3.write_bytes(base64.b64decode(datos["audio_base64"]))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-ar", "44100", "-ac", "1", str(destino)], check=True)
    return _palabras_desde_caracteres(datos["alignment"])


def _silencio(texto: str, cfg: dict, destino: Path) -> list[tuple[str, float, float]]:
    vel = cfg["voz"]["velocidad_palabras_seg"]
    palabras, t = [], 0.0
    for p in texto.split():
        d = max(0.18, len(p) / 13 + 0.12) * (2.7 / vel)
        palabras.append((p, t, t + d))
        t += d + 0.04
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", f"{t:.2f}", str(destino)], check=True)
    return palabras


def duracion(audio: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(audio)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def narrar(escenas: list[dict], cfg: dict, carpeta: Path, prueba: bool = False) -> tuple[Path, list[dict]]:
    """Genera un audio por escena, los une y devuelve (audio_total, escenas con inicio/fin/palabras absolutas)."""
    real = (not prueba and cfg["voz"]["proveedor"] == "elevenlabs"
            and env("ELEVENLABS_API_KEY") and env("ELEVENLABS_VOICE_ID"))
    if not real:
        log("Voz en MODO PRUEBA: audio en silencio con tiempos estimados (configurá ElevenLabs para voz real).")
    generar = _eleven if real else _silencio

    lista, t, resultado = carpeta / "audios.txt", 0.0, []
    with open(lista, "w") as f:
        for i, esc in enumerate(escenas):
            wav = carpeta / f"voz_{i:02d}.wav"
            palabras = generar(esc["narracion"], cfg, wav)
            dur = duracion(wav) + PAUSA
            pad = carpeta / f"voz_{i:02d}_pad.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-af", f"apad=pad_dur={PAUSA}",
                            str(pad)], check=True)
            f.write(f"file '{pad.name}'\n")
            resultado.append({**esc, "inicio": t, "fin": t + dur,
                              "palabras": [(p, t + a, t + b) for p, a, b in palabras]})
            t += dur
    total = carpeta / "narracion.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-c", "copy", str(total)], check=True)
    return total, resultado

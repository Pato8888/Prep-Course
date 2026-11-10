"""Paso 1 — Buscar los reels más virales del nicho y rankearlos."""
from __future__ import annotations

import math
from datetime import datetime, timezone

import requests

from .comun import env, log

APIFY = "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"


def _apify(actor: str, entrada: dict) -> list[dict]:
    token = env("APIFY_TOKEN")
    r = requests.post(APIFY.format(actor=actor), params={"token": token}, json=entrada, timeout=600)
    r.raise_for_status()
    return r.json()


def _normalizar(item: dict) -> dict | None:
    url = item.get("url") or (f"https://www.instagram.com/reel/{item['shortCode']}/" if item.get("shortCode") else None)
    video = item.get("videoUrl")
    vistas = item.get("videoPlayCount") or item.get("videoViewCount") or item.get("playsCount") or 0
    if not url or not video or not vistas:
        return None
    fecha = item.get("timestamp")
    try:
        fecha_dt = datetime.fromisoformat(fecha.replace("Z", "+00:00")) if fecha else None
    except ValueError:
        fecha_dt = None
    return {
        "url": url,
        "video_url": video,
        "autor": item.get("ownerUsername", ""),
        "texto": (item.get("caption") or "")[:1500],
        "vistas": int(vistas),
        "likes": int(item.get("likesCount") or 0),
        "comentarios": int(item.get("commentsCount") or 0),
        "duracion": item.get("videoDuration"),
        "fecha": fecha_dt.isoformat() if fecha_dt else None,
    }


def puntuar(reels: list[dict], cfg: dict) -> list[dict]:
    """Puntaje viral = vistas (log) + tasa de interacción + recencia, según los pesos del config."""
    b = cfg["busqueda"]
    total = b["peso_vistas"] + b["peso_interaccion"] + b["peso_recencia"]
    ahora = datetime.now(timezone.utc)
    max_log = max((math.log10(r["vistas"] + 1) for r in reels), default=1) or 1
    for r in reels:
        interaccion = (r["likes"] + 3 * r["comentarios"]) / max(r["vistas"], 1)
        dias = (ahora - datetime.fromisoformat(r["fecha"])).days if r["fecha"] else b["dias_maximos"]
        recencia = max(0.0, 1 - dias / max(b["dias_maximos"], 1))
        r["tasa_interaccion"] = round(interaccion, 4)
        r["puntaje"] = round(
            (b["peso_vistas"] * math.log10(r["vistas"] + 1) / max_log
             + b["peso_interaccion"] * min(interaccion / 0.10, 1.0)   # 10% = interacción excelente
             + b["peso_recencia"] * recencia) / total * 100, 1)
    return sorted(reels, key=lambda r: r["puntaje"], reverse=True)


def buscar(cfg: dict, prueba: bool = False) -> list[dict]:
    b = cfg["busqueda"]
    if prueba or not env("APIFY_TOKEN"):
        log("Búsqueda en MODO PRUEBA (sin APIFY_TOKEN): uso reels de ejemplo.")
        return puntuar(_ejemplos(), cfg)

    crudos: list[dict] = []
    por_fuente = max(b["cantidad"] // max(len(b["hashtags"]), 1) * 3, 15)
    if b["hashtags"]:
        log(f"Buscando reels por hashtags: {', '.join(b['hashtags'])}")
        crudos += _apify("apify~instagram-hashtag-scraper",
                         {"hashtags": b["hashtags"], "resultsType": "reels", "resultsLimit": por_fuente})
    if b["cuentas"]:
        log(f"Buscando reels de cuentas: {', '.join(b['cuentas'])}")
        crudos += _apify("apify~instagram-reel-scraper", {"username": b["cuentas"], "resultsLimit": por_fuente})

    vistos, reels = set(), []
    for item in crudos:
        r = _normalizar(item)
        if r and r["url"] not in vistos and r["vistas"] >= b["vistas_minimas"]:
            vistos.add(r["url"])
            reels.append(r)
    ranking = puntuar(reels, cfg)
    ranking = [r for r in ranking if not r["fecha"] or
               (datetime.now(timezone.utc) - datetime.fromisoformat(r["fecha"])).days <= b["dias_maximos"]]
    log(f"Encontré {len(reels)} reels válidos; me quedo con los {b['cantidad']} mejores.")
    return ranking[: b["cantidad"]]


def _ejemplos() -> list[dict]:
    hoy = datetime.now(timezone.utc).isoformat()
    base = [
        ("Si te levantás con dolor de espalda, NO es la almohada. Es esto 👇", 1_200_000, 85_000, 2_100),
        ("3 señales de que tu colchón ya está vencido", 640_000, 31_000, 900),
        ("Probé colchones de 3 precios distintos y este me sorprendió", 410_000, 22_000, 1_400),
        ("El error que comete todo el mundo al comprar un colchón", 300_000, 9_000, 300),
        ("Resortes o espuma? La respuesta depende de tu peso", 180_000, 12_000, 650),
    ]
    return [{"url": f"https://www.instagram.com/reel/EJEMPLO{i}/", "video_url": "", "autor": "ejemplo",
             "texto": t, "vistas": v, "likes": l, "comentarios": c, "duracion": 28, "fecha": hoy,
             "transcripcion": t} for i, (t, v, l, c) in enumerate(base)]

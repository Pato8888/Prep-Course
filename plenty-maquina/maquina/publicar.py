"""Paso 7 — Publicar en Instagram (Reels), Facebook (Reels) y TikTok."""
from __future__ import annotations

import time
from pathlib import Path

import requests

from .comun import env, log

GRAPH = "https://graph.facebook.com/v21.0"


def _texto(item: dict) -> str:
    tags = " ".join(f"#{h.lstrip('#')}" for h in item.get("hashtags", []))
    return f"{item['caption']}\n\n{tags}".strip()


def instagram(video: Path, item: dict) -> str:
    token, ig = env("META_ACCESS_TOKEN"), env("META_IG_USER_ID")
    r = requests.post(f"{GRAPH}/{ig}/media", data={
        "media_type": "REELS", "upload_type": "resumable", "caption": _texto(item),
        "share_to_feed": "true", "access_token": token}, timeout=60)
    r.raise_for_status()
    contenedor, uri = r.json()["id"], r.json()["uri"]
    datos = video.read_bytes()
    up = requests.post(uri, data=datos, timeout=600, headers={
        "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(datos))})
    up.raise_for_status()
    for _ in range(60):  # esperar a que Instagram procese el video (hasta ~5 min)
        estado = requests.get(f"{GRAPH}/{contenedor}", params={"fields": "status_code", "access_token": token},
                              timeout=30).json().get("status_code")
        if estado == "FINISHED":
            break
        if estado == "ERROR":
            raise RuntimeError("Instagram rechazó el video al procesarlo")
        time.sleep(5)
    pub = requests.post(f"{GRAPH}/{ig}/media_publish", data={"creation_id": contenedor, "access_token": token}, timeout=60)
    pub.raise_for_status()
    return pub.json()["id"]


def facebook(video: Path, item: dict) -> str:
    token, pagina = env("META_ACCESS_TOKEN"), env("META_PAGE_ID")
    r = requests.post(f"{GRAPH}/{pagina}/video_reels", data={"upload_phase": "start", "access_token": token}, timeout=60)
    r.raise_for_status()
    video_id, url = r.json()["video_id"], r.json()["upload_url"]
    datos = video.read_bytes()
    up = requests.post(url, data=datos, timeout=600, headers={
        "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(datos))})
    up.raise_for_status()
    fin = requests.post(f"{GRAPH}/{pagina}/video_reels", data={
        "upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED",
        "description": _texto(item), "access_token": token}, timeout=60)
    fin.raise_for_status()
    return video_id


def tiktok(video: Path, item: dict, privacidad: str = "PUBLIC_TO_EVERYONE") -> str:
    """Las apps de TikTok sin auditar solo pueden publicar con privacidad SELF_ONLY."""
    token = env("TIKTOK_ACCESS_TOKEN")
    tam = video.stat().st_size
    r = requests.post("https://open.tiktokapis.com/v2/post/publish/video/init/", timeout=60,
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
                      json={"post_info": {"title": _texto(item)[:2200], "privacy_level": privacidad,
                                          "disable_comment": False, "disable_duet": False, "disable_stitch": False},
                            "source_info": {"source": "FILE_UPLOAD", "video_size": tam, "chunk_size": tam,
                                            "total_chunk_count": 1}})
    r.raise_for_status()
    datos = r.json()["data"]
    up = requests.put(datos["upload_url"], data=video.read_bytes(), timeout=600, headers={
        "Content-Type": "video/mp4", "Content-Length": str(tam), "Content-Range": f"bytes 0-{tam - 1}/{tam}"})
    up.raise_for_status()
    return datos["publish_id"]


REDES = {"instagram": (instagram, ("META_ACCESS_TOKEN", "META_IG_USER_ID")),
         "facebook": (facebook, ("META_ACCESS_TOKEN", "META_PAGE_ID")),
         "tiktok": (tiktok, ("TIKTOK_ACCESS_TOKEN",))}


def publicar_item(item: dict, redes: list[str], simular: bool = False) -> dict:
    resultados = item.setdefault("publicado_en", {})
    for red in redes:
        if red in resultados and not str(resultados[red]).startswith("error"):
            continue
        funcion, claves = REDES[red]
        if simular or not all(env(c) for c in claves):
            log(f"  [{red}] simulado (faltan credenciales o modo --simular)")
            resultados[red] = "simulado"
            continue
        try:
            resultados[red] = funcion(Path(item["video"]), item)
            log(f"  [{red}] publicado ✔ ({resultados[red]})")
        except Exception as e:
            resultados[red] = f"error: {e}"
            log(f"  [{red}] ERROR: {e}")
    return item

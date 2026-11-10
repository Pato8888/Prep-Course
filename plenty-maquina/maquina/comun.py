"""Utilidades compartidas: configuración, rutas, logs y estado."""
from __future__ import annotations

import json
import os
import tomllib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "salida"


def cargar_env() -> None:
    """Carga .env si existe (sin dependencias externas)."""
    archivo = RAIZ / ".env"
    if not archivo.exists():
        return
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#", 1)[0].strip()
        if "=" in linea:
            k, v = linea.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def cargar_config() -> dict:
    with open(RAIZ / "config.toml", "rb") as f:
        return tomllib.load(f)


def env(nombre: str) -> str | None:
    valor = os.environ.get(nombre)
    return valor or None


def ahora(cfg: dict) -> datetime:
    return datetime.now(ZoneInfo(cfg["agenda"]["zona_horaria"]))


def carpeta_del_dia(cfg: dict) -> Path:
    c = SALIDA / ahora(cfg).strftime("%Y-%m-%d")
    c.mkdir(parents=True, exist_ok=True)
    return c


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def leer_json(p: Path, defecto=None):
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return defecto


def guardar_json(p: Path, datos) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


# ---- Cola de videos (estado de aprobación / publicación) ----
COLA = SALIDA / "cola.json"


def cola() -> list[dict]:
    return leer_json(COLA, [])


def guardar_cola(items: list[dict]) -> None:
    guardar_json(COLA, items)

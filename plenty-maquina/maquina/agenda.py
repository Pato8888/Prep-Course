"""Paso 6 — Cola de aprobación, agenda de publicación y página de revisión."""
from __future__ import annotations

import html
from datetime import datetime, timedelta

from .comun import SALIDA, ahora, cola, guardar_cola, log


def proximo_horario(cfg: dict, ocupados: set[str]) -> str:
    """Devuelve el próximo horario libre (ISO) según los horarios configurados."""
    zona = ahora(cfg).tzinfo
    dia = ahora(cfg).date()
    for _ in range(60):
        for h in cfg["agenda"]["horarios"]:
            hh, mm = map(int, h.split(":"))
            momento = datetime(dia.year, dia.month, dia.day, hh, mm, tzinfo=zona)
            if momento > ahora(cfg) + timedelta(minutes=5) and momento.isoformat() not in ocupados:
                return momento.isoformat()
        dia += timedelta(days=1)
    raise RuntimeError("No hay horarios libres en los próximos 60 días")


def agendar(item: dict, cfg: dict) -> None:
    ocupados = {i["horario"] for i in cola() if i.get("horario")}
    item["horario"] = proximo_horario(cfg, ocupados)


def aprobar(ids: list[str], cfg: dict) -> None:
    items = cola()
    for item in items:
        if item["estado"] == "pendiente" and ("todos" in ids or item["id"] in ids):
            item["estado"] = "aprobado"
            ocupados = {i["horario"] for i in items if i.get("horario")}
            item["horario"] = proximo_horario(cfg, ocupados)
            log(f"Aprobado {item['id']} → se publica el {item['horario'][:16].replace('T', ' ')}")
    guardar_cola(items)
    pagina_revision()


def rechazar(ids: list[str]) -> None:
    items = cola()
    for item in items:
        if item["id"] in ids and item["estado"] == "pendiente":
            item["estado"] = "rechazado"
            log(f"Rechazado {item['id']}")
    guardar_cola(items)
    pagina_revision()


def pagina_revision() -> None:
    """Genera salida/revision.html para mirar los videos del día antes de aprobarlos."""
    filas = []
    for item in reversed(cola()):
        video = html.escape(str(item["video"]).replace(str(SALIDA) + "/", ""))
        filas.append(f"""
<article class="{item['estado']}">
  <video src="{video}" controls preload="metadata"></video>
  <div>
    <h2>{html.escape(item['titulo'])}</h2>
    <p class="meta"><b>{item['id']}</b> · {item['estado'].upper()}
       {('· ' + item['horario'][:16].replace('T', ' ')) if item.get('horario') else ''}</p>
    <p>{html.escape(item['caption'])}</p>
    <p class="tags">{' '.join('#' + html.escape(h) for h in item.get('hashtags', []))}</p>
    <p class="ref">Estructura: {html.escape(item.get('estructura_usada', ''))}</p>
    <code>python -m maquina aprobar {item['id']}</code>
  </div>
</article>""")
    (SALIDA / "revision.html").write_text(f"""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Revisión de videos</title>
<style>
body{{font-family:system-ui,sans-serif;background:#f4f5f7;color:#111;margin:0;padding:16px}}
h1{{margin:0 0 16px}} article{{display:flex;gap:16px;background:#fff;border-radius:14px;padding:16px;margin-bottom:16px;flex-wrap:wrap}}
video{{width:240px;aspect-ratio:9/16;border-radius:10px;background:#000}} article>div{{flex:1;min-width:240px}}
.meta{{color:#555}} .tags{{color:#1E3A8A}} .ref{{font-size:.9em;color:#666}}
.aprobado{{border-left:6px solid #16a34a}} .pendiente{{border-left:6px solid #f59e0b}}
.rechazado{{opacity:.5;border-left:6px solid #dc2626}} code{{background:#eef;padding:4px 8px;border-radius:6px}}
</style><h1>Videos generados</h1>{''.join(filas) or '<p>Todavía no hay videos.</p>'}""", encoding="utf-8")

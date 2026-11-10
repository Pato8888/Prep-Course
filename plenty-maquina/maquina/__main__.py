"""Máquina de contenido — Plenty Colchones Córdoba.

Uso:
  python -m maquina diario [--prueba] [--cantidad N]   # lo que corre todos los días a las 3 AM
  python -m maquina aprobar <id ...|todos>
  python -m maquina rechazar <id ...>
  python -m maquina publicar [--simular]                # publica lo aprobado cuyo horario ya llegó
  python -m maquina estado
"""
from __future__ import annotations

import argparse
from datetime import datetime

from . import agenda, buscar, guion, publicar, render, transcribir, voz
from .comun import (SALIDA, ahora, cargar_config, cargar_env, carpeta_del_dia, cola, guardar_cola, guardar_json, log)


def diario(cfg: dict, prueba: bool, cantidad: int | None) -> None:
    dia = carpeta_del_dia(cfg)
    cantidad = cantidad or cfg["generacion"]["videos_por_dia"]

    log("1/5 Buscando reels virales del nicho…")
    ranking = buscar.buscar(cfg, prueba)
    guardar_json(dia / "ranking.json", ranking)

    n_ref = cfg["busqueda"]["referencias_a_usar"]
    log(f"2/5 Descargando y transcribiendo las {n_ref} mejores referencias…")
    referencias = transcribir.procesar_referencias(ranking[:n_ref], dia)

    log(f"3/5 Analizando estructuras y escribiendo {cantidad} guiones…")
    resultado = guion.escribir_guiones(referencias, cfg, cantidad, prueba)
    guardar_json(dia / "analisis.json", resultado.model_dump())

    items = cola()
    for n, g in enumerate(resultado.guiones, 1):
        vid = f"{ahora(cfg):%m%d}-{n:02d}"
        carpeta = dia / vid
        carpeta.mkdir(exist_ok=True)
        log(f"4/5 [{vid}] Narración + animación + subtítulos: {g.titulo}")
        audio, escenas = voz.narrar([e.model_dump() for e in g.escenas], cfg, carpeta, prueba)
        archivo = render.renderizar(escenas, audio, cfg, carpeta / f"{vid}.mp4")
        item = {"id": vid, "titulo": g.titulo, "video": str(archivo), "caption": g.caption, "hashtags": g.hashtags,
                "referencia": g.referencia_url, "estructura_usada": g.estructura_usada,
                "estado": "pendiente" if cfg["agenda"]["requiere_aprobacion"] else "aprobado",
                "creado": datetime.now().isoformat()}
        if item["estado"] == "aprobado":
            agenda.agendar(item, cfg)
        items = [i for i in items if i["id"] != vid] + [item]
        guardar_cola(items)

    agenda.pagina_revision()
    log(f"5/5 Listo. Revisá {SALIDA / 'revision.html'} y aprobá con: python -m maquina aprobar <id>")
    publicar_pendientes(cfg, simular=prueba)


def publicar_pendientes(cfg: dict, simular: bool) -> None:
    items, momento = cola(), ahora(cfg)
    for item in items:
        if item["estado"] == "aprobado" and item.get("horario") and datetime.fromisoformat(item["horario"]) <= momento:
            log(f"Publicando {item['id']} — {item['titulo']}")
            publicar.publicar_item(item, cfg["agenda"]["redes"], simular)
            resultados = [str(v) for v in item["publicado_en"].values()]
            if all(not (v.startswith("error") or v == "simulado") for v in resultados):
                item["estado"] = "publicado"
            elif simular:
                item.pop("publicado_en")  # una simulación no cuenta como publicación real
    guardar_cola(items)
    agenda.pagina_revision()


def estado() -> None:
    for i in cola():
        print(f"{i['id']:8} {i['estado']:10} {(i.get('horario') or '')[:16]:16} {i['titulo']}")


def main() -> None:
    cargar_env()
    cfg = cargar_config()
    p = argparse.ArgumentParser(prog="maquina", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("diario"); d.add_argument("--prueba", action="store_true"); d.add_argument("--cantidad", type=int)
    a = sub.add_parser("aprobar"); a.add_argument("ids", nargs="+")
    r = sub.add_parser("rechazar"); r.add_argument("ids", nargs="+")
    pu = sub.add_parser("publicar"); pu.add_argument("--simular", action="store_true")
    sub.add_parser("estado")
    args = p.parse_args()

    if args.cmd == "diario":
        diario(cfg, args.prueba, args.cantidad)
    elif args.cmd == "aprobar":
        agenda.aprobar(args.ids, cfg)
    elif args.cmd == "rechazar":
        agenda.rechazar(args.ids)
    elif args.cmd == "publicar":
        publicar_pendientes(cfg, args.simular)
    else:
        estado()


if __name__ == "__main__":
    main()

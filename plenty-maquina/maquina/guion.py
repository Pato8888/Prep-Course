"""Paso 3 — Analizar la estructura de las referencias y escribir guiones nuevos con Claude."""
from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from .comun import env, log


class Escena(BaseModel):
    narracion: str = Field(description="Lo que dice la voz en off. Frases cortas, español rioplatense/cordobés.")
    texto_pantalla: str = Field(description="Texto grande en pantalla, máximo 6 palabras.")
    visual: Literal["gancho", "producto", "lista", "comparacion", "cta"]
    items: list[str] = Field(default_factory=list, description="Solo para 'lista' o 'comparacion': 2 a 4 ítems cortos.")


class Guion(BaseModel):
    titulo: str
    referencia_url: str = Field(description="URL del reel de referencia en que se inspira la estructura, o '' si es tema propio.")
    estructura_usada: str = Field(description="Patrón tomado de la referencia, p. ej. 'gancho de dolor → 3 señales → solución → CTA'.")
    escenas: list[Escena] = Field(description="La primera escena es el gancho (dura ≤3 segundos). La última es el CTA.")
    caption: str = Field(description="Texto de la publicación, con emojis moderados y CTA a WhatsApp.")
    hashtags: list[str]


class AnalisisReferencia(BaseModel):
    url: str
    por_que_funciono: str
    estructura: str
    tipo_de_gancho: str


class Resultado(BaseModel):
    analisis: list[AnalisisReferencia]
    guiones: list[Guion]


SISTEMA = """Sos guionista de videos cortos (Reels/TikTok) para {nombre}, una tienda de colchones de {ciudad}, Argentina.
Tono de marca: {tono}.
Propuesta de valor: {propuesta}.
Llamado a la acción: "{cta}" (WhatsApp {whatsapp}).

Reglas:
- Usá las referencias SOLO para entender por qué funcionaron (estructura, ritmo, tipo de gancho). Nunca copies su texto,
  ni sus marcas, ni sus datos: cada guion tiene que ser original y hablar de {nombre}.
- La primera escena es un gancho fuerte de máximo 3 segundos (≈8 palabras): curiosidad, dolor concreto o afirmación sorprendente.
- Duración total ≈ {duracion} segundos (≈{palabras} palabras de narración en total).
- Frases cortas, fáciles de leer en subtítulos. Voseo. Nada de promesas médicas ni precios inventados.
- Entre 4 y 7 escenas. La última escena es visual "cta" y menciona WhatsApp o visitar el local en {ciudad}.
"""


def escribir_guiones(referencias: list[dict], cfg: dict, cantidad: int, prueba: bool = False) -> Resultado:
    if prueba or not env("ANTHROPIC_API_KEY"):
        log("Guiones en MODO PRUEBA (sin ANTHROPIC_API_KEY): uso un guion de ejemplo.")
        return _ejemplo(cfg, cantidad)

    import anthropic

    m, g = cfg["marca"], cfg["generacion"]
    sistema = SISTEMA.format(nombre=m["nombre"], ciudad=m["ciudad"], tono=m["tono"],
                             propuesta="; ".join(m["propuesta_valor"]), cta=m["llamado_a_la_accion"],
                             whatsapp=m["whatsapp"], duracion=g["duracion_objetivo_seg"],
                             palabras=int(g["duracion_objetivo_seg"] * cfg["voz"]["velocidad_palabras_seg"]))
    refs = [{k: r.get(k) for k in ("url", "autor", "vistas", "tasa_interaccion", "puntaje", "texto", "transcripcion")}
            for r in referencias]
    pedido = (f"Estas son las referencias más virales del nicho de hoy (ordenadas por puntaje):\n"
              f"<referencias>\n{json.dumps(refs, ensure_ascii=False, indent=1)}\n</referencias>\n\n"
              f"1) Analizá cada referencia: por qué funcionó, su estructura y su tipo de gancho.\n"
              f"2) Escribí {cantidad} guiones nuevos y distintos entre sí para {m['nombre']}, cada uno inspirado en la "
              f"estructura de una referencia con buen potencial. Si faltan referencias útiles, usá estos temas: "
              f"{', '.join(g['temas'])}.")

    client = anthropic.Anthropic()
    respuesta = client.beta.messages.parse(
        model=g["modelo"],
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "high"},
        system=sistema,
        messages=[{"role": "user", "content": pedido}],
        output_format=Resultado,
    )
    if respuesta.stop_reason == "refusal" or respuesta.parsed_output is None:
        raise RuntimeError(f"Claude no devolvió guiones (stop_reason={respuesta.stop_reason}).")
    return respuesta.parsed_output


def _ejemplo(cfg: dict, cantidad: int) -> Resultado:
    m = cfg["marca"]
    guion = Guion(
        titulo="3 señales de que tu colchón ya no da más",
        referencia_url="https://www.instagram.com/reel/EJEMPLO1/",
        estructura_usada="gancho de dolor → lista de 3 señales → solución → CTA",
        escenas=[
            Escena(narracion="Si te levantás más cansado de lo que te acostaste, escuchá esto.",
                   texto_pantalla="¿Te levantás cansado?", visual="gancho"),
            Escena(narracion="Hay tres señales de que tu colchón ya cumplió su ciclo.",
                   texto_pantalla="3 señales", visual="lista",
                   items=["Se hunde en el medio", "Te despertás con dolor", "Dormís mejor en otro lado"]),
            Escena(narracion="Si se hunde en el medio, te levantás con dolor, o dormís mejor en cualquier otro lado, es hora de cambiarlo.",
                   texto_pantalla="Es hora de cambiarlo", visual="producto"),
            Escena(narracion=f"En {m['nombre']} te ayudamos a elegir el ideal según tu peso y tu postura.",
                   texto_pantalla="Asesoramiento gratis", visual="producto"),
            Escena(narracion="Escribinos por WhatsApp y te asesoramos sin compromiso.",
                   texto_pantalla="Escribinos por WhatsApp", visual="cta"),
        ],
        caption=f"¿Tu colchón te está avisando algo? 😴 Te asesoramos gratis por WhatsApp 📲 {m['whatsapp']}",
        hashtags=["colchones", "cordoba", "descanso", "dormirbien"],
    )
    return Resultado(analisis=[], guiones=[guion] * cantidad)

"""Paso 3 — Analizar la estructura de las referencias y escribir guiones nuevos con Claude."""
from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from .comun import env, log


class Escena(BaseModel):
    narracion: str = Field(description="Voz en off de la escena: UNA frase corta (máx. 18 palabras), voseo cordobés.")
    palabras_clave: list[str] = Field(description="1 a 3 palabras de la narración que se destacan en blanco y con recuadro.")
    visual: Literal["titulo", "colchon", "grafico", "comparacion", "pasos", "icono", "producto", "cta"]
    texto_pantalla: str = Field(description="Para 'titulo' y 'cta': texto grande (máx. 6 palabras). En otros visuales, resumen corto.")
    items: list[str] = Field(default_factory=list, description=(
        "colchon: zonas a iluminar en orden (Cabeza, Hombros, Lumbar, Cadera, Piernas). "
        "grafico: etiquetas del eje X. pasos: 2 a 4 pasos cortos. "
        "comparacion: [titulo malo, titulo bueno, resultado malo, resultado bueno]."))
    datos: list[float] = Field(default_factory=list, description="Solo 'grafico': 4 a 7 valores (bajan = rojo, suben = ámbar).")
    tono: Literal["bueno", "malo"] = Field(default="bueno", description="'malo' pinta de rojo las zonas del colchón.")
    icono: Literal["", "pausa", "ojo", "check", "cruz", "alerta", "guardar", "luna", "reloj", "dolor", "cama"] = ""
    etiqueta: str = Field(default="", description="Píldora ámbar debajo del visual, p. ej. '2 · Tu postura'. Opcional.")
    sello: str = Field(default="", description="Sello rojo que cae sobre la escena (1 o 2 palabras, p. ej. 'SE HUNDE'). Usar poco.")


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
- Entre 6 y 9 escenas, cada una de UNA frase. La última es visual "cta" (texto_pantalla tipo "Guardalo" o
  "Escribinos") y menciona WhatsApp o el local en {ciudad}.

Estilo visual (videos explicativos tipo infografía, fondo oscuro, acentos ámbar y rojo):
- Explicá con un concepto visual que se va construyendo: el colchón dividido en zonas que se iluminan, un gráfico que
  sube o baja, pasos numerados, una comparación "así no / así sí", un ícono grande.
- Reusá el mismo visual en escenas seguidas para que la idea avance (p. ej. el colchón iluminando zonas distintas).
- Usá "sello" para el golpe dramático (máx. 1 o 2 por video) y "comparacion" para el cierre antes del CTA.
- Si mencionás una idea con nombre (un estudio, una regla), presentala con visual "titulo".
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
    E = Escena
    guion = Guion(
        titulo="Tu colchón te está avisando",
        referencia_url="https://www.instagram.com/reel/EJEMPLO1/",
        estructura_usada="gancho de dolor → concepto visual que se construye → pasos → comparación → guardalo",
        escenas=[
            E(narracion="Si te levantás con dolor de espalda, el problema no es la almohada.",
              palabras_clave=["dolor", "almohada"], visual="colchon", texto_pantalla="Dolor de espalda",
              items=["Lumbar"], tono="malo", sello="NO ES ESO"),
            E(narracion="Un colchón vencido se hunde justo donde apoyás la cadera.",
              palabras_clave=["hunde", "cadera"], visual="colchon", texto_pantalla="Se hunde",
              items=["Cadera", "Lumbar"], tono="malo", etiqueta="Zona crítica"),
            E(narracion="Y cada noche descansás un poco peor que la anterior.",
              palabras_clave=["peor"], visual="grafico", texto_pantalla="Cada vez peor",
              datos=[9, 8, 6.5, 5.5, 4, 3.2], items=["Año 1", "", "", "", "", "Año 8"], etiqueta="Calidad de descanso"),
            E(narracion="Para elegir bien, mirá tu peso, tu postura, y probalo acostado.",
              palabras_clave=["peso", "postura", "acostado"], visual="pasos", texto_pantalla="3 pasos",
              items=["Tu peso", "Tu postura", "Probalo acostado"]),
            E(narracion="Frená, no te apures, y acostate cinco minutos de verdad.",
              palabras_clave=["frená", "cinco minutos"], visual="icono", icono="pausa", texto_pantalla="Frená",
              etiqueta="5 minutos"),
            E(narracion="Mismo cuerpo, otro colchón: te levantás con otra energía.",
              palabras_clave=["otro colchón", "energía"], visual="comparacion", texto_pantalla="Mismo cuerpo",
              items=["Colchón vencido", "Colchón ideal", "Te levantás cansado", "Te levantás nuevo"]),
            E(narracion="Guardalo, y escribinos por WhatsApp: te asesoramos gratis.",
              palabras_clave=["guardalo", "gratis"], visual="cta", icono="guardar", texto_pantalla="Guardalo"),
        ],
        caption=f"¿Tu colchón te está avisando algo? 😴 Te asesoramos gratis por WhatsApp 📲 {m['whatsapp']}",
        hashtags=["colchones", "cordoba", "descanso", "dormirbien"],
    )
    return Resultado(analisis=[], guiones=[guion] * cantidad)

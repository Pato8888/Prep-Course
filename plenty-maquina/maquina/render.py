"""Paso 5 — Animaciones estilo "explicador" + subtítulos que se arman palabra por palabra.

Estilo (tomado del video de referencia de edición):
- Fondo casi negro con un resplandor azul en el centro.
- Arriba, la frase se va escribiendo al ritmo de la voz: palabras comunes en gris, palabras clave en
  blanco y negrita, y la palabra clave que se acaba de decir queda enmarcada en un recuadro.
- En el centro, una infografía animada (colchón por zonas, gráfico, pasos, comparación, ícono…).
- Etiqueta tipo "píldora" color ámbar debajo, y sellos rojos ("SE HUNDE") que caen sobre la escena.
"""
from __future__ import annotations

import math
import re
import subprocess
import unicodedata
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .comun import RAIZ, log

FUENTES = Path("/usr/share/fonts/opentype/inter")
NEGRA, NEGRITA, SEMI = (str(FUENTES / f"Inter-{p}.otf") for p in ("Black", "Bold", "SemiBold"))


# ---------------- utilidades ----------------
def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def clamp(x: float) -> float:
    return min(max(x, 0.0), 1.0)


def ease_out(x: float) -> float:
    return 1 - (1 - clamp(x)) ** 3


def ease_out_back(x: float) -> float:
    x = clamp(x)
    return 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2


@lru_cache(maxsize=64)
def fuente(ruta: str, tam: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(ruta, tam)


def normal(p: str) -> str:
    p = unicodedata.normalize("NFKD", p.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in p if not unicodedata.combining(c)))


def con_alfa(img: Image.Image, alfa: float) -> Image.Image:
    if alfa >= 0.99:
        return img
    img = img.copy()
    img.putalpha(img.getchannel("A").point(lambda a: int(a * clamp(alfa))))
    return img


def pegar(base: Image.Image, capa: Image.Image, cx: float, cy: float, escala: float = 1.0, alfa: float = 1.0):
    if escala <= 0.02 or alfa <= 0.02:
        return
    if abs(escala - 1) > 0.01:
        capa = capa.resize((max(1, int(capa.width * escala)), max(1, int(capa.height * escala))), Image.BILINEAR)
    base.alpha_composite(con_alfa(capa, alfa), (int(cx - capa.width / 2), int(cy - capa.height / 2)))


def resplandor(capa: Image.Image, radio: int = 18, intensidad: float = 0.9) -> Image.Image:
    glow = capa.filter(ImageFilter.GaussianBlur(radio))
    salida = Image.new("RGBA", capa.size, (0, 0, 0, 0))
    salida.alpha_composite(con_alfa(glow, intensidad))
    salida.alpha_composite(capa)
    return salida


def texto(txt: str, ruta: str, tam: int, color, max_ancho: int | None = None, centrado: bool = True) -> Image.Image:
    f = fuente(ruta, tam)
    lineas = [txt]
    if max_ancho:
        lineas, actual = [], ""
        for p in txt.split():
            prueba = f"{actual} {p}".strip()
            if f.getlength(prueba) <= max_ancho or not actual:
                actual = prueba
            else:
                lineas.append(actual)
                actual = p
        lineas.append(actual)
    alto = int(tam * 1.18)
    w = int(max(f.getlength(l) for l in lineas)) + 8
    img = Image.new("RGBA", (w, alto * len(lineas) + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lineas):
        x = (w - f.getlength(l)) / 2 if centrado else 0
        d.text((x, i * alto), l, font=f, fill=color)
    return img


def pildora(txt: str, fondo, color, tam: int = 46) -> Image.Image:
    f = fuente(NEGRITA, tam)
    w, h = int(f.getlength(txt)) + 2 * 44, int(tam * 1.9)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=fondo)
    d.text((44, (h - tam * 1.2) / 2), txt, font=f, fill=color)
    return img


# ---------------- contexto de estilo ----------------
class Estilo:
    def __init__(self, cfg: dict):
        m, v = cfg["marca"], cfg["video"]
        self.W, self.H, self.fps = v["ancho"], v["alto"], v["fps"]
        self.fondo = hex_rgb(m.get("color_fondo", "#070B16"))
        self.brillo = hex_rgb(m["color_primario"])
        self.acento = hex_rgb(m["color_secundario"])
        self.alerta = hex_rgb(m.get("color_alerta", "#E5484D"))
        self.panel = (22, 35, 66)
        self.borde = (150, 168, 205)
        self.gris = (150, 158, 172)
        self.blanco = (255, 255, 255)
        self.oscuro = (14, 18, 30)
        self.marca, self.whatsapp, self.ciudad = m["nombre"], m["whatsapp"], m["ciudad"]
        self.fotos = sorted(p for p in (RAIZ / v["imagenes_productos"]).glob("*")
                            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
        self.logo = Image.open(RAIZ / v["logo"]).convert("RGBA") if v.get("logo") else None
        self.base = self._fondo()

    def _fondo(self) -> Image.Image:
        W, H = self.W, self.H
        img = Image.new("RGBA", (W, H), (*self.fondo, 255))
        luz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        r = int(W * 0.55)
        ImageDraw.Draw(luz).ellipse((W / 2 - r, H * 0.46 - r, W / 2 + r, H * 0.46 + r), fill=(*self.brillo, 150))
        img.alpha_composite(luz.filter(ImageFilter.GaussianBlur(170)))
        return img


# ---------------- subtítulos que se arman palabra por palabra ----------------
class Subtitulo:
    TAM, MARGEN, MAX_LINEAS, Y0 = 60, 70, 3, 150

    def __init__(self, esc: dict, est: Estilo):
        self.est = est
        claves = {normal(c) for frase in esc.get("palabras_clave", []) for c in frase.split()}
        self.palabras = [(p, a, b, normal(p) in claves) for p, a, b in esc["palabras"]]
        self.f_norm, self.f_clave = fuente(SEMI, self.TAM), fuente(NEGRITA, self.TAM)
        ancho_max = est.W - 2 * self.MARGEN
        esp = self.f_norm.getlength(" ")
        self.pos, linea, x = [], 0, 0.0
        for p, _, _, clave in self.palabras:
            w = (self.f_clave if clave else self.f_norm).getlength(p)
            if x > 0 and x + w > ancho_max:
                linea, x = linea + 1, 0.0
            self.pos.append((linea, x, w))
            x += w + esp
        self.anchos = {}
        for (l, x, w) in self.pos:
            self.anchos[l] = max(self.anchos.get(l, 0), x + w)

    def dibujar(self, cuadro: Image.Image, t: float):
        visibles = [i for i, (_, a, _, _) in enumerate(self.palabras) if a <= t]
        if not visibles:
            return
        pagina = self.pos[visibles[-1]][0] // self.MAX_LINEAS
        d = ImageDraw.Draw(cuadro)
        alto = int(self.TAM * 1.32)
        caja = None
        for i in visibles:
            linea, x, w = self.pos[i]
            if linea // self.MAX_LINEAS != pagina:
                continue
            p, a, _, clave = self.palabras[i]
            xo = (self.est.W - self.anchos[linea]) / 2 + x
            y = self.Y0 + (linea % self.MAX_LINEAS) * alto
            aparicion = clamp((t - a) / 0.12)
            color = self.est.blanco if clave else self.est.gris
            color = tuple(int(c * (0.4 + 0.6 * aparicion)) for c in color)
            d.text((xo, y + (1 - aparicion) * 10), p, font=self.f_clave if clave else self.f_norm, fill=color)
            if clave and t - a < 1.1:
                caja = (xo - 12, y - 6, xo + w + 12, y + self.TAM * 1.2)
        if caja:
            d.rounded_rectangle(caja, 10, outline=(*self.est.acento, 255), width=4)


# ---------------- visuales (infografías) ----------------
def v_titulo(c, esc, lt, dur, est):
    p = ease_out_back(lt / 0.45)
    claves = {normal(x) for frase in esc.get("palabras_clave", []) for x in frase.split()}
    f = fuente(NEGRA, 104)
    lineas, actual = [], []
    for w in esc["texto_pantalla"].split():
        if actual and f.getlength(" ".join(actual + [w])) > est.W - 160:
            lineas.append(actual)
            actual = []
        actual.append(w)
    lineas.append(actual)
    img = Image.new("RGBA", (est.W, 130 * len(lineas) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, linea in enumerate(lineas):
        x = (est.W - f.getlength(" ".join(linea))) / 2
        for w in linea:
            d.text((x, i * 130), w, font=f, fill=est.acento if normal(w) in claves else est.blanco)
            x += f.getlength(w + " ")
    pegar(c, img, est.W / 2, est.H * 0.46, escala=0.7 + 0.3 * p, alfa=clamp(lt / 0.2))


def v_colchon(c, esc, lt, dur, est):
    """Colchón visto desde arriba, dividido en zonas que se iluminan (como el plano de la referencia)."""
    zonas = ["Cabeza", "Hombros", "Lumbar", "Cadera", "Piernas"]
    alturas = [0.16, 0.2, 0.18, 0.2, 0.26]
    resaltar = [normal(z) for z in esc.get("items", [])]
    color_res = est.alerta if esc.get("tono") == "malo" else est.acento
    w, h = 560, 860
    x0, y0 = (est.W - w) / 2, est.H * 0.47 - h / 2
    entrada = ease_out(lt / 0.4)
    capa = Image.new("RGBA", (est.W, est.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    d.rounded_rectangle((x0 - 14, y0 - 14, x0 + w + 14, y0 + h + 14), 40, outline=(*est.borde, 255), width=5)
    y, centros = y0, []
    for i, (z, a) in enumerate(zip(zonas, alturas)):
        zh, n, prog = h * a, normal(z), 0.0
        if n in resaltar:
            k = resaltar.index(n)
            inicio = 0.15 * dur + k * 0.55 * dur / max(len(resaltar), 1)
            prog = ease_out((lt - inicio) / 0.35)
        fill = tuple(int(est.panel[j] * (1 - prog) + color_res[j] * 0.75 * prog) for j in range(3))
        d.rounded_rectangle((x0, y + 4, x0 + w, y + zh - 4), 22, fill=(*fill, 255),
                            outline=(*(color_res if prog > 0.5 else (60, 78, 115)), 255), width=3)
        d.text((x0 + 24, y + 16), z, font=fuente(SEMI, 34), fill=(*(est.oscuro if prog > 0.5 else est.gris), 255))
        if i == 0:  # almohada
            d.rounded_rectangle((x0 + w * 0.22, y + zh * 0.4, x0 + w * 0.78, y + zh * 0.86), 30,
                                fill=(*(est.oscuro if prog > 0.5 else (52, 68, 104)), 255))
        centros.append((x0 + w / 2, y + zh / 2 + 10, prog))
        y += zh
    for (xa, ya, _), (_, yb, _) in zip(centros, centros[1:]):  # columna punteada
        for s in range(0, int(yb - ya), 22):
            d.ellipse((xa - 4, ya + s - 4, xa + 4, ya + s + 4), fill=(*est.acento, 200))
    for (xc, yc, prog) in centros:
        if prog > 0.05:
            r = 20 + 8 * prog
            d.ellipse((xc - r, yc - r, xc + r, yc + r), fill=(*color_res, 255), outline=(255, 255, 255, 255), width=4)
    c.alpha_composite(con_alfa(resplandor(capa, 14, 0.5), entrada))


def _grafico(datos, w, h, prog, color, est, etiquetas=None):
    img = Image.new("RGBA", (w, h + 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line((0, h, w, h), fill=(*est.borde, 120), width=3)
    lo, hi = min(datos), max(datos)
    rango = (hi - lo) or 1
    pts = [(30 + i * (w - 60) / max(len(datos) - 1, 1), 30 + (1 - (v - lo) / rango) * (h - 80)) for i, v in enumerate(datos)]
    n = prog * (len(pts) - 1)
    visibles = pts[: int(n) + 1]
    if int(n) < len(pts) - 1:
        a, b = pts[int(n)], pts[int(n) + 1]
        f = n - int(n)
        visibles.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    for a, b in zip(visibles, visibles[1:]):
        d.line((a, b), fill=(*color, 255), width=9)
    for x, y in pts[: int(n) + 1]:
        d.ellipse((x - 13, y - 13, x + 13, y + 13), fill=(*color, 255))
    for i, e in enumerate((etiquetas or [])[: len(pts)]):
        if i <= n + 0.01:
            tx = texto(e, SEMI, 30, (*est.gris, 255))
            img.alpha_composite(tx, (int(min(max(pts[i][0] - tx.width / 2, 0), w - tx.width)), h + 16))
    return resplandor(img, 12, 0.7)


def v_grafico(c, esc, lt, dur, est):
    datos = esc.get("datos") or [8, 7, 6, 4.5, 3.5, 3]
    color = est.alerta if datos[-1] < datos[0] else est.acento
    g = _grafico(datos, 860, 520, ease_out((lt - 0.2) / (dur * 0.7)), color, est, esc.get("items"))
    pegar(c, g, est.W / 2, est.H * 0.47, alfa=clamp(lt / 0.25))


def v_comparacion(c, esc, lt, dur, est):
    items = esc.get("items") or ["Antes", "Después"]
    tarjetas = [(items[0], est.alerta, [8, 6, 5, 4.5, 4], items[2] if len(items) > 2 else ""),
                (items[1] if len(items) > 1 else "", est.acento, [3, 3.5, 5, 6.5, 8], items[3] if len(items) > 3 else "")]
    for k, (titulo, color, datos, pie) in enumerate(tarjetas):
        inicio = k * dur * 0.4
        p = ease_out_back((lt - inicio) / 0.4)
        if p <= 0.01:
            continue
        tw, th = 450, 520
        t = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        d = ImageDraw.Draw(t)
        d.rounded_rectangle((3, 3, tw - 3, th - 3), 26, fill=(16, 24, 46, 235), outline=(*color, 255), width=5)
        t.alpha_composite(texto(titulo, NEGRITA, 38, (*color, 255), tw - 50, centrado=False), (28, 26))
        t.alpha_composite(_grafico(datos, tw - 60, 230, ease_out((lt - inicio - 0.2) / 0.9), color, est), (30, 120))
        if pie and lt - inicio > 1.0:
            pt = texto(pie, NEGRITA, 34, (255, 255, 255, 255), tw - 50)
            t.alpha_composite(con_alfa(pt, ease_out((lt - inicio - 1.0) / 0.3)),
                              ((tw - pt.width) // 2, th - pt.height - 30))
        pegar(c, t, est.W / 2 + (k * 2 - 1) * 240, est.H * 0.47, escala=0.8 + 0.2 * p, alfa=clamp(p))


def v_pasos(c, esc, lt, dur, est):
    items = esc.get("items") or []
    n = max(len(items), 1)
    alto = 150
    y0 = est.H * 0.47 - (n * alto) / 2
    inicios = [0.1 * dur + k * 0.8 * dur / n for k in range(n)]
    actual = max((k for k in range(len(items)) if lt >= inicios[k]), default=-1)
    for k, it in enumerate(items):
        p = ease_out_back((lt - inicios[k]) / 0.35)
        if p <= 0.01:
            continue
        activo = k == actual
        fila = Image.new("RGBA", (820, 120), (0, 0, 0, 0))
        d = ImageDraw.Draw(fila)
        d.rounded_rectangle((0, 0, 819, 119), 60, fill=(*(est.acento if activo else est.panel), 255),
                            outline=(*(est.acento if activo else (70, 90, 130)), 255), width=3)
        d.ellipse((14, 14, 106, 106), fill=(*(est.oscuro if activo else est.acento), 255))
        fn = fuente(NEGRA, 52)
        d.text((60 - fn.getlength(str(k + 1)) / 2, 28), str(k + 1), font=fn,
               fill=(*(est.acento if activo else est.oscuro), 255))
        d.text((134, 32), it, font=fuente(NEGRITA, 48), fill=(*(est.oscuro if activo else est.blanco), 255))
        pegar(c, fila, est.W / 2 + (1 - clamp(p)) * 200, y0 + k * alto + 60, escala=0.9 + 0.1 * p,
              alfa=clamp(p) * (1 if activo else 0.75))


def _icono(nombre: str, est: Estilo, r: int = 170) -> Image.Image:
    s = r * 2 + 80
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = s / 2
    k = r / 170
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*est.acento, 255))
    o, a = (*est.oscuro, 255), (*est.acento, 255)

    def P(*xy):  # escala coordenadas relativas al centro
        return [(cx + x * k, cy + y * k) for x, y in zip(xy[::2], xy[1::2])]

    if nombre == "pausa":
        d.rounded_rectangle((*P(-60, -70)[0], *P(-18, 70)[0]), 10, fill=o)
        d.rounded_rectangle((*P(18, -70)[0], *P(60, 70)[0]), 10, fill=o)
    elif nombre == "ojo":
        d.ellipse((*P(-110, -60)[0], *P(110, 60)[0]), fill=(255, 255, 255, 255), outline=o, width=8)
        d.ellipse((*P(-42, -42)[0], *P(42, 42)[0]), fill=(*est.panel, 255))
        d.ellipse((*P(-16, -16)[0], *P(16, 16)[0]), fill=o)
    elif nombre == "check":
        d.line(P(-70, 5, -20, 55, 75, -50), fill=o, width=int(30 * k), joint="curve")
    elif nombre == "cruz":
        d.line(P(-60, -60, 60, 60), fill=o, width=int(30 * k))
        d.line(P(60, -60, -60, 60), fill=o, width=int(30 * k))
    elif nombre == "alerta":
        d.polygon(P(0, -85, 90, 70, -90, 70), fill=o)
        d.rectangle((*P(-9, -35)[0], *P(9, 25)[0]), fill=a)
        d.ellipse((*P(-11, 36)[0], *P(11, 58)[0]), fill=a)
    elif nombre == "guardar":
        d.polygon(P(-60, -85, 60, -85, 60, 85, 0, 40, -60, 85), fill=o)
    elif nombre == "luna":
        d.ellipse((*P(-80, -80)[0], *P(80, 80)[0]), fill=o)
        d.ellipse((*P(-40, -105)[0], *P(110, 45)[0]), fill=a)
    elif nombre == "reloj":
        d.ellipse((*P(-85, -85)[0], *P(85, 85)[0]), outline=o, width=int(18 * k))
        d.line(P(0, 0, 0, -55), fill=o, width=int(16 * k))
        d.line(P(0, 0, 40, 20), fill=o, width=int(16 * k))
    elif nombre == "dolor":
        for j in range(3):
            x = -60 + j * 60
            d.line(P(x - 20, -70, x + 20, -10, x - 20, 50, x + 10, 80), fill=o, width=int(16 * k))
    else:  # cama
        d.rounded_rectangle((*P(-100, -10)[0], *P(100, 40)[0]), 12, fill=o)
        d.rounded_rectangle((*P(-100, -70)[0], *P(-50, -10)[0]), 12, fill=o)
        d.rectangle((*P(-100, 40)[0], *P(-85, 75)[0]), fill=o)
        d.rectangle((*P(85, 40)[0], *P(100, 75)[0]), fill=o)
    return resplandor(img, 30, 0.8)


def v_icono(c, esc, lt, dur, est):
    p = ease_out_back(lt / 0.45)
    pegar(c, _icono(esc.get("icono") or "cama", est), est.W / 2, est.H * 0.45, escala=0.4 + 0.6 * p, alfa=clamp(p))


def v_producto(c, esc, lt, dur, est, indice=0):
    if not est.fotos:
        return v_icono(c, {**esc, "icono": esc.get("icono") or "cama"}, lt, dur, est)
    entrada = ease_out(lt / 0.4)
    fw = fh = 820
    foto = Image.open(est.fotos[indice % len(est.fotos)]).convert("RGBA")
    esc_f = max(fw / foto.width, fh / foto.height) * (1.05 + 0.08 * clamp(lt / max(dur, 0.1)))
    foto = foto.resize((int(foto.width * esc_f), int(foto.height * esc_f)), Image.BILINEAR)
    ox, oy = (foto.width - fw) // 2, (foto.height - fh) // 2
    foto = foto.crop((ox, oy, ox + fw, oy + fh))
    mask = Image.new("L", (fw, fh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, fw, fh), 40, fill=255)
    foto.putalpha(mask)
    marco = Image.new("RGBA", (fw + 20, fh + 20), (0, 0, 0, 0))
    ImageDraw.Draw(marco).rounded_rectangle((0, 0, fw + 19, fh + 19), 48, outline=(*est.acento, 255), width=6)
    marco.alpha_composite(foto, (10, 10))
    pegar(c, resplandor(marco, 20, 0.5), est.W / 2, est.H * 0.47 + (1 - entrada) * 80, alfa=entrada)


def v_cta(c, esc, lt, dur, est):
    p = ease_out_back(lt / 0.45)
    pegar(c, _icono(esc.get("icono") or "guardar", est, r=120), est.W / 2, est.H * 0.4, escala=0.5 + 0.5 * p, alfa=clamp(p))
    titulo = texto(esc["texto_pantalla"], NEGRA, 92, (255, 255, 255, 255), est.W - 160)
    pegar(c, titulo, est.W / 2, est.H * 0.555, escala=0.8 + 0.2 * p, alfa=clamp((lt - 0.15) / 0.3))
    late = 1 + 0.04 * math.sin(lt * 7)
    wa = pildora(f"WhatsApp {est.whatsapp}", (37, 211, 102, 255), (255, 255, 255, 255), 44)
    pegar(c, wa, est.W / 2, est.H * 0.67, escala=ease_out_back((lt - 0.4) / 0.4) * late)
    pegar(c, texto(f"{est.marca} · {est.ciudad}", SEMI, 40, (*est.gris, 255)), est.W / 2, est.H * 0.73,
          alfa=clamp((lt - 0.6) / 0.3))


VISUALES = {"titulo": v_titulo, "gancho": v_titulo, "colchon": v_colchon, "grafico": v_grafico,
            "comparacion": v_comparacion, "pasos": v_pasos, "lista": v_pasos, "icono": v_icono,
            "producto": v_producto, "cta": v_cta}


def sello(c, txt, lt, dur, est):
    p = clamp((lt - dur * 0.45) / 0.18)
    if p <= 0:
        return
    f = fuente(NEGRA, 104)
    w, h = int(f.getlength(txt)) + 90, 170
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((4, 4, w - 4, h - 4), 18, outline=(*est.alerta, 255), width=10, fill=(20, 8, 12, 170))
    d.text((45, 22), txt, font=f, fill=(*est.alerta, 255))
    img = img.rotate(6, resample=Image.BICUBIC, expand=True)
    pegar(c, img, est.W / 2, est.H * 0.66, escala=1.6 - 0.6 * p, alfa=p * 0.95)


# ---------------- render principal ----------------
def renderizar(escenas: list[dict], audio: Path, cfg: dict, destino: Path) -> Path:
    est = Estilo(cfg)
    W, H, FPS = est.W, est.H, est.fps
    total = escenas[-1]["fin"]
    n_frames = int(math.ceil(total * FPS))
    subs = [Subtitulo(e, est) for e in escenas]
    pildoras = [pildora(e["etiqueta"], (*est.acento, 255), (*est.oscuro, 255)) if e.get("etiqueta") else None
                for e in escenas]
    marca = texto(est.marca.upper(), NEGRITA, 30, (*est.gris, 200))

    musica = next((p for p in (RAIZ / "assets").glob("musica.*")), None)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(audio)]
    if musica:
        cmd += ["-stream_loop", "-1", "-i", str(musica), "-filter_complex",
                "[2:a]volume=0.12[m];[1:a][m]amix=inputs=2:duration=first[a]", "-map", "0:v", "-map", "[a]"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", str(destino)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    log(f"Renderizando {n_frames} cuadros ({total:.1f}s)…")
    idx = 0
    for fr in range(n_frames):
        t = fr / FPS
        while idx < len(escenas) - 1 and t >= escenas[idx]["fin"]:
            idx += 1
        esc = escenas[idx]
        lt, dur = t - esc["inicio"], esc["fin"] - esc["inicio"]
        cuadro = est.base.copy()

        dibujar = VISUALES.get(esc["visual"], v_icono)
        if dibujar is v_producto:
            v_producto(cuadro, esc, lt, dur, est, indice=idx)
        else:
            dibujar(cuadro, esc, lt, dur, est)
        if esc.get("sello"):
            sello(cuadro, esc["sello"].upper(), lt, dur, est)
        if pildoras[idx] is not None and esc["visual"] != "cta":
            p = ease_out_back((lt - 0.3) / 0.35)
            pegar(cuadro, pildoras[idx], W / 2, H * 0.78, escala=0.6 + 0.4 * p, alfa=clamp(p))
        subs[idx].dibujar(cuadro, t)

        if est.logo:
            pegar(cuadro, est.logo.resize((200, int(200 * est.logo.height / est.logo.width))), W / 2, H - 120)
        else:
            pegar(cuadro, marca, W / 2, H - 110)
        proc.stdin.write(cuadro.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg falló al renderizar el video")
    log(f"Video listo: {destino}")
    return destino

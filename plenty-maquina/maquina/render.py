"""Paso 5 — Animaciones + subtítulos sincronizados → video vertical 1080x1920 listo para publicar."""
from __future__ import annotations

import math
import random
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .comun import RAIZ, log


# ---------------- utilidades de dibujo ----------------
def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease_out_back(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_out(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


@lru_cache(maxsize=32)
def fuente(ruta: str, tam: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(ruta, tam)


def envolver(texto: str, f: ImageFont.FreeTypeFont, ancho: int) -> list[str]:
    lineas, actual = [], ""
    for p in texto.split():
        prueba = f"{actual} {p}".strip()
        if f.getlength(prueba) <= ancho:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def capa_texto(texto: str, ruta_fuente: str, tam: int, ancho: int, color, fondo=None, pad=36) -> Image.Image:
    f = fuente(ruta_fuente, tam)
    lineas = envolver(texto.upper(), f, ancho - 2 * pad)
    alto_linea = int(tam * 1.12)
    w = int(max(f.getlength(l) for l in lineas)) + 2 * pad
    h = alto_linea * len(lineas) + 2 * pad
    img = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if fondo:
        sombra = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sombra).rounded_rectangle((16, 20, w + 16, h + 20), 34, fill=(0, 0, 0, 110))
        img.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(10)))
        d.rounded_rectangle((8, 8, w + 8, h + 8), 34, fill=fondo)
    for i, l in enumerate(lineas):
        x = 8 + (w - f.getlength(l)) / 2
        y = 8 + pad + i * alto_linea
        if not fondo:
            d.text((x, y), l, font=f, fill=(0, 0, 0, 160), stroke_width=10, stroke_fill=(0, 0, 0, 160))
        d.text((x, y), l, font=f, fill=color)
    return img


def pegar_centrado(base: Image.Image, capa: Image.Image, cx: float, cy: float, escala: float = 1.0, alfa: float = 1.0):
    if escala <= 0.01 or alfa <= 0.01:
        return
    if abs(escala - 1) > 0.01:
        capa = capa.resize((max(1, int(capa.width * escala)), max(1, int(capa.height * escala))), Image.BILINEAR)
    if alfa < 0.99:
        capa = capa.copy()
        capa.putalpha(capa.getchannel("A").point(lambda a: int(a * alfa)))
    base.alpha_composite(capa, (int(cx - capa.width / 2), int(cy - capa.height / 2)))


# ---------------- recursos de la escena ----------------
def fondo_base(W: int, H: int, c1, c2) -> Image.Image:
    grad = Image.new("RGB", (1, 256))
    for y in range(256):
        t = y / 255
        grad.putpixel((0, y), tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    img = grad.resize((W, H + 400)).convert("RGBA")
    # manchas de luz suaves (se desplazan con el tiempo)
    luz = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(luz)
    rnd = random.Random(7)
    for _ in range(7):
        r = rnd.randint(180, 420)
        x, y = rnd.randint(0, W), rnd.randint(0, H + 400)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 28))
    img.alpha_composite(luz.filter(ImageFilter.GaussianBlur(90)))
    return img


def colchon_ilustrado(ancho: int, c_primario, c_secundario) -> Image.Image:
    """Ilustración simple de colchón para cuando no hay fotos de producto."""
    h = int(ancho * 0.55)
    img = Image.new("RGBA", (ancho + 60, h + 80), (0, 0, 0, 0))
    sombra = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).ellipse((40, h + 10, ancho + 20, h + 70), fill=(0, 0, 0, 120))
    img.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((30, h * 0.35 + 30, ancho + 30, h + 30), 50, fill=(225, 230, 240))          # base/sommier
    d.rounded_rectangle((30, h * 0.12, ancho + 30, h * 0.62 + 30), 60, fill=(255, 255, 255))       # colchón
    d.rounded_rectangle((30, h * 0.12, ancho + 30, h * 0.24), 40, fill=c_secundario)               # pillow top
    for i in range(1, 8):  # capitoné
        x = 30 + ancho * i / 8
        for yy in (h * 0.36, h * 0.5):
            d.ellipse((x - 9, yy - 9, x + 9, yy + 9), fill=(200, 208, 225))
    d.rounded_rectangle((60, h * 0.74 + 30, ancho, h * 0.8 + 30), 10, fill=c_primario)              # franja
    return img


def fotos_producto(cfg: dict) -> list[Path]:
    carpeta = RAIZ / cfg["video"]["imagenes_productos"]
    return sorted(p for p in carpeta.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})


def preparar_foto(ruta: Path, ancho: int, alto: int) -> Image.Image:
    img = Image.open(ruta).convert("RGBA")
    escala = max(ancho / img.width, alto / img.height) * 1.15  # margen para el zoom
    img = img.resize((int(img.width * escala), int(img.height * escala)), Image.LANCZOS)
    return img


# ---------------- subtítulos (ASS, palabra por palabra) ----------------
def _t(seg: float) -> str:
    h, r = divmod(max(seg, 0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _ass_color(hexa: str) -> str:
    r, g, b = hex_rgb(hexa)
    return f"&H00{b:02X}{g:02X}{r:02X}"


def subtitulos_ass(escenas: list[dict], cfg: dict, destino: Path, palabras_por_bloque: int = 3) -> None:
    v, m = cfg["video"], cfg["marca"]
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {v['ancho']}
PlayResY: {v['alto']}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{v['fuente_subtitulos']},76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,3,2,90,90,{int(v['alto'] * 0.29)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    resaltado = _ass_color(m["color_secundario"])
    eventos = []
    for esc in escenas:
        pal = esc["palabras"]
        for i in range(0, len(pal), palabras_por_bloque):
            bloque = pal[i:i + palabras_por_bloque]
            for j, (_, ini, fin) in enumerate(bloque):
                fin_evento = bloque[j + 1][1] if j + 1 < len(bloque) else fin + 0.12
                partes = []
                for k, (p, _, _) in enumerate(bloque):
                    p = p.upper().replace("{", "").replace("}", "")
                    if k == j:
                        partes.append(f"{{\\c{resaltado}\\fscx112\\fscy112}}{p}{{\\c&H00FFFFFF&\\fscx100\\fscy100}}")
                    else:
                        partes.append(p)
                pop = "{\\fad(60,0)}" if j == 0 else ""
                eventos.append(f"Dialogue: 0,{_t(ini)},{_t(fin_evento)},Sub,,0,0,0,,{pop}{' '.join(partes)}")
    destino.write_text(cab + "\n".join(eventos) + "\n", encoding="utf-8")


# ---------------- render principal ----------------
def renderizar(escenas: list[dict], audio: Path, cfg: dict, destino: Path) -> Path:
    v, m = cfg["video"], cfg["marca"]
    W, H, FPS = v["ancho"], v["alto"], v["fps"]
    F = v["fuente"]
    c1, c2 = hex_rgb(m["color_primario"]), hex_rgb(m["color_secundario"])
    blanco = hex_rgb(m["color_texto"])
    oscuro = tuple(int(c * 0.35) for c in c1)
    total = escenas[-1]["fin"]
    n_frames = int(math.ceil(total * FPS))

    fondo = fondo_base(W, H, c1, oscuro)
    fotos = [preparar_foto(p, W - 160, int(H * 0.36)) for p in fotos_producto(cfg)]
    colchon = colchon_ilustrado(W - 220, c1, c2)
    logo = Image.open(RAIZ / v["logo"]).convert("RGBA") if v.get("logo") else None
    marca = capa_texto(m["nombre"], F, 40, W, (*blanco, 230))

    # Capas pre-renderizadas por escena
    for i, esc in enumerate(escenas):
        gancho = esc["visual"] == "gancho"
        esc["_titulo"] = capa_texto(esc["texto_pantalla"], F, 118 if gancho else 92, W - 120,
                                    (20, 20, 20) if gancho else blanco,
                                    fondo=(*c2, 255) if gancho else None)
        esc["_items"] = [capa_texto(("✓ " if esc["visual"] == "lista" else "") + it, F, 50, W - 120, (25, 25, 25),
                                    fondo=(255, 255, 255, 240), pad=26) for it in esc.get("items", [])]
        esc["_foto"] = fotos[i % len(fotos)] if fotos else None
        if esc["visual"] == "cta":
            esc["_cta"] = capa_texto(f"WhatsApp {m['whatsapp']}", F, 56, W - 160, (255, 255, 255),
                                     fondo=(37, 211, 102, 255), pad=30)
            esc["_dir"] = capa_texto(f"{m['nombre']} · {m['ciudad']}", F, 46, W - 160, (*blanco, 255))

    subs = destino.with_suffix(".ass")
    subtitulos_ass(escenas, cfg, subs)

    musica = next((p for p in (RAIZ / "assets").glob("musica.*")), None)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(audio)]
    if musica:
        cmd += ["-stream_loop", "-1", "-i", str(musica), "-filter_complex",
                "[2:a]volume=0.12[m];[1:a][m]amix=inputs=2:duration=first[a]", "-map", "0:v", "-map", "[a]"]
    fontsdir = str(Path(F).parent)
    cmd += ["-vf", f"ass={subs}:fontsdir={fontsdir}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", str(destino)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    log(f"Renderizando {n_frames} cuadros ({total:.1f}s)…")
    idx = 0
    for fr in range(n_frames):
        t = fr / FPS
        while idx < len(escenas) - 1 and t >= escenas[idx]["fin"]:
            idx += 1
        esc = escenas[idx]
        lt = t - esc["inicio"]                       # tiempo local de la escena
        dur = esc["fin"] - esc["inicio"]

        desplaz = int(200 + 200 * math.sin(t * 0.35))
        cuadro = fondo.crop((0, desplaz, W, desplaz + H)).copy()

        # Visual principal: foto con zoom lento (Ken Burns) o colchón ilustrado flotando
        if esc["visual"] in ("producto", "gancho", "cta", "comparacion") or not esc["_items"]:
            entrada = ease_out(lt / 0.4)
            cy = H * 0.43 + (1 - entrada) * 120
            if esc["_foto"] is not None:
                foto = esc["_foto"]
                z = 1 + 0.08 * (lt / max(dur, 0.1))
                fw, fh = W - 160, int(H * 0.36)
                rec = foto.resize((int(foto.width * z / 1.15), int(foto.height * z / 1.15)), Image.BILINEAR)
                ox, oy = (rec.width - fw) // 2, (rec.height - fh) // 2
                rec = rec.crop((ox, oy, ox + fw, oy + fh))
                mask = Image.new("L", (fw, fh), 0)
                ImageDraw.Draw(mask).rounded_rectangle((0, 0, fw, fh), 48, fill=255)
                rec.putalpha(mask)
                pegar_centrado(cuadro, rec, W / 2, cy, alfa=entrada)
            else:
                flota = 14 * math.sin(t * 2.2)
                pegar_centrado(cuadro, colchon, W / 2, cy + flota, escala=0.9 + 0.1 * entrada, alfa=entrada)

        # Ítems de lista/comparación que entran escalonados
        if esc["_items"]:
            n = len(esc["_items"])
            for k, capa in enumerate(esc["_items"]):
                aparece = (k + 0.3) * dur / (n + 1)
                p = ease_out_back((lt - aparece) / 0.35)
                y = H * 0.29 + k * (capa.height + 18) + capa.height / 2
                pegar_centrado(cuadro, capa, W / 2 + (1 - min(p, 1)) * 300, y, escala=0.85 + 0.15 * min(p, 1),
                               alfa=min(max(p, 0), 1))

        # Título con efecto "pop" (y sacudida en el gancho para frenar el scroll)
        p = ease_out_back(lt / 0.35)
        sx = sy = 0.0
        if esc["visual"] == "gancho" and lt < 0.6:
            sx, sy = 10 * math.sin(lt * 70), 6 * math.cos(lt * 55)
        pegar_centrado(cuadro, esc["_titulo"], W / 2 + sx, H * 0.165 + sy, escala=0.55 + 0.45 * p, alfa=min(lt / 0.12, 1))

        # CTA con latido
        if esc["visual"] == "cta":
            late = 1 + 0.05 * math.sin(lt * 7)
            pegar_centrado(cuadro, esc["_cta"], W / 2, H * 0.79, escala=ease_out_back(lt / 0.4) * late)
            pegar_centrado(cuadro, esc["_dir"], W / 2, H * 0.87, alfa=min(lt / 0.4, 1))

        # Barra de progreso + marca
        d = ImageDraw.Draw(cuadro)
        d.rectangle((0, 0, W, 12), fill=(255, 255, 255, 60))
        d.rectangle((0, 0, int(W * t / total), 12), fill=(*c2, 255))
        if logo:
            pegar_centrado(cuadro, logo.resize((220, int(220 * logo.height / logo.width))), W / 2, H - 110)
        else:
            pegar_centrado(cuadro, marca, W / 2, H - 100, alfa=0.9)

        proc.stdin.write(cuadro.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg falló al renderizar el video")
    log(f"Video listo: {destino}")
    return destino

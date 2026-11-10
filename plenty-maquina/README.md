# Máquina de contenido — Plenty Colchones Córdoba

Este sistema arma Reels y TikToks todos los días sin grabar ni editar. Vos solo aprobás los videos.

```
03:00 ─► 1. Busca los 30 reels más virales del nicho (hashtags y cuentas de config.toml)
         2. Los rankea con un puntaje viral (vistas + interacción + recencia) y elige los 5 de más potencial
         3. Descarga esos videos y los transcribe (Whisper)
         4. Claude analiza por qué funcionó cada uno y escribe guiones NUEVOS para Plenty,
            con un gancho fuerte en los primeros 3 segundos
         5. Genera la voz en off (ElevenLabs), las animaciones y los subtítulos palabra por palabra
         6. Deja los videos en salida/revision.html esperando tu aprobación
Cada 15' ► 7. Publica lo aprobado en Instagram, Facebook y TikTok según la agenda (12:30 / 19:00 / 21:30)
```

> Las referencias se usan **solo para aprender la estructura** (tipo de gancho, ritmo, formato).
> El sistema nunca copia el texto ni el video de otra cuenta: cada guion es original y habla de Plenty.

---

## 1. Instalación (una sola vez)

Necesitás Python 3.11 o más nuevo y `ffmpeg`.

```bash
cd plenty-maquina
pip install -r requirements.txt
cp .env.example .env        # y completá las claves (ver punto 2)
```

Probá que todo ande **sin claves** (genera un video de ejemplo con audio en silencio):

```bash
python -m maquina diario --prueba --cantidad 1
```

Después abrí `salida/revision.html` en el navegador.

## 2. Claves que necesitás (`.env`)

| Clave | Para qué | Dónde se saca |
|---|---|---|
| `APIFY_TOKEN` | Buscar reels virales en Instagram | apify.com → Settings → Integrations (plan gratis/≈USD 5 por mes) |
| `OPENAI_API_KEY` | Transcribir las referencias (Whisper) | platform.openai.com |
| `ANTHROPIC_API_KEY` | Analizar referencias y escribir guiones (Claude) | console.anthropic.com |
| `ELEVENLABS_API_KEY` y `ELEVENLABS_VOICE_ID` | Voz en off en español rioplatense | elevenlabs.io → elegí o cloná una voz |
| `META_ACCESS_TOKEN`, `META_IG_USER_ID`, `META_PAGE_ID` | Publicar en Instagram y Facebook | developers.facebook.com → app con `instagram_content_publish`, `pages_manage_posts` y `pages_read_engagement`. Instagram tiene que ser cuenta profesional y estar vinculada a la página |
| `TIKTOK_ACCESS_TOKEN` | Publicar en TikTok | developers.tiktok.com → Content Posting API. **Hasta que TikTok audite la app, los videos solo se pueden subir como privados** |

Si falta una clave, ese paso funciona en modo prueba y el resto sigue andando.

## 3. Personalizar (`config.toml`)

- **[marca]**: WhatsApp, dirección, tono, colores y CTA de Plenty.
- **[busqueda]**: hashtags, cuentas de referencia, vistas mínimas, antigüedad y pesos del puntaje viral.
- **[generacion]**: videos por día, duración y temas propios de respaldo.
- **[agenda]**: horarios de publicación, redes y si hace falta tu aprobación.
- **Fotos de producto**: poné JPG o PNG de los colchones en `assets/productos/` y aparecen animadas con zoom lento.
  Si no hay fotos, se usa una ilustración de colchón.
- **Logo**: en `[video] logo = "assets/logo.png"`.
- **Música**: un archivo `assets/musica.mp3` (libre de derechos) se mezcla bajito debajo de la voz.

## 4. Uso diario

```bash
python -m maquina diario              # lo que corre solo a las 3 AM
python -m maquina estado              # lista de videos y su estado
python -m maquina aprobar 1110-01     # aprueba un video (o "todos") y lo agenda en el próximo horario libre
python -m maquina rechazar 1110-02
python -m maquina publicar            # publica lo aprobado cuyo horario ya llegó
```

## 5. Dejarlo automático

En una PC siempre prendida o en un servidor chico (VPS de USD 5–6 por mes) con Linux o macOS:

```bash
./programar.sh
```

Esto instala dos tareas: a las 03:00 (hora de Córdoba) genera los videos del día, y cada 15 minutos publica los aprobados.

## Costos aproximados por video

| Paso | Costo |
|---|---|
| Claude (guion) | ≈ USD 0,05–0,15 |
| Whisper | ≈ USD 0,01 por referencia |
| ElevenLabs | ≈ 500 caracteres; el plan Starter alcanza para unos 60 videos por mes |
| Apify | ≈ USD 0,05–0,30 por búsqueda diaria |

## Estructura

```
maquina/buscar.py       búsqueda y puntaje viral
maquina/transcribir.py  descarga y transcripción
maquina/guion.py        análisis y guiones con Claude (salida JSON validada)
maquina/voz.py          voz en off y tiempos por palabra
maquina/render.py       animaciones, subtítulos y exportación MP4 1080x1920
maquina/agenda.py       cola de aprobación, horarios y página de revisión
maquina/publicar.py     Instagram Reels, Facebook Reels y TikTok
```

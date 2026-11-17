# Reglas permanentes · Videos con Claude (Duo0)

- Los videos sin editar están en `crudos/`, las referencias en `referencias/` y los terminados van a `exportados/`.
- Seguir siempre la skill `mi-estilo` (`.claude/skills/mi-estilo/SKILL.md`).
- Salida: MP4 vertical 1080x1920.
- Al editar: transcribir con Whisper (`whisper-cli`, modelo `/opt/whisper.cpp/models/ggml-large-v3-turbo-q5_0.bin`, idioma es, pista "Duo0"); cortar toda pausa de más de 0,1 segundos, muletillas y frases repetidas; agregar subtítulos en español, música y motion graphics (HyperFrames) según mi estilo, y usar lo que sirva de `referencias/`.
- Antes de renderizar, mostrar siempre un storyboard (qué se corta, qué textos y gráficos aparecen y en qué momento) y esperar mi aprobación.
- Después del render, aceptar correcciones en lenguaje simple, por ejemplo: "arrancá directo en el hook", "dejá esa imagen un segundo más", "agregá un punch-in cada vez que digo un número" o "sacá la parte donde repito la frase".
- Nunca borrar ni modificar los archivos originales de `crudos/`.
- Hablarme siempre en castellano simple.

## Herramientas de este entorno
- Voz en off: ElevenLabs (clave guardada en el entorno), voz Argie `arMlPrYpUo1XH5F2zM6R`.
- Clips con IA: Higgsfield API (Kling, image-to-video) solo a partir de fotos reales del equipo.
- Publicar: Supermetrics (Instagram @_duo0) como Reel de prueba, siempre con mi aprobación del video y del caption antes.
- Si este entorno se reinicia, puede hacer falta reinstalar whisper.cpp, yt-dlp y el modelo (ver historial de la sesión).

---
name: mi-estilo
description: Estilo de edición de video de Duo0 (Reels, TikTok, Shorts). Usar SIEMPRE que se edite, arme, subtitule o renderice un video para Duo0, o cuando se pida un storyboard, un Reel o un corte vertical.
---

# Estilo de video Duo0

Inspirado en los mejores Reels de @_duo0 (referencias en `referencias/`), pero es un sistema propio.

## Look
- Salida: MP4 vertical 1080x1920, 30 fps, H.264, audio AAC.
- Luz natural, sin filtros fuertes. Como mucho un retoque leve de brillo/contraste para que todos los clips se vean parejos.
- Paleta: **rosa Duo0 #D86E98** + **blanco**. Nada más.
- Tipografía: **Montserrat**.
  - Hook: línea 1 ExtraBold 68 px, línea 2 Regular 56 px, blanco con sombra suave.
  - Subtítulos: Bold 54 px, blanco, sombra oscura suave, máx. 2 líneas de ~6 palabras.
  - Etiquetas (POV, precios, reloj): caja blanca con texto rosa, o caja rosa con texto blanco, bordes redondeados.
- Zona segura: todo texto entre y=230 y y=1440, dejando libres los 230 px de la derecha. **Nunca texto en la parte de abajo.**

## Dos formatos (elegir según el video)
| | A · Explicado | B · Humor / satisfying |
|---|---|---|
| Cuándo | servicio, precio, franquicia, cómo funciona | chiste, POV, antes/después, satisfying |
| Audio | voz en off Argie (ElevenLabs, voice_id arMlPrYpUo1XH5F2zM6R) o voz real del equipo + música suave | solo música pegadiza |
| Cortes | cada toma dura lo que la frase (2,5–4 s) | cada ~1,5 s; satisfying hasta 4 s |
| Texto | subtítulos sincronizados con la voz | solo el texto del hook + etiquetas |

## Hook (primeros 3 segundos)
- Texto en pantalla desde el cuadro 1, par negrita + fina, tercio superior.
- Primera toma con movimiento (manos, espuma, agua). Nunca un plano quieto.
- Fórmula preferida: humor + número real ("Terapia de pareja: $45.000 / Nosotros: $35.900"). También: POV, dolor, satisfying, contraste.

## Gráficos recurrentes
- Reloj (ej. 10:00 → 11:00) en caja blanca con texto rosa, para videos de "una hora" / "en X horas".
- Marca de agua "DUO0" chica, 40% de opacidad, esquina superior.
- Placa final rosa #D86E98 con el logo DUO0 en blanco, 1 segundo, en todos los videos.
- Emojis: máximo 1 por texto, solo 🧹🧽✨.

## Audio
- Volumen final −14 LUFS.
- Con voz: voz adelante, música 15 dB por debajo.
- Subtítulos con Whisper local (gratis), pasando "Duo0" como pista para que no escriba "Duocero".

## Tono y textos
- Voseo, humor cotidiano de la casa, siempre un dato concreto (precio, tiempo, ambientes, "+1.000 limpiezas por mes").
- CTA con palabra clave: "Comentá HORA" (clientes), "Comentá INFO" (franquicias).
- Datos de marca y precios: ver `../../../duo0-audio/voice.md` si existe; verificar vigencia de precios antes de publicar.

## Nunca
- Texto abajo de la pantalla.
- Frases genéricas ("viví la diferencia", "limpieza, confianza y atención…").
- Humor a costa del equipo.
- Personas hechas con IA. Higgsfield solo para animar fotos reales del equipo de Duo0.

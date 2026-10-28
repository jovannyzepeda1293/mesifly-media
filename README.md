# mesifly-media

Imágenes y videos públicos para las redes sociales de Mesifly (Instagram, Facebook, TikTok y YouTube), publicados con Metricool.

## Estructura
- `posts/AAAA-MM-DD-slug/` — piezas de cada artículo del blog:
  - `feed_XX.jpg` — carrusel 1080×1350 (Instagram y Facebook)
  - `<slug>-short.mp4` — video vertical 1080×1920 (TikTok y YouTube Shorts)
  - `spec.json` — textos de las diapositivas usados para generarlas
- `tools/make_social.py` — generador: `python3 tools/make_social.py spec.json carpeta_salida`
- `tools/fonts/` — Poppins (SIL Open Font License)

Metricool descarga los archivos desde
`https://raw.githubusercontent.com/jovannyzepeda1293/mesifly-media/master/posts/<carpeta>/<archivo>`.

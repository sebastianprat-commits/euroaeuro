# Euro a Euro — web

Sitio estático de `euroaeuro.eu`. El contenido son archivos Markdown; el HTML se genera
con `construir_web.py` y se publica en GitHub Pages en cada `push`.

## Cómo está organizado

```
contenido/publicado/*.md   los artículos, uno por archivo
contenido/borradores/      lo que aún no se publica (aquí no se lee)
construir_web.py           generador: Markdown → HTML, calculadoras, sitemap
limpieza.py                limpieza de los artículos (cortes, restos)
web/                       salida generada (no se versiona)
```

## Verlo en tu PC

```bat
cd C:\AI\Proyectos\Web\euroaeuro
.venv\Scripts\python.exe construir_web.py
.venv\Scripts\python.exe -m http.server 8000 --directory web
```

Y abre `http://localhost:8000`. Hace falta servir por HTTP: el CSS usa rutas absolutas
(`/assets/...`) y con `file://` no carga.

## Publicar

1. Commit y push a `main`.
2. GitHub Actions construye y despliega solo.
3. En el repositorio: **Settings → Pages → Source: GitHub Actions**.
4. Dominio: `euroaeuro.eu` (el workflow escribe el archivo `CNAME`).
   En el registrador: registro `A` a las IP de GitHub Pages y `CNAME www` a
   `usuario.github.io`.

## Escribir un artículo

Crea `contenido/publicado/mi-titulo.md` con esta cabecera:

```markdown
# Título del artículo

## Meta descripción
Una frase de 150 caracteres que resuma el artículo.

El cuerpo en Markdown, con ## para las secciones.
```

El nombre del archivo es el slug de la URL. No lo cambies después de publicar.

## Reglas de la casa

- Un artículo = un archivo. Nada de contenido dentro del Python.
- Si un artículo no está en `publicado/`, no existe para la web.
- Antes de publicar en cantidad, revisar: AdSense penaliza el volumen sin valor.
  La ventaja aquí es el criterio de un profesional con 20 años de experiencia.

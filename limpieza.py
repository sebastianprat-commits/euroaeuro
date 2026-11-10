"""
limpieza.py — prepara un borrador en Markdown antes de publicarlo o revisarlo.

  - Quita del cuerpo la sección "Meta descripción" (y su separador ---).
  - Quita del final la lista de etiquetas y la devuelve aparte, para
    enviarla como etiquetas reales de Blogger.
  - Detecta artículos cortados a mitad de texto (límite de longitud).
"""

import re

RE_META = re.compile(
    r"^\s*(?:#+\s*)?\**\s*meta\s*descripci[oó]n\s*\**\s*:?\s*\**\s*(.*?)\s*$",
    re.IGNORECASE,
)
RE_ETIQ = re.compile(
    r"^\s*(?:#+\s*)?\**\s*etiquetas(?:\s+(?:para|de|sugeridas)[^:\n]*)?\s*\**\s*:?\s*\**\s*(.*?)\s*$",
    re.IGNORECASE,
)
RE_SEP = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")

MAX_ETIQUETAS = 8
MAX_CARACTERES_ETIQUETAS = 200  # límite de Blogger por entrada


def _quitar_meta(resto):
    meta = ""
    for i, linea in enumerate(resto[:15]):
        m = RE_META.match(linea)
        if not m:
            continue
        meta = m.group(1)
        fin = i + 1
        if not meta:  # la descripción va en la línea siguiente
            j = i + 1
            while j < len(resto) and not resto[j].strip():
                j += 1
            if j < len(resto) and not resto[j].lstrip().startswith("#"):
                meta = resto[j].strip()
                fin = j + 1
        k = fin
        while k < len(resto) and not resto[k].strip():
            k += 1
        if k < len(resto) and RE_SEP.match(resto[k]):
            fin = k + 1
        return resto[:i] + resto[fin:], meta
    return resto, meta


def _limpiar_etiqueta(texto):
    return re.sub(r"[#*_`\"“”]", "", texto).strip(" -•\t")


def parsear_etiquetas(bruto):
    """Convierte 'a, b; c' en una lista limpia, sin duplicados y dentro de los límites de Blogger."""
    etiquetas, vistas, total = [], set(), 0
    for trozo in re.split(r"[,;\n]", bruto):
        etiqueta = _limpiar_etiqueta(trozo)
        if not etiqueta or etiqueta.lower() in vistas:
            continue
        if len(etiquetas) >= MAX_ETIQUETAS or total + len(etiqueta) > MAX_CARACTERES_ETIQUETAS:
            break
        etiquetas.append(etiqueta)
        vistas.add(etiqueta.lower())
        total += len(etiqueta) + 1
    return etiquetas


def _quitar_etiquetas(resto):
    for i in range(len(resto) - 1, max(len(resto) - 16, -1), -1):
        m = RE_ETIQ.match(resto[i])
        if not m:
            continue
        bruto = m.group(1)
        if not bruto:  # lista en las líneas siguientes (comas o viñetas)
            bruto = ",".join(l.strip() for l in resto[i + 1:] if l.strip())
        return resto[:i], parsear_etiquetas(bruto)
    return resto, []


def limpiar_articulo(texto):
    """Devuelve (texto_limpio, meta_descripcion, etiquetas)."""
    lineas = texto.strip().split("\n")
    titulo, resto = lineas[0], lineas[1:]
    resto, meta = _quitar_meta(resto)
    resto, etiquetas = _quitar_etiquetas(resto)
    while resto and (not resto[-1].strip() or RE_SEP.match(resto[-1])):
        resto.pop()
    return "\n".join([titulo] + resto), meta, etiquetas


def parece_cortado(texto_limpio):
    """True si el texto acaba a mitad de frase (típico de un corte por longitud)."""
    lineas = [l.strip() for l in texto_limpio.strip().splitlines() if l.strip()]
    if not lineas:
        return True
    return lineas[-1][-1] not in '.?!:;)"”»*|…'

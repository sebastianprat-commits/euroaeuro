"""
Generador local de artículos para Euro a Euro
=============================================
Escribe un borrador con LM Studio (coste 0) siguiendo el formato exacto que
espera construir_web.py, y lo deja en contenido/borradores/ para que lo revises.

Uso:
    python generar.py --lista
    python generar.py --siguiente 1
    python generar.py --tema "Cómo ahorrar con poco dinero" --categoria ahorra
    python generar.py --siguiente 3 --modelo qwen/qwen3.8-27b

Nada se publica solo: mover el .md de borradores/ a publicado/ es tu decisión.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import httpx

AQUI = Path(__file__).resolve().parent
TEMAS = AQUI / "temas.csv"
BORRADORES = AQUI / "contenido" / "borradores"
PUBLICADOS = AQUI / "contenido" / "publicado"

LM = "http://127.0.0.1:1234/v1"
MODELO_PREFERIDO = "qwen/qwen3.5-9b"

AVISO = (
    "*Este artículo tiene un propósito informativo y educativo general. No constituye "
    "asesoramiento financiero personalizado. Para decisiones concretas sobre tu situación "
    "económica, lo recomendable es consultar con un profesional que pueda analizar tu caso "
    "particular.*"
)

SISTEMA = (
    "Eres redactor de Euro a Euro, una web española de educación financiera para personas sin "
    "conocimientos técnicos. Escribes en español de España, con tono cercano, directo y "
    "riguroso. Explicas el porqué de las cosas, no solo el qué. No usas jerga innecesaria, no "
    "tratas al lector como un niño y no prometes rentabilidades."
)


def log(msg: str = "") -> None:
    print(msg, flush=True)


def slug(texto: str, limite: int = 70) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto).strip("-")
    if len(texto) > limite:
        texto = texto[:limite].rsplit("-", 1)[0]
    return texto


def modelo_chat(forzado: str | None) -> str:
    if forzado:
        return forzado
    try:
        r = httpx.get(f"{LM}/models", timeout=10)
        r.raise_for_status()
    except Exception as exc:
        raise SystemExit(
            "No puedo conectar con LM Studio en localhost:1234.\n"
            "  -> Abre LM Studio y activa el servidor local."
        ) from exc
    ids = [m["id"] for m in r.json()["data"] if "embed" not in m["id"].lower()]
    if not ids:
        raise SystemExit("LM Studio no tiene ningún modelo de chat cargado.")
    return MODELO_PREFERIDO if MODELO_PREFERIDO in ids else ids[0]


def instrucciones(tema: str, categoria: str, palabras_clave: str, notas: str) -> str:
    return f"""Escribe un artículo completo sobre: "{tema}".

Contexto interno (no lo repitas literalmente): categoría "{categoria}"; palabras clave: {palabras_clave}; notas del editor: {notas}

FORMATO EXACTO (respétalo al milímetro):

# Título del artículo

## Meta descripción
Una sola frase de entre 140 y 160 caracteres que resuma el artículo.

{AVISO}

Dos o tres párrafos de introducción que planteen el problema real del lector.

De cuatro a seis secciones. Cada una empieza con un encabezado "## " propio, escrito por ti,
específico del tema, y sigue con dos o tres párrafos. Los encabezados no se numeran y no se
repiten entre sí.

## En resumen
- Primera idea clave.
- Segunda idea clave.
- Tercera idea clave.

Etiquetas: palabra1, palabra2, palabra3, palabra4, palabra5

REGLAS:
1. Entre 900 y 1300 palabras en total.
2. De 4 a 6 secciones con "## ". No uses "# " salvo en el título.
3. Los encabezados los inventas tú para este tema concreto. Prohibido usar "Primera sección",
   "Segunda sección", "Introducción", "Conclusión" o cualquier texto de esta plantilla como
   encabezado. Prohibido copiar los encabezados de otro artículo.
4. Escribe íntegramente en español. Ni una palabra en inglés (nada de "affordable", "cash flow",
   "mindset", "financial").
5. Párrafos de 2 a 4 frases. Varía la longitud de las frases: alguna corta, alguna más larga.
6. Incluye al menos un ejemplo numérico con cifras redondas y di expresamente que es ilustrativo.
7. No inventes estadísticas, informes, ni cifras oficiales. No cites fuentes que no existan.
8. No nombres bancos, fondos, productos comerciales ni marcas.
9. No recomiendes comprar ni vender nada concreto.
10. No prometas rentabilidades ni uses "hazte rico", "fácil" o "sin riesgo".
11. No hables de tipos de interés actuales ni de la situación del mercado: cambian y el texto envejece.
12. Empieza directamente por "# ". Nada de "Aquí tienes el artículo" ni comentarios finales.
13. Termina con la línea de etiquetas, sin nada después."""


def limpiar(texto: str) -> str:
    texto = texto.strip()
    # Quitar preámbulos típicos del modelo
    texto = re.sub(r"^(Aquí tienes|Claro|Por supuesto)[^\n]*\n+", "", texto, flags=re.I)
    # Quitar bloques de código envolventes
    if texto.startswith("```"):
        texto = re.sub(r"^```[a-z]*\n", "", texto)
        texto = re.sub(r"\n```\s*$", "", texto)
    # Asegurar que empieza en el título
    m = re.search(r"^# .+$", texto, re.M)
    if m and m.start() > 0:
        texto = texto[m.start():]
    return texto.strip()


RE_META = re.compile(r"^##\s*meta\s*descripci[oó]n\s*:?\s*\n+(.+)$", re.I | re.M)
RE_ETIQ = re.compile(r"^\s*etiquetas\s*:\s*(.+)$", re.I | re.M)
RE_AVISO = re.compile(
    r"\*?Este artículo tiene un propósito informativo.*?particular\.\*?", re.I | re.S
)


def extraer(texto: str) -> tuple[str, str, str, str]:
    """Separa título, cuerpo, meta y etiquetas de lo que ha devuelto el modelo."""
    lineas = texto.splitlines()
    titulo = lineas[0].lstrip("#").strip()
    cuerpo = "\n".join(lineas[1:]).strip()

    meta = ""
    m = RE_META.search(cuerpo)
    if m:
        meta = m.group(1).strip()
        cuerpo = (cuerpo[: m.start()] + "\n\n" + cuerpo[m.end():]).strip()

    etiquetas = ""
    m = RE_ETIQ.search(cuerpo)
    if m:
        etiquetas = m.group(1).strip()
        cuerpo = cuerpo[: m.start()].strip()

    cuerpo = RE_AVISO.sub("", cuerpo).strip()
    return titulo, cuerpo, meta, etiquetas


def derivar_meta(cuerpo: str, limite: int = 155) -> str:
    """Si el modelo no da una meta válida, se saca del primer párrafo."""
    plano = re.sub(r"[#*_>`\[\]]", "", cuerpo)
    plano = re.sub(r"\s+", " ", plano).strip()
    if len(plano) <= limite:
        return plano.rstrip(" ,;:")
    recorte = plano[:limite]
    recorte = recorte.rsplit(" ", 1)[0].rstrip(" ,;:")
    return recorte + "."


def componer(titulo: str, cuerpo: str, meta: str, etiquetas: str) -> str:
    """Monta el archivo con el formato exacto que espera el generador de la web."""
    partes = [f"# {titulo}", "", "## Meta descripción", meta, "", AVISO, "", cuerpo]
    if etiquetas:
        partes += ["", f"Etiquetas: {etiquetas}"]
    return "\n".join(partes).strip() + "\n"


def validar(texto: str) -> list[str]:
    problemas = []
    lineas = [l for l in texto.splitlines() if l.strip()]
    if not lineas or not lineas[0].startswith("# "):
        problemas.append("no empieza por un título '# '")
    if "## meta descripción" not in texto.lower():
        problemas.append("falta la sección '## Meta descripción'")
    if "no constituye asesoramiento financiero personalizado" not in texto.lower():
        problemas.append("falta la frase de aviso legal")
    palabras = len(texto.split())
    if palabras < 700:
        problemas.append(f"demasiado corto ({palabras} palabras)")
    if palabras > 1800:
        problemas.append(f"demasiado largo ({palabras} palabras)")
    if not re.search(r"^## ", texto, re.M):
        problemas.append("no hay secciones '## '")
    if re.search(r"^##\s*(primera|segunda|tercera|cuarta|quinta|sexta)\s+secci[oó]n", texto, re.I | re.M):
        problemas.append("encabezados de plantilla ('Primera sección')")
    genericos = ("la regla del 30 %", "cómo calcular tu capacidad real", "los gastos que se olvidan",
                 "aquí va", "encabezado", "contenido...", "introducción", "conclusión")
    for h in re.findall(r"^##\s*(.+)$", texto, re.M):
        if h.strip().lower().startswith(genericos):
            problemas.append(f"encabezado genérico o copiado: '{h.strip()}'")
            break
    anglicismos = re.findall(
        r"\b(affordable|cash flow|mindset|financial|budget|income|savings)\b", texto, re.I
    )
    if anglicismos:
        problemas.append("anglicismos: " + ", ".join(sorted(set(a.lower() for a in anglicismos))))
    # El cierre se mide en la última línea de texto, ignorando las etiquetas
    cierre = lineas[-1]
    if cierre.lower().startswith("etiquetas:") and len(lineas) > 1:
        cierre = lineas[-2]
    if cierre.strip()[-1] not in '.?!:;")”»*…-':
        problemas.append("el texto acaba a mitad de frase")
    m = re.search(r"##\s*meta descripci[oó]n\s*\n+(.+)", texto, re.I)
    if m:
        largo = len(m.group(1).strip())
        if not 100 <= largo <= 200:
            problemas.append(f"meta descripción de {largo} caracteres (se piden 140-160)")
    return problemas


def generar(tema: str, categoria: str, palabras_clave: str, notas: str,
            modelo: str) -> tuple[str, str]:
    cuerpo = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": SISTEMA},
            {"role": "user", "content": instrucciones(tema, categoria, palabras_clave, notas)},
        ],
        "temperature": 0.6,
        "top_p": 0.9,
        "max_tokens": 3200,
        "stream": True,
    }
    with httpx.stream("POST", f"{LM}/chat/completions", json=cuerpo,
                      timeout=httpx.Timeout(900.0, connect=10.0)) as r:
        r.raise_for_status()
        trozos = []
        for linea in r.iter_lines():
            if not linea.startswith("data: "):
                continue
            datos = linea[6:].strip()
            if datos == "[DONE]":
                break
            try:
                delta = json.loads(datos)["choices"][0]["delta"]
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
            trozos.append(delta.get("content") or "")
    return "".join(trozos)


def leer_temas() -> list[dict]:
    if not TEMAS.exists():
        raise SystemExit(f"No existe {TEMAS.name}")
    with open(TEMAS, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def guardar_temas(filas: list[dict]) -> None:
    campos = ["tema", "categoria", "palabras_clave", "notas", "estado"]
    with open(TEMAS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for fila in filas:
            w.writerow({k: fila.get(k, "") for k in campos})


def existe(slug_txt: str) -> bool:
    for carpeta in (BORRADORES, PUBLICADOS):
        if (carpeta / f"{slug_txt}.md").exists():
            return True
    return False


def procesar(tema: str, categoria: str, claves: str, notas: str, modelo: str) -> bool:
    log(f"\n>> {tema}")
    inicio = time.time()
    bruto = generar(tema, categoria, claves, notas, modelo)
    texto = limpiar(bruto)
    if not texto:
        log("   ERROR: el modelo no devolvió texto")
        return False

    titulo, cuerpo, meta_modelo, etiquetas = extraer(texto)
    if not cuerpo:
        log("   ERROR: el texto no tiene cuerpo tras el título")
        return False
    meta = meta_modelo if 100 <= len(meta_modelo) <= 200 else derivar_meta(cuerpo)
    texto = componer(titulo, cuerpo, meta, etiquetas)
    problemas = validar(texto)

    nombre = slug(titulo)
    destino = BORRADORES / f"{nombre}.md"

    if problemas:
        rechazo = BORRADORES / "_rechazados"
        rechazo.mkdir(parents=True, exist_ok=True)
        (rechazo / f"{nombre}.md").write_text(texto, encoding="utf-8")
        log(f"   RECHAZADO ({'; '.join(problemas)})")
        log(f"   guardado en borradores/_rechazados/{nombre}.md para revisar")
        return False

    BORRADORES.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    (BORRADORES / f"{nombre}.json").write_text(
        json.dumps({"categoria": categoria, "tema": tema, "modelo": modelo},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    palabras = len(texto.split())
    log(f"   OK en {time.time()-inicio:.0f}s · {palabras} palabras · {nombre}.md")
    return True


def main() -> None:
    p = argparse.ArgumentParser(description="Genera artículos con LM Studio")
    p.add_argument("--lista", action="store_true", help="ver temas pendientes")
    p.add_argument("--siguiente", type=int, default=0, metavar="N",
                   help="generar los N siguientes temas pendientes")
    p.add_argument("--tema", help="generar un tema suelto")
    p.add_argument("--categoria", default="ahorra", help="categoría del tema suelto")
    p.add_argument("--modelo", help="forzar un modelo de LM Studio")
    args = p.parse_args()

    if args.lista:
        filas = leer_temas()
        pend = [f for f in filas if f.get("estado", "pendiente") == "pendiente"]
        log(f"{len(pend)} temas pendientes de {len(filas)}:")
        for i, f in enumerate(pend, 1):
            log(f"  {i:2d}. [{f['categoria']}] {f['tema']}")
        return

    modelo = modelo_chat(args.modelo)

    if args.tema:
        ok = procesar(args.tema, args.categoria, "", "ninguna", modelo)
        sys.exit(0 if ok else 1)

    if not args.siguiente:
        p.print_help()
        return

    filas = leer_temas()
    pendientes = [f for f in filas if f.get("estado", "pendiente") == "pendiente"]
    if not pendientes:
        raise SystemExit("No quedan temas pendientes. Añade filas a temas.csv.")

    hechos = 0
    for fila in pendientes[: args.siguiente]:
        if existe(slug(fila["tema"])):
            log(f"\n>> {fila['tema']}\n   ya existe, se salta")
            fila["estado"] = "generado"
            continue
        if procesar(fila["tema"], fila.get("categoria", ""), fila.get("palabras_clave", ""),
                     fila.get("notas", ""), modelo):
            fila["estado"] = "generado"
            hechos += 1
        guardar_temas(filas)

    guardar_temas(filas)
    log(f"\nGenerados {hechos} de {min(args.siguiente, len(pendientes))}.")
    log(f"Revisa los borradores en: {BORRADORES}")
    log("Para publicar: muévelos a contenido/publicado/ y ejecuta construir_web.py")


if __name__ == "__main__":
    main()

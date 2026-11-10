"""
Generador local de artículos para Euro a Euro
=============================================
Escribe un borrador con LM Studio (coste 0) siguiendo el formato exacto que
espera construir_web.py, y lo deja en contenido/borradores/ para que lo revises.

Uso:
    python generar.py --lista
    python generar.py --siguiente 1
    python generar.py --tema "Cómo ahorrar con poco dinero" --categoria ahorra
    python generar.py --siguiente 3 --modelo qwen/qwen3.5-9b   (borradores rápidos)

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
MODELO_PREFERIDO = "qwen/qwen3.8-27b"

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

## Encabezado propio 1
Dos o tres párrafos. Cuanto más concreto, mejor: ejemplos, situaciones y matices.

## Encabezado propio 2
Dos o tres párrafos.

## Encabezado propio 3
Dos o tres párrafos.

## Ejemplo con cifras
Una tabla en Markdown con cabecera, entre 4 y 6 filas y una fila final de total:

| Concepto | Importe | Frecuencia | Coste anual |
|---|---|---|---|
| Ejemplo uno | 30 € | Mensual | 360 € |
| Ejemplo dos | 5 € | Semanal | 260 € |
| **Total** | | | **620 €** |

Dos párrafos explicando qué enseña la tabla. Di expresamente que las cifras son ilustrativas.

## Errores comunes a evitar
- **Error concreto.** Por qué es un error y qué hacer en su lugar.
- **Otro error concreto.** Explicación.
- **Tercer error.** Explicación.
- **Cuarto error.** Explicación.

## Preguntas frecuentes
**¿Primera pregunta del lector?**
Respuesta de dos o tres frases, directa.

**¿Segunda pregunta?**
Respuesta.

**¿Tercera pregunta?**
Respuesta.

**¿Cuarta pregunta?**
Respuesta.

## Para cerrar
Dos párrafos de cierre, en prosa y sin listas. Una idea que se quede con el lector.

Etiquetas: palabra1, palabra2, palabra3, palabra4, palabra5

REGLAS:
1. Entre 1400 y 1900 palabras. Si te quedas corto, profundiza en los matices, no repitas ideas.
2. Seis a ocho secciones con "## ", además del título y de la meta descripción.
3. Los encabezados los inventas tú para este tema concreto. Prohibido usar "Primera sección",
   "Segunda sección", "Introducción" o cualquier texto de esta plantilla como encabezado.
4. La tabla es obligatoria, con cabecera y fila de total. Las cifras, redondas e ilustrativas.
5. La sección "## Errores comunes a evitar" es obligatoria, con cuatro puntos en negrita.
6. La sección "## Preguntas frecuentes" es obligatoria, con cuatro preguntas en negrita y respuesta.
7. Escribe íntegramente en español. Ni una palabra en inglés (nada de "affordable", "cash flow",
   "mindset", "financial").
8. Párrafos de 2 a 4 frases. Varía la longitud: alguna frase corta, alguna más larga.
9. No inventes estadísticas, informes, ni cifras oficiales. No cites fuentes que no existan.
10. No nombres bancos, fondos, productos comerciales ni marcas.
11. No recomiendes comprar ni vender nada concreto.
12. No prometas rentabilidades ni uses "hazte rico", "fácil" o "sin riesgo".
13. No hables de tipos de interés actuales ni de la situación del mercado: cambian y el texto envejece.
14. Empieza directamente por "# ". Nada de "Aquí tienes el artículo" ni comentarios finales.
15. Termina con la línea de etiquetas, sin nada después."""


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


def pulir_meta(meta: str) -> str:
    """Quita aperturas genéricas tipo 'Descubre cómo...' y normaliza espacios."""
    meta = " ".join(meta.split()).strip().strip('"“”')
    for inicio in ("Descubre cómo ", "Descubre ", "Aprende cómo ", "Aprende "):
        if meta.lower().startswith(inicio.lower()):
            meta = meta[len(inicio):]
            meta = meta[0].upper() + meta[1:] if meta else meta
            break
    return meta


def componer(titulo: str, cuerpo: str, meta: str, etiquetas: str) -> str:
    """Monta el archivo con el formato exacto que espera el generador de la web."""
    partes = [f"# {titulo}", "", "## Meta descripción", meta, "", AVISO, "", cuerpo]
    if etiquetas:
        partes += ["", f"Etiquetas: {etiquetas}"]
    return "\n".join(partes).strip() + "\n"


def reescribir_meta(titulo: str, cuerpo: str, modelo: str) -> str:
    """Segunda llamada corta: una meta que no repita el arranque del artículo."""
    peticion = (
        "Escribe UNA sola frase completa, de entre 140 y 160 caracteres, que resuma este "
        "artículo y sirva como meta descripción para buscadores.\n\n"
        "Reglas:\n"
        "- Español de España, tono directo.\n"
        "- No copies ni parafrasees la primera frase del artículo.\n"
        "- La frase debe estar terminada: sujeto, verbo y punto final.\n"
        "- Sin comillas, sin punto y coma, sin dos puntos.\n"
        "- Responde solo con la frase, sin nada más.\n\n"
        f"Título: {titulo}\n\n"
        f"Artículo:\n{cuerpo[:2500]}"
    )
    for intento in (1, 2):
        cuerpo_peticion = {
            "model": modelo,
            "messages": [{"role": "user", "content": peticion}],
            "temperature": 0.5 + 0.1 * intento,
            "max_tokens": 300,
        }
        try:
            r = httpx.post(f"{LM}/chat/completions", json=cuerpo_peticion,
                           timeout=httpx.Timeout(300.0, connect=10.0))
            r.raise_for_status()
            texto = r.json()["choices"][0]["message"].get("content") or ""
        except Exception:
            return ""
        texto = " ".join(texto.split()).strip().strip('"“”')
        if 120 <= len(texto) <= 200 and texto.endswith((".", "!", "?")):
            return texto
        peticion += "\n\nLa respuesta anterior quedó incompleta. Escribe una frase entera y cerrada."
    return ""


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
    if palabras < 1200:
        problemas.append(f"demasiado corto ({palabras} palabras)")
    if palabras > 2600:
        problemas.append(f"demasiado largo ({palabras} palabras)")
    if texto.count("|---") < 1:
        problemas.append("falta la tabla de ejemplo")
    secciones = len(re.findall(r"^## ", texto, re.M))
    if secciones < 6:
        problemas.append(f"solo {secciones} secciones (se piden 6-8)")
    if "errores comunes" not in texto.lower():
        problemas.append("falta la sección 'Errores comunes a evitar'")
    if "preguntas frecuentes" not in texto.lower():
        problemas.append("falta la sección 'Preguntas frecuentes'")
    if len(re.findall(r"\*\*¿[^*]+\?\*\*", texto)) < 3:
        problemas.append("menos de 3 preguntas frecuentes en negrita")
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
        "max_tokens": 4800,
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
    # Si la meta repite el arranque del artículo, se reescribe con una llamada corta
    if meta and meta.lower()[:70] in cuerpo.lower():
        log("   la meta repite el inicio; reescribiendo…")
        nueva = reescribir_meta(titulo, cuerpo, modelo)
        if 100 <= len(nueva) <= 200:
            meta = nueva
    meta = pulir_meta(meta)
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

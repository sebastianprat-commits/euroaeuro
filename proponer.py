"""
Propuesta automática de temas nuevos
====================================
Pide al modelo local una tanda de temas que aún no existan y los añade a temas.csv
como pendientes. Evita repetir los publicados, los que están en cola y los rechazados.

Uso:
    python proponer.py            # 10 temas nuevos
    python proponer.py --n 20
    python proponer.py --ver      # solo enseña qué propondría, sin guardar
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

import httpx

from generar import AQUI, BORRADORES, LM, PUBLICADOS, TEMAS, log, modelo_chat

CATEGORIAS = {"ordena", "ahorra", "invierte"}
CAMPOS = ["tema", "categoria", "palabras_clave", "notas", "estado"]

ANGLICISMOS = re.compile(
    r"\b(affordable|cash flow|mindset|financial|budget|income|savings|lifestyle creep|"
    r"side hustle|money|personal finance|net worth|paycheck)\b",
    re.I,
)

SISTEMA = (
    "Eres editor de contenidos de Euro a Euro, una web española de educación financiera "
    "para personas sin conocimientos técnicos. Conoces qué busca la gente en Google y qué "
    "temas se pueden responder con criterio sin depender de la actualidad."
)


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", texto)


def palabras_clave_tema(texto: str) -> set[str]:
    vacias = {"de", "la", "el", "los", "las", "que", "y", "en", "un", "una", "para", "por",
              "con", "como", "tu", "tus", "su", "sus", "al", "del", "se", "es", "o", "a"}
    return {p for p in normalizar(texto).split() if len(p) > 2 and p not in vacias}


def parecido(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def temas_existentes() -> list[str]:
    titulos = []
    for carpeta in (PUBLICADOS, BORRADORES):
        for ruta in sorted(carpeta.glob("*.md")):
            primera = ruta.read_text(encoding="utf-8").splitlines()[0]
            titulos.append(primera.lstrip("#").strip())
    if TEMAS.exists():
        with open(TEMAS, encoding="utf-8-sig", newline="") as f:
            titulos += [fila["tema"] for fila in csv.DictReader(f) if fila.get("tema")]
    return titulos


def pedir(n: int, modelo: str, existentes: list[str]) -> list[dict]:
    lista = "\n".join(f"- {t}" for t in existentes[-120:])
    peticion = f"""Propón {n} temas nuevos para artículos de finanzas personales.

NO repitas ni reformules ninguno de estos temas, que ya existen o están en cola:
{lista}

Requisitos de cada tema:
- Concreto y con intención de búsqueda real (alguien lo escribiría en Google).
- Que se pueda responder con criterio atemporal, sin depender de tipos de interés ni de
  productos concretos.
- Que no sea una variación de otro tema de la lista.
- Que aporte algo distinto: un ángulo práctico, un error frecuente, una decisión concreta.

Devuelve SOLO un array JSON, sin texto antes ni después, con esta forma exacta:
[
  {{"tema": "Título del artículo", "categoria": "ahorra", "palabras_clave": "palabra1, palabra2, palabra3", "notas": "Enfoque concreto del artículo en una frase."}}
]

"categoria" solo puede ser: ordena, ahorra o invierte."""

    cuerpo = {
        "model": modelo,
        "messages": [{"role": "system", "content": SISTEMA},
                     {"role": "user", "content": peticion}],
        "temperature": 0.9,
        "max_tokens": 3000,
    }
    r = httpx.post(f"{LM}/chat/completions", json=cuerpo,
                   timeout=httpx.Timeout(900.0, connect=10.0))
    r.raise_for_status()
    texto = r.json()["choices"][0]["message"].get("content") or ""
    texto = re.sub(r"^```[a-z]*\n", "", texto.strip())
    texto = re.sub(r"\n```$", "", texto).strip()
    inicio, fin = texto.find("["), texto.rfind("]")
    if inicio == -1 or fin == -1:
        raise SystemExit(f"El modelo no devolvió un JSON válido:\n{texto[:400]}")
    try:
        datos = json.loads(texto[inicio:fin + 1])
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON incompleto ({exc}). Prueba con --n más bajo.") from exc
    return [d for d in datos if isinstance(d, dict) and d.get("tema")]


def main() -> None:
    p = argparse.ArgumentParser(description="Propone temas nuevos y los añade a temas.csv")
    p.add_argument("--n", type=int, default=10, help="cuántos temas proponer (10)")
    p.add_argument("--ver", action="store_true", help="no guardar, solo mostrar")
    p.add_argument("--modelo", help="forzar un modelo de LM Studio")
    args = p.parse_args()

    modelo = modelo_chat(args.modelo)
    existentes = temas_existentes()
    log(f"Modelo: {modelo}")
    log(f"Temas ya existentes: {len(existentes)}. Pidiendo {args.n} nuevos…\n")

    propuestas = pedir(args.n, modelo, existentes)
    conocidos = {normalizar(t): palabras_clave_tema(t) for t in existentes}
    aceptados: list[dict] = []

    for propuesta in propuestas:
        tema = propuesta["tema"].strip()
        categoria = (propuesta.get("categoria") or "ahorra").strip().lower()
        if categoria not in CATEGORIAS:
            categoria = "ahorra"
        if ANGLICISMOS.search(tema):
            log(f"  descartado (anglicismo): {tema}")
            continue
        claves = palabras_clave_tema(tema)
        duplicado = None
        for texto, palabras in conocidos.items():
            if parecido(claves, palabras) >= 0.6:
                duplicado = texto
                break
        if duplicado or any(parecido(claves, palabras_clave_tema(a["tema"])) >= 0.6 for a in aceptados):
            log(f"  descartado (parecido a «{duplicado or 'otro propuesto'}»): {tema}")
            continue
        aceptados.append({"tema": tema, "categoria": categoria,
                          "palabras_clave": propuesta.get("palabras_clave", ""),
                          "notas": propuesta.get("notas", ""), "estado": "pendiente"})
        log(f"  + [{categoria}] {tema}")

    if not aceptados:
        log("\nNo hay ninguno aceptable. Prueba otra vez o sube --n.")
        return

    if args.ver:
        log(f"\n{len(aceptados)} temas aceptables (no guardados, --ver).")
        return

    filas = []
    if TEMAS.exists():
        with open(TEMAS, encoding="utf-8-sig", newline="") as f:
            filas = list(csv.DictReader(f))
    filas.extend(aceptados)
    with open(TEMAS, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS, quoting=csv.QUOTE_ALL)
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({k: fila.get(k, "") for k in CAMPOS})

    log(f"\nAñadidos {len(aceptados)} temas. Total en cola: {len(filas)} filas.")


if __name__ == "__main__":
    main()

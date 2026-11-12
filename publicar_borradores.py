"""
Publica los borradores de euroaeuro que estén pendientes.
Mueve los .md de contenido/borradores/ a contenido/publicado/, reconstruye
la web y hace commit y push.

Uso:
    python publicar_borradores.py
    python publicar_borradores.py --listar   (solo enseña qué hay)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PY = AQUI / ".venv" / "Scripts" / "python.exe"
BORRADORES = AQUI / "contenido" / "borradores"
PUBLICADO = AQUI / "contenido" / "publicado"


def pendientes() -> list[Path]:
    if not BORRADORES.exists():
        return []
    return sorted(p for p in BORRADORES.glob("*.md") if p.stat().st_size > 500)


def main() -> None:
    lista = pendientes()
    if not lista:
        print("No hay borradores pendientes.")
        return

    print(f"{len(lista)} borradores pendientes:")
    for p in lista:
        print(f"  · {p.stem}")

    if "--listar" in sys.argv:
        return

    movidos = []
    for p in lista:
        destino = PUBLICADO / p.name
        if destino.exists():
            print(f"  ya publicado, se omite: {p.name}")
            continue
        shutil.move(str(p), str(destino))
        movidos.append(p.name)
        print(f"  publicado: {p.name}")

    if not movidos:
        print("Nada que mover.")
        return

    print("\nReconstruyendo la web…")
    for comando in (
        [str(PY), str(AQUI / "construir_web.py")],
        ["git", "add", "-A"],
        ["git", "-c", "core.quotepath=false", "commit", "-q", "-m",
         f"Publica {len(movidos)} artículos nuevos ({datetime.now():%Y-%m-%d})"],
        ["git", "push", "origin", "main"],
    ):
        resultado = subprocess.run(comando, cwd=AQUI, capture_output=True,
                                   text=True, encoding="utf-8", errors="ignore")
        if resultado.returncode != 0:
            print(resultado.stdout[-400:])
            print(resultado.stderr[-400:])
            sys.exit(1)

    print(f"\nPublicados {len(movidos)} artículos y subidos a GitHub.")


if __name__ == "__main__":
    main()

@echo off
REM Construye la web y la deja lista para revisar en http://localhost:8000
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
if not exist .venv\Scripts\python.exe (
    echo No encuentro el entorno .venv. Creándolo...
    C:\AI\pythons\cpython-3.12.15\python.exe -m venv .venv
    .venv\Scripts\python.exe -m pip install --quiet markdown
)
.venv\Scripts\python.exe construir_web.py
echo.
echo Abre http://localhost:8000 en el navegador. Ctrl+C para parar.
.venv\Scripts\python.exe -m http.server 8000 --directory web

@echo off
title Sistema de Recomendacion CNSC
color 1F

echo ============================================================
echo   SISTEMA DE RECOMENDACION LABORAL - CNSC
echo   Diana Vasquez - German Mahecha
echo   Maestria en Ciencia de Datos
echo ============================================================
echo.

REM Moverse al directorio donde esta el .bat
cd /d "%~dp0"

REM ── 1. Detectar Python (py, python, python3) ──────────────────
echo [1/5] Verificando Python...
set PYTHON=

REM Intentar con el Python Launcher (py) primero
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=py
    goto :python_ok
)

REM Intentar con python
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto :python_ok
)

REM Intentar con python3
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python3
    goto :python_ok
)

echo.
echo [ERROR] Python no encontrado.
echo         Descargue Python 3.9+ desde: https://www.python.org/downloads/
echo         Marque la opcion "Add Python to PATH" al instalar.
echo.
pause
exit /b 1

:python_ok
%PYTHON% --version
echo.

REM ── 2. Verificar archivos requeridos ─────────────────────────
echo [2/5] Verificando archivos del sistema...
if not exist "modelo_arbol.pkl" (
    echo [ERROR] No se encontro modelo_arbol.pkl
    pause
    exit /b 1
)
if not exist "candidatos_completo.csv" (
    if not exist "ranking_final.csv" (
        echo [ERROR] No se encontro base de candidatos.
        pause
        exit /b 1
    )
)
if not exist "vacantes_opec.csv" (
    if not exist "vacantes.csv" (
        echo [ERROR] No se encontro base de vacantes.
        pause
        exit /b 1
    )
)
echo     Archivos OK
echo.

REM ── 3. Crear entorno virtual ──────────────────────────────────
echo [3/5] Preparando entorno virtual...
if not exist "venv\" (
    echo     Creando entorno virtual...
    %PYTHON% -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo     Entorno virtual OK
)
echo.

REM ── 4. Instalar dependencias ──────────────────────────────────
echo [4/5] Instalando dependencias...
echo     (Puede tardar varios minutos la primera vez)
call venv\Scripts\activate.bat

REM Actualizar pip primero para garantizar compatibilidad con Python 3.9-3.14
venv\Scripts\python.exe -m pip install --upgrade pip -q

REM Instalar dependencias
venv\Scripts\pip.exe install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    echo         Verifique su conexion a internet e intente de nuevo.
    pause
    exit /b 1
)
echo     Dependencias OK
echo.

REM ── 5. Iniciar la aplicacion ──────────────────────────────────
echo [5/5] Iniciando la aplicacion...
echo.
echo ============================================================
echo   Abra su navegador en: http://localhost:8501
echo   Para cerrar presione Ctrl+C en esta ventana.
echo ============================================================
echo.

start "" "http://localhost:8501"
venv\Scripts\streamlit.exe run app.py --browser.gatherUsageStats false --server.port 8501

pause

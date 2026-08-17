@echo off
title Sistema de Recomendacion CNSC
color 1F
chcp 65001 >nul 2>&1

echo ============================================================
echo   SISTEMA DE RECOMENDACION LABORAL - CNSC
echo   Diana Vasquez - German Mahecha
echo   Maestria en Ciencia de Datos
echo ============================================================
echo.

REM ── Moverse al directorio donde esta el .bat ──────────────────
cd /d "%~dp0"

REM ── 1. Verificar Python ───────────────────────────────────────
echo [1/5] Verificando instalacion de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo         Descargue Python 3.9 o superior desde:
    echo         https://www.python.org/downloads/
    echo         Marque la opcion "Add Python to PATH" al instalar.
    echo.
    pause
    exit /b 1
)
python --version
echo.

REM ── 2. Verificar archivos requeridos ─────────────────────────
echo [2/5] Verificando archivos del sistema...

if not exist "modelo_arbol.pkl" (
    echo [ERROR] No se encontro modelo_arbol.pkl
    echo         Asegurese de que este archivo este en la misma carpeta que ejecutar.bat
    pause
    exit /b 1
)

if not exist "candidatos_completo.csv" (
    if not exist "ranking_final.csv" (
        echo [ERROR] No se encontro ninguna base de candidatos.
        echo         Se requiere candidatos_completo.csv o ranking_final.csv
        pause
        exit /b 1
    )
    echo [AVISO] Modo demo: usando ranking_final.csv (58 candidatos)
) else (
    echo OK: candidatos_completo.csv encontrado
)

if not exist "vacantes_opec.csv" (
    if not exist "vacantes.csv" (
        echo [ERROR] No se encontro ninguna base de vacantes.
        pause
        exit /b 1
    )
    echo [AVISO] Usando vacantes.csv (modo demo)
) else (
    echo OK: vacantes_opec.csv encontrado
)

echo OK: modelo_arbol.pkl encontrado
echo.

REM ── 3. Crear entorno virtual si no existe ─────────────────────
echo [3/5] Preparando entorno virtual...
if not exist "venv\" (
    echo     Creando entorno virtual (solo la primera vez)...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo     Entorno virtual ya existe. OK
)
echo.

REM ── 4. Instalar dependencias ──────────────────────────────────
echo [4/5] Instalando dependencias...
echo     (Puede tomar varios minutos la primera vez)
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    echo         Verifique su conexion a internet e intente de nuevo.
    pause
    exit /b 1
)
echo     Dependencias instaladas correctamente.
echo.

REM ── 5. Iniciar la aplicacion ──────────────────────────────────
echo [5/5] Iniciando la aplicacion...
echo.
echo ============================================================
echo   La aplicacion abrira en su navegador en:
echo   http://localhost:8501
echo.
echo   Para cerrar la aplicacion presione Ctrl+C en esta ventana
echo   o cierre esta ventana directamente.
echo ============================================================
echo.

REM Abrir el navegador despues de 4 segundos
start "" timeout /t 4 /nobreak >nul & start "" "http://localhost:8501"

REM Iniciar Streamlit
streamlit run app.py --server.headless false --browser.gatherUsageStats false --server.port 8501

echo.
echo La aplicacion fue cerrada.
pause

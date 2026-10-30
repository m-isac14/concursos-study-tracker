@echo off
title Central de Estudos - Concursos Publicos (Isac)
cd /d "%~dp0"
echo ========================================================
echo   INICIANDO CENTRAL DE ESTUDOS - TRAJETORIA CONCURSOS
echo ========================================================
echo.
echo Abrindo painel no navegador...
"%~dp0venv\Scripts\python.exe" -m streamlit run app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocorreu um erro ao iniciar. Tentando via activate...
    call "%~dp0venv\Scripts\activate.bat"
    python -m streamlit run app.py
)
pause

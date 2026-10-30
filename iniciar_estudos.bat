@echo off
title Central de Estudos - Concursos Publicos (Isac)
cd /d "%~dp0"
echo ========================================================
echo   INICIANDO CENTRAL DE ESTUDOS - TRAJETORIA CONCURSOS
echo ========================================================
echo.
echo Abrindo painel no navegador...
call "venv\Scripts\activate.bat"
streamlit run app.py
pause

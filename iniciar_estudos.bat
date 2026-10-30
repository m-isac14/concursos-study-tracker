@echo off
title DPDF Study Tracker - Isac
cd /d "%~dp0"
echo ========================================================
echo   INICIANDO DPDF STUDY TRACKER - ISAC
echo ========================================================
echo.
echo Abrindo painel no navegador...
call "venv\Scripts\activate.bat"
streamlit run app.py
pause

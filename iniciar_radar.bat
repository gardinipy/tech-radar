@echo off
rem Inicia o Tech Radar usando o Python da pasta venv (nao precisa "ativar" nada).
rem Uso normal: duplo clique (mostra a janela).  Uso oculto: iniciar_radar.bat oculto (grava em radar.log)
cd /d "%~dp0"
title Tech Radar

rem Espera ~20s para o Wi-Fi/rede conectar depois de ligar o PC.
ping -n 21 127.0.0.1 >nul

:loop
if /i "%~1"=="oculto" (
  "venv\Scripts\python.exe" -u main.py >> radar.log 2>&1
) else (
  "venv\Scripts\python.exe" main.py
)
echo.
echo [%date% %time%] O Tech Radar parou. Reiniciando em 30 segundos... >> radar.log
echo [%date% %time%] O Tech Radar parou. Reiniciando em 30 segundos...
ping -n 31 127.0.0.1 >nul
goto loop

@echo off
rem Para o Tech Radar (inclusive quando estiver rodando oculto).
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and ($_.CommandLine -like '*iniciar_radar*' -or $_.CommandLine -like '*tech-radar*main.py*' -or $_.CommandLine -like '* main.py*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo Tech Radar parado.
pause

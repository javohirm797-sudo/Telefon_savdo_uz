@echo off
chcp 65001 > nul
title Telegram Telefon Savdo Boti
echo =======================================================
echo    TELEGRAM TELEFON SAVDO VA BOZOR BOTI
echo =======================================================
echo.
echo Bot ishga tushirilmoqda...
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe main.py
) else (
    python main.py
)

pause

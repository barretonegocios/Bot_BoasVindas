@echo off
title Bot Boas-Vindas
:inicio
echo [INFO] Iniciando Bot Boas-Vindas...
python -u botboasvindas.py
echo [AVISO] Bot encerrado. Reiniciando em 5 segundos...
timeout /t 5
goto inicio

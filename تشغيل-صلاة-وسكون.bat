@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0vendor;%PYTHONPATH%
python main.py

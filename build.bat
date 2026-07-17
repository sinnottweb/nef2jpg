@echo off
setlocal
title NEF to JPG Converter — Build

echo.
echo  ================================================
echo    NEF to JPG Converter — Generando ejecutable
echo  ================================================
echo.

REM ── Verificar Python ─────────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instalalo desde https://python.org
    pause & exit /b 1
)

echo [1/5] Instalando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias.
    pause & exit /b 1
)

echo [2/5] Generando icono...
python create_icon.py
if errorlevel 1 (
    echo [WARN] No se pudo generar el icono, se continua sin el.
)

echo [3/5] Limpiando builds anteriores...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist NEFtoJPG.spec del /f /q NEFtoJPG.spec

echo [4/5] Compilando con PyInstaller...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "NEFtoJPG" ^
    --icon "assets\icon.ico" ^
    --add-data "assets;assets" ^
    --hidden-import "customtkinter" ^
    --hidden-import "rawpy" ^
    --hidden-import "PIL" ^
    --hidden-import "imageio" ^
    --collect-all "customtkinter" ^
    --collect-all "tkinterdnd2" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Fallo la compilacion. Revisa los mensajes de arriba.
    pause & exit /b 1
)

echo.
echo [5/5] Listo!
echo.
echo  El ejecutable esta en: dist\NEFtoJPG.exe
echo.
pause

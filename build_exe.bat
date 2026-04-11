@echo off
chcp 65001 >/dev/null
echo ========================================
echo   HOI4 Map Maker - Build EXE
echo ========================================
echo.

cd /d "%~dp0"

echo Cleaning...
rmdir /s /q dist 2>/dev/null
rmdir /s /q build 2>/dev/null

echo Building (takes a few minutes)...
pyinstaller hoi4_map_maker.spec --noconfirm

if exist "dist\HOI4MapMaker\HOI4MapMaker.exe" (
    echo.
    echo ========================================
    echo   Build OK!
    echo   dist\HOI4MapMaker\HOI4MapMaker.exe
    echo ========================================
) else (
    echo.
    echo   Build FAILED
)

pause

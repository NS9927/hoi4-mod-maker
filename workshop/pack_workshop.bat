@echo off
REM === HOI4 Map Maker Workshop deploy wrapper ===
REM 真正的逻辑在 deploy.ps1, 这里只是为了双击触发
REM
REM 安全语义见 deploy.ps1 头部注释
REM 跑之前先跑 ..\build_exe.bat 生成 dist/HOI4MapMaker/

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy.ps1"
pause

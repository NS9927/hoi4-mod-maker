@echo off
REM === HOI4 Map Maker Workshop 打包脚本 ===
REM 用法: 先跑 PyInstaller，再运行此脚本

set MOD_DIR=D:\Documents\Paradox Interactive\Hearts of Iron IV\mod\hoi4_map_maker
set DIST_DIR=..\dist\HOI4MapMaker

echo [1/3] 清理旧文件...
if exist "%MOD_DIR%" rmdir /s /q "%MOD_DIR%"
mkdir "%MOD_DIR%"

echo [2/3] 复制文件...
REM 复制 PyInstaller 打包结果
xcopy /e /i /q "%DIST_DIR%\*" "%MOD_DIR%\"

REM 复制 descriptor（放在 mod 目录内部）
copy /y "descriptor.mod" "%MOD_DIR%\descriptor.mod"

REM 复制外层 .mod 文件（HOI4 启动器需要）
(
echo version="1.2.0"
echo tags={
echo 	"Utilities"
echo }
echo name="HOI4 Fantasy World Map Maker"
echo supported_version="1.18.*"
echo path="mod/hoi4_map_maker"
) > "D:\Documents\Paradox Interactive\Hearts of Iron IV\mod\hoi4_map_maker.mod"

echo [3/3] 完成！
echo.
echo 外层描述: D:\Documents\Paradox Interactive\Hearts of Iron IV\mod\hoi4_map_maker.mod
echo MOD 目录: %MOD_DIR%
echo.
echo 接下来打开 HOI4 启动器 → Mod Tools → Upload Mod → 选 hoi4_map_maker
pause

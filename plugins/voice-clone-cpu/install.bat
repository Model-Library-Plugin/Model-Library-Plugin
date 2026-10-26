@echo off
chcp 65001 >nul
set "PYEXE=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"
echo.
echo ============================================
echo  OpenVoice 声音克隆 - 一键部署（纯 CPU）
echo  无需显卡，装到 D:\OpenVoice
echo ============================================
echo.
"%PYEXE%" "%~dp0install.py" %*
echo.
pause

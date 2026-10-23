@echo off
chcp 65001 >nul
set "PYEXE=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"
echo 即将部署 GPT-SoVITS（声音克隆），请确保本机有 NVIDIA GPU。
echo.
"%PYEXE%" "%~dp0install.py" %*
echo.
pause

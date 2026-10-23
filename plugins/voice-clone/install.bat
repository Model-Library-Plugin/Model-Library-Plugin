@echo off
chcp 65001 >nul
set "PYEXE=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"
echo.
echo ============================================
echo  GPT-SoVITS 声音克隆 - 一键部署
echo  需要: NVIDIA GPU + conda + git + pwsh
echo  默认: 装到 D:\GPT-SoVITS，HF-Mirror 源，CU126
echo ============================================
echo.
"%PYEXE%" "%~dp0install.py" %*
echo.
pause

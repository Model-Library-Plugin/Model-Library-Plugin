@echo off
chcp 65001 >nul
set "DIR=D:\GPT-SoVITS"
if not exist "%DIR%\webui.py" (
  echo 尚未部署 GPT-SoVITS，请先运行 install.bat
  pause
  exit /b 1
)
cd /d "%DIR%"
"%DIR%\venv\Scripts\python.exe" webui.py
pause

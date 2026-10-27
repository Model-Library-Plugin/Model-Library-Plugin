@echo off
chcp 65001 >nul
set "DIR=D:\OpenVoice"
if not exist "%DIR%\venv\Scripts\python.exe" (
  echo 尚未部署 OpenVoice，请先运行 install.bat
  pause
  exit /b 1
)
rem 离线运行（模型已本地就位）
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
set "HF_ENDPOINT=https://hf-mirror.com"
if exist "D:\ffmpeg\ffmpeg.exe" set "PATH=D:\ffmpeg;%PATH%"

echo 正在启动 OpenVoice WebUI ...
echo 首次启动会自动打开浏览器（Gradio 界面）
echo.
cd /d "%DIR%"
"%DIR%\venv\Scripts\python.exe" -m openvoice.openvoice_app
pause

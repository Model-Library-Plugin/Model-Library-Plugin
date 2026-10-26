@echo off
chcp 65001 >nul
set "DIR=D:\OpenVoice"
if not exist "%DIR%\openvoice\openvoice_app.py" (
  echo 尚未部署 OpenVoice，请先运行 install.bat
  pause
  exit /b 1
)
echo 正在启动 OpenVoice WebUI ...
echo 首次启动会自动打开浏览器（Gradio 界面）
echo.
cd /d "%DIR%"
"%DIR%\venv\Scripts\python.exe" -m openvoice.openvoice_app
pause

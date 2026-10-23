@echo off
chcp 65001 >nul
set "DIR=D:\GPT-SoVITS"
if not exist "%DIR%\webui.py" (
  echo 尚未部署 GPT-SoVITS，请先运行 install.bat
  pause
  exit /b 1
)
echo 正在启动 GPT-SoVITS WebUI ...
echo 首次启动会自动打开浏览器，地址 http://localhost:9874
echo.
cd /d "%DIR%"
set "CONDA=conda"
if not exist "%USERPROFILE%\Miniconda3\Scripts\conda.exe" (
  if exist "C:\ProgramData\Miniconda3\Scripts\conda.exe" set "CONDA=C:\ProgramData\Miniconda3\Scripts\conda.exe"
)
"%CONDA%" run -n GPTSoVits python webui.py zh_CN
pause

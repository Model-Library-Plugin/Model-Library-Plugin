@echo off
chcp 65001 >nul
set "DIR=D:\OpenVoice"
set "PYEXE=%DIR%\venv\Scripts\python.exe"
if not exist "%PYEXE%" (
  echo 尚未部署 OpenVoice，请先运行 install.bat
  pause
  exit /b 1
)
rem 离线运行（模型已本地就位），避免联网超时
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
set "HF_ENDPOINT=https://hf-mirror.com"
rem ffmpeg（音频解码需要）
if exist "D:\ffmpeg\ffmpeg.exe" set "PATH=D:\ffmpeg;%PATH%"

echo.
echo ============================================================
echo  声音克隆：用参考音频克隆音色，合成目标文本（纯 CPU）
echo ============================================================
echo.
echo  参考音频建议：3~10 秒清晰人声（wav/mp3），背景越安静越好
echo.
set /p REF=请输入参考音频完整路径（要克隆的音色）: 
set /p TXT=请输入要合成的文本: 
set /p LANG=请输入语言代码 ZH/EN/JP/KR/ES/FR（默认 ZH）: 
if "%LANG%"=="" set "LANG=ZH"
echo.
echo 正在克隆（纯 CPU 较慢，约 1~3 分钟，请耐心等待）...
"%PYEXE%" "%~dp0clone.py" --ref "%REF%" --text "%TXT%" --lang "%LANG%" -o "%~dp0clone_out.wav"
echo.
if exist "%~dp0clone_out.wav" echo 结果已保存: %~dp0clone_out.wav
pause

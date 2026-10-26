@echo off
chcp 65001 >nul
set "DIR=D:\OpenVoice"
set "PYEXE=%DIR%\venv\Scripts\python.exe"
if not exist "%PYEXE%" (
  echo 尚未部署 OpenVoice，请先运行 install.bat
  pause
  exit /b 1
)
echo.
echo 声音克隆：用参考音频克隆音色，合成目标文本。
echo.
echo 示例：
echo   %PYEXE% clone.py --ref 参考音频.wav --text "你好世界" --lang ZH
echo.
set /p REF=请输入参考音频路径（要克隆的音色）: 
set /p TXT=请输入要合成的文本: 
set /p LANG=请输入语言代码 ZH/EN/JP/KR/ES/FR（默认 ZH）: 
if "%LANG%"=="" set "LANG=ZH"
echo.
echo 正在克隆（纯 CPU 较慢，请耐心等待）...
"%PYEXE%" "%~dp0clone.py" --ref "%REF%" --text "%TXT%" --lang "%LANG%" -o "%~dp0clone_out.wav"
echo.
if exist "%~dp0clone_out.wav" echo 结果已保存: %~dp0clone_out.wav
pause

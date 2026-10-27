@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title OpenVoice 声音克隆 - 继续安装（补 transformers + 下载模型）

rem ===== 路径配置 =====
set "PY=C:\Users\ZhuanZ（无密码）\AppData\Local\Programs\Python\Python311\python.exe"
set "VENV=D:\OpenVoice\venv"
set "VENVPY=%VENV%\Scripts\python.exe"
set "CKPT=D:\OpenVoice\checkpoints_v2"
set "PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple"
set "HF=https://hf-mirror.com"

rem ===== 如果 venv 的 python 找不到，回退到系统 3.11 =====
if not exist "%VENVPY%" (
    echo [错误] 找不到 venv: %VENVPY%
    echo 请先确认 D:\OpenVoice\venv 已存在（之前部署已建过）。
    pause
    exit /b 1
)

echo ============================================================
echo  OpenVoice 声音克隆 - 继续安装
echo ============================================================
echo.

echo [1/3] 修复 transformers（MeloTTS 日文依赖）...
rem 直接把 wheel 解压覆盖到 site-packages，绕开 pip 卸载残缺目录时可能卡住的问题
set "WHEEL=D:\pip_cache\transformers-5.20.2-py3-none-any.whl"
if not exist "%WHEEL%" (
    echo   未找到离线 wheel，先用清华镜像下载...
    "%VENVPY%" -m pip download transformers --no-deps -d "D:\pip_cache" -i "%PIP_INDEX%"
)
"%VENVPY%" -c "import zipfile,sys; w=zipfile.ZipFile(r'%WHEEL%'); w.extractall(r'%VENV%\Lib\site-packages'); print('  解压覆盖完成, 共', len(w.namelist()), '个文件')"
echo.

echo [2/3] 下载 V2 模型（hf-mirror）...
if not exist "%CKPT%" mkdir "%CKPT%"
if not exist "%CKPT%\converter" mkdir "%CKPT%\converter"
if not exist "%CKPT%\base_speakers\ses" mkdir "%CKPT%\base_speakers\ses"

rem converter（核心转换器）
echo   下载 converter/checkpoint.pth ...
"%VENVPY%" -c "import urllib.request; urllib.request.urlretrieve('%HF%/myshell-ai/OpenVoiceV2/resolve/main/converter/checkpoint.pth', r'%CKPT%\converter\checkpoint.pth'); print('  OK')"
echo   下载 converter/config.json ...
"%VENVPY%" -c "import urllib.request; urllib.request.urlretrieve('%HF%/myshell-ai/OpenVoiceV2/resolve/main/converter/config.json', r'%CKPT%\converter\config.json'); print('  OK')"

rem base_speakers（各语言基础音色）
for %%L in (en-au en-br en-default en-india en-newest en-us es fr jp kr zh) do (
    echo   下载 base_speakers/ses/%%L.pth ...
    "%VENVPY%" -c "import urllib.request; urllib.request.urlretrieve('%HF%/myshell-ai/OpenVoiceV2/resolve/main/base_speakers/ses/%%L.pth', r'%CKPT%\base_speakers\ses\%%L.pth'); print('  OK')"
)
echo.

echo [3/3] 验证核心模块能否加载...
"%VENVPY%" -c "import sys; sys.path.insert(0, r'D:\OpenVoice'); sys.path.insert(0, r'D:\MeloTTS'); from openvoice.api import ToneColorConverter; print('  ToneColorConverter OK'); from melo.api import TTS; print('  melo TTS OK')"
if errorlevel 1 (
    echo.
    echo [警告] 模块加载有报错，请把上面错误截图发我。
) else (
    echo.
    echo ============================================================
    echo  全部完成！现在可以克隆了：
    echo    python clone.py --ref 参考音频.wav --text "要说的文本" --lang ZH
    echo  或双击 start.bat 打开 WebUI
    echo ============================================================
)
echo.
pause

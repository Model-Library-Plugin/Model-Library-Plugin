# voice-tts — 本地声音插件（离线中文语音合成）

把文本变成可播放的语音，**完全离线**，不依赖任何在线 API，不产生任何费用。
适合给本地大语言模型（Ollama、LM Studio 等）的回复配上声音，或给视频自动配音。

## 能力

- 文本 → 语音（wav），可选同时导出 mp3
- 语速可调（`-r`，>1 慢速朗读，<1 加速）
- 中文女声「huayan」（Piper 神经语音模型，自然度远好于系统机械音）
- 纯 Python 标准库实现，插件本体零第三方依赖

## 快速开始

Windows 下直接把写好文案的 txt 拖到 `一键配音.bat` 图标上即可。

命令行用法：

```bash
# 直接合成一句话
python voice.py -t "你好，这是本地语音插件合成的声音"

# 从文本文件合成，并同时导出 mp3
python voice.py -f 文案.txt --mp3

# 调整语速（1.0 正常，1.25 慢速，0.8 加速），指定输出目录
python voice.py -t "你好" -r 1.25 -o 输出目录
```

运行后会在控制台打印生成的音频文件路径，直接双击即可播放。

## 引擎安装（一次性）

插件脚本依赖本机已安装的 Piper 引擎与中文模型：

1. 下载引擎：[piper_windows_amd64.zip](https://github.com/rhasspy/piper/releases)（约 22 MB），解压到 `C:\piper-tts`。
2. 下载中文音色：`zh_CN-huayan-medium.onnx` 与 `.onnx.json`（来自 [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices)，国内可用 hf-mirror.com），放到 `C:\piper-tts`。
3. （可选，导出 mp3 用）安装 ffmpeg 到 `C:\ffmpeg\ffmpeg.exe`。

> 注意：Piper/espeak-ng 无法处理含中文的路径，引擎必须放在**纯英文路径**下。

引擎路径如与默认不同，用环境变量覆盖：`VOICE_PIPER_DIR`、`VOICE_MODEL`、`VOICE_FFMPEG`。

## 在 LLM 工作流中使用

插件入口 `voice.py` 对程序友好：传入文本、返回音频路径（打印到 stdout），可以被任意本地 Agent / 脚本调用：

```
LLM 生成回复文本 → python voice.py -t "<回复>" → 得到 wav 路径 → 播放/发送
```

## 验证环境

- Windows 10/11 + Python 3.11+
- Piper 2023.11.14-2 + zh_CN-huayan-medium 模型
- 本插件已在真实机器上完成「文本 → wav → mp3」全流程验证

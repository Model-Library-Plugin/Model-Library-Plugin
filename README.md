# Model-Library-Plugin

This is a plugin library for finding and storing various plugins to integrate with local large language models.

一个用于本地大语言模型的插件库：收录可直接落地的实用插件，每个插件自带说明、元数据与可运行入口。

## 插件索引

| 插件 | 目录 | 能力 | 依赖 |
|---|---|---|---|
| **voice-tts** 本地声音插件 | [`plugins/voice-tts/`](plugins/voice-tts/) | 文本 → 语音（离线中文 TTS，语速可调，输出 wav/mp3），可给本地 LLM 的回复配音 | Piper 引擎（本机安装，纯离线） |
| **video-maker** 一键成片插件 | [`plugins/video-maker/`](plugins/video-maker/) | 文案 → 竖屏短视频（分句配音 + 字幕时间轴 + 渐变画面切换 + ffmpeg 合成 mp4） | Piper 引擎 + ffmpeg（纯离线） |
| **voice-clone** 声音克隆插件 | [`plugins/voice-clone/`](plugins/voice-clone/) | 几秒参考音频克隆音色 → 合成任意文本（封装 GPT-SoVITS，含环境体检 + 国内镜像一键部署 + 启动器） | NVIDIA GPU（建议 6G 显存，纯 CPU 不可用） |
| **voice-clone-cpu** 声音克隆插件（免显卡） | [`plugins/voice-clone-cpu/`](plugins/voice-clone-cpu/) | 几秒参考音频克隆音色 → 跨语种合成（封装 OpenVoice V2，纯 CPU 可跑，零样本免训练） | 无需 GPU（Python 3.10/3.11） |

## 目录约定

```
plugins/
└── <插件名>/
    ├── plugin.json   # 插件元数据（名称、能力、入口、依赖）
    ├── README.md     # 用法说明
    └── ...           # 插件代码与启动器
```

## 如何使用一个插件

进入插件目录，阅读该插件的 `README.md`，按说明运行其入口脚本即可。所有插件均不引入在线服务依赖的设计原则：能离线，就离线。

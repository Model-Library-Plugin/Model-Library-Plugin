# voice-clone-cpu 声音克隆插件（OpenVoice，纯 CPU 可用）

用一段参考音频克隆音色，再用该音色合成任意文本，支持中/英/日/韩/法/西跨语种。
封装 [OpenVoice V2](https://github.com/myshell-ai/OpenVoice)（myshell-ai，MIT 协议，可商用）。

**和 voice-clone（GPT-SoVITS）的区别：本插件无需 NVIDIA GPU，纯 CPU 就能跑。**

## 特点

- ✅ 无需显卡，纯 CPU 可跑（合成一句约 30~60 秒）
- ✅ 零样本克隆：一段 3~10 秒参考音频即可，无需训练
- ✅ 跨语种：中文音色可以直接说英文/日文/韩文等
- ✅ MIT 协议，可商用
- ✅ 完全离线运行（模型本地就位后，克隆过程不联网）

## 硬门槛

- 磁盘建议 >= 8G 剩余空间（依赖 + 模型约 4G，建议装到 D 盘）
- Python 3.10 ~ 3.11（3.12+ 部分旧依赖不兼容）
- 需要 git（源码下载用）
- ffmpeg（音频解码用，脚本会自动探测 `D:\ffmpeg\ffmpeg.exe`）

## 三步使用

1. **体检**：双击 `check_env.py`（或 `python check_env.py`）
2. **部署**：双击 `install.bat`（自动：下载源码 → 建 venv → 装依赖 → 下模型 → 打补丁）
3. **克隆**：双击 `一键克隆.bat` 按提示输入，或命令行：

```bash
python clone.py --ref 参考音频.wav --text "你好，世界" --lang ZH
python clone.py --ref 参考.mp3 --text "Hello world" --lang EN --speed 1.2
```

语言代码：`ZH` 中文 / `EN` 英文 / `EN_NEWEST` 英文(新) / `JP` 日文 / `KR` 韩文 / `ES` 西语 / `FR` 法语

也可以双击 `start.bat` 打开 Gradio 网页界面。

## 部署做了什么（国内镜像）

| 环节 | 做法 | 镜像 |
|---|---|---|
| 源码 | codeload 下载 OpenVoice tarball | github.com 直连 |
| 依赖 | pip install（清华镜像，numpy/av 版本已兼容处理） | pypi.tuna.tsinghua.edu.cn |
| transformers | 降级到 4.44.2（5.x import 太重会卡死） | 清华镜像 |
| 模型 | urllib 下载 V2 权重 + MeloTTS 中文模型 | hf-mirror.com |
| MeloTTS | git clone + patch_melotts.py 补丁（惰性化 BERT） | github.com |

默认安装目录 `D:\OpenVoice`（纯英文路径，规避中文路径坑）。可用 `install.py --dir <路径>` 自定义。

## 关键技术处理（踩坑记录）

本插件在真实部署中踩过并解决了这些坑，已全部固化进脚本：

1. **transformers 必须降级**：5.x 的 `import transformers` 会加载海量子模块，在纯 CPU 机器上卡死/超时。降到 4.44.2（连带 tokenizers 0.19.1 + huggingface-hub 0.25.2）。
2. **MeloTTS 模块级 BERT 加载**：官方代码在 import 时就会加载 7 个语言的 BERT tokenizer（联网下载 + 硬编码 cuda）。`patch_melotts.py` 把这些全部改成惰性加载，中文克隆完全不碰它们。
3. **hf-mirror 的 LFS 坑**：`.pth`/`.bin` 大文件用 `huggingface_hub` 下载会拿到 0 字节（LFS 指针没解析），必须用 `urllib`/curl 直接下载 `resolve/main` 直链。
4. **官方 se_extractor 硬编码 cuda**：`split_audio_whisper` 里 `WhisperModel(device="cuda")` 写死。clone.py 改为直接 `converter.extract_se()` 提取整段音色，绕开 whisper 分段。
5. **离线模式**：clone.py 自动设置 `HF_HUB_OFFLINE=1` + `TRANSFORMERS_OFFLINE=1`，避免合成时去 xethub 下载 safetensors 而超时。

## 模型说明

OpenVoice V2 权重从 HF 镜像仓库 `myshell-ai/OpenVoiceV2` 下载（官方 S3 直链已 404，此镜像仓库内容一致）：

- `converter/checkpoint.pth` + `config.json` —— 音色转换器（核心）
- `base_speakers/ses/*.pth` —— 各语言基础音色（含中文 zh.pth）
- MeloTTS 中文模型 `myshell-ai/MeloTTS-Chinese` → 下载到 `D:\OpenVoice\melo_models\ZH\`
- 中文 BERT `bert-base-multilingual-uncased`（合成中文时必须，用于韵律特征）

## 验证状态（本机已完整跑通）

- ✅ **环境体检** `check_env.py` —— 正确判断磁盘/网络/Python
- ✅ **完整部署** —— 依赖全部装齐、模型全部下载、MeloTTS 补丁生效
- ✅ **中文克隆合成** —— 已在无 GPU 机器上实测跑通：参考音频 → 提取音色 → MeloTTS 合成 → 音色转换 → 输出 wav（约 1 分钟/句）
- ⚠️ 英文/日文/韩文/法文/西文克隆：依赖链已就位（g2p_en/mecab/pykakasi 等已装），但**未逐语种实测**。中文是核心需求，已充分验证。

## 上游

- 项目：https://github.com/myshell-ai/OpenVoice
- 论文：[OpenVoice: Versatile Instant Voice Cloning](https://arxiv.org/abs/2312.01479)
- 协议：MIT（可自由使用、修改、商用）

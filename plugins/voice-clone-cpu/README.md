# voice-clone-cpu 声音克隆插件（OpenVoice，纯 CPU 可用）

用一段参考音频克隆音色，再用该音色合成任意文本，支持中/英/日/韩/法/西跨语种。
封装 [OpenVoice V2](https://github.com/myshell-ai/OpenVoice)（myshell-ai，MIT 协议，可商用）。

**和 voice-clone（GPT-SoVITS）的区别：本插件无需 NVIDIA GPU，纯 CPU 就能跑。**

## 特点

- ✅ 无需显卡，纯 CPU 可跑（合成一句约几十秒）
- ✅ 零样本克隆：一段参考音频即可，无需训练
- ✅ 跨语种：中文音色可以直接说英文/日文/韩文等
- ✅ MIT 协议，可商用

## 硬门槛

- 磁盘建议 >= 5G 剩余空间（依赖 + 模型，建议装到 D 盘）
- Python 3.10 ~ 3.11（3.12+ 部分旧依赖不兼容）
- 需要 git（源码下载用）

## 三步使用

1. **体检**：双击 `check_env.py`（或 `python check_env.py`）
2. **部署**：双击 `install.bat`（自动：下载源码 → 建 venv → 装依赖 → 下模型）
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
| 依赖 | pip install（清华镜像，numpy 版本已兼容处理） | pypi.tuna.tsinghua.edu.cn |
| 模型 | 下载 V2 权重 | hf-mirror.com（`myshell-ai/OpenVoiceV2`） |
| MeloTTS | pip 安装 + unidic 词典 | github + 清华镜像 |

默认安装目录 `D:\OpenVoice`（纯英文路径，规避中文路径坑）。可用 `install.py --dir <路径>` 自定义。

## 模型说明

OpenVoice V2 权重从 HF 镜像仓库 `myshell-ai/OpenVoiceV2` 下载（官方 S3 直链已 404，此镜像仓库内容一致）：

- `converter/checkpoint.pth` + `config.json` —— 音色转换器（核心）
- `base_speakers/ses/*.pth` —— 各语言基础音色（含中文 zh.pth）

## 常见问题

- **合成很慢**：纯 CPU 属正常，一句几十秒。有显卡的机器会自动用 GPU（代码里 `torch.cuda.is_available()` 自动判断）。
- **numpy 报错**：本插件已自动处理版本兼容（去掉钉死的 1.22.0，改用 `numpy<2.0`）。
- **日文合成报错**：unidic 词典未下载成功，只影响日文，其他语言不受影响。

## 验证边界（重要）

- **已验证**：环境体检脚本 `check_env.py` 能正确判断磁盘/网络/Python；源码结构、V2 调用流程、模型仓库已逐行核对官方仓库与 demo_part3.ipynb。
- **未完整验证**：完整部署 + 实际克隆合成（依赖多、模型较大，未在本机跑通完整链路）。首次部署若个别依赖报错，以[官方 USAGE](https://github.com/myshell-ai/OpenVoice/blob/main/docs/USAGE.md) 为准微调。

## 上游

- 项目：https://github.com/myshell-ai/OpenVoice
- 论文：[OpenVoice: Versatile Instant Voice Cloning](https://arxiv.org/abs/2312.01479)
- 协议：MIT（可自由使用、修改、商用）

# voice-clone 声音克隆插件（GPT-SoVITS 一键部署器）

用几秒参考音频克隆音色，再用该音色合成任意文本。封装开源顶流
[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)（MIT 协议，中文克隆效果最好）。

## 硬门槛（务必先看）

- **必须有 NVIDIA GPU**（建议 6G 显存以上）。纯 CPU 不可用：合成一句 10 秒的克隆语音，CPU 要跑好几分钟，没有实用价值。
- 磁盘建议 >= 8G 剩余空间（模型 + 依赖，建议装到 D 盘）。
- Python 3.9 ~ 3.11（PyTorch 兼容范围）。

## 三步使用

1. **体检**：双击 `check_env.py`（或 `python check_env.py`），看本机能不能跑。
2. **部署**：环境通过后双击 `install.bat`，全流程国内镜像自动安装（源码走 ghfast、依赖走清华 pip、模型走 hf-mirror）。
3. **启动**：部署完成后双击 `start.bat`，打开 WebUI，导入参考音频开始克隆。

## 国内镜像一览

| 环节 | 用什么 | 镜像 |
|---|---|---|
| 克隆源码 | `git clone RVC-Boss/GPT-SoVITS` | ghfast.top |
| 装依赖 | `pip install torch` + `requirements.txt` | 清华 pypi |
| 下模型 | `huggingface-cli lj1995/GPT-SoVITS` | hf-mirror.com |

默认安装目录 `D:\GPT-SoVITS`（纯英文路径，规避 Windows 原生程序的中文路径坑）。
可用 `install.py --dir <路径>` 自定义。

## 验证边界（重要）

本插件在**无 GPU 的 Windows 机器**上开发：

- **已验证**：环境体检脚本 `check_env.py` 能正确判断 GPU / 磁盘 / 网络 / Python。
- **未完整验证**：`install.py` 的完整部署流程（需要 NVIDIA GPU，本机没有）。脚本已按国内镜像写好，若个别依赖报错，以 [官方 README](https://github.com/RVC-Boss/GPT-SoVITS) 为准微调。

## 上游

- 项目：https://github.com/RVC-Boss/GPT-SoVITS
- 协议：MIT（可自由使用、修改、商用）

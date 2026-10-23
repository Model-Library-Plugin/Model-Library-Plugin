# voice-clone 声音克隆插件（GPT-SoVITS 一键部署器）

用几秒参考音频克隆音色，再用该音色合成任意文本。封装开源顶流
[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)（MIT 协议，中文克隆效果最好）。

## 硬门槛（务必先看）

- **必须有 NVIDIA GPU**（建议 6G 显存以上）。纯 CPU 可用但极慢：合成一句 10 秒的克隆语音要跑好几分钟。
- 磁盘建议 >= 15G 剩余空间（依赖 + 模型，建议装到 D 盘）。
- 需要预装：**conda**（Miniconda）、**git**、**PowerShell 7（pwsh）**——GPT-SoVITS 官方安装脚本依赖这三样。

## 三步使用

1. **体检**：双击 `check_env.py`（或 `python check_env.py`），看本机能不能跑。
2. **部署**：双击 `install.bat`，自动完成：环境体检 → ghfast 镜像克隆源码 → 建 conda 环境 → 调用官方 `install.ps1`（国内镜像下载模型 + 装 PyTorch）→ 生成启动器。
3. **启动**：双击 `start.bat`，打开 WebUI（默认 `http://localhost:9874`），导入参考音频开始克隆。

## 部署做了什么（薄封装官方脚本）

本插件的 `install.py` **不自己重造依赖安装**，而是薄封装官方 `install.ps1`，
把容易写错的 CUDA wheel 版本、模型下载地址、依赖清单都交给官方脚本，只做三件增值事：

| 环节 | 做法 | 国内镜像 |
|---|---|---|
| 克隆源码 | `git clone RVC-Boss/GPT-SoVITS` | ghfast.top |
| 建环境 | `conda create -n GPTSoVits python=3.10` | conda 默认源 |
| 依赖/模型 | 调用官方 `install.ps1` | 模型默认 **HF-Mirror**（也可 `--source ModelScope`） |
| 装 PyTorch | 官方 `--Device` 选 CU126/CU128/CPU | download.pytorch.org |

## 模型清单（官方 install.ps1 实际下载）

| 模型包 | 用途 | 大小（约） |
|---|---|---|
| `pretrained_models.zip` | 核心预训练权重（GPT + SoVITS + 特征提取） | ~2.5G |
| `G2PWModel.zip` | 中文多音字消歧 | ~500M |
| `nltk_data.zip` | 英文分词数据 | ~50M |
| `open_jtalk_dic_utf_8-1.11.tar.gz` | 日文发音字典 | ~200M |
| `uvr5_weights.zip`（可选 `--DownloadUVR5`） | 人声分离 | ~2G |

模型仓库：`XXXXRT/GPT-SoVITS-Pretrained`（官方脚本内置，无需手动填）。

## 常用参数

```bash
python install.py                      # 默认 D:\GPT-SoVITS，HF-Mirror 源，CU126
python install.py --source ModelScope  # 换 ModelScope 模型源（HF-Mirror 慢时）
python install.py --device CU128       # 显卡驱动支持 CUDA 12.8 时
python install.py --device CPU         # 无显卡，强行装 CPU 版（能跑但慢）
```

默认安装目录 `D:\GPT-SoVITS`（纯英文路径，规避 Windows 原生程序的中文路径坑）。

## 验证边界（重要）

本插件在**无 GPU 的 Windows 机器**上开发：

- **已验证**：环境体检脚本 `check_env.py` 能正确判断 GPU / 磁盘 / 网络 / Python；部署流程已按官方 `install.ps1` 源码逐行核对（CUDA 版本、模型仓库名、依赖文件名均对齐官方）。
- **未完整验证**：`install.py` 的完整部署（需要 NVIDIA GPU + conda，本机没有）。首次在显卡机器上跑若有个别环节报错，以 [官方 README](https://github.com/RVC-Boss/GPT-SoVITS) 为准微调。

## 上游

- 项目：https://github.com/RVC-Boss/GPT-SoVITS
- 官方安装：`pwsh -F install.ps1 --Device CU126 --Source HF-Mirror`
- 协议：MIT（可自由使用、修改、商用）

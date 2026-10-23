# -*- coding: utf-8 -*-
"""voice-clone 插件：GPT-SoVITS 一键部署脚本（官方 install.ps1 的薄封装）

在带 NVIDIA GPU 的 Windows 机器上部署开源声音克隆项目 GPT-SoVITS
（https://github.com/RVC-Boss/GPT-SoVITS ，MIT 协议，中文效果最好）。

本脚本不自己重造依赖安装逻辑，而是「薄封装」官方安装脚本 install.ps1，
把容易写错的 CUDA wheel 版本、模型下载地址、依赖清单全部交给官方脚本，
只做三件增值事：
  1) 环境体检（GPU / 磁盘 / Python / git / conda / 网络）
  2) 自动选择国内可用的模型源（默认 HF-Mirror，避开 HuggingFace 直连）
  3) 自动选择 CUDA 版本（按显卡驱动，缺省 CU126）

官方 install.ps1 会完成：
  - conda 装 ffmpeg + cmake
  - 下载预训练模型（pretrained_models / G2PWModel / nltk_data / open_jtalk）
  - 按 CUDA 版本装 PyTorch（cu126/cu128/cpu）
  - pip 装 extra-req.txt + requirements.txt

用法：
  python install.py                      # 默认：D:\\GPT-SoVITS，HF-Mirror 源，CU126
  python install.py --source ModelScope  # 换 ModelScope 模型源
  python install.py --device CU128       # 指定 CUDA 版本
  python install.py --device CPU         # 无显卡时强行装 CPU 版（可跑，但很慢）

环境变量：CLONE_INSTALL_DIR / CLONE_SOURCE / CLONE_DEVICE
"""
import argparse
import os
import shutil
import subprocess
import sys

DEFAULT_DIR = r"D:\GPT-SoVITS"
REPO = "https://ghfast.top/https://github.com/RVC-Boss/GPT-SoVITS.git"
DEFAULT_SOURCE = os.environ.get("CLONE_SOURCE", "HF-Mirror")   # HF | HF-Mirror | ModelScope
DEFAULT_DEVICE = os.environ.get("CLONE_DEVICE", "CU126")       # CU126 | CU128 | CPU
CONDA_ENV = "GPTSoVits"  # 与官方 README 一致的 conda 环境名


def run(cmd, cwd=None, env=None, check=False):
    e = dict(os.environ)
    if env:
        e.update(env)
    print("  $ " + " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, env=e, check=False)


def which(name):
    return shutil.which(name) is not None


def find_conda():
    """定位 conda 可执行文件：PATH 或常见安装目录。"""
    if which("conda"):
        return "conda"
    for base in (
        os.environ.get("USERPROFILE", ""),
        r"C:\ProgramData",
        r"C:\Miniconda3",
        r"C:\Program Files",
    ):
        if not base:
            continue
        for sub in ("Miniconda3", "anaconda3", "miniconda3", "Anaconda3"):
            for exe in ("Scripts\\conda.exe", "condabin\\conda.bat", "Scripts\\conda.bat"):
                p = os.path.join(base, sub, exe)
                if os.path.exists(p):
                    return p
    return None


def check_env():
    print("[1/5] 环境体检 ...")
    here = os.path.dirname(os.path.abspath(__file__))
    r = run([sys.executable, os.path.join(here, "check_env.py")])
    if r.returncode != 0:
        return False
    if not which("git"):
        print("  [缺] git 未安装，请先装 Git for Windows：https://git-scm.com/")
        return False
    conda = find_conda()
    if not conda:
        print("  [缺] conda 未安装（GPT-SoVITS 官方脚本依赖 conda 装 ffmpeg/cmake）。")
        print("       请先装 Miniconda：https://docs.conda.io/en/latest/miniconda.html")
        return False
    print("  [OK] conda: {}".format(conda))
    return True


def step_clone(target):
    if os.path.exists(os.path.join(target, ".git")):
        print("[跳过] 已存在仓库：{}".format(target))
        return True
    print("[2/5] 克隆 GPT-SoVITS 源码（ghfast 镜像）...")
    r = run(["git", "clone", REPO, target])
    return r.returncode == 0


def step_conda_env(conda):
    """创建 conda 环境（若不存在），返回激活后调用 python 的前缀。"""
    print("[3/5] 准备 conda 环境 {} ...".format(CONDA_ENV))
    r = run([conda, "env", "list"])
    # 检查环境是否已存在
    exists = False
    try:
        out = subprocess.run([conda, "env", "list"], capture_output=True, text=True).stdout
        exists = any(line.split()[0] == CONDA_ENV for line in out.splitlines() if line and not line.startswith("#"))
    except Exception:
        pass
    if exists:
        print("  [跳过] conda 环境已存在：{}".format(CONDA_ENV))
    else:
        r = run([conda, "create", "-n", CONDA_ENV, "python=3.10", "-y"])
        if r.returncode != 0:
            return None
    return True


def step_official_install(conda, target, device, source):
    """调用官方 install.ps1（在 conda 环境内用 pwsh 执行）。"""
    print("[4/5] 调用官方 install.ps1（device={}, source={}）...".format(device, source))
    if not which("pwsh"):
        print("  [缺] PowerShell 7 (pwsh) 未安装，官方脚本需要它。")
        print("       安装：winget install Microsoft.PowerShell  或 https://github.com/PowerShell/PowerShell")
        return False
    script = os.path.join(target, "install.ps1")
    if not os.path.exists(script):
        print("  [缺] 找不到 {}".format(script))
        return False
    # 在 conda 环境里激活后跑 pwsh，把官方脚本的 conda/pip 调用指向该环境
    activate = [conda, "run", "-n", CONDA_ENV, "pwsh", "-F", script,
                "--Device", device, "--Source", source]
    r = run(activate, cwd=target)
    return r.returncode == 0


def step_launcher(target, conda):
    """生成 start.bat：激活 conda 环境后启动官方 webui.py。"""
    print("[5/5] 生成 start.bat 启动器 ...")
    bat = os.path.join(target, "start.bat")
    with open(bat, "w", encoding="gbk") as f:
        f.write("@echo off\r\n")
        f.write("chcp 65001 >nul\r\n")
        f.write('cd /d "{}"\r\n'.format(target))
        f.write('"{}" run -n {} python webui.py zh_CN\r\n'.format(conda, CONDA_ENV))
        f.write("pause\r\n")
    print("  启动器已生成：{}".format(bat))
    return True


def main():
    ap = argparse.ArgumentParser(description="GPT-SoVITS 一键部署（官方脚本薄封装）")
    ap.add_argument("--dir", default=os.environ.get("CLONE_INSTALL_DIR", DEFAULT_DIR))
    ap.add_argument("--source", default=DEFAULT_SOURCE,
                    choices=["HF", "HF-Mirror", "ModelScope"], help="模型下载源")
    ap.add_argument("--device", default=DEFAULT_DEVICE,
                    choices=["CU126", "CU128", "CPU"], help="CUDA 版本")
    args = ap.parse_args()

    target = args.dir
    print("=" * 56)
    print("GPT-SoVITS 一键部署（官方 install.ps1 薄封装）")
    print("  安装目录 : {}".format(target))
    print("  模型源   : {}".format(args.source))
    print("  CUDA     : {}".format(args.device))
    print("=" * 56)

    if not check_env():
        print("\n环境体检未通过，已停止。请按上面提示处理后重试。")
        return 1

    conda = find_conda()
    os.makedirs(target, exist_ok=True)

    if not step_clone(target):
        print("克隆失败，请检查网络后重试。")
        return 1

    if not step_conda_env(conda):
        print("conda 环境创建失败。")
        return 1

    if not step_official_install(conda, target, args.device, args.source):
        print("\n官方 install.ps1 执行失败。常见原因：")
        print("  - 显卡驱动未装 CUDA，或 CUDA 版本选错（试试 --device CPU）")
        print("  - 模型源下载超时（换 --source ModelScope 或 HF 重试）")
        return 1

    step_launcher(target, conda)

    print("=" * 56)
    print("部署完成！启动：双击 {}".format(os.path.join(target, "start.bat")))
    print("首次打开 WebUI 后，导入参考音频即可克隆音色。")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    sys.exit(main())

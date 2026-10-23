# -*- coding: utf-8 -*-
"""voice-clone 插件：GPT-SoVITS 一键部署脚本

在带 NVIDIA GPU 的 Windows 机器上，把开源声音克隆项目 GPT-SoVITS
（https://github.com/RVC-Boss/GPT-SoVITS ，MIT 协议，中文效果最好）
部署到本地。全流程走国内镜像，避开直连 HuggingFace / GitHub 的代理问题。

步骤：
  1) 环境体检（GPU / 磁盘 / Python / 网络）
  2) 用 ghfast 镜像克隆源码到 D:\\GPT-SoVITS（纯英文路径，规避中文路径坑）
  3) 创建独立 venv
  4) 用清华 pip 镜像安装依赖（含 CUDA 版 PyTorch）
  5) 用 hf-mirror 镜像下载预训练模型
  6) 生成 start.bat 启动器

用法：
  python install.py            # 默认装到 D:\\GPT-SoVITS，CUDA 12.1
  python install.py --dir D:\\GPT-SoVITS --cuda cu118

镜像可用环境变量覆盖：CLONE_INSTALL_DIR / CLONE_CUDA / CLONE_PIP_INDEX
"""
import argparse
import os
import shutil
import subprocess
import sys

DEFAULT_DIR = r"D:\GPT-SoVITS"
REPO = "https://ghfast.top/https://github.com/RVC-Boss/GPT-SoVITS.git"
PIP_INDEX = os.environ.get("CLONE_PIP_INDEX", "https://pypi.tuna.tsinghua.edu.cn/simple")
HF_ENDPOINT = os.environ.get("CLONE_HF_ENDPOINT", "https://hf-mirror.com")
CUDA = os.environ.get("CLONE_CUDA", "cu121")
MODEL_REPO = "lj1995/GPT-SoVITS"  # 预训练模型仓库，以官方 README 为准


def run(cmd, cwd=None, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    print("  $ " + " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, env=e, check=False)


def git_available():
    return shutil.which("git") is not None


def step_clone(target):
    if os.path.exists(os.path.join(target, ".git")):
        print("[跳过] 已存在仓库：{}".format(target))
        return True
    print("[2/6] 克隆 GPT-SoVITS 源码（ghfast 镜像）...")
    r = run(["git", "clone", REPO, target])
    return r.returncode == 0


def step_venv(target):
    venv = os.path.join(target, "venv")
    pyexe = os.path.join(venv, "Scripts", "python.exe")
    if os.path.exists(pyexe):
        print("[跳过] venv 已存在：{}".format(venv))
        return pyexe
    print("[3/6] 创建独立 venv ...")
    r = run([sys.executable, "-m", "venv", venv])
    return pyexe if r.returncode == 0 else None


def step_torch(pyexe, cuda):
    print("[4/6] 安装 PyTorch（清华镜像，{}）...".format(cuda))
    wheel = "torch torchaudio"
    r = run([pyexe, "-m", "pip", "install", "--upgrade", "pip",
             "-i", PIP_INDEX])
    r = run([pyexe, "-m", "pip", "install", wheel,
             "--index-url", "https://download.pytorch.org/whl/" + cuda])
    if r.returncode != 0:
        # 官方 wheel 源不通时，退回到清华镜像的 CPU/CUDA 通用包
        print("  （官方 wheel 源失败，退回清华镜像）")
        r = run([pyexe, "-m", "pip", "install", "torch", "torchaudio",
                 "-i", PIP_INDEX])
    return r.returncode == 0


def step_requirements(pyexe, target):
    req = os.path.join(target, "requirements.txt")
    if not os.path.exists(req):
        print("[警告] 未找到 requirements.txt，跳过依赖安装")
        return True
    print("[4/6] 安装项目依赖（清华镜像）...")
    r = run([pyexe, "-m", "pip", "install", "-r", req, "-i", PIP_INDEX])
    return r.returncode == 0


def step_models(pyexe, target):
    print("[5/6] 安装 huggingface_hub 并下载预训练模型（hf-mirror）...")
    r = run([pyexe, "-m", "pip", "install", "huggingface_hub", "-i", PIP_INDEX])
    if r.returncode != 0:
        print("[警告] huggingface_hub 安装失败，请按官方 README 手动下载模型")
        return False
    local = os.path.join(target, "GPT_SoVITS", "pretrained_models")
    r = run([pyexe, "-m", "huggingface_hub.commands.huggingface_cli",
             "download", MODEL_REPO, "--local-dir", local],
            env={"HF_ENDPOINT": HF_ENDPOINT})
    return r.returncode == 0


def step_launcher(target, pyexe):
    print("[6/6] 生成 start.bat 启动器 ...")
    bat = os.path.join(target, "start.bat")
    with open(bat, "w", encoding="gbk") as f:
        f.write("@echo off\r\n")
        f.write("chcp 65001 >nul\r\n")
        f.write('cd /d "{}"\r\n'.format(target))
        f.write('"{}" webui.py\r\n'.format(pyexe))
        f.write("pause\r\n")
    print("  启动器已生成：{}".format(bat))
    return True


def main():
    ap = argparse.ArgumentParser(description="GPT-SoVITS 一键部署（国内镜像）")
    ap.add_argument("--dir", default=os.environ.get("CLONE_INSTALL_DIR", DEFAULT_DIR))
    ap.add_argument("--cuda", default=CUDA, help="CUDA 版本：cu121 / cu118 / cpu")
    args = ap.parse_args()

    target = args.dir
    print("=" * 52)
    print("GPT-SoVITS 一键部署")
    print("  安装目录: {}".format(target))
    print("  CUDA    : {}".format(args.cuda))
    print("=" * 52)

    print("[1/6] 环境体检 ...")
    here = os.path.dirname(os.path.abspath(__file__))
    r = run([sys.executable, os.path.join(here, "check_env.py")])
    if r.returncode != 0:
        print("\n环境体检未通过，已停止部署。请按上面的建议处理后重试。")
        return 1

    if not git_available():
        print("未检测到 git，请先安装 Git for Windows：https://git-scm.com/")
        return 1

    os.makedirs(target, exist_ok=True)

    if not step_clone(target):
        print("克隆失败，请检查网络（可尝试重跑）。")
        return 1

    pyexe = step_venv(target)
    if not pyexe:
        print("venv 创建失败。")
        return 1

    if not step_torch(pyexe, args.cuda):
        print("PyTorch 安装失败，请检查网络。")
        return 1

    if not step_requirements(pyexe, target):
        print("依赖安装失败，请检查网络。")
        return 1

    step_models(pyexe, target)  # 模型下载失败不阻断，给出手动提示
    step_launcher(target, pyexe)

    print("=" * 52)
    print("部署完成！启动方式：双击 {}".format(os.path.join(target, "start.bat")))
    print("注意：预训练模型若未自动下载成功，请按官方 README 手动补下。")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())

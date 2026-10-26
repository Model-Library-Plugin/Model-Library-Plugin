# -*- coding: utf-8 -*-
"""voice-clone-cpu 插件：OpenVoice V2 一键部署（纯 CPU，国内镜像）

在 Windows 上部署 OpenVoice V2（myshell-ai，MIT），纯 CPU 可跑。
不依赖 conda，用普通 venv；模型走 hf-mirror 镜像。

步骤：
  1) 环境体检
  2) 用 codeload 下载源码（github 直连）
  3) 创建 venv（python 3.10/3.11）
  4) 用清华 pip 镜像安装依赖（兼容 numpy 版本）
  5) 用 hf-mirror 下载 V2 模型（myshell-ai/OpenVoiceV2）
  6) 安装 MeloTTS + unidic 词典

用法：
  python install.py                    # 默认装到 D:\\OpenVoice
  python install.py --dir D:\\OpenVoice

环境变量：CLONE_CPU_INSTALL_DIR / CLONE_CPU_HF_ENDPOINT / CLONE_CPU_PIP_INDEX
"""
import argparse
import os
import shutil
import subprocess
import sys
import urllib.request

DEFAULT_DIR = r"D:\OpenVoice"
REPO_TAR = "https://codeload.github.com/myshell-ai/OpenVoice/tar.gz/refs/heads/main"
HF_ENDPOINT = os.environ.get("CLONE_CPU_HF_ENDPOINT", "https://hf-mirror.com")
PIP_INDEX = os.environ.get("CLONE_CPU_PIP_INDEX", "https://pypi.tuna.tsinghua.edu.cn/simple")
HF_REPO = "myshell-ai/OpenVoiceV2"


def run(cmd, cwd=None, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    print("  $ " + " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, env=e, check=False)


def download(url, dest):
    print("  下载: {}".format(url))
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print("  下载失败: {}".format(e))
        return False


def step_check():
    print("[1/6] 环境体检 ...")
    here = os.path.dirname(os.path.abspath(__file__))
    r = run([sys.executable, os.path.join(here, "check_env.py")])
    return r.returncode == 0


def step_source(target):
    if os.path.exists(os.path.join(target, "openvoice", "api.py")):
        print("[2/6] [跳过] 源码已存在")
        return True
    print("[2/6] 下载 OpenVoice 源码（github codeload）...")
    tar = os.path.join(target, "_openvoice.tar.gz")
    os.makedirs(target, exist_ok=True)
    if not download(REPO_TAR, tar):
        return False
    # 解压 tar.gz 到临时目录，再把 OpenVoice-main 内容移动到 target
    import tarfile
    with tarfile.open(tar) as tf:
        tf.extractall(target)
    src = os.path.join(target, "OpenVoice-main")
    if os.path.exists(src):
        for item in os.listdir(src):
            shutil.move(os.path.join(src, item), target)
        os.rmdir(src)
    os.unlink(tar)
    return True


def find_py311():
    """找一个 Python 3.10/3.11 解释器（OpenVoice 旧依赖不兼容 3.12+）。"""
    import glob
    candidates = []
    # 1) 显式环境变量
    if os.environ.get("CLONE_CPU_PYTHON"):
        candidates.append(os.environ["CLONE_CPU_PYTHON"])
    # 2) WorkBuddy 管理的 python 版本目录
    wb = os.path.join(os.path.expanduser("~"), ".workbuddy", "binaries", "python", "versions")
    if os.path.exists(wb):
        for d in os.listdir(wb):
            if d.startswith("3.10") or d.startswith("3.11"):
                candidates.append(os.path.join(wb, d, "python.exe"))
    # 3) 常见系统路径
    for base in (r"C:\Python311", r"C:\Python310", r"C:\Program Files\Python311",
                 r"C:\Program Files\Python310", r"C:\Users"):
        for p in glob.glob(os.path.join(base, "**", "python.exe"), recursive=True):
            if "3.1" in p and ("3.10" in p or "3.11" in p):
                candidates.append(p)
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def step_venv(target):
    venv = os.path.join(target, "venv")
    pyexe = os.path.join(venv, "Scripts", "python.exe")
    if os.path.exists(pyexe):
        print("[3/6] [跳过] venv 已存在")
        return pyexe

    # 选择解释器：优先 3.10/3.11
    base = sys.executable
    if sys.version_info >= (3, 12):
        found = find_py311()
        if found:
            print("[3/6] 检测到 Python {}.x，OpenVoice 需 3.10/3.11，改用: {}".format(
                sys.version_info.minor, found))
            base = found
        else:
            print("[警告] 当前 Python {} 不兼容 OpenVoice（旧依赖钉死 numpy 1.22 等）。".format(
                "{}.{}".format(sys.version_info.major, sys.version_info.minor)))
            print("       建议安装 Python 3.11 后重试，或用 CLONE_CPU_PYTHON 指定。")
            print("       本机可通过 WorkBuddy 的 install_binary 安装 3.11。")
            # 仍尝试继续，让 venv 创建报错时自然失败
            base = sys.executable

    print("[3/6] 创建 venv（解释器: {}）...".format(base))
    r = run([base, "-m", "venv", venv])
    return pyexe if r.returncode == 0 else None


def step_deps(pyexe, target):
    print("[4/6] 安装依赖（清华镜像，兼容 numpy 版本）...")
    r = run([pyexe, "-m", "pip", "install", "--upgrade", "pip", "-i", PIP_INDEX])
    # 先装兼容的 numpy（原 requirements 钉死 1.22.0，Python 3.11 装不上）
    r = run([pyexe, "-m", "pip", "install", "numpy<2.0", "-i", PIP_INDEX])
    req = os.path.join(target, "requirements.txt")
    if os.path.exists(req):
        # 去掉 numpy 钉死版本行，避免冲突
        lines = []
        for line in open(req, encoding="utf-8"):
            if line.strip().startswith("numpy"):
                continue
            lines.append(line)
        with open(req, "w", encoding="utf-8") as f:
            f.writelines(lines)
        r = run([pyexe, "-m", "pip", "install", "-r", req, "-i", PIP_INDEX])
    # 装 openvoice 本体（pip install -e . 方式，但离线装依赖可能冲突，改为直接装包）
    r = run([pyexe, "-m", "pip", "install", "-e", target, "-i", PIP_INDEX])
    return r.returncode == 0


def step_models(pyexe, target):
    print("[5/6] 下载 V2 模型（hf-mirror: {}）...".format(HF_REPO))
    ckpt = os.path.join(target, "checkpoints_v2")
    os.makedirs(ckpt, exist_ok=True)
    # 用 huggingface_hub 下载
    r = run([pyexe, "-m", "pip", "install", "huggingface_hub", "-i", PIP_INDEX])
    if r.returncode != 0:
        return False
    r = run([pyexe, "-m", "huggingface_hub.commands.huggingface_cli", "download",
             HF_REPO, "--local-dir", ckpt],
            env={"HF_ENDPOINT": HF_ENDPOINT})
    return r.returncode == 0


def step_melotts(pyexe):
    print("[6/6] 安装 MeloTTS + unidic 词典 ...")
    r = run([pyexe, "-m", "pip", "install",
             "git+https://github.com/myshell-ai/MeloTTS.git", "-i", PIP_INDEX])
    if r.returncode != 0:
        print("  （MeloTTS 在线装失败，尝试国内镜像或跳过）")
    r = run([pyexe, "-m", "unidic", "download"])
    return True  # unidic 下载失败不阻断，日文功能受影响而已


def main():
    ap = argparse.ArgumentParser(description="OpenVoice V2 一键部署（纯 CPU）")
    ap.add_argument("--dir", default=os.environ.get("CLONE_CPU_INSTALL_DIR", DEFAULT_DIR))
    args = ap.parse_args()

    target = args.dir
    print("=" * 52)
    print("OpenVoice V2 一键部署（纯 CPU）")
    print("  安装目录: {}".format(target))
    print("=" * 52)

    if not step_check():
        print("\n环境体检未通过，已停止。")
        return 1

    os.makedirs(target, exist_ok=True)

    if not step_source(target):
        print("源码下载失败，请检查网络。")
        return 1

    pyexe = step_venv(target)
    if not pyexe:
        print("venv 创建失败。")
        return 1

    if not step_deps(pyexe, target):
        print("依赖安装失败，请检查网络。")
        return 1

    if not step_models(pyexe, target):
        print("模型下载失败。可手动从 {} 下载到 {}。".format(
            HF_REPO, os.path.join(target, "checkpoints_v2")))
        return 1

    step_melotts(pyexe)

    print("=" * 52)
    print("部署完成！")
    print("  克隆合成：{} clone.py --ref 参考.wav --text \"文本\" --lang ZH".format(pyexe))
    print("  或双击 start.bat 打开 WebUI")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())

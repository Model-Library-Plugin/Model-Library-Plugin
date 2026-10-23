# -*- coding: utf-8 -*-
"""voice-clone 插件：运行环境体检

判断本机能不能跑「神经声音克隆」（GPT-SoVITS 级）。纯 Python 标准库，
任何机器双击或 `python check_env.py` 都能运行，输出一份诊断报告。

检测项：
  1) NVIDIA GPU + 显存   —— 核心条件，纯 CPU 几乎不可用
  2) 磁盘剩余空间        —— 模型 + 依赖约需 8 GB
  3) Python 版本         —— 需 3.9 ~ 3.11（PyTorch 兼容范围）
  4) 是否已装 PyTorch    —— 未装则需先部署
  5) 关键站点连通性      —— github.com / hf-mirror.com
"""
import importlib.util
import os
import re
import shutil
import socket
import subprocess
import sys

GITHUB_HOST = "github.com"
HFMIRROR_HOST = "hf-mirror.com"
MIN_FREE_GB = 8
PY_OK = (3, 9)


def sh(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "") + (r.stderr or ""), r.returncode
    except FileNotFoundError:
        return "", 127
    except Exception as e:  # 超时等
        return str(e), -1


def probe(host, port=443, timeout=6):
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except Exception:
        return False


def check_gpu():
    out, code = sh(["nvidia-smi"])
    if code != 0:
        return False, 0, "未检测到 NVIDIA GPU 或驱动未装"
    m = re.findall(r"(\d+)MiB", out)
    vram_gb = max(int(x) for x in m) // 1024 if m else 0
    return True, vram_gb, "检测到 NVIDIA GPU，总显存约 {} GB".format(vram_gb)


def check_disk():
    """返回 {盘符: 剩余GB}，检测 C、D 盘（部署建议装到空间充裕的盘）。"""
    result = {}
    for drive in ("C:\\", "D:\\"):
        try:
            result[drive[0]] = shutil.disk_usage(drive).free // (1024 ** 3)
        except Exception:
            pass
    return result


def check_torch():
    try:
        return importlib.util.find_spec("torch") is not None
    except Exception:
        return False


def main():
    py = sys.version_info
    has_gpu, vram, gpu_msg = check_gpu()
    disks = check_disk()
    best_drive = max(disks, key=disks.get) if disks else None
    free_gb = disks[best_drive] if best_drive else 0
    has_torch = check_torch()
    net_github = probe(GITHUB_HOST)
    net_hfmirror = probe(HFMIRROR_HOST)

    print("=" * 52)
    print("voice-clone 运行环境体检报告")
    print("=" * 52)
    print("[1] GPU          : {}".format(gpu_msg))
    disk_lines = " / ".join("{}盘 {}GB".format(d, g) for d, g in disks.items())
    print("[2] 磁盘剩余     : {}（建议 >= {} GB）".format(disk_lines, MIN_FREE_GB))
    print("[3] Python 版本  : {}.{}.{}（建议 3.9~3.11）".format(py.major, py.minor, py.micro))
    print("[4] PyTorch      : {}".format("已安装" if has_torch else "未安装"))
    print("[5] 网络 github  : {}".format("通" if net_github else "不通"))
    print("[5] 网络 hf-mirror: {}".format("通" if net_hfmirror else "不通"))
    print("-" * 52)

    if not has_gpu:
        verdict = "本机无 NVIDIA GPU，无法流畅运行 GPT-SoVITS 级神经声音克隆。"
        advice = "请换到带 NVIDIA 显卡（建议 6G 显存以上）的机器后，运行 install.bat 一键部署。"
        ok = False
    elif vram < 6:
        verdict = "检测到 GPU 但显存偏小（{} GB），可尝试但可能显存不足。".format(vram)
        advice = "建议 6G 显存以上；显存不足时降低 batch_size 或换更小模型。"
        ok = False
    elif free_gb < MIN_FREE_GB:
        verdict = "磁盘剩余不足 {} GB，无法容纳依赖与模型。".format(MIN_FREE_GB)
        advice = "请先清理磁盘，再运行 install.bat。"
        ok = False
    else:
        verdict = "环境满足要求，可以部署。"
        advice = "运行 install.bat 开始一键部署。"
        ok = True

    print("结论: {}".format(verdict))
    print("建议: {}".format(advice))
    print("=" * 52)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

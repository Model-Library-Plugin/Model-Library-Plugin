# -*- coding: utf-8 -*-
"""voice-clone-cpu 插件：环境体检（OpenVoice 纯 CPU 声音克隆）

检测本机能否运行 OpenVoice 声音克隆，输出体检报告。
纯 Python 标准库，无第三方依赖，可直接运行。

用法：
  python check_env.py
"""
import os
import shutil
import socket
import subprocess
import sys
import urllib.request

MIN_FREE_GB = 5


def check_gpu():
    """检测 NVIDIA GPU。OpenVoice 纯 CPU 也能跑，GPU 只是加速。"""
    try:
        out = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            vram = "未知"
            for line in out.stdout.splitlines():
                if "MiB" in line:
                    vram = line.strip()
                    break
            return True, vram, "检测到 NVIDIA GPU"
    except Exception:
        pass
    return False, None, "无 NVIDIA GPU（OpenVoice 纯 CPU 也能跑，速度较慢）"


def check_disk():
    result = {}
    for drive in ("C:\\", "D:\\"):
        try:
            result[drive[0]] = shutil.disk_usage(drive).free // (1024 ** 3)
        except Exception:
            pass
    return result


def check_python():
    v = sys.version_info
    ver = "{}.{}.{}".format(v.major, v.minor, v.micro)
    if (v.major, v.minor) in ((3, 10), (3, 11)):
        return True, ver, "版本合适"
    return False, ver, "建议 3.10~3.11（3.12+ 部分旧依赖不兼容）"


def check_net():
    results = []
    for name, url in (
        ("github", "https://github.com"),
        ("hf-mirror", "https://hf-mirror.com"),
        ("pypi-清华", "https://pypi.tuna.tsinghua.edu.cn/simple"),
    ):
        try:
            req = urllib.request.Request(url, method="HEAD")
            urllib.request.urlopen(req, timeout=8)
            results.append((name, "通"))
        except Exception:
            results.append((name, "不通"))
    return results


def main():
    print("=" * 52)
    print("voice-clone-cpu 运行环境体检报告（OpenVoice）")
    print("=" * 52)
    ok = True

    has_gpu, vram, gpu_msg = check_gpu()
    if has_gpu:
        print("[1] GPU          : {}".format(gpu_msg))
    else:
        print("[1] GPU          : {}（纯 CPU 可跑）".format(gpu_msg))

    disks = check_disk()
    disk_lines = " / ".join("{}盘 {}GB".format(d, g) for d, g in disks.items())
    free_ok = any(g >= MIN_FREE_GB for g in disks.values())
    if not free_ok:
        ok = False
    print("[2] 磁盘剩余     : {}（建议 >= {} GB）".format(disk_lines, MIN_FREE_GB))

    py_ok, ver, py_msg = check_python()
    # Python 版本仅提示（install.py 会自动探测 3.10/3.11），不硬失败
    warn = "" if py_ok else "（install.py 会自动找 3.10/3.11，找不到才停）"
    print("[3] Python 版本  : {}（{}）{}".format(ver, py_msg, warn))

    for name, status in check_net():
        flag = "通" if status == "通" else "不通"
        print("[4] 网络 {:<6} : {}".format(name, flag))

    if not shutil.which("git"):
        ok = False
        print("[5] git          : 未安装（部署需要）")

    print("-" * 52)
    if not ok:
        print("结论: 环境有缺失项，请按上面提示处理后重试。")
    else:
        print("结论: 环境就绪，可运行 install.bat 部署 OpenVoice。")
        if not has_gpu:
            print("提示: 纯 CPU 合成速度较慢（一句约几十秒），属正常现象。")
    print("=" * 52)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

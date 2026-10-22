# -*- coding: utf-8 -*-
"""voice-tts 插件：本地离线中文语音合成（文本 → 语音）

把文本变成可播放的语音，完全离线运行，不依赖任何在线 API。

依赖（本机已部署）：
  - Piper 引擎:  C:\\piper-tts\\piper.exe
  - 中文音色:    C:\\piper-tts\\zh_CN-huayan-medium.onnx
  - ffmpeg:      C:\\ffmpeg\\ffmpeg.exe（仅导出 mp3 时需要）

路径可用环境变量覆盖：VOICE_PIPER_DIR / VOICE_MODEL / VOICE_FFMPEG

重要实现细节：piper 与 ffmpeg 是 Windows 原生程序，无法处理含中文的文件
路径。因此所有中间文件固定放在英文临时目录（引擎目录下的 tmp\\），合成
完成后再由 Python 移动到用户指定的任意路径。

用法：
  python voice.py -t "你好，世界"
  python voice.py -f 文案.txt --mp3
  python voice.py -t "慢一点朗读" -r 1.25 -o 输出目录
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

PIPER_DIR = os.environ.get("VOICE_PIPER_DIR", r"C:\piper-tts")
MODEL = os.environ.get("VOICE_MODEL", os.path.join(PIPER_DIR, "zh_CN-huayan-medium.onnx"))
PIPER = os.path.join(PIPER_DIR, "piper.exe")
FFMPEG = os.environ.get("VOICE_FFMPEG", r"C:\ffmpeg\ffmpeg.exe")
TMP = os.path.join(PIPER_DIR, "tmp")  # 固定英文路径，引擎程序专用


def ensure_engine():
    missing = [p for p in (PIPER, MODEL) if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(
            "找不到引擎文件：{}（可用环境变量 VOICE_PIPER_DIR / VOICE_MODEL 指定）".format(", ".join(missing))
        )
    os.makedirs(TMP, exist_ok=True)


def synth(text, out_wav, rate=1.0):
    """文本 → wav。rate 即 Piper 的 length_scale：>1 变慢，<1 变快。"""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    tmp_txt = os.path.join(TMP, "in-{}.txt".format(stamp))
    tmp_wav = os.path.join(TMP, "out-{}.wav".format(stamp))
    with open(tmp_txt, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        with open(tmp_txt, "rb") as fin:
            subprocess.run(
                [PIPER, "-m", MODEL, "--length_scale", str(rate), "-f", tmp_wav],
                stdin=fin, check=True, capture_output=True,
            )
    finally:
        if os.path.exists(tmp_txt):
            os.unlink(tmp_txt)

    if not os.path.exists(tmp_wav) or os.path.getsize(tmp_wav) == 0:
        raise RuntimeError("语音合成失败：未生成有效音频")
    shutil.move(tmp_wav, out_wav)


def to_mp3(wav, mp3):
    """wav → mp3。输入输出路径可能含中文，先在英文临时目录转换再移动。"""
    if not os.path.exists(FFMPEG):
        raise FileNotFoundError("找不到 ffmpeg: {}（可用环境变量 VOICE_FFMPEG 指定）".format(FFMPEG))
    stamp = time.strftime("%Y%m%d-%H%M%S")
    src = wav
    tmp_mp3 = os.path.join(TMP, "mp3-{}.mp3".format(stamp))
    if not _is_ascii(wav):
        # 源 wav 路径含非 ASCII：先复制到临时目录再转
        src = os.path.join(TMP, "src-{}.wav".format(stamp))
        shutil.copyfile(wav, src)
    try:
        subprocess.run([FFMPEG, "-y", "-i", src, "-c:a", "libmp3lame", "-b:a", "128k", tmp_mp3],
                       check=True, capture_output=True)
        shutil.move(tmp_mp3, mp3)
    finally:
        if src != wav and os.path.exists(src):
            os.unlink(src)


def _is_ascii(s):
    try:
        s.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def main():
    ap = argparse.ArgumentParser(description="本地中文语音合成（Piper TTS，离线）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("-t", "--text", help="要合成的文本")
    g.add_argument("-f", "--file", help="要合成的文本文件（UTF-8）")
    ap.add_argument("-o", "--out-dir", default=".", help="输出目录（默认当前目录）")
    ap.add_argument("-n", "--name", default=None, help="输出文件名（不含扩展名，默认按时间生成）")
    ap.add_argument("-r", "--rate", type=float, default=1.0,
                    help="语速：1.0 正常，>1 慢，<1 快（默认 1.0）")
    ap.add_argument("--mp3", action="store_true", help="同时输出 mp3")
    args = ap.parse_args()

    text = args.text
    if args.file:
        with open(args.file, encoding="utf-8-sig") as f:
            text = f.read().strip()
    if not text:
        print("文本为空")
        return 1

    ensure_engine()
    os.makedirs(args.out_dir, exist_ok=True)
    name = args.name or time.strftime("voice-%Y%m%d-%H%M%S")
    wav = os.path.join(args.out_dir, name + ".wav")

    synth(text, wav, args.rate)
    print(wav)

    if args.mp3:
        mp3 = os.path.join(args.out_dir, name + ".mp3")
        to_mp3(wav, mp3)
        print(mp3)
    return 0


if __name__ == "__main__":
    sys.exit(main())

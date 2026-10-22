# -*- coding: utf-8 -*-
"""video-maker 插件：一键成片（文案 → 配音视频）

把一篇文案自动变成完整的竖屏短视频：
分句 → 本地 TTS 配音 → 按句生成字幕与渐变画面 → ffmpeg 合成 mp4。
全程离线，无需任何在线 API。

依赖（本机已部署）：
  - Piper 引擎:  C:\\piper-tts\\piper.exe（含 zh_CN-huayan-medium 模型）
  - ffmpeg:      C:\\ffmpeg\\ffmpeg.exe（需含 libx264 与 libfreetype）

路径可用环境变量覆盖：VOICE_PIPER_DIR / VOICE_MODEL / VOICE_FFMPEG / VIDEO_FONT

重要实现细节：piper 与 ffmpeg 是 Windows 原生程序，无法处理含中文的文件
路径。因此所有中间文件固定放在英文临时目录（引擎目录下的 tmp\\），成品
再由 Python 移动到目标位置。

用法：
  把写好文案的 txt 拖到「一键成片.bat」图标上；或：
  python make_video.py 文案.txt
"""
import os
import re
import shutil
import subprocess
import sys

PIPER_DIR = os.environ.get("VOICE_PIPER_DIR", r"C:\piper-tts")
MODEL = os.environ.get("VOICE_MODEL", os.path.join(PIPER_DIR, "zh_CN-huayan-medium.onnx"))
PIPER = os.path.join(PIPER_DIR, "piper.exe")
FFMPEG = os.environ.get("VOICE_FFMPEG", r"C:\ffmpeg\ffmpeg.exe")
FONT = os.environ.get("VIDEO_FONT", r"C:\Windows\Fonts\simhei.ttf")
TMP = os.path.join(PIPER_DIR, "tmp")  # 固定英文路径，引擎程序专用

PALETTES = [
    ((16, 24, 48), (72, 36, 108)),    # 深蓝 -> 紫
    ((56, 28, 88), (176, 72, 48)),    # 紫 -> 暖橙
    ((14, 44, 64), (30, 92, 72)),     # 青蓝 -> 绿
    ((40, 20, 60), (20, 60, 90)),     # 深紫 -> 蓝
    ((70, 30, 50), (24, 50, 80)),     # 酒红 -> 藏蓝
]

LINE_CHARS = 14  # 每行最多字数（超长自动换行）


def read_text(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read().strip()


def split_sentences(text):
    parts = [s.strip() for s in re.split(r"[。！？!?；;\n]+", text) if s.strip()]
    return parts if parts else [text]


def wrap(text, width=LINE_CHARS):
    return "\n".join(text[i:i + width] for i in range(0, len(text), width))


def make_bg(path, top, bottom, w=1080, h=1920):
    def lerp(a, b, t):
        return int(a + (b - a) * t)

    with open(path, "wb") as f:
        f.write("P6\n{} {}\n255\n".format(w, h).encode())
        for y in range(h):
            t = y / (h - 1)
            f.write(bytes((lerp(top[0], bottom[0], t),
                           lerp(top[1], bottom[1], t),
                           lerp(top[2], bottom[2], t))) * w)


def get_duration(wav):
    r = subprocess.run([FFMPEG, "-i", wav], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        return 0.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(TMP, "input.txt")
    if not os.path.exists(src):
        print("没找到文案文件。用法：把写好文案的 txt 拖到「一键成片.bat」图标上。")
        return 1
    text = read_text(src)
    if not text:
        print("文案是空的，先往 txt 里写点内容。")
        return 1

    for p in (PIPER, MODEL, FFMPEG):
        if not os.path.exists(p):
            print("找不到依赖：{}（可用环境变量 VOICE_PIPER_DIR / VOICE_FFMPEG 指定）".format(p))
            return 1
    os.makedirs(TMP, exist_ok=True)
    txt_local = os.path.join(TMP, "input.txt")
    shutil.copyfile(src, txt_local)

    print("[1/4] 正在配音（本地 Piper 引擎）...")
    wav = os.path.join(TMP, "audio.wav")
    with open(txt_local, "rb") as fin:
        subprocess.run([PIPER, "-m", MODEL, "-f", wav], stdin=fin,
                       capture_output=True, check=True)
    total = get_duration(wav)
    if total <= 0:
        print("配音失败（音频时长为 0）。")
        return 1
    print("      配音完成，时长 {:.1f} 秒".format(total))

    print("[2/4] 正在生成画面与字幕...")
    sents = split_sentences(text)
    chars = [max(len(s), 1) for s in sents]
    total_chars = sum(chars)

    inputs = []
    segs = []
    t = 0.0
    for i, s in enumerate(sents):
        dur = total * chars[i] / total_chars
        end = min(t + dur, total)
        segs.append((t, end, s))
        bg = os.path.join(TMP, "bg{}.ppm".format(i))
        top, bottom = PALETTES[i % len(PALETTES)]
        make_bg(bg, top, bottom)
        sub = os.path.join(TMP, "sub{}.txt".format(i))
        with open(sub, "w", encoding="utf-8") as f:
            f.write(wrap(s))
        inputs += ["-loop", "1", "-t", "{:.2f}".format(dur), "-i", bg]
        t = end

    n = len(segs)
    audio_idx = n
    inputs += ["-i", wav]

    bg_chain = "".join("[{}:v]".format(i) for i in range(n)) + \
        "concat=n={}:v=1:a=0[bg]".format(n)
    subs = []
    font = FONT.replace("\\", "/")
    font_filter = font[0] + "\\:" + font[2:]  # C:/xxx -> C\:/xxx（滤镜转义）
    for i, (st, en, _s) in enumerate(segs):
        sub_path = os.path.join(TMP, "sub{}.txt".format(i)).replace("\\", "/")
        subs.append(
            "drawtext=fontfile='" + font_filter + "'"
            ":textfile='C\\:/" + sub_path.split(":/", 1)[1] + "'"
            ":fontcolor=white:fontsize=50:x=(w-text_w)/2:y=h*0.42"
            ":line_spacing=24:box=1:boxcolor=black@0.25:boxborderw=18"
            ":enable='between(t,{:.2f},{:.2f})'".format(st, en)
        )
    filters = bg_chain + ";[bg]" + ",".join(subs) + "[v]"

    print("[3/4] 正在合成视频（画面切换 + 字幕 + 配音）...")
    out_local = os.path.join(TMP, "output.mp4")
    cmd = [FFMPEG, "-y", *inputs, "-filter_complex", filters,
           "-map", "[v]", "-map", "{}:a".format(audio_idx),
           "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-shortest", out_local]
    subprocess.run(cmd, check=True, capture_output=True)

    print("[4/4] 保存结果...")
    base = os.path.splitext(os.path.basename(src))[0]
    dst = os.path.join(os.path.dirname(os.path.abspath(src)), base + ".mp4")
    shutil.copyfile(out_local, dst)
    print("完成！视频已保存：{}".format(dst))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("出错了：{}".format(e))
        sys.exit(1)

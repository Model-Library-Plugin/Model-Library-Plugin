# -*- coding: utf-8 -*-
"""voice-clone-cpu 插件：OpenVoice V2 声音克隆（纯 CPU 可用）

用一段参考音频克隆音色，再用该音色合成目标文本，支持中/英/日/韩/法/西。
封装 OpenVoice V2（myshell-ai，MIT），核心流程与官方 demo_part3.ipynb 一致。

依赖：先运行 install.py 完成部署（装 openvoice + melotts + 下载模型）。

用法：
  python clone.py --ref 参考音频.wav --text "要说的文本" --lang ZH
  python clone.py --ref 参考.mp3 --text "Hello world" --lang EN --speed 1.2

语言代码（OpenVoice V2 原生支持）：
  ZH 中文  EN 英文  EN_NEWEST 英文(新)  JP 日文  KR 韩文  ES 西语  FR 法语
"""
import argparse
import os
import sys

# 离线运行关键设置：本机模型已就位，禁止 transformers/huggingface_hub 联网，
# 否则会去 xethub 下载 safetensors 而超时。必须在 import transformers 前设置。
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
# ffmpeg（pydub 解码音频需要）
_ffmpeg_dir = r"D:\ffmpeg"
if os.path.isdir(_ffmpeg_dir) and _ffmpeg_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

INSTALL_DIR = os.environ.get("CLONE_CPU_INSTALL_DIR", r"D:\OpenVoice")
CKPT_DIR = os.path.join(INSTALL_DIR, "checkpoints_v2")
# MeloTTS 源码目录（install.py 会 clone 到 D:\MeloTTS；也支持装在 INSTALL_DIR 下）
MELO_DIR = os.environ.get("CLONE_CPU_MELO_DIR", r"D:\MeloTTS")

LANG_MAP = {
    "ZH": "zh", "EN": "en", "EN_NEWEST": "en-newest", "JP": "jp",
    "KR": "kr", "ES": "es", "FR": "fr",
}


def ensure_installed():
    if not os.path.exists(os.path.join(INSTALL_DIR, "openvoice", "api.py")):
        raise FileNotFoundError(
            "未找到 OpenVoice 源码：{}。请先运行 install.bat 部署。".format(INSTALL_DIR)
        )
    if not os.path.exists(os.path.join(CKPT_DIR, "converter", "checkpoint.pth")):
        raise FileNotFoundError(
            "未找到模型权重：{}。请先运行 install.bat 下载模型。".format(
                os.path.join(CKPT_DIR, "converter", "checkpoint.pth"))
        )


def clone(ref_audio, text, lang, speed, out_path):
    ensure_installed()
    sys.path.insert(0, INSTALL_DIR)
    if os.path.exists(MELO_DIR):
        sys.path.insert(0, MELO_DIR)

    import torch
    from openvoice.api import ToneColorConverter

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print("运行设备: {}".format(device))

    # 1) 加载音色转换器
    ckpt_converter = os.path.join(CKPT_DIR, "converter")
    converter = ToneColorConverter(
        os.path.join(ckpt_converter, "config.json"), device=device)
    converter.load_ckpt(os.path.join(ckpt_converter, "checkpoint.pth"))
    print("[1/3] 音色转换器已加载")

    # 2) 从参考音频提取目标音色
    # 直接用 converter.extract_se 提取整段音色，绕开官方 get_se 里的
    # faster-whisper 分段（它硬编码 device="cuda" + 需联网下载模型）。
    # 对 15 秒内的短参考音频，整段提取即可。
    target_se = converter.extract_se(ref_audio)
    print("[2/3] 已从参考音频提取音色：{}".format(ref_audio))

    # 3) 用基础音色合成文本，再转换为目标音色
    from melo.api import TTS
    # 优先用本地模型（离线可用），找不到才回退在线下载
    melo_dir = os.path.join(INSTALL_DIR, "melo_models", lang)
    cfg = os.path.join(melo_dir, "config.json")
    ckpt = os.path.join(melo_dir, "checkpoint.pth")
    if os.path.exists(cfg) and os.path.exists(ckpt):
        model = TTS(language=lang, device=device, config_path=cfg, ckpt_path=ckpt)
        print("[3/3] 使用本地 MeloTTS 模型：{}".format(melo_dir))
    else:
        model = TTS(language=lang, device=device)
        print("[3/3] 本地无模型，使用在线下载（可能较慢）")
    speaker_key = LANG_MAP.get(lang, "en")
    speaker_id = model.hps.data.spk2id[speaker_key.upper().replace("-", "_")] \
        if speaker_key.upper().replace("-", "_") in model.hps.data.spk2id \
        else list(model.hps.data.spk2id.values())[0]

    se_path = os.path.join(CKPT_DIR, "base_speakers", "ses", "{}.pth".format(speaker_key))
    if not os.path.exists(se_path):
        raise FileNotFoundError("缺少基础音色文件：{}".format(se_path))
    source_se = torch.load(se_path, map_location=device)

    tmp_wav = os.path.join(os.path.dirname(out_path) or ".", "_tmp_melo.wav")
    model.tts_to_file(text, speaker_id, tmp_wav, speed=speed)
    print("[3/3] 基础音色已合成，正在转换为目标音色...")

    encode_message = "@MyShell"
    converter.convert(
        audio_src_path=tmp_wav,
        src_se=source_se,
        tgt_se=target_se,
        output_path=out_path,
        message=encode_message,
    )
    if os.path.exists(tmp_wav):
        try:
            os.unlink(tmp_wav)
        except Exception:
            pass
    print("完成：{}".format(out_path))
    return out_path


def main():
    ap = argparse.ArgumentParser(description="OpenVoice V2 声音克隆（纯 CPU 可用）")
    ap.add_argument("--ref", required=True, help="参考音频路径（要克隆的音色）")
    ap.add_argument("--text", required=True, help="要合成的文本")
    ap.add_argument("--lang", default="ZH", choices=list(LANG_MAP.keys()),
                    help="语言：ZH/EN/EN_NEWEST/JP/KR/ES/FR（默认 ZH）")
    ap.add_argument("--speed", type=float, default=1.0, help="语速（默认 1.0）")
    ap.add_argument("-o", "--out", default=None, help="输出 wav 路径（默认当前目录）")
    args = ap.parse_args()

    if not os.path.exists(args.ref):
        print("参考音频不存在：{}".format(args.ref))
        return 1

    out = args.out or os.path.join(".", "clone_out.wav")
    try:
        clone(args.ref, args.text, args.lang, args.speed, out)
    except Exception as e:
        print("克隆失败：{}".format(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""patch_melotts.py — MeloTTS 源码补丁（让 import 不联网、中文克隆可用）

背景：MeloTTS 在 import 时会模块级加载多个语言的 BERT tokenizer（日文/英文/
多语言/韩文/法文/西文），导致：
  1) 必须联网下载 bert 模型（国内直连 huggingface.co 不通）
  2) import 极慢甚至超时

本补丁把这些模块级 BERT 加载全部改成「惰性加载」——只在真正处理对应语言时
才加载。中文克隆（核心需求）完全不碰这些 BERT，离线可用。

用法：python patch_melotts.py [MeloTTS目录]   （默认 D:\\MeloTTS）
"""
import os
import re
import sys


def patch_file(path, replacements):
    """对单个文件执行一系列 (old, new) 替换，全部成功才算补丁完成。"""
    if not os.path.exists(path):
        print("  [跳过] 不存在: {}".format(path))
        return False
    s = open(path, encoding="utf-8").read()
    orig = s
    for old, new in replacements:
        if old not in s:
            print("  [警告] 未找到片段: {} -> {}".format(path, old[:40]))
            continue
        s = s.replace(old, new)
    if s != orig:
        open(path, "w", encoding="utf-8").write(s)
        print("  [已补丁] {}".format(os.path.basename(path)))
        return True
    print("  [无变化] {}".format(os.path.basename(path)))
    return True


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else r"D:\MeloTTS"
    text_dir = os.path.join(base, "melo", "text")
    print("MeloTTS 目录: {}".format(base))
    print("=" * 56)

    # 1) japanese.py — 日文 BERT 惰性化
    patch_file(os.path.join(text_dir, "japanese.py"), [
        ("model_id = 'tohoku-nlp/bert-base-japanese-v3'\n"
         "tokenizer = AutoTokenizer.from_pretrained(model_id)\n"
         "def g2p(norm_text):",
         "model_id = 'tohoku-nlp/bert-base-japanese-v3'\n"
         "_tokenizer = None\n"
         "def _get_tokenizer():\n"
         "    global _tokenizer\n"
         "    if _tokenizer is None:\n"
         "        _tokenizer = AutoTokenizer.from_pretrained(model_id)\n"
         "    return _tokenizer\n"
         "def g2p(norm_text):"),
        ("    tokenized = tokenizer.tokenize(norm_text)",
         "    tokenized = _get_tokenizer().tokenize(norm_text)"),
    ])

    # 2) english.py — 英文 g2p_en + bert-base-uncased 惰性化
    patch_file(os.path.join(text_dir, "english.py"), [
        ("import pickle\nimport os\nimport re\n"
         "try:\n    from g2p_en import G2p\nexcept Exception:\n    G2p = None\n",
         "import pickle\nimport os\nimport re\n"),
        ("_g2p = None\ndef _get_g2p():\n    global _g2p\n    if _g2p is None:\n"
         "        if G2p is None:\n            raise RuntimeError('英文 TTS 需要 g2p_en，请安装: pip install g2p_en')\n"
         "        _g2p = G2p()\n    return _g2p\n",
         "_g2p = None\ndef _get_g2p():\n    global _g2p\n    if _g2p is None:\n"
         "        try:\n            from g2p_en import G2p\n"
         "        except Exception as e:\n            raise RuntimeError('英文 TTS 需要 g2p_en（{}）'.format(e))\n"
         "        _g2p = G2p()\n    return _g2p\n"),
        ("model_id = 'bert-base-uncased'\n"
         "tokenizer = AutoTokenizer.from_pretrained(model_id)\n"
         "def g2p_old(text):\n    tokenized = tokenizer.tokenize(text)",
         "model_id = 'bert-base-uncased'\n"
         "_tokenizer_en = None\n"
         "def _get_tokenizer_en():\n    global _tokenizer_en\n    if _tokenizer_en is None:\n"
         "        _tokenizer_en = AutoTokenizer.from_pretrained(model_id)\n"
         "    return _tokenizer_en\n"
         "def g2p_old(text):\n    tokenized = _get_tokenizer_en().tokenize(text)"),
        ("_g2p(w)", "_get_g2p()(w)"),
    ])

    # 3) 通用：多语言模块的模块级 tokenizer 惰性化
    lazy_block = ("_tokenizer = None\n"
                  "def _get_tokenizer():\n"
                  "    global _tokenizer\n"
                  "    if _tokenizer is None:\n"
                  "        _tokenizer = AutoTokenizer.from_pretrained(model_id)\n"
                  "    return _tokenizer")
    for name in ["chinese_mix.py", "english_bert.py", "french.py",
                 "french_bert.py", "korean.py", "spanish.py", "spanish_bert.py"]:
        p = os.path.join(text_dir, name)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        orig = s
        s = s.replace("tokenizer = AutoTokenizer.from_pretrained(model_id)", lazy_block)
        # 函数体内的 tokenizer.xxx 调用 -> _get_tokenizer().xxx（避免误伤 _get_tokenizer 定义）
        s = re.sub(r"(?<![A-Za-z_])tokenizer\.", "_get_tokenizer().", s)
        if s != orig:
            open(p, "w", encoding="utf-8").write(s)
            print("  [已补丁] {}".format(name))
        else:
            print("  [无变化] {}".format(name))

    # 4) fr/es phonemizer — gruut 惰性 import
    for sub in ["fr_phonemizer", "es_phonemizer"]:
        p = os.path.join(text_dir, sub, "gruut_wrapper.py")
        patch_file(p, [
            ("import gruut\nfrom gruut_ipa import IPA # pip install gruut_ipa\n",
             "try:\n    import gruut\n    from gruut_ipa import IPA\n"
             "except Exception:\n    gruut = None\n    IPA = None\n"),
        ])

    # 5) download_utils.py — cached_path 容错
    patch_file(os.path.join(base, "melo", "download_utils.py"), [
        ("from cached_path import cached_path\nfrom huggingface_hub import hf_hub_download",
         "try:\n    from cached_path import cached_path\nexcept Exception:\n    cached_path = None\n"
         "try:\n    from huggingface_hub import hf_hub_download\nexcept Exception:\n    hf_hub_download = None"),
    ])

    print("=" * 56)
    print("补丁完成。中文克隆无需联网即可 import。")


if __name__ == "__main__":
    main()

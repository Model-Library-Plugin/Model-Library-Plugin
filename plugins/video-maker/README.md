# video-maker — 一键成片插件（文案转配音短视频）

把一篇文案自动变成**能直接发布的竖屏短视频**：自动分句 → 本地 TTS 配音 →
按句生成字幕与渐变画面 → ffmpeg 合成 1080x1920 的 mp4。
**全程离线**，无需联网、无需任何 API Key。

是 [voice-tts](../voice-tts/) 声音插件的进阶版：在配音之上，补齐了画面切换、
字幕时间轴与视频合成两环。

## 流水线（对应 MoneyPrinterTurbo 的核心环节）

```
文案 txt ──> 分句（按 。！？；换行）
        ──> Piper TTS 配音（得到总时长）
        ──> 按字数比例给每句分配时间段
        ──> 每句：一张渐变背景 + 一段字幕（自动换行）
        ──> ffmpeg：背景 concat + drawtext 字幕 + 配音 → mp4
```

## 快速开始

Windows：把写好文案的 txt **拖到 `一键成片.bat` 图标上**，同目录即生成同名 mp4。

命令行：

```bash
python make_video.py 文案.txt
```

## 文案建议

- 使用中文（Piper 中文模型对英文混排支持有限）
- 用句号/问号/感叹号/分号/换行分句——每句会成为一段画面和一条字幕
- 单句建议不超过 30 字，过长会自动换行但观感下降

## 依赖安装（一次性，与 voice-tts 共用）

1. Piper 引擎 + 中文模型 → `C:\piper-tts`（见 [voice-tts README](../voice-tts/README.md)）
2. ffmpeg（含 libx264、libfreetype）→ `C:\ffmpeg\ffmpeg.exe`
3. 中文字体：系统自带的黑体即可，默认用 `C:\Windows\Fonts\simhei.ttf`

> 坑提示：piper 与 ffmpeg 是 Windows 原生程序，**无法处理含中文的文件路径**。
> 本插件已内置规避：所有中间文件固定在英文临时目录，成品再移动到目标位置。

## 自定义

- **换配色**：改脚本顶部 `PALETTES`（多组渐变首尾色，按句轮换）
- **换字体/字号**：`VIDEO_FONT` 环境变量；字号在 `drawtext` 的 `fontsize=50`
- **换分辨率**：`make_bg` 的 `w, h`（注意保持竖屏比例适配目标平台）
- **调语速**：配音命令加 `--length_scale`（对应 voice-tts 的 `-r`）

## 验证环境

- Windows 10/11 + Python 3.11+
- 已实测：5 句文案（17.2 秒配音）一键成片，三段画面切换 + 字幕 + 配音全部正确

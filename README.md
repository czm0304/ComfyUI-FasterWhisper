# ComfyUI-FasterWhisper 🎤

<p align="center">
  <img src="https://img.shields.io/badge/ComfyUI-Custom_Node-blue" alt="ComfyUI">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow" alt="Python">
</p>

基于 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 的 ComfyUI 视频/音频语音识别和字幕烧录插件。支持多语言识别、AI翻译、双语字幕烧录等功能。

## ✨ 功能特点

- 🎬 **媒体加载器**: 支持加载视频和音频文件，自动提取音频
- 🎤 **语音识别**: 使用 faster-whisper 进行高效语音识别，支持 19+ 种语言
- 🤖 **AI 翻译**: 支持 Ollama 本地模型和 OpenAI 兼容 API 进行字幕翻译
- 📝 **字幕烧录**: 将字幕烧录到视频中，支持双语字幕和自定义样式
- 💾 **视频保存**: 保存处理后的视频，支持预览
- 📄 **文本展示**: 查看和保存 SRT 字幕内容

## 📸 截图预览

<!-- 可以添加工作流截图 -->
```
[媒体加载器] → 音频输出 → [语音识别文字] → SRT输出 → [文本展示框]
      ↓                           ↓
   视频输出                  翻译SRT输出
      ↓                           ↓
      └──────→ [文本与视频烧录] ←────┘
                     ↓
              烧录后视频输出
                     ↓
               [保存视频]
```

---

## 📦 安装

### 方法 1: 手动安装

1. 将此插件文件夹复制到 `ComfyUI/custom_nodes/` 目录下：

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/YOUR_USERNAME/ComfyUI-FasterWhisper.git
```

2. 安装依赖：

```bash
cd ComfyUI-FasterWhisper
pip install -r requirements.txt
```

3. 重启 ComfyUI

### 方法 2: 通过 ComfyUI Manager

在 ComfyUI Manager 中搜索 "FasterWhisper" 并安装。

---

## 🔧 依赖要求

### 必需依赖

| 依赖 | 版本 | 说明 |
|------|------|------|
| faster-whisper | ≥1.0.0 | 语音识别引擎 |
| av (PyAV) | ≥10.0.0 | 音频/视频处理 |
| requests | ≥2.28.0 | HTTP 请求（用于 LLM API） |
| torch | ≥2.0.0 | PyTorch（用于 CUDA 检测） |

### GPU 加速依赖（可选）

如需 GPU 加速，请安装 CUDA 相关库：

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*
```

**Linux 环境变量设置：**
```bash
export LD_LIBRARY_PATH=`python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'`
```

### FFmpeg（字幕烧录必需）

字幕烧录功能需要系统安装 FFmpeg：

| 系统 | 安装命令 |
|------|----------|
| Windows | 下载 [FFmpeg](https://ffmpeg.org/download.html) 并添加到 PATH |
| Linux | `sudo apt install ffmpeg` |
| macOS | `brew install ffmpeg` |

---

## 📁 模型说明

### 模型存储位置

Whisper 模型会自动下载并保存到：
```
ComfyUI/models/faster-whisper/
```

### 支持的模型

| 模型 | 大小 | 精度 | 速度 | 推荐场景 |
|------|------|------|------|----------|
| tiny | ~75 MB | 最低 | 最快 | 快速测试 |
| tiny.en | ~75 MB | 低 | 最快 | 英语快速识别 |
| base | ~145 MB | 低 | 快 | 简单场景 |
| base.en | ~145 MB | 中低 | 快 | 英语简单场景 |
| small | ~500 MB | 中 | 中 | 一般使用 |
| small.en | ~500 MB | 中 | 中 | 英语一般使用 |
| medium | ~1.5 GB | 高 | 较慢 | 高质量需求 |
| medium.en | ~1.5 GB | 高 | 较慢 | 英语高质量 |
| large-v1 | ~3 GB | 很高 | 慢 | 专业场景 |
| large-v2 | ~3 GB | 很高 | 慢 | 专业场景 |
| **large-v3** | ~3 GB | **最高** | 慢 | **推荐** |
| large-v3-turbo | ~3 GB | 最高 | 较快 | 速度与质量平衡 |
| distil-large-v2 | ~1.5 GB | 高 | 快 | 高效推理 |
| distil-large-v3 | ~1.5 GB | 高 | 快 | 高效推理 |
| distil-medium.en | ~800 MB | 中 | 快 | 英语高效推理 |
| distil-small.en | ~400 MB | 中低 | 很快 | 英语快速推理 |

---

## 🎯 节点详细说明

### 🎬 媒体加载器 (MediaLoader)

加载视频或音频文件，自动提取音频用于语音识别。

#### 输入参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| media_file | 下拉选择 | ✅ | - | 选择已上传的媒体文件 |
| upload_file | STRING | ❌ | "" | 上传新文件的路径 |

#### 输出

| 输出 | 类型 | 说明 |
|------|------|------|
| 音频输出 | AUDIO_PATH | 音频文件路径（从视频提取或直接使用） |
| 视频输出 | VIDEO_PATH | 视频文件路径（音频文件时为空） |

#### 支持的格式

- **视频**: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`
- **音频**: `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`

---

### 🎤 语音识别文字 (SpeechRecognition)

使用 faster-whisper 进行语音识别，支持多语言和 AI 翻译。

#### 输入参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| audio_path | AUDIO_PATH | ✅ | - | 音频文件路径 |
| model | 下拉选择 | ✅ | large-v3 | Whisper 模型选择 |
| compute_type | 下拉选择 | ✅ | float16 | 计算精度类型 |
| language | 下拉选择 | ✅ | auto | 识别语言 |
| translation_language | 下拉选择 | ✅ | 无翻译 | 翻译目标语言 |
| llm_api | LLM_API | ❌ | - | 外部 LLM API 配置（优先使用） |
| ollama_model | 下拉选择 | ❌ | qwen2.5:7b | 本地 Ollama 翻译模型 |
| ollama_url | STRING | ❌ | http://localhost:11434 | Ollama API 地址 |
| beam_size | INT | ❌ | 5 | Beam size (1-10)，越大越准确但越慢 |
| vad_filter | BOOLEAN | ❌ | True | 启用 VAD 过滤器过滤无声部分 |

#### 计算精度说明

| 精度类型 | 显存占用 | 速度 | 精度 | 说明 |
|----------|----------|------|------|------|
| float32 | 最高 | 慢 | 最高 | CPU 默认 |
| float16 | 中 | 快 | 高 | GPU 推荐 |
| int8 | 最低 | 最快 | 中 | 低显存推荐 |
| int8_float16 | 低 | 快 | 中高 | 平衡选择 |
| bfloat16 | 中 | 快 | 高 | 新GPU支持 |

#### 支持的语言

- 自动检测、中文、英语、日语、韩语、法语、德语、西班牙语、俄语、意大利语、葡萄牙语、荷兰语、波兰语、土耳其语、阿拉伯语、泰语、越南语、印尼语、印地语

#### 输出

| 输出 | 类型 | 说明 |
|------|------|------|
| SRT文件输出 | SRT_TEXT | 原始 SRT 字幕内容 |
| 翻译后SRT输出 | SRT_TEXT | 翻译后的 SRT 字幕内容 |

---

### 🤖 LLM API 配置 (LLMApi)

配置外部大模型 API 作为翻译模型，支持 OpenAI 兼容 API 和 Ollama。

#### 输入参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| api_type | 下拉选择 | ✅ | OpenAI兼容 | API 类型 (OpenAI兼容/Ollama/自定义) |
| api_url | STRING | ✅ | http://localhost:11434/v1/chat/completions | API 端点地址 |
| model_name | STRING | ✅ | qwen2.5:7b | 模型名称 |
| api_key | STRING | ❌ | "" | API 密钥（如需要） |
| temperature | FLOAT | ❌ | 0.3 | 生成温度 (0.0-2.0)，越低越确定 |
| max_tokens | INT | ❌ | 1024 | 最大生成 token 数 (64-8192) |
| system_prompt | STRING | ❌ | "" | 自定义系统提示词（支持 `{target_language}` 占位符） |

#### API 端点示例

| API 类型 | 端点格式 |
|----------|----------|
| OpenAI 兼容 | `http://xxx/v1/chat/completions` |
| Ollama | `http://localhost:11434/api/generate` |

#### 输出

| 输出 | 类型 | 说明 |
|------|------|------|
| LLM API | LLM_API | API 配置对象，连接到语音识别节点 |

---

### 📝 文本与视频烧录 (VideoBurn)

将字幕烧录到视频中，支持原文和翻译双语字幕，可独立设置样式。

#### 输入参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| video_path | VIDEO_PATH | ✅ | - | 视频文件路径 |
| srt_text | SRT_TEXT | ❌ | - | 原始 SRT 字幕 |
| translated_srt | SRT_TEXT | ❌ | - | 翻译后的 SRT 字幕 |

**原文字幕样式：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| text_size | INT | 24 | 字体大小 (8-72) |
| text_color | 下拉选择 | white | 字体颜色 |
| text_position_x | INT | -1 | X位置 (-1居中, -2右对齐, 正数为距左边距离) |
| text_position_y | INT | 50 | 距视频底部边距 (-1默认50像素) |
| text_outline_color | 下拉选择 | black | 描边颜色 |
| text_outline_width | INT | 2 | 描边宽度 (0-10) |

**翻译字幕样式：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| trans_text_size | INT | 20 | 字体大小 (8-72) |
| trans_text_color | 下拉选择 | yellow | 字体颜色 |
| trans_position_x | INT | -1 | X位置 (-1居中, -2右对齐) |
| trans_position_y | INT | -2 | 距底部边距 (-2自动在原文上方) |
| trans_outline_color | 下拉选择 | black | 描边颜色 |
| trans_outline_width | INT | 2 | 描边宽度 (0-10) |

**字体设置：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| font_name | STRING | Arial | 字体名称（需系统已安装） |

#### 可用颜色

`white`, `black`, `red`, `green`, `blue`, `yellow`, `cyan`, `magenta`, `orange`, `pink`, `purple`, `gray`, `light_gray`, `dark_gray`

#### 输出

| 输出 | 类型 | 说明 |
|------|------|------|
| 烧录后视频 | BURNED_VIDEO_PATH | 烧录字幕后的视频路径 |

---

### 💾 保存视频 (SaveVideo)

保存处理后的视频到输出目录。

#### 输入参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| video_path | BURNED_VIDEO_PATH | ✅ | - | 要保存的视频文件路径 |
| filename_prefix | STRING | ❌ | output | 输出文件名前缀 |
| overwrite | BOOLEAN | ❌ | False | 是否覆盖同名文件 |

#### 输出

| 输出 | 类型 | 说明 |
|------|------|------|
| 保存路径 | STRING | 保存的文件完整路径 |

#### 输出目录

视频保存到：`ComfyUI/output/faster_whisper_videos/`

---

### 📄 文本展示框 (TextDisplay)

显示 SRT 字幕内容，支持保存为文件。

#### 输入参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| srt_text | SRT_TEXT | ✅ | - | 原始 SRT 字幕文本 |
| translated_srt_text | SRT_TEXT | ❌ | - | 翻译后的 SRT 字幕文本 |
| save_to_file | BOOLEAN | ❌ | False | 是否保存为文件 |
| filename | STRING | ❌ | subtitles | 保存的文件名（不含扩展名） |

#### 输出

| 输出 | 类型 | 说明 |
|------|------|------|
| 原文内容 | STRING | 原始字幕文本 |
| 翻译内容 | STRING | 翻译后字幕文本 |

#### SRT 文件保存目录

`ComfyUI/output/faster_whisper_srt/`

---

## 🔄 使用教程

### 基础工作流：视频语音识别

1. 添加 **媒体加载器** 节点，上传视频文件
2. 添加 **语音识别文字** 节点，连接音频输出
3. 选择合适的模型和语言
4. 添加 **文本展示框** 节点查看结果

### 进阶工作流：双语字幕烧录

1. 完成基础工作流
2. 在语音识别节点选择翻译目标语言
3. 配置 Ollama 模型或连接 **LLM API 配置** 节点
4. 添加 **文本与视频烧录** 节点
5. 连接视频输出、SRT输出、翻译SRT输出
6. 调整字幕样式参数
7. 添加 **保存视频** 节点保存结果

### 使用外部 LLM API 翻译

1. 添加 **LLM API 配置** 节点
2. 选择 API 类型（OpenAI兼容/Ollama）
3. 填写 API 地址和模型名称
4. 如需要，填写 API 密钥
5. 将 LLM API 输出连接到语音识别节点的 llm_api 输入

---

## 🌐 翻译配置

### 使用本地 Ollama

1. 安装 [Ollama](https://ollama.ai/)
2. 拉取翻译模型：
   ```bash
   ollama pull qwen2.5:7b
   # 或其他模型
   ollama pull llama3.1:8b
   ollama pull gemma2:9b
   ```
3. 在语音识别节点中选择模型和目标语言

### 使用 OpenAI 兼容 API

支持任何 OpenAI 兼容的 API 服务：
- OpenAI API
- Azure OpenAI
- 本地部署的 vLLM、text-generation-webui 等
- 第三方 API 服务

---

## ⚡ 性能优化建议

| 优化项 | 说明 |
|--------|------|
| 使用 `int8` 精度 | 显著减少显存占用，适合低显存GPU |
| 启用 `vad_filter` | 跳过静音部分，加快处理速度 |
| 使用 `distil` 系列模型 | 速度更快，精度略有下降 |
| 使用 `large-v3-turbo` | 速度与质量的最佳平衡 |
| 降低 `beam_size` | 减少到 1-3 可加快速度 |

---

## 📝 常见问题

### Q: 模型下载很慢？

模型从 Hugging Face Hub 下载，可以设置国内镜像：

```bash
# Linux/macOS
export HF_ENDPOINT=https://hf-mirror.com

# Windows PowerShell
$env:HF_ENDPOINT="https://hf-mirror.com"

# Windows CMD
set HF_ENDPOINT=https://hf-mirror.com
```

### Q: CUDA 不可用？

1. 确保安装了 NVIDIA 显卡驱动
2. 安装 CUDA 版本的 PyTorch
3. 安装 cuBLAS 和 cuDNN：
   ```bash
   pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*
   ```

### Q: FFmpeg 未找到？

确保 FFmpeg 已安装并添加到系统 PATH：

**Windows:**
1. 下载 [FFmpeg](https://ffmpeg.org/download.html)
2. 解压到如 `C:\ffmpeg`
3. 将 `C:\ffmpeg\bin` 添加到系统环境变量 PATH

**验证安装：**
```bash
ffmpeg -version
```

### Q: 字幕烧录失败？

1. 检查 FFmpeg 是否正确安装
2. 确保视频文件路径不含特殊字符
3. 检查是否有足够的磁盘空间
4. 查看 ComfyUI 控制台的错误信息

### Q: 翻译不工作？

1. 确保 Ollama 服务正在运行：`ollama serve`
2. 检查模型是否已下载：`ollama list`
3. 验证 API 地址是否正确
4. 如使用外部 API，检查 API 密钥是否有效

---

## 📜 许可证

MIT License

---

## 🙏 致谢

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - 高效的 Whisper 推理实现
- [OpenAI Whisper](https://github.com/openai/whisper) - 原始 Whisper 模型
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 强大的节点式 AI 工作流
- [Ollama](https://ollama.ai/) - 本地大语言模型运行

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. 提交 Pull Request

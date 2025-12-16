"""
ComfyUI-FasterWhisper: Video/Audio Transcription Plugin
使用 faster-whisper 进行语音识别和字幕生成的 ComfyUI 插件

功能:
- 媒体加载器: 加载视频和音频文件，支持预览
- 语音识别: 使用 faster-whisper 进行语音转文字
- 视频烧录: 将字幕烧录到视频中
- 保存视频: 保存处理后的视频
- 文本展示: 查看 SRT 字幕内容
"""

import os
import folder_paths

# 确保模型目录存在
MODELS_DIR = os.path.join(folder_paths.models_dir, "faster-whisper")
os.makedirs(MODELS_DIR, exist_ok=True)

# 确保媒体输入目录存在
MEDIA_INPUT_DIR = os.path.join(folder_paths.get_input_directory(), "media")
os.makedirs(MEDIA_INPUT_DIR, exist_ok=True)

# 导入节点类
from .nodes.media_loader import MediaLoaderNode
from .nodes.speech_recognition import SpeechRecognitionNode
from .nodes.video_burn import VideoBurnNode
from .nodes.save_video import SaveVideoNode
from .nodes.text_display import TextDisplayNode
from .nodes.llm_api import LLMApiNode

# 节点类映射
NODE_CLASS_MAPPINGS = {
    "MediaLoader": MediaLoaderNode,
    "SpeechRecognition": SpeechRecognitionNode,
    "VideoBurn": VideoBurnNode,
    "SaveVideo": SaveVideoNode,
    "TextDisplay": TextDisplayNode,
    "LLMApi": LLMApiNode,
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "MediaLoader": "🎬 媒体加载器 (视频/音频)",
    "SpeechRecognition": "🎤 语音识别文字",
    "VideoBurn": "📝 文本与视频烧录",
    "SaveVideo": "💾 保存视频",
    "TextDisplay": "📄 文本展示框",
    "LLMApi": "🤖 LLM API 配置",
}

# Web 目录
WEB_DIRECTORY = "./web"

# 导出
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

# 打印加载信息
print("\033[92m[FasterWhisper]\033[0m 插件加载成功!")
print(f"\033[92m[FasterWhisper]\033[0m 模型目录: {MODELS_DIR}")
print(f"\033[92m[FasterWhisper]\033[0m 媒体目录: {MEDIA_INPUT_DIR}")

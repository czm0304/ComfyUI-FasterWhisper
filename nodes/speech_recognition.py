"""
语音识别文字节点 - 使用 faster-whisper 进行语音识别
支持多种模型、精度、语言选择，以及使用 Ollama 或外部 LLM API 进行翻译
"""

import os
import json
import requests
import folder_paths
from pathlib import Path
from .llm_api import call_llm_api

# 模型存储路径
MODELS_DIR = os.path.join(folder_paths.models_dir, "faster-whisper")
os.makedirs(MODELS_DIR, exist_ok=True)

# 支持的模型列表
WHISPER_MODELS = [
    "tiny",
    "tiny.en",
    "base",
    "base.en",
    "small",
    "small.en",
    "medium",
    "medium.en",
    "large-v1",
    "large-v2",
    "large-v3",
    "large-v3-turbo",
    "distil-large-v2",
    "distil-large-v3",
    "distil-medium.en",
    "distil-small.en",
]

# 模型精度选项
COMPUTE_TYPES = [
    "float32",
    "float16",
    "int8",
    "int8_float16",
    "int8_float32",
    "int8_bfloat16",
    "bfloat16",
]

# 支持的语言列表
LANGUAGES = [
    "auto (自动检测)",
    "zh (中文)",
    "en (英语)",
    "ja (日语)",
    "ko (韩语)",
    "fr (法语)",
    "de (德语)",
    "es (西班牙语)",
    "ru (俄语)",
    "it (意大利语)",
    "pt (葡萄牙语)",
    "nl (荷兰语)",
    "pl (波兰语)",
    "tr (土耳其语)",
    "ar (阿拉伯语)",
    "th (泰语)",
    "vi (越南语)",
    "id (印尼语)",
    "hi (印地语)",
]

# 翻译目标语言
TRANSLATION_LANGUAGES = [
    "无翻译",
    "zh-CN (简体中文)",
    "zh-TW (繁体中文)",
    "en (英语)",
    "ja (日语)",
    "ko (韩语)",
    "fr (法语)",
    "de (德语)",
    "es (西班牙语)",
    "ru (俄语)",
    "it (意大利语)",
    "pt (葡萄牙语)",
    "ar (阿拉伯语)",
    "th (泰语)",
    "vi (越南语)",
]


class SpeechRecognitionNode:
    """
    语音识别文字节点
    - 输入：音频路径
    - 输出：SRT字幕文件、翻译后的SRT字幕文件
    """
    
    def __init__(self):
        self.model = None
        self.current_model_name = None
        self.current_compute_type = None
    
    @classmethod
    def INPUT_TYPES(cls):
        # 获取可用的 Ollama 模型
        ollama_models = cls._get_ollama_models()
        
        return {
            "required": {
                "audio_path": ("AUDIO_PATH", {
                    "tooltip": "音频文件路径"
                }),
                "model": (WHISPER_MODELS, {
                    "default": "large-v3",
                    "tooltip": "选择 Whisper 模型"
                }),
                "compute_type": (COMPUTE_TYPES, {
                    "default": "float16",
                    "tooltip": "模型精度/计算类型"
                }),
                "language": (LANGUAGES, {
                    "default": "auto (自动检测)",
                    "tooltip": "识别语言"
                }),
                "translation_language": (TRANSLATION_LANGUAGES, {
                    "default": "无翻译",
                    "tooltip": "翻译目标语言"
                }),
            },
            "optional": {
                "llm_api": ("LLM_API", {
                    "tooltip": "外部 LLM API 配置（优先使用，如连接则忽略下方 Ollama 设置）"
                }),
                "ollama_model": (ollama_models, {
                    "default": ollama_models[0] if ollama_models else "无可用模型",
                    "tooltip": "本地 Ollama 翻译模型（当未连接外部 LLM API 时使用）"
                }),
                "ollama_url": ("STRING", {
                    "default": "http://localhost:11434",
                    "multiline": False,
                    "tooltip": "Ollama API 地址（当未连接外部 LLM API 时使用）"
                }),
                "beam_size": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 10,
                    "step": 1,
                    "tooltip": "Beam size 参数，越大越准确但越慢"
                }),
                "vad_filter": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "启用 VAD 过滤器过滤无声部分"
                }),
            },
        }
    
    RETURN_TYPES = ("SRT_TEXT", "SRT_TEXT")
    RETURN_NAMES = ("SRT文件输出", "翻译后SRT输出")
    FUNCTION = "transcribe"
    CATEGORY = "FasterWhisper/识别"
    OUTPUT_NODE = False
    
    @classmethod
    def _get_ollama_models(cls):
        """获取本地 Ollama 可用模型列表"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models_data = response.json()
                models = [m['name'] for m in models_data.get('models', [])]
                if models:
                    return models
        except:
            pass
        return ["qwen2.5:7b", "llama3.1:8b", "gemma2:9b", "无可用模型"]
    
    def _load_model(self, model_name, compute_type):
        """加载 Whisper 模型"""
        if self.model is not None and self.current_model_name == model_name and self.current_compute_type == compute_type:
            return self.model
        
        try:
            from faster_whisper import WhisperModel
            
            # 检查是否有 CUDA
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # 调整 CPU 上的计算类型
            if device == "cpu" and compute_type in ["float16", "int8_float16", "bfloat16", "int8_bfloat16"]:
                compute_type = "int8" if "int8" in compute_type else "float32"
            
            # 模型路径
            model_path = os.path.join(MODELS_DIR, model_name)
            
            # 如果本地没有模型，使用模型名称（会自动下载）
            if not os.path.exists(model_path):
                model_path = model_name
            
            print(f"[FasterWhisper] 加载模型: {model_name}, 设备: {device}, 精度: {compute_type}")
            
            self.model = WhisperModel(
                model_path,
                device=device,
                compute_type=compute_type,
                download_root=MODELS_DIR
            )
            self.current_model_name = model_name
            self.current_compute_type = compute_type
            
            return self.model
            
        except ImportError:
            raise ImportError("请安装 faster-whisper: pip install faster-whisper")
    
    def _parse_language(self, language_str):
        """解析语言字符串"""
        if language_str.startswith("auto"):
            return None
        return language_str.split(" ")[0]
    
    def _segments_to_srt(self, segments):
        """将识别结果转换为 SRT 格式"""
        srt_content = []
        for i, segment in enumerate(segments, 1):
            start_time = self._format_timestamp(segment.start)
            end_time = self._format_timestamp(segment.end)
            text = segment.text.strip()
            srt_content.append(f"{i}\n{start_time} --> {end_time}\n{text}\n")
        return "\n".join(srt_content)
    
    def _format_timestamp(self, seconds):
        """格式化时间戳为 SRT 格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _translate_with_ollama(self, srt_content, target_language, ollama_model, ollama_url):
        """使用 Ollama 翻译 SRT 内容"""
        if target_language == "无翻译" or not srt_content:
            return ""
        
        target_lang = target_language.split(" ")[0]
        lang_names = {
            "zh-CN": "简体中文",
            "zh-TW": "繁体中文",
            "en": "英语",
            "ja": "日语",
            "ko": "韩语",
            "fr": "法语",
            "de": "德语",
            "es": "西班牙语",
            "ru": "俄语",
            "it": "意大利语",
            "pt": "葡萄牙语",
            "ar": "阿拉伯语",
            "th": "泰语",
            "vi": "越南语",
        }
        target_lang_name = lang_names.get(target_lang, target_lang)
        
        # 解析 SRT 并逐条翻译
        lines = srt_content.strip().split("\n\n")
        translated_lines = []
        
        for block in lines:
            parts = block.strip().split("\n")
            if len(parts) >= 3:
                index = parts[0]
                timestamp = parts[1]
                text = "\n".join(parts[2:])
                
                # 翻译文本
                translated_text = self._call_ollama(
                    text, target_lang_name, ollama_model, ollama_url
                )
                
                translated_lines.append(f"{index}\n{timestamp}\n{translated_text}")
        
        return "\n\n".join(translated_lines)
    
    def _call_ollama(self, text, target_language, model, url):
        """调用 Ollama API 进行翻译"""
        try:
            prompt = f"请将以下文本翻译成{target_language}，只输出翻译结果，不要任何解释或额外内容：\n{text}"
            
            response = requests.post(
                f"{url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', text).strip()
            else:
                print(f"[FasterWhisper] Ollama 翻译失败: {response.status_code}")
                return text
                
        except Exception as e:
            print(f"[FasterWhisper] Ollama 翻译错误: {str(e)}")
            return text
    
    def _translate_with_llm_api(self, srt_content, target_language, llm_api_config):
        """使用外部 LLM API 翻译 SRT 内容"""
        if target_language == "无翻译" or not srt_content:
            return ""
        
        target_lang = target_language.split(" ")[0]
        lang_names = {
            "zh-CN": "简体中文",
            "zh-TW": "繁体中文",
            "en": "英语",
            "ja": "日语",
            "ko": "韩语",
            "fr": "法语",
            "de": "德语",
            "es": "西班牙语",
            "ru": "俄语",
            "it": "意大利语",
            "pt": "葡萄牙语",
            "ar": "阿拉伯语",
            "th": "泰语",
            "vi": "越南语",
        }
        target_lang_name = lang_names.get(target_lang, target_lang)
        
        # 解析 SRT 并逐条翻译
        lines = srt_content.strip().split("\n\n")
        translated_lines = []
        
        for block in lines:
            parts = block.strip().split("\n")
            if len(parts) >= 3:
                index = parts[0]
                timestamp = parts[1]
                text = "\n".join(parts[2:])
                
                # 使用外部 LLM API 翻译
                translated_text = call_llm_api(llm_api_config, text, target_lang_name)
                
                translated_lines.append(f"{index}\n{timestamp}\n{translated_text}")
        
        return "\n\n".join(translated_lines)
    
    def transcribe(self, audio_path, model, compute_type, language, translation_language,
                   llm_api=None, ollama_model="", ollama_url="http://localhost:11434", beam_size=5, vad_filter=True):
        """
        执行语音识别
        """
        if not audio_path or not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 加载模型
        whisper_model = self._load_model(model, compute_type)
        
        # 解析语言
        lang = self._parse_language(language)
        
        print(f"[FasterWhisper] 开始识别: {audio_path}")
        print(f"[FasterWhisper] 语言: {lang if lang else '自动检测'}, Beam Size: {beam_size}")
        
        # 执行识别
        segments, info = whisper_model.transcribe(
            audio_path,
            language=lang,
            beam_size=beam_size,
            vad_filter=vad_filter,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        
        # 转换为列表（触发实际识别）
        segments_list = list(segments)
        
        print(f"[FasterWhisper] 检测到语言: {info.language} (概率: {info.language_probability:.2f})")
        print(f"[FasterWhisper] 识别完成，共 {len(segments_list)} 个片段")
        
        # 生成 SRT 内容
        srt_content = self._segments_to_srt(segments_list)
        
        # 翻译（如果需要）
        translated_srt = ""
        if translation_language != "无翻译":
            print(f"[FasterWhisper] 开始翻译到: {translation_language}")
            
            # 优先使用外部 LLM API
            if llm_api is not None:
                print(f"[FasterWhisper] 使用外部 LLM API: {llm_api.get('api_type', '')} - {llm_api.get('model_name', '')}")
                translated_srt = self._translate_with_llm_api(
                    srt_content, translation_language, llm_api
                )
            elif ollama_model and ollama_model != "无可用模型":
                print(f"[FasterWhisper] 使用内置 Ollama: {ollama_model}")
                translated_srt = self._translate_with_ollama(
                    srt_content, translation_language, ollama_model, ollama_url
                )
            else:
                print(f"[FasterWhisper] 警告: 未配置翻译模型，跳过翻译")
            
            if translated_srt:
                print(f"[FasterWhisper] 翻译完成")
        
        return (srt_content, translated_srt)

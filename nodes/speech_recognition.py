"""
语音识别文字节点 - 使用 faster-whisper 进行语音识别
支持多种模型、精度、语言选择，以及使用 Ollama 或外部 LLM API 进行翻译
"""

import os
import requests
import folder_paths
from pathlib import Path
import inspect
import tempfile
import numpy as np
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
        return {
            "required": {
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
                "audio_path": ("AUDIO_PATH", {
                    "tooltip": "音频文件路径（来自媒体加载器）"
                }),
                "audio": ("AUDIO", {
                    "tooltip": "音频输入（来自ComfyUI原生音频节点）"
                }),
                "llm_model": ("LLM_API", {
                    "tooltip": "大模型配置（连接本地大模型设置或云端大模型设置）"
                }),
                "beam_size": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 10,
                    "step": 1,
                    "tooltip": "Beam size 参数，越大越准确但越慢"
                }),
                "batch_size": ("INT", {
                    "default": 8,
                    "min": 1,
                    "max": 64,
                    "step": 1,
                    "tooltip": "批处理大小（batch_size），增大可显著加速但会增加显存占用"
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
    
    def _audio_to_file(self, audio):
        """
        将 ComfyUI 原生 AUDIO 类型转换为临时音频文件
        AUDIO 类型格式: {"waveform": tensor, "sample_rate": int}
        """
        try:
            import scipy.io.wavfile as wavfile
        except ImportError:
            raise ImportError("请安装 scipy: pip install scipy")
        
        waveform = audio["waveform"]
        sample_rate = audio["sample_rate"]
        
        # 转换为 numpy 数组
        if hasattr(waveform, 'cpu'):
            waveform = waveform.cpu().numpy()
        
        # 确保格式正确 (samples,) 或 (channels, samples)
        if waveform.ndim == 3:
            # (batch, channels, samples) -> (samples,)
            waveform = waveform.squeeze(0)
            if waveform.ndim == 2:
                waveform = waveform.mean(axis=0)  # 转为单声道
        elif waveform.ndim == 2:
            waveform = waveform.mean(axis=0)  # 转为单声道
        
        # 归一化到 int16 范围
        waveform = np.clip(waveform, -1.0, 1.0)
        waveform_int16 = (waveform * 32767).astype(np.int16)
        
        # 保存为临时 wav 文件
        temp_dir = os.path.join(folder_paths.get_temp_directory(), "audio_input")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"audio_input_{id(audio)}.wav")
        
        wavfile.write(temp_path, sample_rate, waveform_int16)
        return temp_path

    def transcribe(self, model, compute_type, language, translation_language,
                   audio_path=None, audio=None, llm_model=None, beam_size=5, batch_size=8, vad_filter=True):
        """
        执行语音识别
        """
        # 确定音频来源
        actual_audio_path = None
        
        if audio is not None:
            # 使用 ComfyUI 原生 AUDIO 类型
            print("[FasterWhisper] 使用 ComfyUI 原生音频输入")
            actual_audio_path = self._audio_to_file(audio)
        elif audio_path:
            actual_audio_path = audio_path
        
        if not actual_audio_path or not os.path.exists(actual_audio_path):
            raise FileNotFoundError(f"音频文件不存在或未提供音频输入。请连接 '音频路径' 或 'audio' 输入。")
        
        # 加载模型
        whisper_model = self._load_model(model, compute_type)
        
        # 解析语言
        lang = self._parse_language(language)
        
        print(f"[FasterWhisper] 开始识别: {actual_audio_path}")
        print(f"[FasterWhisper] 语言: {lang if lang else '自动检测'}, Beam Size: {beam_size}")
        
        transcribe_kwargs = {
            "language": lang,
            "beam_size": beam_size,
            "vad_filter": vad_filter,
            "vad_parameters": dict(min_silence_duration_ms=500),
        }

        try:
            sig = inspect.signature(whisper_model.transcribe)
            if "batch_size" in sig.parameters:
                transcribe_kwargs["batch_size"] = batch_size
            else:
                if batch_size != 8:
                    print("[FasterWhisper] 警告: 当前 faster-whisper 版本不支持 batch_size 参数，将忽略该设置")
        except Exception:
            pass

        # 执行识别
        try:
            segments, info = whisper_model.transcribe(
                actual_audio_path,
                **transcribe_kwargs,
            )
        except TypeError as e:
            if "batch_size" in transcribe_kwargs and "batch_size" in str(e):
                transcribe_kwargs.pop("batch_size", None)
                print("[FasterWhisper] 警告: WhisperModel.transcribe 不支持 batch_size，已自动忽略并重试")
                segments, info = whisper_model.transcribe(
                    actual_audio_path,
                    **transcribe_kwargs,
                )
            else:
                raise
        
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

            if llm_model is not None:
                print(f"[FasterWhisper] 使用大模型: {llm_model.get('api_type', '')} - {llm_model.get('model_name', '')}")
                translated_srt = self._translate_with_llm_api(srt_content, translation_language, llm_model)
            else:
                print(f"[FasterWhisper] 警告: 未连接大模型配置节点，跳过翻译")
            
            if translated_srt:
                print(f"[FasterWhisper] 翻译完成")
        
        return (srt_content, translated_srt)

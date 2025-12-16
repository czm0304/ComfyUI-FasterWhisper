"""
媒体加载器节点 - 加载视频和音频文件
支持视频循环播放预览和音频悬停播放
"""

import os
import tempfile
import hashlib
import folder_paths
from pathlib import Path

# 确保媒体目录存在
MEDIA_INPUT_DIR = os.path.join(folder_paths.get_input_directory(), "media")
os.makedirs(MEDIA_INPUT_DIR, exist_ok=True)

class MediaLoaderNode:
    """
    媒体加载器节点
    - 支持加载视频和音频文件
    - 视频输出端：输出带音频的视频路径
    - 音频输出端：输出音频路径（从视频中提取或直接加载）
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        # 获取已上传的媒体文件列表
        media_files = []
        if os.path.exists(MEDIA_INPUT_DIR):
            for f in os.listdir(MEDIA_INPUT_DIR):
                ext = os.path.splitext(f)[1].lower()
                if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg']:
                    media_files.append(f)
        
        if not media_files:
            media_files = ["请上传媒体文件"]
        
        return {
            "required": {
                "media_file": (media_files, {
                    "default": media_files[0] if media_files else "",
                    "tooltip": "选择要加载的媒体文件"
                }),
            },
            "optional": {
                "upload_file": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "点击下方按钮选择文件上传",
                    "tooltip": "上传的文件路径"
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }
    
    RETURN_TYPES = ("AUDIO_PATH", "VIDEO_PATH")
    RETURN_NAMES = ("音频输出", "视频输出")
    FUNCTION = "load_media"
    CATEGORY = "FasterWhisper/媒体"
    OUTPUT_NODE = False
    
    @classmethod
    def IS_CHANGED(cls, media_file, upload_file="", unique_id=None):
        if media_file and media_file != "请上传媒体文件":
            file_path = os.path.join(MEDIA_INPUT_DIR, media_file)
            if os.path.exists(file_path):
                m = hashlib.md5()
                with open(file_path, 'rb') as f:
                    m.update(f.read())
                return m.hexdigest()
        return ""
    
    def load_media(self, media_file, upload_file="", unique_id=None):
        """
        加载媒体文件
        返回音频路径和视频路径
        """
        if media_file == "请上传媒体文件":
            raise ValueError("请先上传媒体文件！点击节点中的'加载文件'按钮选择文件。")
        
        file_path = os.path.join(MEDIA_INPUT_DIR, media_file)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        ext = os.path.splitext(media_file)[1].lower()
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg']
        
        audio_path = ""
        video_path = ""
        
        if ext in video_extensions:
            video_path = file_path
            # 从视频中提取音频
            audio_path = self._extract_audio_from_video(file_path)
        elif ext in audio_extensions:
            audio_path = file_path
            video_path = ""  # 音频文件没有视频输出
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        return (audio_path, video_path)
    
    def _extract_audio_from_video(self, video_path):
        """
        从视频中提取音频
        使用 PyAV 或 moviepy 进行提取
        """
        try:
            import av
            
            # 生成临时音频文件路径
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            audio_output_dir = os.path.join(folder_paths.get_temp_directory(), "extracted_audio")
            os.makedirs(audio_output_dir, exist_ok=True)
            audio_path = os.path.join(audio_output_dir, f"{video_name}_audio.wav")
            
            # 如果已经提取过，直接返回
            if os.path.exists(audio_path):
                return audio_path
            
            # 使用 PyAV 提取音频
            container = av.open(video_path)
            audio_stream = next((s for s in container.streams if s.type == 'audio'), None)
            
            if audio_stream is None:
                raise ValueError("视频文件中没有音频轨道")
            
            # 创建输出容器
            output_container = av.open(audio_path, 'w')
            output_stream = output_container.add_stream('pcm_s16le', rate=16000, layout='mono')
            
            resampler = av.audio.resampler.AudioResampler(
                format='s16',
                layout='mono',
                rate=16000
            )
            
            for frame in container.decode(audio_stream):
                frame.pts = None
                resampled_frames = resampler.resample(frame)
                for resampled_frame in resampled_frames:
                    for packet in output_stream.encode(resampled_frame):
                        output_container.mux(packet)
            
            # Flush encoder
            for packet in output_stream.encode():
                output_container.mux(packet)
            
            output_container.close()
            container.close()
            
            return audio_path
            
        except ImportError:
            # 如果没有 PyAV，尝试使用 moviepy
            try:
                from moviepy.editor import VideoFileClip
                
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                audio_output_dir = os.path.join(folder_paths.get_temp_directory(), "extracted_audio")
                os.makedirs(audio_output_dir, exist_ok=True)
                audio_path = os.path.join(audio_output_dir, f"{video_name}_audio.wav")
                
                if os.path.exists(audio_path):
                    return audio_path
                
                video = VideoFileClip(video_path)
                video.audio.write_audiofile(audio_path, fps=16000, nbytes=2, codec='pcm_s16le')
                video.close()
                
                return audio_path
                
            except ImportError:
                raise ImportError("请安装 av 或 moviepy: pip install av moviepy")
        
        except Exception as e:
            raise RuntimeError(f"提取音频失败: {str(e)}")

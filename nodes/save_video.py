"""
保存视频节点 - 保存处理后的视频文件
支持在节点内预览视频
"""

import os
import shutil
import hashlib
import folder_paths
from pathlib import Path

# 输出目录
OUTPUT_DIR = os.path.join(folder_paths.get_output_directory(), "faster_whisper_videos")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class SaveVideoNode:
    """
    保存视频节点
    - 输入：烧录后的视频路径
    - 保存视频到输出目录
    - 支持视频预览
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("BURNED_VIDEO_PATH", {
                    "tooltip": "要保存的视频文件路径"
                }),
            },
            "optional": {
                "filename_prefix": ("STRING", {
                    "default": "output",
                    "multiline": False,
                    "tooltip": "输出文件名前缀"
                }),
                "overwrite": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否覆盖同名文件"
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("保存路径",)
    FUNCTION = "save_video"
    CATEGORY = "FasterWhisper/视频"
    OUTPUT_NODE = True
    
    def save_video(self, video_path, filename_prefix="output", overwrite=False, unique_id=None):
        """
        保存视频文件
        """
        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 获取原始文件扩展名
        _, ext = os.path.splitext(video_path)
        if not ext:
            ext = ".mp4"
        
        # 生成输出文件名
        if overwrite:
            output_filename = f"{filename_prefix}{ext}"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
        else:
            # 找到不重复的文件名
            counter = 1
            while True:
                if counter == 1:
                    output_filename = f"{filename_prefix}{ext}"
                else:
                    output_filename = f"{filename_prefix}_{counter:04d}{ext}"
                
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                if not os.path.exists(output_path):
                    break
                counter += 1
        
        # 复制文件到输出目录
        print(f"[FasterWhisper] 保存视频: {output_path}")
        shutil.copy2(video_path, output_path)
        
        # 返回结果，包含预览信息
        results = {
            "ui": {
                "video": [{
                    "filename": output_filename,
                    "subfolder": "faster_whisper_videos",
                    "type": "output",
                    "format": "video/mp4"
                }]
            },
            "result": (output_path,)
        }
        
        return results
    
    @classmethod
    def IS_CHANGED(cls, video_path, filename_prefix="output", overwrite=False, unique_id=None):
        if video_path and os.path.exists(video_path):
            m = hashlib.md5()
            with open(video_path, 'rb') as f:
                # 只读取前 1MB 用于哈希
                m.update(f.read(1024 * 1024))
            return m.hexdigest()
        return ""

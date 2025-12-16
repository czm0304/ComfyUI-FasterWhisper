"""
文本展示框节点 - 显示 SRT 字幕内容
"""

import os
import folder_paths


class TextDisplayNode:
    """
    文本展示框节点
    - 输入：SRT 文本（必需）、翻译后SRT文本（可选）
    - 显示带时间线的字幕内容
    - 当有翻译文本时，左边显示原文，右边显示翻译
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "srt_text": ("SRT_TEXT", {
                    "tooltip": "SRT字幕文本（原文）"
                }),
            },
            "optional": {
                "translated_srt_text": ("SRT_TEXT", {
                    "tooltip": "翻译后的SRT字幕文本"
                }),
                "save_to_file": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否保存为文件"
                }),
                "filename": ("STRING", {
                    "default": "subtitles",
                    "multiline": False,
                    "tooltip": "保存的文件名（不含扩展名）"
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("原文内容", "翻译内容")
    FUNCTION = "display_text"
    CATEGORY = "FasterWhisper/工具"
    OUTPUT_NODE = True
    
    def display_text(self, srt_text, translated_srt_text=None, save_to_file=False, filename="subtitles", unique_id=None):
        """
        显示文本内容
        """
        if not srt_text:
            srt_text = "（无字幕内容）"
        
        # 处理翻译文本
        if not translated_srt_text:
            translated_srt_text = ""
        
        # 如果需要保存文件
        saved_path = ""
        saved_translated_path = ""
        if save_to_file and srt_text and srt_text != "（无字幕内容）":
            output_dir = os.path.join(folder_paths.get_output_directory(), "faster_whisper_srt")
            os.makedirs(output_dir, exist_ok=True)
            
            # 找到不重复的文件名
            counter = 1
            while True:
                if counter == 1:
                    output_filename = f"{filename}.srt"
                    output_translated_filename = f"{filename}_translated.srt"
                else:
                    output_filename = f"{filename}_{counter:04d}.srt"
                    output_translated_filename = f"{filename}_{counter:04d}_translated.srt"
                
                output_path = os.path.join(output_dir, output_filename)
                if not os.path.exists(output_path):
                    break
                counter += 1
            
            # 保存原文文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_text)
            saved_path = output_path
            print(f"[FasterWhisper] SRT 文件已保存: {output_path}")
            
            # 保存翻译文件（如果有）
            if translated_srt_text:
                output_translated_path = os.path.join(output_dir, output_translated_filename)
                with open(output_translated_path, 'w', encoding='utf-8') as f:
                    f.write(translated_srt_text)
                saved_translated_path = output_translated_path
                print(f"[FasterWhisper] 翻译SRT 文件已保存: {output_translated_path}")
        
        # 返回结果
        results = {
            "ui": {
                "text": [srt_text],
                "translated_text": [translated_srt_text] if translated_srt_text else [],
                "saved_path": [saved_path] if saved_path else [],
                "saved_translated_path": [saved_translated_path] if saved_translated_path else []
            },
            "result": (srt_text, translated_srt_text)
        }
        
        return results
    
    @classmethod
    def IS_CHANGED(cls, srt_text, translated_srt_text=None, save_to_file=False, filename="subtitles", unique_id=None):
        return (srt_text if srt_text else "") + (translated_srt_text if translated_srt_text else "")

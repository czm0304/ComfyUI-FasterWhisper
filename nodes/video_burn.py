"""
文本与视频烧录节点 - 将字幕烧录到视频中
支持原文和翻译文本的独立样式设置
"""

import os
import re
import tempfile
import folder_paths
from pathlib import Path

# 颜色名称到十六进制的映射
COLOR_MAP = {
    "white": "#FFFFFF",
    "black": "#000000",
    "red": "#FF0000",
    "green": "#00FF00",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "cyan": "#00FFFF",
    "magenta": "#FF00FF",
    "orange": "#FFA500",
    "pink": "#FFC0CB",
    "purple": "#800080",
    "gray": "#808080",
    "light_gray": "#D3D3D3",
    "dark_gray": "#404040",
}

COLOR_CHOICES = list(COLOR_MAP.keys())


class VideoBurnNode:
    """
    文本与视频烧录节点
    - 输入：视频路径、SRT字幕、翻译后的SRT字幕
    - 输出：烧录后的视频路径
    - 支持文本大小、颜色、位置的独立设置
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("VIDEO_PATH", {
                    "tooltip": "视频文件路径"
                }),
            },
            "optional": {
                "srt_text": ("SRT_TEXT", {
                    "tooltip": "SRT字幕文本"
                }),
                "translated_srt": ("SRT_TEXT", {
                    "tooltip": "翻译后的SRT字幕文本"
                }),
                # 原文字幕设置
                "text_size": ("INT", {
                    "default": 24,
                    "min": 8,
                    "max": 72,
                    "step": 1,
                    "tooltip": "原文字幕字体大小"
                }),
                "text_color": (COLOR_CHOICES, {
                    "default": "white",
                    "tooltip": "原文字幕颜色"
                }),
                "text_position_x": ("INT", {
                    "default": -1,
                    "min": -2,
                    "max": 3840,
                    "step": 1,
                    "tooltip": "原文字幕X位置 (-1居中, -2右对齐, 正数为距左边距离)"
                }),
                "text_position_y": ("INT", {
                    "default": 50,
                    "min": -1,
                    "max": 2160,
                    "step": 1,
                    "tooltip": "原文字幕距离视频底部的边距 (-1表示默认50像素)"
                }),
                "text_outline_color": (COLOR_CHOICES, {
                    "default": "black",
                    "tooltip": "原文字幕描边颜色"
                }),
                "text_outline_width": ("INT", {
                    "default": 2,
                    "min": 0,
                    "max": 10,
                    "step": 1,
                    "tooltip": "原文字幕描边宽度"
                }),
                # 翻译字幕设置
                "trans_text_size": ("INT", {
                    "default": 20,
                    "min": 8,
                    "max": 72,
                    "step": 1,
                    "tooltip": "翻译字幕字体大小"
                }),
                "trans_text_color": (COLOR_CHOICES, {
                    "default": "yellow",
                    "tooltip": "翻译字幕颜色"
                }),
                "trans_position_x": ("INT", {
                    "default": -1,
                    "min": -2,
                    "max": 3840,
                    "step": 1,
                    "tooltip": "翻译字幕X位置 (-1居中, -2右对齐, 正数为距左边距离)"
                }),
                "trans_position_y": ("INT", {
                    "default": -2,
                    "min": -2,
                    "max": 2160,
                    "step": 1,
                    "tooltip": "翻译字幕距离视频底部的边距 (-1表示默认50像素，-2表示自动在原文字幕上方)"
                }),
                "trans_outline_color": (COLOR_CHOICES, {
                    "default": "black",
                    "tooltip": "翻译字幕描边颜色"
                }),
                "trans_outline_width": ("INT", {
                    "default": 2,
                    "min": 0,
                    "max": 10,
                    "step": 1,
                    "tooltip": "翻译字幕描边宽度"
                }),
                # 字体设置
                "font_name": ("STRING", {
                    "default": "Arial",
                    "tooltip": "字体名称 (需要系统已安装)"
                }),
            },
        }
    
    RETURN_TYPES = ("BURNED_VIDEO_PATH",)
    RETURN_NAMES = ("烧录后视频",)
    FUNCTION = "burn_subtitles"
    CATEGORY = "FasterWhisper/视频"
    OUTPUT_NODE = False
    
    def _parse_srt(self, srt_content):
        """解析 SRT 内容为字幕列表"""
        if not srt_content:
            return []
        
        subtitles = []
        blocks = srt_content.strip().split("\n\n")
        
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) >= 3:
                try:
                    # 解析时间戳
                    timestamp_line = lines[1]
                    match = re.match(
                        r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                        timestamp_line
                    )
                    if match:
                        start_h, start_m, start_s, start_ms = map(int, match.groups()[:4])
                        end_h, end_m, end_s, end_ms = map(int, match.groups()[4:])
                        
                        start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
                        end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
                        
                        text = "\n".join(lines[2:])
                        
                        subtitles.append({
                            'start': start_time,
                            'end': end_time,
                            'text': text
                        })
                except Exception as e:
                    print(f"[FasterWhisper] 解析字幕块失败: {e}")
                    continue
        
        return subtitles
    
    def _hex_to_ass_color(self, hex_color):
        """将十六进制颜色转换为 ASS 格式颜色"""
        # ASS 颜色格式: &HBBGGRR&
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"&H00{b:02X}{g:02X}{r:02X}&"
        return "&H00FFFFFF&"
    
    def _create_ass_file(self, subtitles, translated_subtitles, video_width, video_height,
                         text_size, text_color, text_pos_x, text_pos_y, text_outline_color, text_outline_width,
                         trans_size, trans_color, trans_pos_x, trans_pos_y, trans_outline_color, trans_outline_width,
                         font_name):
        """创建 ASS 字幕文件"""
        
        # 计算Y位置 - Y值直接表示从视频底部算起的边距
        if text_pos_y == -1:
            text_margin_v = 50
        else:
            text_margin_v = text_pos_y
        
        if trans_pos_y == -2:
            trans_margin_v = text_margin_v + text_size + 10
        elif trans_pos_y == -1:
            trans_margin_v = 50
        else:
            trans_margin_v = trans_pos_y
        
        # 计算X位置和对齐方式
        # ASS Alignment: 1=左下, 2=底部居中, 3=右下
        if text_pos_x == -1:
            text_alignment = 2  # 居中
            text_margin_l = 10
            text_margin_r = 10
        elif text_pos_x == -2:
            text_alignment = 3  # 右对齐
            text_margin_l = 10
            text_margin_r = 10
        else:
            text_alignment = 1  # 左对齐
            text_margin_l = text_pos_x
            text_margin_r = 10
        
        if trans_pos_x == -1:
            trans_alignment = 2  # 居中
            trans_margin_l = 10
            trans_margin_r = 10
        elif trans_pos_x == -2:
            trans_alignment = 3  # 右对齐
            trans_margin_l = 10
            trans_margin_r = 10
        else:
            trans_alignment = 1  # 左对齐
            trans_margin_l = trans_pos_x
            trans_margin_r = 10
        
        # ASS 文件头
        ass_content = f"""[Script Info]
Title: FasterWhisper Subtitles
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Original,{font_name},{text_size},{self._hex_to_ass_color(text_color)},&H000000FF&,{self._hex_to_ass_color(text_outline_color)},&H80000000&,0,0,0,0,100,100,0,0,1,{text_outline_width},1,{text_alignment},{text_margin_l},{text_margin_r},{text_margin_v},1
Style: Translated,{font_name},{trans_size},{self._hex_to_ass_color(trans_color)},&H000000FF&,{self._hex_to_ass_color(trans_outline_color)},&H80000000&,0,0,0,0,100,100,0,0,1,{trans_outline_width},1,{trans_alignment},{trans_margin_l},{trans_margin_r},{trans_margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # 添加原文字幕
        for sub in subtitles:
            start_str = self._seconds_to_ass_time(sub['start'])
            end_str = self._seconds_to_ass_time(sub['end'])
            text = sub['text'].replace('\n', '\\N')
            ass_content += f"Dialogue: 0,{start_str},{end_str},Original,,0,0,0,,{text}\n"
        
        # 添加翻译字幕
        for sub in translated_subtitles:
            start_str = self._seconds_to_ass_time(sub['start'])
            end_str = self._seconds_to_ass_time(sub['end'])
            text = sub['text'].replace('\n', '\\N')
            ass_content += f"Dialogue: 1,{start_str},{end_str},Translated,,0,0,0,,{text}\n"
        
        # 保存 ASS 文件
        ass_dir = os.path.join(folder_paths.get_temp_directory(), "ass_subtitles")
        os.makedirs(ass_dir, exist_ok=True)
        ass_path = os.path.join(ass_dir, "subtitles.ass")
        
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        return ass_path
    
    def _seconds_to_ass_time(self, seconds):
        """将秒数转换为 ASS 时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def _get_video_info(self, video_path):
        """获取视频信息"""
        try:
            import av
            container = av.open(video_path)
            video_stream = next((s for s in container.streams if s.type == 'video'), None)
            if video_stream:
                width = video_stream.width
                height = video_stream.height
                container.close()
                return width, height
        except:
            pass
        
        # 默认值
        return 1920, 1080
    
    def burn_subtitles(self, video_path, srt_text="", translated_srt="",
                       text_size=24, text_color="white", text_position_x=-1, text_position_y=-1,
                       text_outline_color="black", text_outline_width=2,
                       trans_text_size=20, trans_text_color="yellow", trans_position_x=-1, trans_position_y=-2,
                       trans_outline_color="black", trans_outline_width=2,
                       font_name="Arial"):
        """
        将字幕烧录到视频
        """
        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 将颜色名称转换为十六进制
        text_color = COLOR_MAP.get(text_color, "#FFFFFF")
        text_outline_color = COLOR_MAP.get(text_outline_color, "#000000")
        trans_text_color = COLOR_MAP.get(trans_text_color, "#FFFF00")
        trans_outline_color = COLOR_MAP.get(trans_outline_color, "#000000")
        
        # 解析字幕
        subtitles = self._parse_srt(srt_text) if srt_text else []
        translated_subtitles = self._parse_srt(translated_srt) if translated_srt else []
        
        if not subtitles and not translated_subtitles:
            print("[FasterWhisper] 没有字幕需要烧录，返回原视频")
            return (video_path,)
        
        # 获取视频尺寸
        video_width, video_height = self._get_video_info(video_path)
        
        print(f"[FasterWhisper] 视频尺寸: {video_width}x{video_height}")
        print(f"[FasterWhisper] 原文字幕: {len(subtitles)} 条")
        print(f"[FasterWhisper] 翻译字幕: {len(translated_subtitles)} 条")
        
        # 创建 ASS 字幕文件
        ass_path = self._create_ass_file(
            subtitles, translated_subtitles, video_width, video_height,
            text_size, text_color, text_position_x, text_position_y, text_outline_color, text_outline_width,
            trans_text_size, trans_text_color, trans_position_x, trans_position_y, trans_outline_color, trans_outline_width,
            font_name
        )
        
        # 输出视频路径
        output_dir = os.path.join(folder_paths.get_temp_directory(), "burned_videos")
        os.makedirs(output_dir, exist_ok=True)
        
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{video_name}_burned.mp4")
        
        # 使用 FFmpeg 烧录字幕
        try:
            import subprocess
            
            # 构建 FFmpeg 命令
            # Windows 路径需要转义
            ass_path_escaped = ass_path.replace('\\', '/').replace(':', '\\:')
            
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vf', f"ass='{ass_path_escaped}'",
                '-c:a', 'copy',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                output_path
            ]
            
            print(f"[FasterWhisper] 执行 FFmpeg 命令...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            
            if result.returncode != 0:
                print(f"[FasterWhisper] FFmpeg 错误: {result.stderr}")
                # 尝试使用 srt 滤镜
                return self._burn_with_srt_filter(video_path, srt_text, translated_srt, output_path,
                                                   text_size, text_color, trans_text_size, trans_text_color)
            
            print(f"[FasterWhisper] 字幕烧录完成: {output_path}")
            return (output_path,)
            
        except FileNotFoundError:
            raise RuntimeError("FFmpeg 未安装或不在 PATH 中，请安装 FFmpeg")
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg 处理超时")
        except Exception as e:
            raise RuntimeError(f"字幕烧录失败: {str(e)}")
    
    def _burn_with_srt_filter(self, video_path, srt_text, translated_srt, output_path,
                               text_size, text_color, trans_size, trans_color):
        """使用 SRT 滤镜作为备选方案"""
        import subprocess
        
        # 保存 SRT 文件
        srt_dir = os.path.join(folder_paths.get_temp_directory(), "srt_subtitles")
        os.makedirs(srt_dir, exist_ok=True)
        
        filters = []
        
        if srt_text:
            srt_path = os.path.join(srt_dir, "original.srt")
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_text)
            srt_path_escaped = srt_path.replace('\\', '/').replace(':', '\\:')
            filters.append(f"subtitles='{srt_path_escaped}':force_style='FontSize={text_size},PrimaryColour={self._hex_to_ffmpeg_color(text_color)}'")
        
        if translated_srt:
            trans_srt_path = os.path.join(srt_dir, "translated.srt")
            with open(trans_srt_path, 'w', encoding='utf-8') as f:
                f.write(translated_srt)
            trans_path_escaped = trans_srt_path.replace('\\', '/').replace(':', '\\:')
            filters.append(f"subtitles='{trans_path_escaped}':force_style='FontSize={trans_size},PrimaryColour={self._hex_to_ffmpeg_color(trans_color)},MarginV=80'")
        
        if not filters:
            return (video_path,)
        
        filter_str = ','.join(filters)
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', filter_str,
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg 烧录失败: {result.stderr}")
        
        return (output_path,)
    
    def _hex_to_ffmpeg_color(self, hex_color):
        """将十六进制颜色转换为 FFmpeg 格式"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            # FFmpeg 使用 &HBBGGRR 格式
            r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
            return f"&H00{b}{g}{r}"
        return "&H00FFFFFF"

"""
路径工具模块 - 处理文件路径
"""

import os
import sys

def get_comfyui_path():
    """获取 ComfyUI 根目录"""
    # 尝试从已知位置推断
    current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 检查是否在 custom_nodes 目录下
    if 'custom_nodes' in current_path:
        comfyui_path = os.path.dirname(os.path.dirname(current_path))
        return comfyui_path
    
    # 默认返回当前目录的上两级
    return os.path.dirname(os.path.dirname(current_path))


def ensure_dir(path):
    """确保目录存在"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path


def get_models_dir():
    """获取模型目录"""
    try:
        import folder_paths
        return folder_paths.models_dir
    except ImportError:
        comfyui_path = get_comfyui_path()
        return os.path.join(comfyui_path, "models")


def get_input_dir():
    """获取输入目录"""
    try:
        import folder_paths
        return folder_paths.get_input_directory()
    except ImportError:
        comfyui_path = get_comfyui_path()
        return os.path.join(comfyui_path, "input")


def get_output_dir():
    """获取输出目录"""
    try:
        import folder_paths
        return folder_paths.get_output_directory()
    except ImportError:
        comfyui_path = get_comfyui_path()
        return os.path.join(comfyui_path, "output")


def get_temp_dir():
    """获取临时目录"""
    try:
        import folder_paths
        return folder_paths.get_temp_directory()
    except ImportError:
        import tempfile
        return tempfile.gettempdir()


def get_faster_whisper_models_dir():
    """获取 faster-whisper 模型目录"""
    models_dir = get_models_dir()
    fw_models_dir = os.path.join(models_dir, "faster-whisper")
    ensure_dir(fw_models_dir)
    return fw_models_dir


def get_media_input_dir():
    """获取媒体输入目录"""
    input_dir = get_input_dir()
    media_dir = os.path.join(input_dir, "media")
    ensure_dir(media_dir)
    return media_dir

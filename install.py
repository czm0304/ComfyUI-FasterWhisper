"""
ComfyUI-FasterWhisper 安装脚本
"""

import subprocess
import sys
import os

def install_requirements():
    """安装依赖"""
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    print("=" * 50)
    print("ComfyUI-FasterWhisper 安装程序")
    print("=" * 50)
    
    if os.path.exists(requirements_path):
        print("\n正在安装依赖...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", requirements_path
            ])
            print("\n✅ 依赖安装完成！")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ 安装失败: {e}")
            return False
    else:
        print("\n⚠️ 未找到 requirements.txt 文件")
        
    # 检查 FFmpeg
    print("\n检查 FFmpeg...")
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ FFmpeg 已安装")
        else:
            print("⚠️ FFmpeg 未正确安装")
    except FileNotFoundError:
        print("⚠️ FFmpeg 未安装，字幕烧录功能将不可用")
        print("   请从 https://ffmpeg.org/download.html 下载并安装")
    
    # 检查 CUDA
    print("\n检查 CUDA...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA 可用: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️ CUDA 不可用，将使用 CPU 进行推理")
    except ImportError:
        print("⚠️ PyTorch 未安装")
    
    print("\n" + "=" * 50)
    print("安装完成！请重启 ComfyUI 以加载插件。")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    install_requirements()

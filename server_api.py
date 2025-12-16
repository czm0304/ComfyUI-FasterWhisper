"""
ComfyUI-FasterWhisper 服务器 API 扩展
处理媒体文件上传和视图
"""

import os
import shutil
import folder_paths
from aiohttp import web

# 媒体输入目录
MEDIA_INPUT_DIR = os.path.join(folder_paths.get_input_directory(), "media")
os.makedirs(MEDIA_INPUT_DIR, exist_ok=True)


async def get_media_files(request):
    """获取已上传的媒体文件列表"""
    media_files = []
    
    if os.path.exists(MEDIA_INPUT_DIR):
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg']
        all_extensions = video_extensions + audio_extensions
        
        for filename in os.listdir(MEDIA_INPUT_DIR):
            ext = os.path.splitext(filename)[1].lower()
            if ext in all_extensions:
                file_path = os.path.join(MEDIA_INPUT_DIR, filename)
                file_size = os.path.getsize(file_path)
                file_type = 'video' if ext in video_extensions else 'audio'
                
                media_files.append({
                    'name': filename,
                    'size': file_size,
                    'type': file_type,
                    'extension': ext
                })
    
    return web.json_response({
        'files': media_files,
        'directory': MEDIA_INPUT_DIR
    })


async def delete_media_file(request):
    """删除媒体文件"""
    data = await request.json()
    filename = data.get('filename')
    
    if not filename:
        return web.json_response({'error': '未指定文件名'}, status=400)
    
    file_path = os.path.join(MEDIA_INPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        return web.json_response({'error': '文件不存在'}, status=404)
    
    try:
        os.remove(file_path)
        return web.json_response({'success': True, 'message': f'已删除 {filename}'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def get_ollama_models(request):
    """获取本地 Ollama 可用模型"""
    import aiohttp
    
    url = request.query.get('url', 'http://localhost:11434')
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{url}/api/tags', timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m['name'] for m in data.get('models', [])]
                    return web.json_response({'models': models})
                else:
                    return web.json_response({'models': [], 'error': 'Ollama 响应错误'})
    except Exception as e:
        return web.json_response({'models': [], 'error': str(e)})


def register_routes(app):
    """注册 API 路由"""
    app.router.add_get('/faster_whisper/media_files', get_media_files)
    app.router.add_post('/faster_whisper/delete_media', delete_media_file)
    app.router.add_get('/faster_whisper/ollama_models', get_ollama_models)


# ComfyUI 会自动调用这个函数
def setup_routes(app):
    register_routes(app)

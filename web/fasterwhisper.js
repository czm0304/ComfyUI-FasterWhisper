/**
 * ComfyUI-FasterWhisper 前端脚本
 * 处理文件上传、视频预览和音频播放
 */

import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// 媒体类型常量
const VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
const AUDIO_EXTENSIONS = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'];

/**
 * 上传文件到服务器
 */
async function uploadMediaFile(file) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('subfolder', 'media');
    formData.append('type', 'input');
    
    try {
        const response = await api.fetchApi('/upload/image', {
            method: 'POST',
            body: formData
        });
        
        if (response.status === 200) {
            const result = await response.json();
            return result.name;
        } else {
            console.error('[FasterWhisper] 上传失败:', response.statusText);
            return null;
        }
    } catch (error) {
        console.error('[FasterWhisper] 上传错误:', error);
        return null;
    }
}

/**
 * 创建样式
 */
function addStyles() {
    if (document.getElementById('faster-whisper-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'faster-whisper-styles';
    style.textContent = `
        .fw-upload-btn {
            width: 100%;
            padding: 12px 20px;
            margin: 8px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .fw-upload-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        .fw-upload-btn:active {
            transform: translateY(0);
        }
        
        .fw-upload-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .fw-media-preview {
            width: 100%;
            max-width: 320px;
            margin: 10px auto;
            border-radius: 10px;
            overflow: hidden;
            background: #1e1e2e;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        .fw-media-preview video {
            width: 100%;
            height: auto;
            display: block;
        }
        
        .fw-audio-container {
            padding: 20px;
            text-align: center;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        }
        
        .fw-audio-icon {
            font-size: 48px;
            margin-bottom: 15px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .fw-audio-container audio {
            width: 100%;
            margin-top: 10px;
        }
        
        .fw-text-display {
            width: 100%;
            max-height: 350px;
            overflow-y: auto;
            background: #1e1e2e;
            border-radius: 10px;
            padding: 15px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            line-height: 1.6;
            white-space: pre-wrap;
            color: #e0e0e0;
            border: 1px solid #3d3d5c;
        }
        
        .fw-text-dual-container {
            width: 100%;
            display: flex;
            gap: 10px;
        }
        
        .fw-text-column {
            flex: 1;
            max-height: 350px;
            overflow-y: auto;
            background: #1e1e2e;
            border-radius: 10px;
            padding: 15px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            line-height: 1.6;
            white-space: pre-wrap;
            color: #e0e0e0;
            border: 1px solid #3d3d5c;
        }
        
        .fw-text-column::-webkit-scrollbar {
            width: 8px;
        }
        
        .fw-text-column::-webkit-scrollbar-track {
            background: #1e1e2e;
            border-radius: 4px;
        }
        
        .fw-text-column::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 4px;
        }
        
        .fw-column-header {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid #3d3d5c;
            font-size: 13px;
        }
        
        .fw-column-content {
            white-space: pre-wrap;
        }
        
        .fw-text-display::-webkit-scrollbar {
            width: 8px;
        }
        
        .fw-text-display::-webkit-scrollbar-track {
            background: #1e1e2e;
            border-radius: 4px;
        }
        
        .fw-text-display::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 4px;
        }
        
        .fw-info-badge {
            display: inline-block;
            padding: 4px 10px;
            background: #667eea;
            color: white;
            border-radius: 12px;
            font-size: 11px;
            margin-top: 8px;
        }
    `;
    document.head.appendChild(style);
}

/**
 * 注册 MediaLoader 节点扩展
 */
app.registerExtension({
    name: "FasterWhisper.MediaLoader",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "FW_MediaLoader") return;
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            onNodeCreated?.apply(this, arguments);
            
            addStyles();
            
            const node = this;
            node.size[0] = Math.max(node.size[0], 350);
            
            // 创建主容器
            const container = document.createElement('div');
            container.style.cssText = 'padding: 10px; display: flex; flex-direction: column; gap: 10px;';
            
            // 创建上传按钮
            const uploadBtn = document.createElement('button');
            uploadBtn.className = 'fw-upload-btn';
            uploadBtn.innerHTML = '📁 <span>加载文件</span>';
            container.appendChild(uploadBtn);
            
            // 创建预览容器
            const previewContainer = document.createElement('div');
            previewContainer.className = 'fw-media-preview';
            previewContainer.style.display = 'none';
            container.appendChild(previewContainer);
            
            // 文件选择处理
            uploadBtn.addEventListener('click', () => {
                const accept = [...VIDEO_EXTENSIONS, ...AUDIO_EXTENSIONS].join(',');
                const fileInput = document.createElement('input');
                fileInput.type = 'file';
                fileInput.accept = accept;
                fileInput.style.display = 'none';
                document.body.appendChild(fileInput);
                
                fileInput.addEventListener('change', async (e) => {
                    const file = e.target.files[0];
                    if (!file) {
                        document.body.removeChild(fileInput);
                        return;
                    }
                    
                    uploadBtn.innerHTML = '⏳ <span>上传中...</span>';
                    uploadBtn.disabled = true;
                    
                    const filename = await uploadMediaFile(file);
                    
                    if (filename) {
                        // 更新节点的 media_file widget
                        const mediaWidget = node.widgets.find(w => w.name === 'media_file');
                        if (mediaWidget) {
                            if (!mediaWidget.options.values.includes(filename)) {
                                mediaWidget.options.values.push(filename);
                            }
                            mediaWidget.value = filename;
                            mediaWidget.callback?.(filename);
                        }
                        
                        // 更新预览
                        updateMediaPreview(filename, previewContainer);
                        uploadBtn.innerHTML = '✅ <span>加载成功！点击更换</span>';
                    } else {
                        uploadBtn.innerHTML = '❌ <span>上传失败，点击重试</span>';
                    }
                    
                    uploadBtn.disabled = false;
                    document.body.removeChild(fileInput);
                });
                
                fileInput.click();
            });
            
            // 添加 DOM widget
            const widget = node.addDOMWidget('fw_media_loader', 'custom', container);
            widget.serialize = false;
            
            // 监听选择变化
            const mediaWidget = node.widgets.find(w => w.name === 'media_file');
            if (mediaWidget) {
                const originalCallback = mediaWidget.callback;
                mediaWidget.callback = function(value) {
                    originalCallback?.apply(this, arguments);
                    if (value && value !== "请上传媒体文件") {
                        updateMediaPreview(value, previewContainer);
                    }
                };
                
                // 初始加载
                setTimeout(() => {
                    if (mediaWidget.value && mediaWidget.value !== "请上传媒体文件") {
                        updateMediaPreview(mediaWidget.value, previewContainer);
                    }
                }, 200);
            }
        };
    }
});

/**
 * 更新媒体预览
 */
function updateMediaPreview(filename, container) {
    container.innerHTML = '';
    container.style.display = 'block';
    
    if (!filename || filename === "请上传媒体文件") {
        container.style.display = 'none';
        return;
    }
    
    const ext = filename.substring(filename.lastIndexOf('.')).toLowerCase();
    const isVideo = VIDEO_EXTENSIONS.includes(ext);
    const mediaUrl = `/view?filename=${encodeURIComponent(filename)}&subfolder=media&type=input`;
    
    if (isVideo) {
        const video = document.createElement('video');
        video.src = mediaUrl;
        video.controls = true;
        video.loop = true;
        video.muted = false;
        video.style.cssText = 'width: 100%; height: auto; display: block;';
        container.appendChild(video);
        video.play().catch(() => {});
    } else {
        const audioContainer = document.createElement('div');
        audioContainer.className = 'fw-audio-container';
        
        const icon = document.createElement('div');
        icon.className = 'fw-audio-icon';
        icon.textContent = '🎵';
        
        const audio = document.createElement('audio');
        audio.src = mediaUrl;
        audio.controls = true;
        audio.style.width = '100%';
        
        const hint = document.createElement('div');
        hint.className = 'fw-info-badge';
        hint.textContent = '鼠标悬停自动播放';
        
        audioContainer.appendChild(icon);
        audioContainer.appendChild(audio);
        audioContainer.appendChild(hint);
        container.appendChild(audioContainer);
        
        // 鼠标悬停播放
        container.addEventListener('mouseenter', () => {
            if (audio.paused) audio.play().catch(() => {});
        });
        container.addEventListener('mouseleave', () => {
            if (!audio.paused) audio.pause();
        });
    }
}

/**
 * 注册 TextDisplay 节点扩展
 */
app.registerExtension({
    name: "FasterWhisper.TextDisplay",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "FW_TextDisplay") return;
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            onNodeCreated?.apply(this, arguments);
            
            addStyles();
            
            const node = this;
            node.size[0] = Math.max(node.size[0], 500);
            
            // 创建主容器
            const mainContainer = document.createElement('div');
            mainContainer.style.width = '100%';
            
            // 创建单列显示容器
            const singleDisplay = document.createElement('div');
            singleDisplay.className = 'fw-text-display';
            singleDisplay.textContent = '等待输入 SRT 字幕...';
            mainContainer.appendChild(singleDisplay);
            
            // 创建双列显示容器
            const dualContainer = document.createElement('div');
            dualContainer.className = 'fw-text-dual-container';
            dualContainer.style.display = 'none';
            
            // 左侧原文列
            const leftColumn = document.createElement('div');
            leftColumn.className = 'fw-text-column';
            const leftHeader = document.createElement('div');
            leftHeader.className = 'fw-column-header';
            leftHeader.textContent = '📝 原文';
            const leftContent = document.createElement('div');
            leftContent.className = 'fw-column-content';
            leftColumn.appendChild(leftHeader);
            leftColumn.appendChild(leftContent);
            
            // 右侧翻译列
            const rightColumn = document.createElement('div');
            rightColumn.className = 'fw-text-column';
            const rightHeader = document.createElement('div');
            rightHeader.className = 'fw-column-header';
            rightHeader.textContent = '🌐 翻译';
            const rightContent = document.createElement('div');
            rightContent.className = 'fw-column-content';
            rightColumn.appendChild(rightHeader);
            rightColumn.appendChild(rightContent);
            
            dualContainer.appendChild(leftColumn);
            dualContainer.appendChild(rightColumn);
            mainContainer.appendChild(dualContainer);
            
            const widget = node.addDOMWidget('fw_text_display', 'custom', mainContainer);
            widget.serialize = false;
            
            // 保存引用
            node._fwMainContainer = mainContainer;
            node._fwSingleDisplay = singleDisplay;
            node._fwDualContainer = dualContainer;
            node._fwLeftContent = leftContent;
            node._fwRightContent = rightContent;
        };
        
        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function(message) {
            onExecuted?.apply(this, arguments);
            
            if (!message || !this._fwMainContainer) return;
            
            const originalText = message.text && message.text[0] ? message.text[0] : '';
            const translatedText = message.translated_text && message.translated_text[0] ? message.translated_text[0] : '';
            
            if (translatedText) {
                // 双列模式
                this._fwSingleDisplay.style.display = 'none';
                this._fwDualContainer.style.display = 'flex';
                this._fwLeftContent.textContent = originalText;
                this._fwRightContent.textContent = translatedText;
                this.size[0] = Math.max(this.size[0], 700);
            } else {
                // 单列模式
                this._fwSingleDisplay.style.display = 'block';
                this._fwDualContainer.style.display = 'none';
                this._fwSingleDisplay.textContent = originalText || '等待输入 SRT 字幕...';
            }
            
            // 触发节点大小更新
            this.setDirtyCanvas(true, true);
        };
    }
});

/**
 * 注册 SaveVideo 节点扩展
 */
app.registerExtension({
    name: "FasterWhisper.SaveVideo",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "FW_SaveVideo") return;
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            onNodeCreated?.apply(this, arguments);
            
            addStyles();
            
            const node = this;
            node.size[0] = Math.max(node.size[0], 350);
            
            // 创建视频预览容器
            const previewContainer = document.createElement('div');
            previewContainer.className = 'fw-media-preview';
            previewContainer.style.display = 'none';
            
            const video = document.createElement('video');
            video.controls = true;
            video.loop = true;
            video.style.cssText = 'width: 100%; height: auto; display: block;';
            previewContainer.appendChild(video);
            
            const widget = node.addDOMWidget('fw_video_preview', 'custom', previewContainer);
            widget.serialize = false;
            
            node._fwVideoPreview = previewContainer;
            node._fwVideoElement = video;
        };
        
        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function(message) {
            onExecuted?.apply(this, arguments);
            
            if (message && message.video && message.video[0]) {
                const videoInfo = message.video[0];
                const videoUrl = `/view?filename=${encodeURIComponent(videoInfo.filename)}&subfolder=${encodeURIComponent(videoInfo.subfolder)}&type=${videoInfo.type}`;
                
                if (this._fwVideoPreview && this._fwVideoElement) {
                    this._fwVideoPreview.style.display = 'block';
                    this._fwVideoElement.src = videoUrl;
                    this._fwVideoElement.load();
                }
            }
        };
    }
});

/**
 * 注册 SpeechRecognition 节点扩展
 */
app.registerExtension({
    name: "FasterWhisper.SpeechRecognition",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "FW_LocalOllamaModelLoader") return;
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            onNodeCreated?.apply(this, arguments);
            
            addStyles();
            
            const node = this;
            node.size[0] = Math.max(node.size[0], 380);
            
            // 添加刷新 Ollama 模型按钮
            const container = document.createElement('div');
            container.style.cssText = 'padding: 5px;';
            
            const refreshBtn = document.createElement('button');
            refreshBtn.className = 'fw-upload-btn';
            refreshBtn.innerHTML = '🔄 <span>刷新 Ollama 模型</span>';
            refreshBtn.style.background = 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)';
            
            refreshBtn.addEventListener('click', async () => {
                refreshBtn.innerHTML = '⏳ <span>获取中...</span>';
                refreshBtn.disabled = true;
                
                try {
                    const ollamaUrlWidget = node.widgets.find(w => w.name === 'ollama_url');
                    const url = ollamaUrlWidget?.value || 'http://localhost:11434';
                    
                    const response = await fetch(`${url}/api/tags`);
                    if (response.ok) {
                        const data = await response.json();
                        const models = data.models?.map(m => m.name) || [];
                        
                        const ollamaModelWidget = node.widgets.find(w => w.name === 'ollama_model');
                        if (ollamaModelWidget && models.length > 0) {
                            ollamaModelWidget.options.values = models;
                            ollamaModelWidget.value = models[0];
                            refreshBtn.innerHTML = `✅ <span>找到 ${models.length} 个模型</span>`;
                        } else {
                            refreshBtn.innerHTML = '⚠️ <span>未找到模型</span>';
                        }
                    } else {
                        refreshBtn.innerHTML = '❌ <span>连接失败</span>';
                    }
                } catch (e) {
                    refreshBtn.innerHTML = '❌ <span>无法连接 Ollama</span>';
                }
                
                refreshBtn.disabled = false;
                setTimeout(() => {
                    refreshBtn.innerHTML = '🔄 <span>刷新 Ollama 模型</span>';
                }, 3000);
            });
            
            container.appendChild(refreshBtn);
            
            const widget = node.addDOMWidget('fw_refresh_ollama', 'custom', container);
            widget.serialize = false;
        };
    }
});

/**
 * 注册 VideoBurn 节点扩展
 */
app.registerExtension({
    name: "FasterWhisper.VideoBurn",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "FW_VideoBurn") return;
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            onNodeCreated?.apply(this, arguments);
            
            addStyles();
            
            const node = this;
            node.size[0] = Math.max(node.size[0], 380);
        };
    }
});

console.log('[FasterWhisper] 插件前端已加载 ✨');

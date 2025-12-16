"""
LLM API 节点 - 用于配置外部大模型 API 作为翻译模型
支持 OpenAI 兼容 API、Ollama、以及其他自定义 API
"""

import requests
import json


# 预设的 API 类型
API_TYPES = [
    "OpenAI兼容",
    "Ollama",
    "自定义",
]


class LLMApiNode:
    """
    LLM API 配置节点
    - 输出：LLM_API 配置对象，可连接到语音识别节点作为翻译模型
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_type": (API_TYPES, {
                    "default": "OpenAI兼容",
                    "tooltip": "API 类型"
                }),
                "api_url": ("STRING", {
                    "default": "http://localhost:11434/v1/chat/completions",
                    "multiline": False,
                    "tooltip": "API 端点地址\nOpenAI兼容: http://xxx/v1/chat/completions\nOllama: http://localhost:11434/api/generate"
                }),
                "model_name": ("STRING", {
                    "default": "qwen2.5:7b",
                    "multiline": False,
                    "tooltip": "模型名称"
                }),
            },
            "optional": {
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "API 密钥（如需要）"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.3,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "生成温度，越低越确定"
                }),
                "max_tokens": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 8192,
                    "step": 64,
                    "tooltip": "最大生成 token 数"
                }),
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "系统提示词（可选，留空使用默认翻译提示）"
                }),
            },
        }
    
    RETURN_TYPES = ("LLM_API",)
    RETURN_NAMES = ("LLM API",)
    FUNCTION = "create_api_config"
    CATEGORY = "FasterWhisper/API"
    OUTPUT_NODE = False
    
    def create_api_config(self, api_type, api_url, model_name, 
                          api_key="", temperature=0.3, max_tokens=1024, system_prompt=""):
        """
        创建 LLM API 配置对象
        """
        config = {
            "api_type": api_type,
            "api_url": api_url,
            "model_name": model_name,
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system_prompt": system_prompt,
        }
        
        print(f"[FasterWhisper] LLM API 配置: {api_type} - {model_name}")
        
        return (config,)


def call_llm_api(config, prompt, target_language):
    """
    调用 LLM API 进行翻译
    
    Args:
        config: LLM API 配置对象
        prompt: 要翻译的文本
        target_language: 目标语言名称
    
    Returns:
        翻译后的文本
    """
    api_type = config.get("api_type", "OpenAI兼容")
    api_url = config.get("api_url", "")
    model_name = config.get("model_name", "")
    api_key = config.get("api_key", "")
    temperature = config.get("temperature", 0.3)
    max_tokens = config.get("max_tokens", 1024)
    system_prompt = config.get("system_prompt", "")
    
    # 默认翻译系统提示
    if not system_prompt:
        system_prompt = f"你是一个专业的翻译助手。请将用户提供的文本翻译成{target_language}，只输出翻译结果，不要任何解释或额外内容。"
    else:
        # 替换目标语言占位符
        system_prompt = system_prompt.replace("{target_language}", target_language)
    
    try:
        if api_type == "Ollama":
            return _call_ollama_api(api_url, model_name, prompt, system_prompt, temperature)
        else:
            # OpenAI 兼容 API 或自定义
            return _call_openai_compatible_api(
                api_url, model_name, api_key, prompt, system_prompt, temperature, max_tokens
            )
    except Exception as e:
        print(f"[FasterWhisper] LLM API 调用错误: {str(e)}")
        return prompt  # 返回原文


def _call_ollama_api(api_url, model_name, prompt, system_prompt, temperature):
    """调用 Ollama API"""
    # 构建完整提示
    full_prompt = f"{system_prompt}\n\n{prompt}"
    
    response = requests.post(
        api_url,
        json={
            "model": model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        return result.get('response', prompt).strip()
    else:
        print(f"[FasterWhisper] Ollama API 错误: {response.status_code}")
        return prompt


def _call_openai_compatible_api(api_url, model_name, api_key, prompt, system_prompt, temperature, max_tokens):
    """调用 OpenAI 兼容 API"""
    headers = {
        "Content-Type": "application/json",
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        # 标准 OpenAI 格式
        choices = result.get('choices', [])
        if choices:
            message = choices[0].get('message', {})
            return message.get('content', prompt).strip()
        return prompt
    else:
        print(f"[FasterWhisper] OpenAI API 错误: {response.status_code} - {response.text}")
        return prompt

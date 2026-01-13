"""
LLM API 节点 - 用于配置外部大模型 API 作为翻译模型
支持 OpenAI 兼容 API、Ollama、以及其他自定义 API
"""

import requests
import json
import re


def _clean_translation_output(text, original_text=""):
    """清理翻译输出，移除解释性内容"""
    if not text:
        return text
    
    # 移除 <think>...</think> 标签（deepseek-r1 等推理模型）
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # 移除末尾的中文注释（如：（译文：...）、（翻译：...））
    text = re.sub(r'[（\(]\s*(?:译文|翻译|注|备注)[：:].+?[）\)]\s*$', '', text)
    
    # 移除末尾换行后的中文内容（翻译到英文时不应有中文）
    text = re.sub(r'\n+[\u4e00-\u9fff].+$', '', text)
    
    # 常见解释性前缀模式
    patterns = [
        # The phrase "X" ... "Y" 模式
        r'^.*?[Tt]he (?:phrase|word|text|sentence)\s*["\'\u201c].+?["\'\u201d].*?["\'\u201c](.+?)["\'\u201d].*$',
        r'^.*?(?:can be translated (?:to|as|into)|translates to|translation (?:is|would be)|means)\s*["\'“]?(.+?)["\'”]?\s*\.?$',
        r'^.*?(?:翻译(?:为|成|结果是|如下))[\s：:]*["\'“]?(.+?)["\'”]?\s*$',
        r'^.*?(?:的\w+翻译是)[\s：:]*["\'“]?(.+?)["\'”]?\s*$',
        r'^.*?(?:in \w+ (?:is|would be))[\s:]*["\'“]?(.+?)["\'”]?\s*\.?$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            extracted = match.group(1).strip()
            if extracted:
                text = extracted
                break
    
    # 移除包裹的引号
    text = re.sub(r'^["\'“\u300c](.+)["\'”\u300d]$', r'\1', text.strip())
    
    return text.strip()


# 预设的 API 类型
API_TYPES = [
    "OpenAI兼容",
    "Google Gemini",
    "Claude",
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
        system_prompt = f"你是翻译机器。用户输入任何内容，你只输出{target_language}译文，不说任何其他话。"
    else:
        # 替换目标语言占位符
        system_prompt = system_prompt.replace("{target_language}", target_language)
    
    # 保存原始文本，用于异常时返回
    original_text = prompt
    
    # 在用户输入前添加翻译指令，强制模型直接输出译文
    prompt = f"翻译成{target_language}（只输出译文）：{prompt}"
    
    try:
        if api_type == "Ollama":
            result = _call_ollama_api(api_url, model_name, prompt, system_prompt, temperature)
        elif api_type == "Google Gemini":
            result = _call_gemini_api(api_url, model_name, api_key, prompt, system_prompt, temperature, max_tokens)
        elif api_type == "Claude":
            result = _call_claude_api(api_url, model_name, api_key, prompt, system_prompt, temperature, max_tokens)
        else:
            # OpenAI 兼容 API 或自定义
            api_format = config.get("api_format", "自动检测")
            result = _call_openai_compatible_api(
                api_url, model_name, api_key, prompt, system_prompt, temperature, max_tokens, api_format
            )
        
        # 后处理：清理解释性内容
        return _clean_translation_output(result)
    except Exception as e:
        print(f"[FasterWhisper] LLM API 调用错误: {str(e)}")
        return original_text  # 返回原文（不带翻译指令）


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
        timeout=300
    )
    
    if response.status_code == 200:
        result = response.json()
        return result.get('response', prompt).strip()
    else:
        print(f"[FasterWhisper] Ollama API 错误: {response.status_code}")
        return prompt


def _call_gemini_api(api_url, model_name, api_key, prompt, system_prompt, temperature, max_tokens):
    """调用 Google Gemini API"""
    # Gemini API URL 格式: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
    if not api_url:
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    
    # 如果 URL 不包含 model，添加 model
    if ":generateContent" not in api_url:
        api_url = f"{api_url.rstrip('/')}/models/{model_name}:generateContent"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    # Gemini 使用 URL 参数传递 API key
    url_with_key = f"{api_url}?key={api_key}"
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n{prompt}"}]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    }
    
    print(f"[FasterWhisper] API 模式: Gemini, Model: {model_name}")
    
    response = requests.post(
        url_with_key,
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        candidates = result.get('candidates', [])
        if candidates:
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if parts:
                return parts[0].get('text', prompt).strip()
        return prompt
    else:
        print(f"[FasterWhisper] Gemini API 错误: {response.status_code} - {response.text}")
        return prompt


def _call_claude_api(api_url, model_name, api_key, prompt, system_prompt, temperature, max_tokens):
    """调用 Anthropic Claude API"""
    if not api_url:
        api_url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": model_name,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
    }
    
    print(f"[FasterWhisper] API 模式: Claude, Model: {model_name}")
    
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result.get('content', [])
        if content:
            for block in content:
                if block.get('type') == 'text':
                    return block.get('text', prompt).strip()
        return prompt
    else:
        print(f"[FasterWhisper] Claude API 错误: {response.status_code} - {response.text}")
        return prompt


def _call_openai_compatible_api(api_url, model_name, api_key, prompt, system_prompt, temperature, max_tokens, api_format="自动检测"):
    """调用 OpenAI 兼容 API（支持 chat/completions、completions 和 responses 三种格式）"""
    headers = {
        "Content-Type": "application/json",
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # 确定 API 格式: chat, completions, responses
    api_mode = "chat"  # 默认
    
    if api_format == "Completions (prompt)":
        api_mode = "completions"
    elif api_format == "Chat Completions (messages)":
        api_mode = "chat"
    elif api_format == "Responses (input)":
        api_mode = "responses"
    else:
        # 自动检测：根据 URL 判断
        if "/responses" in api_url:
            api_mode = "responses"
        elif "/completions" in api_url and "/chat/completions" not in api_url:
            api_mode = "completions"
        else:
            api_mode = "chat"
    
    print(f"[FasterWhisper] API 模式: {api_mode}, URL: {api_url}")
    
    # 根据模式构建请求体
    if api_mode == "completions":
        # Completions API 格式（用于 doubao-seed 等模型）
        full_prompt = f"{system_prompt}\n\n{prompt}"
        payload = {
            "model": model_name,
            "prompt": full_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
    elif api_mode == "responses":
        # Responses API 格式（火山方舟 doubao-seed 等模型）
        payload = {
            "model": model_name,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}]
                },
                {
                    "role": "user", 
                    "content": [{"type": "input_text", "text": prompt}]
                }
            ],
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
    else:
        # Chat Completions API 格式（标准 OpenAI）
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
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        
        if api_mode == "responses":
            # Responses API 返回格式
            output = result.get('output', [])
            if output:
                for item in output:
                    if item.get('type') == 'message':
                        content = item.get('content', [])
                        for c in content:
                            if c.get('type') == 'output_text':
                                return c.get('text', prompt).strip()
            return prompt
        
        choices = result.get('choices', [])
        if choices:
            if api_mode == "completions":
                # Completions 格式返回 text
                return choices[0].get('text', prompt).strip()
            else:
                # Chat 格式返回 message.content
                message = choices[0].get('message', {})
                return message.get('content', prompt).strip()
        return prompt
    else:
        print(f"[FasterWhisper] OpenAI API 错误: {response.status_code} - {response.text}")
        return prompt

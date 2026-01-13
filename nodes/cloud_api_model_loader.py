PROVIDERS = [
    "OpenAI",
    "OpenAI兼容",
    "自定义",
]

API_FORMATS = [
    "自动检测",
    "Chat Completions (messages)",
    "Completions (prompt)",
    "Responses (input)",
]


_DEFAULT_PROVIDER_URLS = {
    "OpenAI": "https://api.openai.com/v1/chat/completions",
    "OpenAI兼容": "https://api.openai.com/v1/chat/completions",
    "自定义": "",
}


class CloudApiModelLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "provider": (PROVIDERS, {
                    "default": "OpenAI兼容",
                    "tooltip": "API 提供商",
                }),
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "API 密钥",
                }),
                "model_name": ("STRING", {
                    "default": "gpt-4o-mini",
                    "multiline": False,
                    "tooltip": "模型名称",
                }),
            },
            "optional": {
                "api_url": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "API 端点地址（可选，留空使用提供商默认值；需为 OpenAI 兼容 /v1/chat/completions）",
                }),
                "temperature": ("FLOAT", {
                    "default": 0.3,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "生成温度",
                }),
                "max_tokens": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 8192,
                    "step": 64,
                    "tooltip": "最大生成 token 数",
                }),
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "系统提示词（可选，留空使用默认翻译提示）",
                }),
                "api_format": (API_FORMATS, {
                    "default": "自动检测",
                    "tooltip": "API 格式：\n- 自动检测: 根据 URL 自动判断\n- Chat Completions: 使用 messages 数组\n- Completions: 使用 prompt 字符串（doubao-seed 等）",
                }),
            },
        }

    RETURN_TYPES = ("LLM_API",)
    RETURN_NAMES = ("LLM Model",)
    FUNCTION = "create_cloud_model_config"
    CATEGORY = "FasterWhisper/API"
    OUTPUT_NODE = False

    def create_cloud_model_config(
        self,
        provider,
        api_key,
        model_name,
        api_url="",
        temperature=0.3,
        max_tokens=1024,
        system_prompt="",
        api_format="自动检测",
    ):
        resolved_api_url = (api_url or "").strip()
        if not resolved_api_url:
            resolved_api_url = _DEFAULT_PROVIDER_URLS.get(provider, "")

        config = {
            "provider": provider,
            "api_type": "OpenAI兼容",
            "api_url": resolved_api_url,
            "model_name": model_name,
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system_prompt": system_prompt,
            "api_format": api_format,
        }

        print(f"[FasterWhisper] Cloud API 模型配置: {provider} - {model_name}")

        return (config,)

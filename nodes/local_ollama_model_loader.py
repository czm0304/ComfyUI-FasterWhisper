import requests


class LocalOllamaModelLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        ollama_models = cls._get_ollama_models()

        return {
            "required": {
                "ollama_model": (ollama_models, {
                    "default": ollama_models[0] if ollama_models else "无可用模型",
                    "tooltip": "本地 Ollama 模型",
                }),
                "ollama_url": ("STRING", {
                    "default": "http://localhost:11434",
                    "multiline": False,
                    "tooltip": "Ollama API 地址",
                }),
            },
            "optional": {
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
                    "tooltip": "最大生成 token 数（Ollama generate 接口可能忽略）",
                }),
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "系统提示词（可选，留空使用默认翻译提示）",
                }),
            },
        }

    RETURN_TYPES = ("LLM_API",)
    RETURN_NAMES = ("LLM Model",)
    FUNCTION = "create_local_model_config"
    CATEGORY = "FasterWhisper/API"
    OUTPUT_NODE = False

    @classmethod
    def _get_ollama_models(cls):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models_data = response.json()
                models = [m["name"] for m in models_data.get("models", [])]
                if models:
                    return models
        except Exception:
            pass

        return ["qwen2.5:7b", "llama3.1:8b", "gemma2:9b", "无可用模型"]

    def create_local_model_config(self, ollama_model, ollama_url, temperature=0.3, max_tokens=1024, system_prompt=""):
        base_url = (ollama_url or "").rstrip("/")
        api_url = f"{base_url}/api/generate" if base_url else "http://localhost:11434/api/generate"

        config = {
            "api_type": "Ollama",
            "api_url": api_url,
            "model_name": ollama_model,
            "api_key": "",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system_prompt": system_prompt,
        }

        print(f"[FasterWhisper] 本地大模型配置: Ollama - {ollama_model}")

        return (config,)

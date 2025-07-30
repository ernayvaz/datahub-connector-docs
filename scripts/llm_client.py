import os
import requests


class LLMClient:
    """Base class for LLM clients."""
    def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        raise NotImplementedError("generate() must be implemented by subclasses")


class OpenAIClient(LLMClient):
    def __init__(self):
        try:
            import openai
            self.openai = openai
        except ImportError as e:
            raise RuntimeError("openai package is required for OpenAIClient")
        token = os.getenv("LLM_TOKEN") or os.getenv("OPENAI_API_KEY")
        if not token:
            raise RuntimeError("OpenAI API key not set in LLM_TOKEN or OPENAI_API_KEY")
        self.openai.api_key = token
        # Model name can be overridden via LLM_MODEL
        self.model = os.getenv("LLM_MODEL", "gpt-4o")

    def generate(self, prompt: str) -> str:
        response = self.openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content


class OllamaClient(LLMClient):
    def __init__(self):
        # Default Ollama local endpoint; override via LLM_ENDPOINT
        self.endpoint = os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "mistral")
        # Timeout for long model loads/generations
        self.timeout = int(os.getenv("LLM_TIMEOUT", "300"))

    def generate(self, prompt: str) -> str:
        resp = requests.post(
            self.endpoint,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=self.timeout
        )
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns {'response': '...'}
        return data.get("response", "")


class InternalLLMClient(LLMClient):
    def __init__(self):
        self.endpoint = os.getenv("LLM_ENDPOINT")
        self.token = os.getenv("LLM_TOKEN")
        if not self.endpoint:
            raise RuntimeError("LLM_ENDPOINT not set for internal provider")
        if not self.token:
            raise RuntimeError("LLM_TOKEN not set for internal provider")

    def generate(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(
            self.endpoint,
            json={"prompt": prompt},
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        # Assume internal service returns {'response': '...'} or raw text
        return data.get("response") or data.get("text") or resp.text


def get_llm_client() -> LLMClient:
    """Factory to return an LLM client based on LLM_PROVIDER env var."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    # Restrict external LLM providers in production environment
    env_mode = os.getenv("APP_ENV", "development").lower()
    if env_mode == "production" and provider not in ("internal", "internal_llm"):
        raise RuntimeError(f"External LLM provider '{provider}' not allowed in production")
    if provider == "openai":
        return OpenAIClient()
    elif provider == "ollama":
        return OllamaClient()
    elif provider in ("internal", "internal_llm"):
        return InternalLLMClient()
    else:
        raise RuntimeError(f"Unknown LLM provider: {provider}") 
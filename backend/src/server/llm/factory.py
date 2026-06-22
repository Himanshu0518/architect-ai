import os

from .providers import (
    GeminiProvider,
    GroqProvider,
    OpenRouterProvider,
    CerebrasProvider,
)


class LLMFactory:
    _providers = {
        "openrouter": OpenRouterProvider,
        "groq": GroqProvider,
        "gemini": GeminiProvider,
        "cerebras": CerebrasProvider,
    }

    @classmethod
    def create(cls, provider: str | None = None):
        provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        provider = provider.lower()

        if provider not in cls._providers:
            raise ValueError(f"Unsupported provider: {provider}")

        return cls._providers[provider]()
    
    @classmethod
    def get_all_providers(cls):
        """Returns instantiated providers for all available ones to be used for fallback chaining."""
        instances = []
        for name, provider_cls in cls._providers.items():
            try:
                instances.append((name, provider_cls().get_llm()))
            except ValueError:
                # API key missing for this provider, skip
                continue
        return instances
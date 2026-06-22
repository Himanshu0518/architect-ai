import os

from crewai import LLM

from .base import BaseLLMProvider
from dotenv import load_dotenv

load_dotenv()

class GeminiProvider(BaseLLMProvider):

    def get_llm(self) -> LLM:

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found.")

        return LLM(
            model="gemini/gemini-2.5-flash",
            api_key=api_key,
        )


class GroqProvider(BaseLLMProvider):

    def get_llm(self) -> LLM:

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY not found.")

        return LLM(
            model="groq/llama-3.3-70b-versatile",
            api_key=api_key,
        )

class OpenRouterProvider(BaseLLMProvider):

    def get_llm(self) -> LLM:
        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found.")

        # Using a reliable fast model from openrouter
        return LLM(
            model="openrouter/meta-llama/llama-3.3-70b-instruct",
            api_key=api_key,
        )

class CerebrasProvider(BaseLLMProvider):

    def get_llm(self) -> LLM:
        api_key = os.getenv("CEREBRAS_API_KEY")

        if not api_key:
            raise ValueError("CEREBRAS_API_KEY not found.")

        return LLM(
            model="cerebras/llama3.1-8b",
            api_key=api_key,
        )

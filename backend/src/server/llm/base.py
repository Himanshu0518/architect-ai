from abc import ABC, abstractmethod
from crewai import LLM


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def get_llm(self) -> LLM:
        """Return a configured CrewAI LLM instance."""
        pass
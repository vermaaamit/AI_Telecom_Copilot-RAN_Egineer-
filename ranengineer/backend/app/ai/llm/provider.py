import os
from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    def explain(self, question: str, evidence: dict[str, Any]) -> str:
        """Return an engineering explanation grounded exclusively in supplied evidence."""
        pass


def get_llm_provider() -> LLMProvider:
    """Return configured Azure OpenAI provider if environment variables are present, else fallback to deterministic provider."""
    from app.ai.llm.azure_openai import AzureOpenAIProvider
    from app.ai.llm.deterministic import DeterministicLLMProvider

    azure_provider = AzureOpenAIProvider.from_environment()
    if azure_provider is not None:
        return azure_provider
    return DeterministicLLMProvider()

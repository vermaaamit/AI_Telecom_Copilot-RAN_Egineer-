import os
from typing import Any

import httpx

from app.ai.llm.provider import LLMProvider
from app.ai.prompts.system_prompt import RAN_COPILOT_SYSTEM_PROMPT, format_evidence_prompt


class AzureOpenAIProvider(LLMProvider):
    def __init__(self, endpoint: str, api_key: str, deployment: str, api_version: str = "2024-10-21") -> None:
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.deployment = deployment
        self.api_version = api_version

    @classmethod
    def from_environment(cls) -> "AzureOpenAIProvider | None":
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        if not all((endpoint, api_key, deployment)):
            return None
        return cls(
            endpoint=endpoint,
            api_key=api_key,
            deployment=deployment,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )

    def explain(self, question: str, evidence: dict[str, Any]) -> str:
        prompt = format_evidence_prompt(question, evidence)
        url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "messages": [
                {"role": "system", "content": RAN_COPILOT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 800,
        }
        with httpx.Client(timeout=25.0) as client:
            response = client.post(url, params={"api-version": self.api_version}, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

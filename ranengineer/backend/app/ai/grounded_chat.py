import logging
from typing import Any

import httpx

from app.ai.guardrails.grounding import apply_guardrails
from app.ai.intent import parse_intent
from app.ai.llm.azure_openai import AzureOpenAIProvider
from app.ai.llm.deterministic import DeterministicLLMProvider
from app.ai.llm.provider import get_llm_provider
from app.ai.tools.analytics_tools import execute_intent

logger = logging.getLogger("ranengineer.chat")


def answer_question(question: str, dataset: dict[str, Any]) -> dict[str, Any]:
    # 1. Parse natural language intent into structured query
    intent = parse_intent(question)
    logger.info("Parsed intent: %s (limit=%s, target=%s, kpi=%s)", intent.name, intent.limit, intent.target_id, intent.kpi)

    # 2. Execute controlled deterministic analytics tool (AI never touches raw database)
    evidence = execute_intent(
        dataset=dataset,
        intent_name=intent.name,
        limit=intent.limit,
        target_id=intent.target_id,
        target_id_2=intent.target_id_2,
        kpi=intent.kpi,
        threshold=intent.threshold,
        direction=intent.direction,
    )

    # 3. Choose provider (Azure OpenAI if configured, else deterministic generator)
    provider = get_llm_provider()
    provider_mode = "azure_openai_grounded" if isinstance(provider, AzureOpenAIProvider) else "grounded_deterministic"
    warning = None

    try:
        raw_explanation = provider.explain(question, evidence)
    except (httpx.HTTPError, Exception) as exc:
        logger.warning("LLM provider failed: %s; falling back to deterministic explanation.", exc)
        fallback = DeterministicLLMProvider()
        raw_explanation = fallback.explain(question, evidence)
        provider_mode = "grounded_deterministic"
        warning = f"AI provider was unavailable ({type(exc).__name__}); returned deterministic analysis."

    # 4. Enforce grounding and safety guardrails
    final_answer, guardrail_report = apply_guardrails(raw_explanation, evidence)

    result = {
        "mode": provider_mode,
        "intent": intent.name,
        "intent_parameters": {
            "limit": intent.limit,
            "target_id": intent.target_id,
            "target_id_2": intent.target_id_2,
            "kpi": intent.kpi,
            "threshold": intent.threshold,
            "direction": intent.direction,
        },
        "tool_called": intent.name,
        "evidence": evidence,
        "answer": final_answer,
        "guardrail_report": guardrail_report,
    }
    if warning:
        result["warning"] = warning

    return result

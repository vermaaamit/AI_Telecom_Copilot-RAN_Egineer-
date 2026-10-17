from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeDoc(BaseModel):
    id: str
    title: str
    domain: str
    keywords: list[str] = Field(default_factory=list)
    source: str
    content: str
    relevance_score: float = 0.0


class KnowledgeSearchResult(BaseModel):
    query: str
    total_matched: int
    documents: list[KnowledgeDoc] = Field(default_factory=list)
    disclaimer: str = (
        "Telecom engineering standards provided for domain guidance. "
        "Domain knowledge does not replace numerical telemetry calculations."
    )


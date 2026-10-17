from __future__ import annotations

import json
import re
from pathlib import Path
from app.ai.rag.models import KnowledgeDoc, KnowledgeSearchResult


def _find_docs_path() -> Path:
    # 1. Project relative (backend/app/ai/rag/retriever.py -> configs/knowledge/documents.json)
    candidate_1 = Path(__file__).resolve().parents[4] / "configs" / "knowledge" / "documents.json"
    if candidate_1.exists():
        return candidate_1
    # 2. Container root mount path
    candidate_2 = Path("/configs/knowledge/documents.json")
    if candidate_2.exists():
        return candidate_2
    # 3. Fallback relative
    candidate_3 = Path("configs/knowledge/documents.json")
    if candidate_3.exists():
        return candidate_3
    return candidate_1


class RanKnowledgeRetriever:
    """Deterministic Telecom Knowledge Base & RAG Retriever."""

    def __init__(self, doc_path: Path | None = None) -> None:
        self.doc_path = doc_path or _find_docs_path()
        self._documents: list[KnowledgeDoc] = self._load_documents()

    def _load_documents(self) -> list[KnowledgeDoc]:
        if not self.doc_path.exists():
            return []
        try:
            with self.doc_path.open(encoding="utf-8") as f:
                data = json.load(f)
                return [KnowledgeDoc(**item) for item in data]
        except Exception:
            return []

    def search_ran_knowledge(self, query: str, limit: int = 3) -> KnowledgeSearchResult:
        tokens = set(re.findall(r"\w+", query.lower()))
        if not tokens or not self._documents:
            return KnowledgeSearchResult(query=query, total_matched=0, documents=[])

        scored_docs: list[KnowledgeDoc] = []

        for doc in self._documents:
            score = 0.0
            doc_title_lower = doc.title.lower()
            doc_content_lower = doc.content.lower()
            doc_domain_lower = doc.domain.lower()
            doc_keywords = [k.lower() for k in doc.keywords]

            for token in tokens:
                if len(token) < 2:
                    continue
                # Title token match
                if token in doc_title_lower:
                    score += 5.0
                # Keyword exact match
                if token in doc_keywords:
                    score += 4.0
                # Domain match
                if token in doc_domain_lower:
                    score += 3.0
                # Content occurrences
                content_count = doc_content_lower.count(token)
                if content_count > 0:
                    score += min(content_count * 1.0, 5.0)

            if score > 0:
                doc_copy = doc.model_copy()
                doc_copy.relevance_score = round(score, 2)
                scored_docs.append(doc_copy)

        scored_docs.sort(key=lambda d: d.relevance_score, reverse=True)
        top_results = scored_docs[:limit]

        return KnowledgeSearchResult(
            query=query,
            total_matched=len(scored_docs),
            documents=top_results,
        )


_retriever: RanKnowledgeRetriever | None = None


def get_knowledge_retriever() -> RanKnowledgeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RanKnowledgeRetriever()
    return _retriever


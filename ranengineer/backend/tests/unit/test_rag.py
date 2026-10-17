from app.ai.rag.retriever import RanKnowledgeRetriever


def test_knowledge_retriever_keyword_search():
    retriever = RanKnowledgeRetriever()
    res = retriever.search_ran_knowledge("interference and rsrp", limit=2)
    assert res.total_matched >= 1
    assert len(res.documents) <= 2
    top_doc = res.documents[0]
    assert "3GPP" in top_doc.title or "Interference" in top_doc.title
    assert top_doc.relevance_score > 0


def test_knowledge_retriever_oran_search():
    retriever = RanKnowledgeRetriever()
    res = retriever.search_ran_knowledge("non-rt ric A1 policy rApp", limit=1)
    assert res.total_matched >= 1
    assert "ORAN-RIC-003" in res.documents[0].id
    assert "O-RAN" in res.documents[0].domain


def test_knowledge_retriever_empty_query():
    retriever = RanKnowledgeRetriever()
    res = retriever.search_ran_knowledge("")
    assert res.total_matched == 0
    assert len(res.documents) == 0


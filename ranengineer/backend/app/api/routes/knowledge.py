from fastapi import APIRouter, Query
from app.ai.rag import get_knowledge_retriever

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search", summary="Search 3GPP & O-RAN engineering standards and troubleshooting guides")
def search_knowledge(
    q: str = Query(..., min_length=2, description="Telecom query or issue description"),
    limit: int = Query(3, ge=1, le=10),
) -> dict[str, object]:
    result = get_knowledge_retriever().search_ran_knowledge(query=q, limit=limit)
    return result.model_dump(mode="json")


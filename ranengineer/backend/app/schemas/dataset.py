from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, object]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    dataset_id: str

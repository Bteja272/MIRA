from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.langgraph_agent_service import (
    LangGraphAgentService,
)


router = APIRouter(tags=["Query"])


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    document_id: str | None = None


@router.post("/query")
def query_agent(request: QueryRequest):
    return LangGraphAgentService.query(
        query=request.query,
        document_id=request.document_id,
    )
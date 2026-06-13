from fastapi import APIRouter
from pydantic import BaseModel

from app.services.langgraph_agent_service import LangGraphAgentService


router = APIRouter(tags=["Query"])


class QueryRequest(BaseModel):
    query: str


@router.post("/query")
def query_agent(request: QueryRequest):
    return LangGraphAgentService.query(
        request.query
    )
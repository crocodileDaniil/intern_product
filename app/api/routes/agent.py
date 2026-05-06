from fastapi import APIRouter

from app.schemas.agent import AgentQueryRequest, AgentQueryResponse


router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/query", response_model=AgentQueryResponse)
def query_agent(payload: AgentQueryRequest) -> AgentQueryResponse:
    return AgentQueryResponse(
        question=payload.question,
        answer=(
            "Пока это заглушка. В будущем здесь будет модуль анализа "
            "запроса и поиск по коммерческим предложениям."
        ),
    )

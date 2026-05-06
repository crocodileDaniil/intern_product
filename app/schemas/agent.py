from pydantic import BaseModel


class AgentQueryRequest(BaseModel):
    question: str


class AgentQueryResponse(BaseModel):
    question: str
    answer: str

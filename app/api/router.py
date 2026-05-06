from fastapi import APIRouter

from app.api.routes.agent import router as agent_router
from app.api.routes.documents import router as documents_router
from app.api.routes.jobs import router as jobs_router


api_router = APIRouter(prefix="/api")
api_router.include_router(documents_router)
api_router.include_router(jobs_router)
api_router.include_router(agent_router)

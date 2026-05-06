from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.services.file_storage import ensure_upload_dir


app = FastAPI(
    title="Commercial Offers Backend",
    description="Backend для загрузки и первичного учёта коммерческих предложений в PDF.",
    version="1.0.0",
)


@app.on_event("startup")
def create_tables() -> None:
    ensure_upload_dir()
    Base.metadata.create_all(bind=engine)
    app.state.upload_dir = str(settings.upload_dir)


app.include_router(api_router)

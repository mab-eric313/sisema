from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.api import api_router
from core.config import settings

FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"

app = FastAPI(
    title=settings.PROJECT_NAME,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_HOST],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.frontend("/", directory=FRONTEND_DIR)

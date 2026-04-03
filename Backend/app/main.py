from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.db.init_db import initialize_database
from app.services.upload_service import ensure_upload_dir


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version=settings.project_version,
        description="FastAPI backend for the DevEla project.",
    )
    frontend_dir = Path(__file__).resolve().parents[2] / "Frontend"

    # Open CORS for local development while frontend/backend are served separately.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup_event() -> None:
        initialize_database()
        ensure_upload_dir()

    @app.get("/", tags=["Root"])
    def read_root() -> dict[str, str]:
        response = {"message": "DevEla FastAPI backend is running."}
        if frontend_dir.exists():
            response["frontend_url"] = "http://127.0.0.1:8000/frontend/index.html"
        return response

    app.include_router(api_router, prefix="/api")
    if frontend_dir.exists():
        app.mount("/frontend", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    return app


app = create_app()

from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.profile import router as profile_router
from app.api.routes.submission import router as submission_router
from app.api.routes.submissions import router as submissions_router
from app.api.routes.usecase import router as usecase_router
from app.api.routes.video import router as video_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/v1", tags=["Health"])
api_router.include_router(auth_router, prefix="/v1")
api_router.include_router(profile_router, prefix="/v1")
api_router.include_router(usecase_router, prefix="/v1")
api_router.include_router(submission_router, prefix="/v1")
api_router.include_router(submissions_router, prefix="/v1")
api_router.include_router(video_router, prefix="/v1")
api_router.include_router(admin_router, prefix="/v1")

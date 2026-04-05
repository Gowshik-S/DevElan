from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.services.upload_service import ALLOWED_VIDEO_EXTENSIONS

router = APIRouter(tags=["Pages"])

frontend_dir = Path(__file__).resolve().parents[4] / "Frontend"
templates = Jinja2Templates(directory=str(frontend_dir))

PREFERRED_VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".webm", ".avi")


def _get_ordered_video_extensions() -> list[str]:
    ordered = [ext for ext in PREFERRED_VIDEO_EXTENSIONS if ext in ALLOWED_VIDEO_EXTENSIONS]
    remaining = sorted(ext for ext in ALLOWED_VIDEO_EXTENSIONS if ext not in ordered)
    return ordered + remaining


def _render_template(request: Request, template_name: str, context: dict[str, object] | None = None) -> HTMLResponse:
    response = templates.TemplateResponse(request, template_name, context or {})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing_page(request: Request) -> HTMLResponse:
    return _render_template(request, "index.html")


@router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_page(request: Request) -> HTMLResponse:
    return _render_template(request, "admin.html")


@router.get("/submissions", response_class=HTMLResponse, include_in_schema=False)
def submissions_page(request: Request) -> HTMLResponse:
    return _render_template(request, "form.html")


@router.get("/user-home", response_class=HTMLResponse, include_in_schema=False)
def user_home_page(request: Request) -> HTMLResponse:
    return _render_template(
        request,
        "user_home.html",
        {
            "max_upload_size_mb": settings.max_upload_size_mb,
            "allowed_video_extensions": _get_ordered_video_extensions(),
        },
    )


@router.get("/user-profile", response_class=HTMLResponse, include_in_schema=False)
def user_profile_page(request: Request) -> HTMLResponse:
    return _render_template(request, "user_profile.html")


@router.get("/index.html", include_in_schema=False)
def index_legacy() -> RedirectResponse:
    return RedirectResponse(url="/", status_code=307)


@router.get("/admin.html", include_in_schema=False)
def admin_legacy() -> RedirectResponse:
    return RedirectResponse(url="/admin", status_code=307)


@router.get("/form.html", include_in_schema=False)
def submissions_legacy() -> RedirectResponse:
    return RedirectResponse(url="/submissions", status_code=307)


@router.get("/user_home.html", include_in_schema=False)
def user_home_legacy() -> RedirectResponse:
    return RedirectResponse(url="/user-home", status_code=307)


@router.get("/user_profile.html", include_in_schema=False)
def user_profile_legacy() -> RedirectResponse:
    return RedirectResponse(url="/user-profile", status_code=307)

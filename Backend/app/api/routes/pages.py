from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings

router = APIRouter(tags=["Pages"])

frontend_dir = Path(__file__).resolve().parents[4] / "Frontend"
templates = Jinja2Templates(directory=str(frontend_dir))


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "admin.html")


@router.get("/submissions", response_class=HTMLResponse, include_in_schema=False)
def submissions_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "form.html")


@router.get("/user-home", response_class=HTMLResponse, include_in_schema=False)
def user_home_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "user_home.html",
        {"max_upload_size_mb": settings.max_upload_size_mb},
    )


@router.get("/user-profile", response_class=HTMLResponse, include_in_schema=False)
def user_profile_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "user_profile.html")


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

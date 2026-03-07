from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

from app.config import settings
from app.topics import get_topics_from_snowflake

router = APIRouter(tags=["core"])


@router.get("/", include_in_schema=False)
def root():
    index_path = Path(__file__).resolve().parent.parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return RedirectResponse(url="/docs")


@router.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}


@router.get("/meta/topics")
def meta_topics():
    try:
        topics = get_topics_from_snowflake()
        return {"topics": topics}
    except Exception as exc:
        return {"topics": [], "error": str(exc)}

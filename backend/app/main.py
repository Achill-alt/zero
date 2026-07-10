from contextlib import asynccontextmanager
import os
import logging
from functools import lru_cache
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, init_fts5, SessionLocal
from app.services.search_service import reindex_all_contracts

logger = logging.getLogger("uvicorn")


@lru_cache(maxsize=1)
def _check_weasyprint() -> bool:
    """Check if WeasyPrint is available (requires GTK3/Pango/Cairo system libs).
    Lazily evaluated on first call to avoid ~150ms import penalty at startup.
    """
    try:
        from weasyprint import HTML  # noqa: F401
        return True
    except (OSError, ImportError):
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    init_fts5()
    os.makedirs(settings.upload_dir, exist_ok=True)
    db = SessionLocal()
    try:
        reindex_all_contracts(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom validation error handler — translate Pydantic errors to Chinese
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        loc = error.get("loc", [])
        field = loc[-1] if len(loc) > 0 else ""
        if field in ("body", "__root__"):
            field = ""
        msg = error.get("msg", "")
        err_type = error.get("type", "")

        # Translate common Pydantic error messages to Chinese
        ctx = error.get("ctx", {})
        translation_map = {
            "missing": f"「{field}」为必填项" if field else "缺少必填字段",
            "string_type": f"「{field}」必须是文本",
            "integer_type": f"「{field}」必须是整数",
            "number_type": f"「{field}」必须是数字",
            "string_too_short": f"「{field}」长度不足，至少需要 {ctx.get('min_length', '?')} 个字符",
            "string_too_long": f"「{field}」超出长度限制，最多 {ctx.get('max_length', '?')} 个字符",
            "value_error.any_str.min_length": f"「{field}」长度不足，至少需要 {ctx.get('limit_value', '?')} 个字符",
            "value_error.any_str.max_length": f"「{field}」超出长度限制，最多 {ctx.get('limit_value', '?')} 个字符",
        }
        errors.append(translation_map.get(err_type, msg))
    if not errors:
        errors.append("请求参数校验失败")
    return JSONResponse(
        status_code=422,
        content={"detail": "；".join(errors)},
    )


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "pdf_available": _check_weasyprint(),
    }


from app.api import auth, contracts, approvals, approval_chains, search, templates, users, audit_logs, attachments, notifications, exports  # noqa: E402,F401

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(contracts.router, prefix="/api/v1/contracts", tags=["contracts"])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["approvals"])
app.include_router(approval_chains.router, prefix="/api/v1/approval-chains", tags=["approval-chains"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(audit_logs.router, prefix="/api/v1/audit-logs", tags=["audit-logs"])
app.include_router(attachments.router, prefix="/api/v1", tags=["attachments"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(exports.router, prefix="/api/v1", tags=["exports"])

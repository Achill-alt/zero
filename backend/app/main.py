from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, init_fts5, SessionLocal
from app.services.search_service import reindex_all_contracts


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    init_fts5()
    os.makedirs(settings.upload_dir, exist_ok=True)
    # Reindex existing contracts with jieba segmentation (idempotent)
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


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


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

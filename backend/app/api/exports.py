"""
Export API endpoints — Excel (.xlsx) and PDF contract list download.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contract import Contract
from app.middleware.auth import get_current_user
from app.utils.serializers import contract_to_dict
from app.services.export_service import export_contracts_excel, export_contracts_pdf

router = APIRouter()

MAX_EXPORT_ROWS = 5000


def _fetch_contracts(
    db: Session,
    status: str | None,
    type: str | None,
    search: str | None,
):
    """Return all matching contracts (no pagination), capped at MAX_EXPORT_ROWS."""
    if search:
        # Use FTS search for text queries
        from app.services.search_service import search_contracts as fts_search
        result = fts_search(db, search, page=1, page_size=MAX_EXPORT_ROWS, status=status)
        return [contract_to_dict(c) for c in result["items"]]

    query = db.query(Contract)
    if status:
        query = query.filter(Contract.status == status)
    if type:
        query = query.filter(Contract.contract_type == type)

    items = query.order_by(Contract.created_at.desc()).limit(MAX_EXPORT_ROWS).all()
    return [contract_to_dict(c) for c in items]


@router.get("/contracts/export/excel")
def export_excel(
    status: str | None = Query(None),
    type: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Export filtered contract list as .xlsx file."""
    contracts = _fetch_contracts(db, status, type, search)
    buffer = export_contracts_excel(contracts)
    filename = f"contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/contracts/export/pdf")
def export_pdf(
    status: str | None = Query(None),
    type: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Export filtered contract list as .pdf file."""
    from fastapi import HTTPException

    contracts = _fetch_contracts(db, status, type, search)
    try:
        buffer = export_contracts_pdf(contracts)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    filename = f"contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

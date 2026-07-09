from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.search_service import search_contracts
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("", response_model=dict)
def search(
    q: str = Query(default=""),
    type: str = Query(None),
    status: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = search_contracts(db, q, type, status, date_from, date_to, page, page_size)
    return {"data": result, "message": "success"}

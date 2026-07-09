from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import authenticate_user, create_user
from app.middleware.auth import create_access_token, get_current_user, require_role
from app.schemas.auth import UserResponse
from app.utils.serializers import user_to_dict

router = APIRouter()


@router.post("/login", response_model=dict)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.username, req.password)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": user_to_dict(user),
        },
        "message": "success",
    }


@router.post("/register", response_model=dict)
def register(req: RegisterRequest, db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    user = create_user(db, req)
    return {
        "data": user_to_dict(user),
        "message": "success",
    }


@router.get("/me", response_model=dict)
def me(current_user=Depends(get_current_user)):
    return {
        "data": user_to_dict(current_user),
        "message": "success",
    }

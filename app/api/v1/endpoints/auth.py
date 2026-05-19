from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from app.core.security import create_access_token, verify_password
from app.db.database_connection import get_session
from app.models import User
from sqlmodel import Session, select

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    user_role: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    """
    Placeholder login endpoint. Replace with real credential check / DB lookup.
    """
    user = session.exec(select(User).where(User.email == payload.email)).first()

    if not user or not verify_password(payload.password, user.salt, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")

    token = create_access_token(subject=payload.email)
    return TokenResponse(access_token=token, user_role=user.role)


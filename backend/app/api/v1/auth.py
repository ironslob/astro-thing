from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, EmailStr

from app.api.deps import DbDep, optional_user
from app.core.config import settings
from app.core.security import SESSION_TTL_SECONDS, create_session_token
from app.models.user import User
from app.services import auth as auth_service

router = APIRouter()


class MagicLinkIn(BaseModel):
    email: EmailStr


def _set_session(response: Response, user: User) -> None:
    token = create_session_token(user.id, user.email)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )


@router.post("/auth/magic-link")
def magic_link(payload: MagicLinkIn, db: DbDep) -> dict:
    try:
        auth_service.request_magic_link(db, payload.email)
    except OSError as exc:
        raise HTTPException(
            status_code=503, detail="We couldn't send email just now. Try again shortly."
        ) from exc
    return {"ok": True, "message": "Check your email for a sign-in link."}


@router.get("/auth/verify")
def verify(db: DbDep, response: Response, token: str = Query(min_length=8)) -> dict:
    user = auth_service.consume_magic_token(db, token)
    if user is None:
        raise HTTPException(status_code=400, detail="That sign-in link is invalid or has expired.")
    _set_session(response, user)
    return {"ok": True, "user": {"id": str(user.id), "email": user.email}}


@router.post("/auth/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(settings.session_cookie_name, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: Annotated[User | None, Depends(optional_user)]) -> dict:
    if user is None:
        return {"user": None}
    return {"user": {"id": str(user.id), "email": user.email}}

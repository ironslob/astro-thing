from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.config import settings

SESSION_TTL_SECONDS = 60 * 60 * 24 * 30
MAGIC_TTL_SECONDS = 60 * 15


def _sign(payload: str) -> str:
    digest = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{digest}"


def _verify(token: str) -> str | None:
    if "." not in token:
        return None
    payload, digest = token.rsplit(".", 1)
    expected = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, expected):
        return None
    return payload


def create_session_token(user_id: UUID, email: str) -> str:
    body = json.dumps(
        {
            "uid": str(user_id),
            "email": email,
            "exp": int((datetime.now(UTC) + timedelta(seconds=SESSION_TTL_SECONDS)).timestamp()),
        },
        separators=(",", ":"),
    )
    return _sign(body)


def parse_session_token(token: str) -> dict[str, Any] | None:
    payload = _verify(token)
    if not payload:
        return None
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if int(data.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
        return None
    return data


def new_magic_token() -> str:
    return secrets.token_urlsafe(32)

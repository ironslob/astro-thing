from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis import get_redis
from app.core.security import MAGIC_TTL_SECONDS, new_magic_token
from app.models.user import User

logger = logging.getLogger(__name__)


def request_magic_link(db: Session, email: str) -> None:
    token = new_magic_token()
    redis = get_redis()
    redis.setex(f"magic:{token}", MAGIC_TTL_SECONDS, email.lower())
    verify_url = f"{settings.frontend_base_url.rstrip('/')}/auth/verify?token={token}"
    _send_email(email, verify_url)
    logger.info("magic_link queued")


def consume_magic_token(db: Session, token: str) -> User | None:
    redis = get_redis()
    email = redis.get(f"magic:{token}")
    if not email:
        return None
    redis.delete(f"magic:{token}")
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_user(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def _send_email(to_addr: str, verify_url: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Your Astro Window sign-in link"
    msg["From"] = settings.smtp_from
    msg["To"] = to_addr
    msg.set_content(
        "Sign in to Astro Window with this link (valid for 15 minutes):\n\n"
        f"{verify_url}\n\n"
        "If you didn't request this, you can ignore the email.\n"
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.send_message(msg)
    except OSError:
        logger.exception("smtp_send_failed")
        raise

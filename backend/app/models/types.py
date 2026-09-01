from __future__ import annotations

from sqlalchemy import JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

UUID_PK = Uuid(as_uuid=True).with_variant(PGUUID(as_uuid=True), "postgresql")
JSON_DOC = JSON().with_variant(JSONB, "postgresql")

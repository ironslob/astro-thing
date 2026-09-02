"""Add images JSON list to deep-sky objects.

Revision ID: 003_dso_images
Revises: 002_geocoding_search
Create Date: 2026-09-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_dso_images"
down_revision: Union[str, None] = "002_geocoding_search"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    json_type = sa.JSON() if bind.dialect.name != "postgresql" else postgresql.JSONB()
    op.add_column(
        "deep_sky_objects",
        sa.Column("images", json_type, nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    op.drop_column("deep_sky_objects", "images")

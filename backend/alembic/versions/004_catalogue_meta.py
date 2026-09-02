"""Store the digest of the last applied catalogue bundle.

Revision ID: 004_catalogue_meta
Revises: 003_dso_images
Create Date: 2026-09-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_catalogue_meta"
down_revision: Union[str, None] = "003_dso_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "catalogue_meta",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("catalogue_meta")

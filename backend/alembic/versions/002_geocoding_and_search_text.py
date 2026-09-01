"""Drop bundled UK places; add catalogue search_text.

Revision ID: 002_geocoding_search
Revises: 001_initial
Create Date: 2026-09-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_geocoding_search"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_uk_places_place_type", table_name="uk_places")
    op.drop_index("ix_uk_places_search_name", table_name="uk_places")
    op.drop_index("ix_uk_places_name", table_name="uk_places")
    op.drop_table("uk_places")

    op.add_column(
        "deep_sky_objects",
        sa.Column("search_text", sa.String(length=1024), nullable=False, server_default=""),
    )
    op.create_index("ix_deep_sky_objects_search_text", "deep_sky_objects", ["search_text"])
    op.create_index("ix_deep_sky_objects_beginner_prior", "deep_sky_objects", ["beginner_prior"])


def downgrade() -> None:
    op.drop_index("ix_deep_sky_objects_beginner_prior", table_name="deep_sky_objects")
    op.drop_index("ix_deep_sky_objects_search_text", table_name="deep_sky_objects")
    op.drop_column("deep_sky_objects", "search_text")

    op.create_table(
        "uk_places",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("place_type", sa.String(length=32), nullable=False),
        sa.Column("population", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("search_name", sa.String(length=128), nullable=False),
    )
    op.create_index("ix_uk_places_name", "uk_places", ["name"])
    op.create_index("ix_uk_places_search_name", "uk_places", ["search_name"])
    op.create_index("ix_uk_places_place_type", "uk_places", ["place_type"])

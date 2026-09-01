"""Initial schema.

Revision ID: 001_initial
Revises:
Create Date: 2026-09-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    uuid_type = sa.Uuid() if not is_pg else postgresql.UUID(as_uuid=True)
    json_type = sa.JSON() if not is_pg else postgresql.JSONB()

    op.create_table(
        "users",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "saved_locations",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "name", name="uq_saved_location_user_name"),
    )
    op.create_index("ix_saved_locations_user_id", "saved_locations", ["user_id"])

    op.create_table(
        "weather_forecast_cache",
        sa.Column("cell_key", sa.String(length=32), primary_key=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", json_type, nullable=False),
    )
    op.create_index("ix_weather_forecast_cache_fetched_at", "weather_forecast_cache", ["fetched_at"])

    op.create_table(
        "observation_assessments",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column(
            "saved_location_id",
            uuid_type,
            sa.ForeignKey("saved_locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assessment_hash", sa.String(length=64), nullable=False),
        sa.Column("assessment", json_type, nullable=False),
    )
    op.create_index("ix_observation_assessments_saved_location_id", "observation_assessments", ["saved_location_id"])
    op.create_index("ix_observation_assessments_generated_at", "observation_assessments", ["generated_at"])

    op.create_table(
        "deep_sky_objects",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("primary_name", sa.String(length=128), nullable=False),
        sa.Column("common_name", sa.String(length=128), nullable=True),
        sa.Column("catalogue_ids", json_type, nullable=False),
        sa.Column("object_type", sa.String(length=64), nullable=False),
        sa.Column("friendly_type", sa.String(length=64), nullable=False),
        sa.Column("ra", sa.Float(), nullable=False),
        sa.Column("dec", sa.Float(), nullable=False),
        sa.Column("magnitude", sa.Float(), nullable=True),
        sa.Column("angular_size", sa.Float(), nullable=True),
        sa.Column("beginner_prior", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("metadata", json_type, nullable=False),
    )
    op.create_index("ix_deep_sky_objects_primary_name", "deep_sky_objects", ["primary_name"])
    op.create_index("ix_deep_sky_objects_object_type", "deep_sky_objects", ["object_type"])

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


def downgrade() -> None:
    op.drop_table("uk_places")
    op.drop_table("deep_sky_objects")
    op.drop_table("observation_assessments")
    op.drop_table("weather_forecast_cache")
    op.drop_table("saved_locations")
    op.drop_table("users")

"""dados de bem-estar da garmin

Revision ID: 9b2e4d1a6c58
Revises: 3f1a9c2b7d40
Create Date: 2026-11-25 01:10:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9b2e4d1a6c58"
down_revision: str | Sequence[str] | None = "3f1a9c2b7d40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "garmin_wellness",
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column(
            "fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("source", "day"),
    )


def downgrade() -> None:
    op.drop_table("garmin_wellness")

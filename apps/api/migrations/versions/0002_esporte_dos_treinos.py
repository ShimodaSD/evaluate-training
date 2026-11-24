"""esporte dos treinos planejados e atividades, potência média

Revision ID: 3f1a9c2b7d40
Revises: 7c784e2845fe
Create Date: 2026-11-24 23:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3f1a9c2b7d40"
down_revision: str | Sequence[str] | None = "7c784e2845fe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("activities", sa.Column("avg_power_w", sa.Float(), nullable=True))
    op.add_column(
        "planned_workouts",
        sa.Column("sport", sa.String(length=10), server_default="run", nullable=False),
    )
    # Mesmas regras de app.services.activities.normalize_sport para os dados já salvos.
    op.execute(
        """
        UPDATE activities SET sport = CASE
            WHEN sport IS NULL THEN 'run'
            WHEN lower(sport) LIKE '%swim%' THEN 'swim'
            WHEN lower(sport) LIKE '%cycl%' OR lower(sport) LIKE '%bik%'
                OR lower(sport) LIKE '%ride%' THEN 'bike'
            WHEN lower(sport) LIKE '%run%' THEN 'run'
            ELSE 'other'
        END
        """
    )
    with op.batch_alter_table("activities") as batch:
        batch.alter_column(
            "sport", existing_type=sa.String(length=50), server_default="run", nullable=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("activities") as batch:
        batch.alter_column(
            "sport", existing_type=sa.String(length=50), server_default=None, nullable=True
        )
    op.drop_column("planned_workouts", "sport")
    op.drop_column("activities", "avg_power_w")

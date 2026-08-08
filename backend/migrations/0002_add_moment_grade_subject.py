"""
Add grade and subject columns to learning_moments.

Part of Persistent Visual Memory — lets moments carry textbook context
(grade, subject) used by the /moments API and semantic search.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_moment_grade_subject"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("learning_moments", sa.Column("grade", sa.Integer(), nullable=True))
    op.add_column("learning_moments", sa.Column("subject", sa.String(128), nullable=True))


def downgrade() -> None:
    op.drop_column("learning_moments", "subject")
    op.drop_column("learning_moments", "grade")

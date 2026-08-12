"""baseline: ai_sessions table (SessionEngine state persistence)

Revision ID: 0001
Revises:
Create Date: 2026-08-12

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_sessions",
        sa.Column("session_id", sa.String(), primary_key=True),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ai_sessions")

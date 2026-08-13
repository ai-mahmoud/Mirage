"""add user_consents table

Legal/compliance groundwork (Phase 7 of the production-readiness
roadmap — see /home/dr4who/.claude/plans/tidy-spinning-babbage.md).

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-13

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_consents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("document", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_consents")

"""add Organization + User tables, nullable org_id on sessions

Multi-tenancy groundwork (Phase 1 of the production-readiness roadmap —
see /home/dr4who/.claude/plans/tidy-spinning-babbage.md). Schema only:
org_id is nullable and unenforced here — auth (Phase 2) is what actually
scopes queries by it and makes it required.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-12

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("org_id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("plan_tier", sa.String(), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("org_id", sa.String(), sa.ForeignKey("organizations.org_id"), nullable=False),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.add_column("sessions", sa.Column("org_id", sa.String(), sa.ForeignKey("organizations.org_id"), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "org_id")
    op.drop_table("users")
    op.drop_table("organizations")

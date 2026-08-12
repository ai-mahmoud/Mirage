"""baseline: sessions + evidence tables (matches the pre-Postgres schema)

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
        "sessions",
        sa.Column("session_id", sa.String(), primary_key=True),
        sa.Column("ai_session_id", sa.String(), nullable=True),
        sa.Column("candidate_name", sa.String(), nullable=False),
        sa.Column("interview_type", sa.String(), nullable=False),
        sa.Column("position", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("observer_name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("trust_overall", sa.Float(), nullable=False, server_default="75.0"),
        sa.Column("trust_dimensions", sa.JSON(), nullable=False),
        sa.Column("evidence_confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("recommendation_confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("recommendation_status", sa.String(), nullable=False, server_default="evidence_insufficient"),
        sa.Column("recommendation_label", sa.String(), nullable=False, server_default="Insufficient Evidence"),
        sa.Column("current_risk", sa.String(), nullable=False, server_default="insufficient"),
        sa.Column("executive_summary", sa.String(), nullable=True),
    )
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("ai_evidence_id", sa.String(), nullable=False, unique=True),
        sa.Column("session_id", sa.String(), sa.ForeignKey("sessions.session_id"), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("polarity", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("supporting_signals", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evidence")
    op.drop_table("sessions")

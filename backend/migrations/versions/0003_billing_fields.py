"""add stripe_customer_id + subscription_status to organizations

Billing groundwork (Phase 6 of the production-readiness roadmap — see
/home/dr4who/.claude/plans/tidy-spinning-babbage.md). plan_tier already
exists from Phase 1's baseline; this adds what checkout/webhook handling
(billing_service.py) needs to track a real Stripe subscription.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-13

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("stripe_customer_id", sa.String(), nullable=True))
    op.create_unique_constraint(
        "uq_organizations_stripe_customer_id", "organizations", ["stripe_customer_id"]
    )
    op.add_column("organizations", sa.Column("subscription_status", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("organizations", "subscription_status")
    op.drop_constraint("uq_organizations_stripe_customer_id", "organizations", type_="unique")
    op.drop_column("organizations", "stripe_customer_id")

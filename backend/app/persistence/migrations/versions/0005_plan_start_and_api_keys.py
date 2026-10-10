"""Per-quarter plan start date and API keys entered in Settings.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("quarters", sa.Column("plan_start", sa.Date(), nullable=True))
    op.add_column("app_settings", sa.Column("openai_api_key", sa.String(500), nullable=True))
    op.add_column("app_settings", sa.Column("gemini_api_key", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("app_settings", "gemini_api_key")
    op.drop_column("app_settings", "openai_api_key")
    op.drop_column("quarters", "plan_start")

"""add ai_analysis to alert_records

Revision ID: 2733fdbc9397
Revises: 7767ffc9a3bb
Create Date: 2026-08-09 19:18:46.628492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2733fdbc9397'
down_revision: Union[str, None] = '7767ffc9a3bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('alert_records', sa.Column('ai_analysis', sa.Text(), nullable=True, comment='AI根因分析结果'))


def downgrade() -> None:
    op.drop_column('alert_records', 'ai_analysis')

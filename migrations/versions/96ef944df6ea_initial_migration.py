"""Initial migration

Revision ID: 96ef944df6ea
Revises:
Create Date: 2026-03-05 10:56:30.410184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96ef944df6ea'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'automation_templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('source_platform', sa.String(), nullable=False),
        sa.Column('trigger_app', sa.String(), nullable=False),
        sa.Column('action_apps', sa.JSON(), nullable=False),
        sa.Column('complexity_score', sa.Integer(), nullable=True),
        sa.Column('maintenance_level', sa.String(), nullable=True),
        sa.Column('monthly_opex', sa.Float(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )


def downgrade() -> None:
    op.drop_table('automation_templates')

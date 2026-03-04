"""add metrics columns

Revision ID: add_metrics_cols
Revises:
Create Date: 2024-03-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_metrics_cols'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('automation_templates', sa.Column('trigger_app', sa.String(), nullable=True))
    op.add_column('automation_templates', sa.Column('action_apps', sa.JSON(), nullable=True))
    op.add_column('automation_templates', sa.Column('complexity_score', sa.Integer(), nullable=True))
    op.add_column('automation_templates', sa.Column('maintenance_level', sa.String(), nullable=True))
    op.add_column('automation_templates', sa.Column('monthly_opex', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('automation_templates', 'monthly_opex')
    op.drop_column('automation_templates', 'maintenance_level')
    op.drop_column('automation_templates', 'complexity_score')
    op.drop_column('automation_templates', 'action_apps')
    op.drop_column('automation_templates', 'trigger_app')

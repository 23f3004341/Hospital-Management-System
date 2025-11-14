"""Clean schema after compare_type fix

Revision ID: f7e2b15387ba
Revises: be00aabfef2b
Create Date: 2025-11-08 22:47:58.417342

"""
from alembic import op
import sqlalchemy as sa

revision = 'f7e2b15387ba'
down_revision = 'be00aabfef2b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users_account', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_blacklisted', sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table('users_account', schema=None) as batch_op:
        batch_op.drop_column('is_blacklisted')

"""Add patient extra fields

Revision ID: e2931fce3bb3
Revises: f7e2b15387ba
Create Date: 2025-11-09 08:38:29.921509

"""
from alembic import op
import sqlalchemy as sa

revision = 'e2931fce3bb3'
down_revision = 'f7e2b15387ba'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users_account', schema=None) as batch_op:
        batch_op.add_column(sa.Column('height', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('weight', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('marital_status', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('medications', sa.String(length=5), nullable=True))
        batch_op.add_column(sa.Column('emergency_name', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('emergency_relation', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('emergency_contact', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('pincode', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('city', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('state', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('country', sa.String(length=80), nullable=True))

def downgrade():
    with op.batch_alter_table('users_account', schema=None) as batch_op:
        batch_op.drop_column('country')
        batch_op.drop_column('state')
        batch_op.drop_column('city')
        batch_op.drop_column('pincode')
        batch_op.drop_column('emergency_contact')
        batch_op.drop_column('emergency_relation')
        batch_op.drop_column('emergency_name')
        batch_op.drop_column('medications')
        batch_op.drop_column('marital_status')
        batch_op.drop_column('weight')
        batch_op.drop_column('height')
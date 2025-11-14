"""Add name fields and other schema changes

Revision ID: be00aabfef2b
Revises: 
Create Date: 2025-11-08 00:43:19.916302

"""
from alembic import op
import sqlalchemy as sa


revision = 'be00aabfef2b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users_account', schema=None) as batch_op:
        batch_op.add_column(sa.Column('first_name', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('middle_name', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('last_name', sa.String(length=80), nullable=True))
        batch_op.alter_column('password',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=256),
               existing_nullable=False)


def downgrade():
    with op.batch_alter_table('users_account', schema=None) as batch_op:
        batch_op.alter_column('password',
               existing_type=sa.String(length=256),
               type_=sa.VARCHAR(length=100),
               existing_nullable=False)
        batch_op.drop_column('last_name')
        batch_op.drop_column('middle_name')
        batch_op.drop_column('first_name')


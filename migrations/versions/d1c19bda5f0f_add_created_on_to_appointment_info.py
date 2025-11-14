"""add created_on to appointment_info

Revision ID: d1c19bda5f0f
Revises: b525cb25a73d
Create Date: 2025-11-12 05:46:05.625809

"""
from alembic import op
import sqlalchemy as sa

revision = 'd1c19bda5f0f'
down_revision = 'b525cb25a73d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('appointment_info', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('created_on', sa.DateTime(), nullable=True)
        )

    op.execute(
        "UPDATE appointment_info SET created_on = '2025-01-01 00:00:00' WHERE created_on IS NULL"
    )
    with op.batch_alter_table('appointment_info', schema=None) as batch_op:
        batch_op.alter_column(
            'created_on',
            existing_type=sa.DateTime(),
            nullable=False
        )


def downgrade():
    with op.batch_alter_table('appointment_info', schema=None) as batch_op:
        batch_op.drop_column('created_on')

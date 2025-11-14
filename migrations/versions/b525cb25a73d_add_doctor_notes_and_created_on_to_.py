"""add doctor_notes and created_on to treatment_info

Revision ID: b525cb25a73d
Revises: e2931fce3bb3
Create Date: 2025-11-12 05:39:42.751223

"""
from alembic import op
import sqlalchemy as sa

revision = 'b525cb25a73d'
down_revision = 'e2931fce3bb3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('appointment_info', schema=None) as batch_op:
        batch_op.alter_column('appointment_date',
               existing_type=sa.VARCHAR(length=25),
               type_=sa.Date(),
               nullable=False)

    with op.batch_alter_table('treatment_info', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_on', sa.DateTime(), nullable=True))
        batch_op.alter_column('treatment_name',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=150),
               existing_nullable=False)
        batch_op.alter_column('diagnosis',
               existing_type=sa.TEXT(),
               nullable=True)
        batch_op.alter_column('patient_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('doctor_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.drop_column('date')
        batch_op.drop_column('notes')


def downgrade():
    with op.batch_alter_table('treatment_info', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notes', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('date', sa.DATETIME(), nullable=True))
        batch_op.alter_column('doctor_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('patient_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('diagnosis',
               existing_type=sa.TEXT(),
               nullable=False)
        batch_op.alter_column('treatment_name',
               existing_type=sa.String(length=150),
               type_=sa.VARCHAR(length=200),
               existing_nullable=False)
        batch_op.drop_column('created_on')

    with op.batch_alter_table('appointment_info', schema=None) as batch_op:
        batch_op.alter_column('appointment_date',
               existing_type=sa.Date(),
               type_=sa.VARCHAR(length=25),
               nullable=True)


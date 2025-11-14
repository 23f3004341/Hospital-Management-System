"""Add address_line2 column only"""

from alembic import op
import sqlalchemy as sa

revision = '1e9ed00b2ad6'
down_revision = 'd1c19bda5f0f'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users_account', sa.Column('address_line2', sa.String(length=255)))

def downgrade():
    op.drop_column('users_account', 'address_line2')

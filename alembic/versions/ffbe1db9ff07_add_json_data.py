"""Add json data

Revision ID: ffbe1db9ff07
Revises: 7bac5d541671
Create Date: 2017-10-13 00:12:28.055946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffbe1db9ff07'
down_revision = '7bac5d541671'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sessions', sa.Column('data', sa.String))


def downgrade():
    op.drop_column('data')

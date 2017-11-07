"""create first table

Revision ID: 7bac5d541671
Revises: 
Create Date: 2017-10-11 00:07:17.450666

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7bac5d541671'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sessions',
        sa.Column('user_id', sa.Integer, primary_key=True),
        sa.Column('update_id', sa.Integer),
        sa.Column('chat_id', sa.Integer),
        sa.Column('user_name', sa.String(20)),
        sa.Column('first_name', sa.String(20)),
        sa.Column('last_name', sa.String(30))
    )



    #pass


def downgrade():
    op.drop_table('sessions')
    #pass

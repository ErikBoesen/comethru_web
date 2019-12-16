"""add address

Revision ID: 5c6026965ef1
Revises: fb4e8e2b7a16
Create Date: 2019-12-16 16:45:41.853008

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c6026965ef1'
down_revision = 'fb4e8e2b7a16'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('address', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'address')
    # ### end Alembic commands ###

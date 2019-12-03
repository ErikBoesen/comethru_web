"""empty message

Revision ID: 2beed43a5d46
Revises: 4bb64fd6de2c
Create Date: 2019-12-02 23:35:04.868938

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2beed43a5d46'
down_revision = '4bb64fd6de2c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('end_time', sa.DateTime(), nullable=True))
    op.add_column('events', sa.Column('ended', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'ended')
    op.drop_column('events', 'end_time')
    # ### end Alembic commands ###

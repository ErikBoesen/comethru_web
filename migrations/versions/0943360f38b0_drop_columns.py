"""drop columns

Revision ID: 0943360f38b0
Revises: 5b9405ee499c
Create Date: 2019-12-18 20:14:11.400011

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0943360f38b0'
down_revision = '5b9405ee499c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'avatar')
    op.drop_column('users', 'lat')
    op.drop_column('users', 'lng')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('lng', sa.FLOAT(), nullable=True))
    op.add_column('users', sa.Column('lat', sa.FLOAT(), nullable=True))
    op.add_column('users', sa.Column('avatar', sa.VARCHAR(length=120), nullable=True))
    # ### end Alembic commands ###

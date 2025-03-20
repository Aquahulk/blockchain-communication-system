"""Add chain column to NFT table

Revision ID: bc84e647a4bb
Revises: 003874134b0c
Create Date: 2025-03-20 00:20:35.216940

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc84e647a4bb'
down_revision = '003874134b0c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('NFT', schema=None) as batch_op:
        batch_op.add_column(sa.Column('chain', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('NFT', schema=None) as batch_op:
        batch_op.drop_column('chain')

    # ### end Alembic commands ###

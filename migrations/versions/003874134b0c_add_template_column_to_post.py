"""Add template column to Post

Revision ID: 003874134b0c
Revises: 918b85959e22
Create Date: 2025-03-19 00:10:11.706764

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003874134b0c'
down_revision = '918b85959e22'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.alter_column('category',
               existing_type=sa.VARCHAR(length=50),
               nullable=True,
               existing_server_default=sa.text("'general'"))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.alter_column('category',
               existing_type=sa.VARCHAR(length=50),
               nullable=False,
               existing_server_default=sa.text("'general'"))

    # ### end Alembic commands ###

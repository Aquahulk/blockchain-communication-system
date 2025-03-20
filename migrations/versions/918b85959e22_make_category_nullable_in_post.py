"""Make category nullable in Post

Revision ID: 918b85959e22
Revises: 1e03ec0af094
Create Date: 2025-03-19 00:09:07.752255

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '918b85959e22'
down_revision = '1e03ec0af094'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.alter_column('category',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.alter_column('category',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)

    # ### end Alembic commands ###

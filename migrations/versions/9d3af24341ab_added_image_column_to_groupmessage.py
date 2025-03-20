"""Added image column to GroupMessage

Revision ID: 9d3af24341ab
Revises: 
Create Date: 2025-02-13 18:45:29.420647

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d3af24341ab'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('group_message', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(length=256), nullable=True))
        batch_op.alter_column('content',
               existing_type=sa.TEXT(),
               nullable=True)

    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(length=256), nullable=True))
        batch_op.alter_column('sender',
               existing_type=sa.VARCHAR(length=42),
               type_=sa.String(length=128),
               existing_nullable=False)
        batch_op.alter_column('receiver',
               existing_type=sa.VARCHAR(length=42),
               type_=sa.String(length=128),
               existing_nullable=False)
        batch_op.alter_column('content',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.Text(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.alter_column('content',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=500),
               nullable=False)
        batch_op.alter_column('receiver',
               existing_type=sa.String(length=128),
               type_=sa.VARCHAR(length=42),
               existing_nullable=False)
        batch_op.alter_column('sender',
               existing_type=sa.String(length=128),
               type_=sa.VARCHAR(length=42),
               existing_nullable=False)
        batch_op.drop_column('image')

    with op.batch_alter_table('group_message', schema=None) as batch_op:
        batch_op.alter_column('content',
               existing_type=sa.TEXT(),
               nullable=False)
        batch_op.drop_column('image')

    # ### end Alembic commands ###

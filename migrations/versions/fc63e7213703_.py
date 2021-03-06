"""empty message

Revision ID: fc63e7213703
Revises: 68cc22b6a734
Create Date: 2019-02-26 14:30:49.596404

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'fc63e7213703'
down_revision = '68cc22b6a734'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('missions', sa.Column('is_terminated', sa.Boolean(), nullable=True))
    op.drop_column('missions', 'is_terminate')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('missions', sa.Column('is_terminate', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.drop_column('missions', 'is_terminated')
    # ### end Alembic commands ###

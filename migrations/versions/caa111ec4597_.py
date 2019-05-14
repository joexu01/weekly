"""empty message

Revision ID: caa111ec4597
Revises: b2ee1137731d
Create Date: 2019-05-11 10:37:19.199086

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'caa111ec4597'
down_revision = 'b2ee1137731d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('comments', 'body_html')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comments', sa.Column('body_html', mysql.TEXT(), nullable=True))
    # ### end Alembic commands ###
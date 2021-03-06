"""start

Revision ID: 201d2190f570
Revises: None
Create Date: 2013-12-30 01:39:08.646513

"""

# revision identifiers, used by Alembic.
revision = '201d2190f570'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('device',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('devicetoken', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('devicetoken')
    )
    op.create_table('app',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('association',
    sa.Column('app_id', sa.Integer(), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['app_id'], ['app.id'], ),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], )
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('association')
    op.drop_table('app')
    op.drop_table('device')
    ### end Alembic commands ###

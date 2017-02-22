""" Add bambukupdatelogs table

Revision ID: 2b194f6c44e1
Revises: start_bambuk
Create Date: 2016-07-25 17:08:30.135729

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b194f6c44e1'
down_revision = 'start_bambuk'


def upgrade():
    op.create_table(
        'bambukupdatelogs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('obj_id', sa.String(length=36), nullable=True),
        sa.Column('obj_type', sa.String(length=36), nullable=True),
        sa.Column('action_type', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('nb_retry', sa.SmallInteger, default=0, nullable=False),
        sa.Column('last_retry', sa.DateTime, nullable=True),
        sa.Column('next_retry', sa.DateTime, nullable=True),
        sa.Column('extra_id', sa.String(length=36), nullable=True),
        sa.Column('extra_data', sa.String(length=255), nullable=True),
    )

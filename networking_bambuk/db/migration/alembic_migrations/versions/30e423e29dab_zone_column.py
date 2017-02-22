""" Add zone column

Revision ID: 30e423e29dab
Revises: 2b194f6c44e1
Create Date: 2016-08-07 14:43:53.088971

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30e423e29dab'
down_revision = '2b194f6c44e1'


def upgrade():
    op.add_column('ml2_vxlan_endpoints',
                  sa.Column('zone',
                            sa.String(length=50),
                            nullable=True))
    op.add_column('ml2_geneve_endpoints',
                  sa.Column('zone',
                            sa.String(length=50),
                            nullable=True))
    op.add_column('ml2_gre_endpoints',
                  sa.Column('zone',
                            sa.String(length=50),
                            nullable=True))

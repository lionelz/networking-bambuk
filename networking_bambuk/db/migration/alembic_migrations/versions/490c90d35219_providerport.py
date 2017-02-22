
""" Add providerports table
Revision ID: 490c90d35219
Revises: 30e423e29dab
Create Date: 2017-01-31 08:54:13.511188
"""

# revision identifiers, used by Alembic.
revision = '490c90d35219'
down_revision = '30e423e29dab'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'providerports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('provider_ip', sa.String(length=64), nullable=False),
        sa.Column('provider_mngt_ip', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id'))

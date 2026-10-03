"""Merge multiple heads

Revision ID: ddd131aba767
Revises: 1655c9aa6d0c, cfc5b5ed3e23
Create Date: 2026-10-03 14:37:01.744193

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ddd131aba767'
down_revision = ('1655c9aa6d0c', 'cfc5b5ed3e23')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

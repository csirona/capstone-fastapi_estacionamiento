"""Add last_connection column

Revision ID: 24d332463407
Revises: 520efca4cee3
Create Date: 2023-10-27 03:19:41.415049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24d332463407'
down_revision: Union[str, None] = '520efca4cee3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add the "last_connection" column to the "users" table
    op.add_column('users', sa.Column('last_connection', sa.DateTime, nullable=True))


def downgrade() -> None:
    pass

"""Add last_connection column

Revision ID: 520efca4cee3
Revises: 162c0d40f8be
Create Date: 2023-10-27 03:18:59.413659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '520efca4cee3'
down_revision: Union[str, None] = '162c0d40f8be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add the "last_connection" column to the "users" table
    op.add_column('users', sa.Column('last_connection', sa.DateTime, nullable=True))


def downgrade() -> None:
    pass

"""Add parking_movements table22

Revision ID: d544afb53652
Revises: 80a387d7910d
Create Date: 2023-10-29 04:11:13.223656

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd544afb53652'
down_revision: Union[str, None] = '80a387d7910d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

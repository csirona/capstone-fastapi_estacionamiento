"""Add parking_movements table

Revision ID: 67d34564f6f8
Revises: 2aebaff14c3c
Create Date: 2023-10-29 03:58:52.009947

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67d34564f6f8'
down_revision: Union[str, None] = '2aebaff14c3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

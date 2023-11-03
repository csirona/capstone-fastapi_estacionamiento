"""Change data type of id column

Revision ID: bd92ef5fca72
Revises: d544afb53652
Create Date: 2023-11-01 05:07:06.153748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd92ef5fca72'
down_revision: Union[str, None] = 'd544afb53652'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

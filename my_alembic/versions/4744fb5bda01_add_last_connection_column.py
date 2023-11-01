"""Add last_connection column

Revision ID: 4744fb5bda01
Revises: 24d332463407
Create Date: 2023-10-27 03:25:04.369180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4744fb5bda01'
down_revision: Union[str, None] = '24d332463407'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('users', sa.Column('last_connection', sa.DateTime, nullable=True))

def downgrade() -> None:
    pass

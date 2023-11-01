"""add_user_role

Revision ID: 2aebaff14c3c
Revises: 4744fb5bda01
Create Date: 2023-10-28 16:19:30.326327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2aebaff14c3c'
down_revision: Union[str, None] = '4744fb5bda01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column('users', sa.Column('role', sa.String, default='user'))

def downgrade():
    op.drop_column('users', 'role')

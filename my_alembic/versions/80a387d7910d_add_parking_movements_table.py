"""Add parking_movements table

Revision ID: 80a387d7910d
Revises: 67d34564f6f8
Create Date: 2023-10-29 03:59:49.767367

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80a387d7910d'
down_revision: Union[str, None] = '67d34564f6f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.create_table(
        'parking_movements',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('entry_time', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('exit_time', sa.DateTime),
        sa.Column('parking_spot_id', sa.Integer, sa.ForeignKey('parking_spots.id')),
        sa.Column('total_cost', sa.Float),
        sa.Column('vehicle_type', sa.String),
        sa.Column('license_plate', sa.String),
        sa.Column('notes', sa.String),
    )

def downgrade():
    op.drop_table('parking_movements')


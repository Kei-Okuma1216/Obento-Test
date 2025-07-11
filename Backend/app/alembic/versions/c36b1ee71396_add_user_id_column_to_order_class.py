"""Add user_id column to Order Class

Revision ID: c36b1ee71396
Revises: fcf39177b19a
Create Date: 2025-06-09 11:04:06.085857

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c36b1ee71396'
down_revision: Union[str, None] = 'fcf39177b19a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Orders', sa.Column('user_id', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Orders', 'user_id')
    # ### end Alembic commands ###

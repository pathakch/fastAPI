"""create user address column

Revision ID: 602eb67745cd
Revises: ff3b6d8221c5
Create Date: 2025-10-10 09:27:54.321642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '602eb67745cd'
down_revision: Union[str, Sequence[str], None] = 'ff3b6d8221c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('address', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'address')

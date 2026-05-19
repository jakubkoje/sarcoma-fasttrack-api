"""Use just doctor not practitioner

Revision ID: 30cfc686db50
Revises: 
Create Date: 2025-11-30 11:04:00.277385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '30cfc686db50'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Minimal add of doctor_id column; mapping handled in later migration.
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS doctor_id INTEGER")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reports', 'doctor_id')

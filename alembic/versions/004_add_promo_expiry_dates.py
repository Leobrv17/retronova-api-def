"""Add expiry dates to promo codes

Revision ID: 004
Revises: 003
Create Date: 2025-07-08 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajouter les colonnes de dates de péremption
    op.add_column('promo_codes', sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True))
    op.add_column('promo_codes', sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('promo_codes', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    # Supprimer les colonnes en cas de rollback
    op.drop_column('promo_codes', 'is_active')
    op.drop_column('promo_codes', 'valid_until')
    op.drop_column('promo_codes', 'valid_from')
# alembic/versions/003_make_player2_optional.py
"""Make player2_id optional in scores

Revision ID: 003
Revises: 002
Create Date: 2025-07-01 16:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rendre player2_id optionnel (nullable)
    op.alter_column('scores', 'player2_id',
                    existing_type=sa.INTEGER(),
                    nullable=True,
                    existing_nullable=False)

    # Rendre score_j2 optionnel (nullable)
    op.alter_column('scores', 'score_j2',
                    existing_type=sa.INTEGER(),
                    nullable=True,
                    existing_nullable=False)


def downgrade() -> None:
    # ATTENTION: Cette migration peut échouer s'il y a des scores avec player2_id NULL
    # Il faudrait d'abord supprimer ou migrer ces scores

    # Supprimer les scores avec player2_id NULL avant de remettre la contrainte
    op.execute("DELETE FROM scores WHERE player2_id IS NULL")

    # Remettre les contraintes NOT NULL
    op.alter_column('scores', 'score_j2',
                    existing_type=sa.INTEGER(),
                    nullable=False,
                    existing_nullable=True)

    op.alter_column('scores', 'player2_id',
                    existing_type=sa.INTEGER(),
                    nullable=False,
                    existing_nullable=True)
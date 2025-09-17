"""add indexes to molecules table

Revision ID: 503e994157a8
Revises: 4d46842d7666
Create Date: 2025-10-13 14:28:44.512581

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "503e994157a8"
down_revision: Union[str, Sequence[str], None] = "4d46842d7666"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  """Upgrade schema."""
  op.create_index(
    "ix_molecules_h_bond_donors", "molecules", ["h_bond_donors"], unique=False
  )
  op.create_index(
    "ix_molecules_h_bond_acceptors", "molecules", ["h_bond_acceptors"], unique=False
  )
  op.create_index(
    "ix_molecules_rotatable_bonds", "molecules", ["rotatable_bonds"], unique=False
  )
  op.create_index(
    "ix_molecules_chemical_formula", "molecules", ["chemical_formula"], unique=False
  )


def downgrade() -> None:
  """Downgrade schema."""
  op.drop_index("ix_molecules_chemical_formula", table_name="molecules")
  op.drop_index("ix_molecules_rotatable_bonds", table_name="molecules")
  op.drop_index("ix_molecules_h_bond_acceptors", table_name="molecules")
  op.drop_index("ix_molecules_h_bond_donors", table_name="molecules")

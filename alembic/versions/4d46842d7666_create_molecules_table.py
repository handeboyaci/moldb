"""Create molecules table

Revision ID: 4d46842d7666
Revises:
Create Date: 2025-10-08 02:37:02.229830

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from src.app.database_types import RDKitBfpType, RDKitMolType

# revision identifiers, used by Alembic.
revision: str = "4d46842d7666"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  """Upgrade schema."""
  op.create_table(
    "molecules",
    sa.Column("id", sa.UUID(), nullable=False),
    sa.Column("inchi", sa.String(), nullable=False),
    sa.Column("inchikey", sa.String(length=27), nullable=False),
    sa.Column("smiles", sa.String(), nullable=False),
    sa.Column("mol", RDKitMolType(), nullable=True),
    sa.Column("molecular_weight", sa.REAL(), nullable=False),
    sa.Column("chemical_formula", sa.String(length=255), nullable=False),
    sa.Column("logp", sa.REAL(), nullable=False),
    sa.Column("tpsa", sa.REAL(), nullable=False),
    sa.Column("h_bond_donors", sa.Integer(), nullable=False),
    sa.Column("h_bond_acceptors", sa.Integer(), nullable=False),
    sa.Column("rotatable_bonds", sa.Integer(), nullable=False),
    sa.Column("morgan_fingerprint", RDKitBfpType(), nullable=False),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("inchi"),
    sa.UniqueConstraint("inchikey"),
  )
  op.create_index(
    "ix_molecules_mol",
    "molecules",
    ["mol"],
    unique=False,
    postgresql_using="gist",
  )
  op.create_index(
    "ix_molecules_morgan_fingerprint",
    "molecules",
    ["morgan_fingerprint"],
    unique=False,
    postgresql_using="gist",
  )
  op.create_index(
    "ix_molecules_molecular_weight",
    "molecules",
    ["molecular_weight"],
    unique=False,
  )
  op.create_index("ix_molecules_logp", "molecules", ["logp"], unique=False)
  op.create_index("ix_molecules_tpsa", "molecules", ["tpsa"], unique=False)


def downgrade() -> None:
  """Downgrade schema."""
  op.drop_index("ix_molecules_tpsa", table_name="molecules")
  op.drop_index("ix_molecules_logp", table_name="molecules")
  op.drop_index("ix_molecules_molecular_weight", table_name="molecules")
  op.drop_index("ix_molecules_morgan_fingerprint", table_name="molecules")
  op.drop_index("ix_molecules_mol", table_name="molecules")
  op.drop_table("molecules")

"""Add update_molecule_data function and trigger

Revision ID: ac7d5c906d8f
Revises: 3e019f076fda
Create Date: 2025-10-08 21:00:08.592030

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ac7d5c906d8f"
down_revision: Union[str, Sequence[str], None] = "3e019f076fda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  """Upgrade schema."""
  op.execute("CREATE EXTENSION IF NOT EXISTS rdkit;")
  op.execute("DROP TRIGGER IF EXISTS update_molecule_data_trigger ON molecules;")
  op.execute("DROP FUNCTION IF EXISTS update_molecule_data();")
  op.execute(
    """
        CREATE OR REPLACE FUNCTION update_molecule_data()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.morgan_fingerprint = morganbv_fp(mol_from_smiles(NEW.smiles::cstring));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
  )
  op.execute(
    """
        CREATE TRIGGER update_molecule_data_trigger
        BEFORE INSERT OR UPDATE ON molecules
        FOR EACH ROW EXECUTE FUNCTION update_molecule_data();
        """
  )


def downgrade() -> None:
  """Downgrade schema."""
  op.execute("DROP TRIGGER IF EXISTS update_molecule_data_trigger ON molecules;")
  op.execute("DROP FUNCTION IF EXISTS update_molecule_data();")

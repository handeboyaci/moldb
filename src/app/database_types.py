from rdkit import Chem, DataStructs
from sqlalchemy.types import LargeBinary, String, TypeDecorator


class RDKitMolType(TypeDecorator):
  impl = LargeBinary

  cache_ok = True

  def process_bind_param(self, value, dialect):
    if value is None:
      return value
    if isinstance(value, Chem.Mol):
      return value.ToBinary()
    raise ValueError("Expected an RDKit Mol object.")

  def process_result_value(self, value, dialect):
    if value is None:
      return value
    return Chem.Mol(value)


class RDKitBfpType(TypeDecorator):
  impl = String  # Store as binary text representation

  cache_ok = True

  def process_bind_param(self, value, dialect):
    if value is None:
      return value
    if isinstance(value, DataStructs.ExplicitBitVect):
      return DataStructs.BitVectToText(value)  # Use BitVectToText for string representation
    raise ValueError("Expected an RDKit ExplicitBitVect object.")

  def process_result_value(self, value, dialect):
    if value is None:
      return value
    return DataStructs.CreateFromFPSText(value)  # Use CreateFromFPSText to reconstruct from string

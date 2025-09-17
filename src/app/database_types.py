from rdkit import Chem, DataStructs
from sqlalchemy.types import UserDefinedType


class RDKitMolType(UserDefinedType):
  def get_col_spec(self):
    return "mol"

  def bind_processor(self, dialect):
    def process(value):
      if value is None:
        return None
      if isinstance(value, Chem.Mol):
        return Chem.MolToSmiles(value)
      return value

    return process

  def result_processor(self, dialect, coltype):
    def process(value):
      if value is None:
        return None
      return Chem.MolFromSmiles(value)

    return process


class RDKitBfpType(UserDefinedType):
  def get_col_spec(self):
    return "bfp"

  def bind_processor(self, dialect):
    def process(value):
      if value is None:
        return None
      return DataStructs.BitVectToFPSText(value)  # ty: ignore[unresolved-attribute]

    return process

  def result_processor(self, dialect, coltype):
    def process(value):
      if value is None:
        return None
      return DataStructs.CreateFromFPSText(value)  # ty: ignore[unresolved-attribute]

    return process

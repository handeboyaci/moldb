import os
import sys
from unittest.mock import Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest

from src.app.models.molecule import Molecule, MoleculeInDB
from src.app.services.molecule_service import MoleculeService


@pytest.fixture
def mock_molecule_repository():
  return Mock()


@pytest.fixture
def molecule_service(mock_molecule_repository, monkeypatch):
  mock_redis = Mock()
  monkeypatch.setattr("src.app.services.molecule_service.get_redis_client", lambda: mock_redis)
  service = MoleculeService(db=Mock())
  service.repository = mock_molecule_repository
  return service


def test_search_molecules(molecule_service, mock_molecule_repository):
  # Arrange
  mock_molecules = [
    Molecule(id="1", smiles="CCO", molecular_weight=46.07, chemical_formula="C2H6O"),
    Molecule(id="2", smiles="CCC", molecular_weight=44.10, chemical_formula="C3H8"),
  ]
  mock_molecule_repository.search.return_value = mock_molecules

  # Act
  result = molecule_service.search_molecules(min_mol_weight=40, max_mol_weight=50)

  # Assert
  mock_molecule_repository.search.assert_called_once_with(
    min_mol_weight=40,
    max_mol_weight=50,
    min_logp=None,
    max_logp=None,
    min_tpsa=None,
    max_tpsa=None,
    min_h_bond_donors=None,
    max_h_bond_donors=None,
    min_h_bond_acceptors=None,
    max_h_bond_acceptors=None,
    min_rotatable_bonds=None,
    max_rotatable_bonds=None,
    inchi=None,
    inchikey=None,
    smiles=None,
    chemical_formula=None,
  )
  assert result == mock_molecules


def test_search_molecules_no_filters(molecule_service, mock_molecule_repository):
  # Arrange
  mock_molecules = [
    Molecule(id="1", smiles="CCO", molecular_weight=46.07, chemical_formula="C2H6O"),
    Molecule(id="2", smiles="CCC", molecular_weight=44.10, chemical_formula="C3H8"),
  ]
  mock_molecule_repository.search.return_value = mock_molecules

  # Act
  result = molecule_service.search_molecules()

  # Assert
  mock_molecule_repository.search.assert_called_once_with(
    min_mol_weight=None,
    max_mol_weight=None,
    min_logp=None,
    max_logp=None,
    min_tpsa=None,
    max_tpsa=None,
    min_h_bond_donors=None,
    max_h_bond_donors=None,
    min_h_bond_acceptors=None,
    max_h_bond_acceptors=None,
    min_rotatable_bonds=None,
    max_rotatable_bonds=None,
    inchi=None,
    inchikey=None,
    smiles=None,
    chemical_formula=None,
  )
  assert result == mock_molecules


def test_search_molecules_with_inchi(molecule_service, mock_molecule_repository):
  # Arrange
  mock_molecules = [
    Molecule(id="1", smiles="CCO", inchi="InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3"),
  ]
  mock_molecule_repository.search.return_value = mock_molecules

  # Act
  result = molecule_service.search_molecules(inchi="InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3")

  # Assert
  mock_molecule_repository.search.assert_called_once_with(
    min_mol_weight=None,
    max_mol_weight=None,
    min_logp=None,
    max_logp=None,
    min_tpsa=None,
    max_tpsa=None,
    min_h_bond_donors=None,
    max_h_bond_donors=None,
    min_h_bond_acceptors=None,
    max_h_bond_acceptors=None,
    min_rotatable_bonds=None,
    max_rotatable_bonds=None,
    inchi="InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3",
    inchikey=None,
    smiles=None,
    chemical_formula=None,
  )
  assert result == mock_molecules


def test_create_molecule_success(molecule_service, mock_molecule_repository):
  # Arrange
  smiles = "CCO"
  mock_molecule_repository.create_molecule.return_value = "some_molecule"

  # Act
  result = molecule_service.create_molecule(smiles)

  # Assert
  mock_molecule_repository.create_molecule.assert_called_once()
  call_args = mock_molecule_repository.create_molecule.call_args[0][0]

  assert isinstance(call_args, MoleculeInDB)
  assert call_args.smiles == smiles
  assert call_args.inchikey == "LFQSCWFLJHTTHZ-UHFFFAOYSA-N"
  assert result == "some_molecule"


def test_create_molecule_invalid_smiles(molecule_service, mock_molecule_repository):
  # Arrange
  smiles = "invalid_smiles"

  # Act & Assert
  with pytest.raises(ValueError, match="Invalid SMILES string"):
    molecule_service.create_molecule(smiles)

  mock_molecule_repository.create_molecule.assert_not_called()


def test_find_similar_molecules(molecule_service, mock_molecule_repository):
  # Arrange
  smiles = "CCO"
  min_similarity = 0.8
  mock_return = ["similar_molecule_1", "similar_molecule_2"]
  mock_molecule_repository.find_similar.return_value = mock_return

  # Act
  result = molecule_service.find_similar_molecules(smiles, min_similarity)

  # Assert
  mock_molecule_repository.find_similar.assert_called_once_with(smiles, min_similarity, False)
  assert result == mock_return


def test_substructure_search(molecule_service, mock_molecule_repository):
  # Arrange
  smiles = "CC"
  mock_return = ["molecule_with_substructure"]
  mock_molecule_repository.substructure_search.return_value = mock_return

  # Act
  result = molecule_service.substructure_search(smiles)

  # Assert
  mock_molecule_repository.substructure_search.assert_called_once_with(smiles)
  assert result == mock_return

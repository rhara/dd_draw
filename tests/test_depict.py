from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Geometry import Point3D

from dd_draw.depict import _orient_horizontal, mol_to_svg


def _make_tall_mol() -> Chem.Mol:
    """A short zig-zag chain whose 2D layout we pin to be taller than wide,
    to exercise the horizontal-reorientation logic deterministically."""
    mol = Chem.MolFromSmiles("CCCC")
    AllChem.Compute2DCoords(mol)
    conf = mol.GetConformer()
    ys = [0.0, 4.0, 8.0, 12.0]
    for i, y in enumerate(ys):
        conf.SetAtomPosition(i, Point3D(0.3 * (i % 2), y, 0.0))
    return mol


def _bbox(mol: Chem.Mol) -> tuple[float, float]:
    conf = mol.GetConformer()
    xs = [conf.GetAtomPosition(i).x for i in range(mol.GetNumAtoms())]
    ys = [conf.GetAtomPosition(i).y for i in range(mol.GetNumAtoms())]
    return max(xs) - min(xs), max(ys) - min(ys)


def test_orient_horizontal_rotates_tall_layout_to_wide():
    mol = _make_tall_mol()
    w_before, h_before = _bbox(mol)
    assert h_before > w_before  # sanity check on the fixture itself

    _orient_horizontal(mol)
    w_after, h_after = _bbox(mol)
    assert w_after >= h_after


def test_mol_to_svg_orient_horizontal_default_does_not_mutate_caller_mol():
    mol = _make_tall_mol()
    w_before, h_before = _bbox(mol)

    mol_to_svg(mol)  # orient_horizontal=True by default

    w_after, h_after = _bbox(mol)
    assert (w_after, h_after) == (w_before, h_before)


def test_mol_to_svg_no_orient_horizontal_keeps_layout_tall():
    mol = _make_tall_mol()
    svg_default = mol_to_svg(mol, orient_horizontal=True)
    svg_kept = mol_to_svg(mol, orient_horizontal=False)
    assert svg_default != svg_kept


def test_mol_to_svg_atom_and_bond_indices_add_annotations():
    mol = Chem.MolFromSmiles("CCO")
    plain = mol_to_svg(mol)
    atoms_only = mol_to_svg(mol, atom_indices=True)
    bonds_only = mol_to_svg(mol, bond_indices=True)
    both = mol_to_svg(mol, atom_indices=True, bond_indices=True)

    note = "class='note'"
    assert plain.count(note) == 0
    assert atoms_only.count(note) == mol.GetNumAtoms()
    assert bonds_only.count(note) == mol.GetNumBonds()
    assert both.count(note) == mol.GetNumAtoms() + mol.GetNumBonds()


def test_mol_to_svg_inline_strips_xml_decl():
    mol = Chem.MolFromSmiles("CCO")
    svg = mol_to_svg(mol, width=100, height=80)
    assert svg.strip().startswith("<svg")
    assert "<?xml" not in svg


def test_mol_to_svg_not_inline_keeps_xml_decl():
    mol = Chem.MolFromSmiles("CCO")
    svg = mol_to_svg(mol, width=100, height=80, inline=False)
    assert svg.strip().startswith("<?xml")


def test_mol_to_svg_does_not_mutate_input():
    mol = Chem.MolFromSmiles("CCO")
    assert mol.GetNumConformers() == 0
    mol_to_svg(mol)
    assert mol.GetNumConformers() == 0


def test_mol_to_svg_respects_size():
    mol = Chem.MolFromSmiles("c1ccccc1")
    svg = mol_to_svg(mol, width=321, height=123)
    assert "321" in svg
    assert "123" in svg

from rdkit import Chem

from dd_draw.depict import mol_to_svg


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

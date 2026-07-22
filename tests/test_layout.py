from pathlib import Path

import pytest

from dd_draw.layout import MoleculeGrid

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_from_sdf_loads_records_and_default_properties():
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf")
    assert len(grid) == 29
    props = grid.display_properties()
    assert "MW" in props and "Score" in props


def test_from_smiles_compute_props_and_explicit_properties(tmp_path):
    smi = tmp_path / "mols.smi"
    smi.write_text("CCO ethanol\nCC methane\n")
    grid = MoleculeGrid.from_smiles(smi, properties=["MW"], compute_props=["MW", "LogP"])
    assert grid.display_properties() == ["MW"]  # explicit subset wins over union
    assert "MW" in grid.records[0].props and "LogP" in grid.records[0].props


def test_from_file_dispatches_and_rejects_unknown(tmp_path):
    smi = tmp_path / "mols.smi"
    smi.write_text("CCO ethanol\n")
    assert len(MoleculeGrid.from_file(smi)) == 1
    with pytest.raises(ValueError):
        MoleculeGrid.from_file(tmp_path / "mols.xyz")


def test_sort_by_ascending_and_descending():
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf")
    grid.sort_by("MW", ascending=True)
    mws = [r.props["MW"] for r in grid.records]
    assert mws == sorted(mws)

    grid.sort_by("MW", ascending=False)
    mws = [r.props["MW"] for r in grid.records]
    assert mws == sorted(mws, reverse=True)


def test_sort_by_returns_self_for_chaining():
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf")
    assert grid.sort_by("MW") is grid


def test_sort_by_missing_values_sort_last(tmp_path):
    smi = tmp_path / "mols.smi"
    smi.write_text("CCO has_score\nCC no_score\n")
    grid = MoleculeGrid.from_smiles(smi)
    grid.records[0].props["Score"] = 5.0
    # no_score has no "Score" key at all

    grid.sort_by("Score", ascending=True)
    assert grid.records[-1].name == "no_score"

    grid.sort_by("Score", ascending=False)
    assert grid.records[-1].name == "no_score"

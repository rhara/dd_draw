from pathlib import Path

import pytest
from rdkit import Chem

from dd_draw.io_utils import (
    DESCRIPTORS,
    compute_descriptors,
    load_molecules,
    merge_properties_csv,
    read_sdf,
    read_smi,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_read_smi_parses_name_and_default(tmp_path):
    smi = tmp_path / "mols.smi"
    smi.write_text("CCO ethanol\nCC\n")
    records = read_smi(smi)
    assert [r.name for r in records] == ["ethanol", "mol1"]
    assert all(r.mol is not None for r in records)
    assert records[0].props == {}


def test_read_smi_rejects_bad_smiles(tmp_path):
    smi = tmp_path / "bad.smi"
    smi.write_text("not_a_smiles x\n")
    with pytest.raises(ValueError):
        read_smi(smi)


def test_read_sdf_extracts_sd_tags_and_name(tmp_path):
    mol = Chem.MolFromSmiles("CCO")
    mol.SetProp("_Name", "ethanol")
    mol.SetProp("Foo", "bar")
    sdf = tmp_path / "one.sdf"
    writer = Chem.SDWriter(str(sdf))
    writer.write(mol)
    writer.close()

    records = read_sdf(sdf)
    assert len(records) == 1
    assert records[0].name == "ethanol"
    assert records[0].props["Foo"] == "bar"


def test_load_molecules_dispatches_by_extension(tmp_path):
    smi = tmp_path / "mols.smi"
    smi.write_text("CCO ethanol\n")
    records = load_molecules(smi)
    assert len(records) == 1

    with pytest.raises(ValueError):
        load_molecules(tmp_path / "mols.unknown")


def test_sample_drugs_load_cleanly():
    smi_records = read_smi(DATA_DIR / "sample_drugs.smi")
    sdf_records = read_sdf(DATA_DIR / "sample_drugs.sdf")
    assert len(smi_records) == 29
    assert len(sdf_records) == 29
    assert sdf_records[0].props["MW"] > 0
    assert "Score" in sdf_records[0].props


def test_compute_descriptors_adds_named_properties(tmp_path):
    records = _one_record(tmp_path, "CCO ethanol")
    out = compute_descriptors(records, ["MW", "LogP"])
    assert set(out[0].props) == {"MW", "LogP"}
    assert out[0].props["MW"] == pytest.approx(46.07, abs=0.1)
    # original record untouched
    assert records[0].props == {}


def test_compute_descriptors_rejects_unknown_name(tmp_path):
    records = _one_record(tmp_path, "CCO ethanol")
    with pytest.raises(ValueError):
        compute_descriptors(records, ["NotADescriptor"])


def test_compute_descriptors_all_available_names_run(tmp_path):
    records = _one_record(tmp_path, "CCO ethanol")
    out = compute_descriptors(records, list(DESCRIPTORS))
    assert set(out[0].props) == set(DESCRIPTORS)


def test_merge_properties_csv_matches_by_name(tmp_path):
    records = _one_record(tmp_path, "CCO ethanol\nCC methane")
    csv_path = tmp_path / "props.csv"
    csv_path.write_text("name,Score\nethanol,1.5\nunmatched,9\n")

    out = merge_properties_csv(records, csv_path)
    assert out[0].props["Score"] == 1.5
    assert "Score" not in out[1].props  # methane has no matching row


def test_merge_properties_csv_explicit_key_column(tmp_path):
    records = _one_record(tmp_path, "CCO ethanol")
    csv_path = tmp_path / "props.csv"
    csv_path.write_text("id,label,Score\nethanol,x,2.0\n")

    out = merge_properties_csv(records, csv_path, key_column="id")
    assert out[0].props["Score"] == 2.0
    assert out[0].props["label"] == "x"


def _one_record(tmp_path, text: str):
    smi = tmp_path / f"in_{abs(hash(text))}.smi"
    smi.write_text(text + "\n")
    return read_smi(smi)

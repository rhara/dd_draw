from pathlib import Path

import pytest

from dd_draw.cli import main

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_cli_html_output(tmp_path):
    out = tmp_path / "grid.html"
    main([str(DATA_DIR / "sample_drugs.sdf"), "-o", str(out), "--props", "MW,LogP"])
    assert out.exists()
    assert "<svg" in out.read_text()


def test_cli_pdf_output(tmp_path):
    out = tmp_path / "grid.pdf"
    main([str(DATA_DIR / "sample_drugs.sdf"), "-o", str(out)])
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF")


def test_cli_compute_props_on_smi(tmp_path):
    out = tmp_path / "grid.html"
    main([str(DATA_DIR / "sample_drugs.smi"), "-o", str(out), "--compute-props", "MW,LogP", "--sort-by", "MW"])
    assert out.exists()


def test_cli_unrecognized_output_extension_exits(tmp_path):
    out = tmp_path / "grid.png"
    with pytest.raises(SystemExit):
        main([str(DATA_DIR / "sample_drugs.sdf"), "-o", str(out)])


def test_cli_sort_by_descending(tmp_path):
    out = tmp_path / "grid.html"
    main([str(DATA_DIR / "sample_drugs.sdf"), "-o", str(out), "--sort-by", "MW", "--descending"])
    assert out.exists()


def test_cli_atom_and_bond_indices(tmp_path):
    out = tmp_path / "grid.html"
    main([str(DATA_DIR / "sample_drugs.sdf"), "-o", str(out), "--atom-indices", "--bond-indices"])
    assert "class='note'" in out.read_text()


def test_cli_no_orient_horizontal(tmp_path):
    out_default = tmp_path / "default.html"
    out_kept = tmp_path / "kept.html"
    main([str(DATA_DIR / "sample_drugs.sdf"), "-o", str(out_default)])
    main([str(DATA_DIR / "sample_drugs.sdf"), "-o", str(out_kept), "--no-orient-horizontal"])
    assert out_default.read_text() != out_kept.read_text()


def test_cli_font_size(tmp_path):
    out = tmp_path / "grid.html"
    main([str(DATA_DIR / "sample_drugs.sdf"), "-o", str(out), "--font-size", "14"])
    html = out.read_text()
    assert "font-size: 14pt" in html
    assert "font-size: 16pt" in html


def test_cli_cell_gap(tmp_path):
    out = tmp_path / "grid.html"
    main([str(DATA_DIR / "sample_drugs.sdf"), "-o", str(out), "--cell-gap", "3"])
    assert "gap: 3px" in out.read_text()

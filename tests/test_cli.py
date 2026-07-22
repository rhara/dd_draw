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

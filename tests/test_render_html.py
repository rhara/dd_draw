from pathlib import Path

from dd_draw.layout import MoleculeGrid
from dd_draw.render_html import format_value, render_html

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_render_html_is_self_contained_and_has_all_cells():
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW", "LogP"])
    html = render_html(grid)
    assert html.count("<svg") == len(grid)
    assert "cdn" not in html.lower() and "<script src" not in html and "<link " not in html
    for rec in grid.records:
        assert rec.name in html


def test_render_html_missing_property_shows_em_dash(tmp_path):
    smi = tmp_path / "mols.smi"
    smi.write_text("CCO ethanol\n")
    grid = MoleculeGrid.from_smiles(smi, properties=["NotPresent"])
    html = render_html(grid)
    assert "—" in html


def test_render_html_escapes_special_characters(tmp_path):
    smi = tmp_path / "mols.smi"
    smi.write_text("CCO <script>alert(1)</script>\n")
    grid = MoleculeGrid.from_smiles(smi)
    html = render_html(grid)
    assert "<script>alert(1)</script>" not in html


def test_format_value_rounds_floats_and_marks_missing():
    assert format_value(None) == "—"
    assert format_value(1.23456) == "1.23"
    assert format_value("text") == "text"


def test_format_value_mw_always_shows_two_decimals():
    assert format_value(180.16, "MW") == "180.16"
    assert format_value(180.1, "MW") == "180.10"
    assert format_value(46.07, "MW") == "46.07"
    # unaffected properties keep the general 3-significant-figure format
    assert format_value(180.16, "LogP") == "180"


def test_render_html_mw_shows_two_decimals():
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW"])
    html = render_html(grid)
    aspirin = next(r for r in grid.records if r.name == "aspirin")
    assert f"{aspirin.props['MW']:.2f}" in html


def test_render_html_default_font_size():
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW"])
    html = render_html(grid)
    assert "font-size: 7pt" in html  # property text
    assert "font-size: 9pt" in html  # compound name


def test_render_html_custom_font_size():
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW"], font_size=12)
    html = render_html(grid)
    assert "font-size: 12pt" in html
    assert "font-size: 14pt" in html


def test_render_html_default_cell_gap():
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW"])
    html = render_html(grid)
    assert "gap: 8px" in html


def test_render_html_custom_cell_gap():
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW"], cell_gap=2)
    html = render_html(grid)
    assert "gap: 2px" in html

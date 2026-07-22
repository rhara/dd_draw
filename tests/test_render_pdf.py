import re
from pathlib import Path

from pypdf import PdfReader

from dd_draw.layout import MoleculeGrid

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_render_pdf_writes_valid_pdf_with_expected_pages(tmp_path):
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW", "LogP"], mols_per_row=4)
    out = tmp_path / "grid.pdf"
    grid.to_pdf(out)

    assert out.exists()
    reader = PdfReader(str(out))
    assert len(reader.pages) >= 1
    # 29 records at 4/row and a handful of rows/page should need more than one page
    assert len(reader.pages) >= 2


def test_render_pdf_single_page_for_small_grid(tmp_path):
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf")
    grid.records = grid.records[:3]
    out = tmp_path / "small.pdf"
    grid.to_pdf(out)

    reader = PdfReader(str(out))
    assert len(reader.pages) == 1


def test_render_pdf_empty_grid_does_not_crash(tmp_path):
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf")
    grid.records = []
    out = tmp_path / "empty.pdf"
    grid.to_pdf(out)
    assert out.exists()


def test_render_pdf_larger_font_size_needs_more_pages(tmp_path):
    small_font = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW", "LogP"], mols_per_row=4, font_size=7)
    large_font = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW", "LogP"], mols_per_row=4, font_size=40)

    small_out, large_out = tmp_path / "small_font.pdf", tmp_path / "large_font.pdf"
    small_font.to_pdf(small_out)
    large_font.to_pdf(large_out)

    assert len(PdfReader(str(large_out)).pages) > len(PdfReader(str(small_out)).pages)


def _page_content(path) -> str:
    return PdfReader(str(path)).pages[0].get_contents().get_data().decode("latin-1")


def test_render_pdf_draws_one_border_per_cell(tmp_path):
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW"])
    grid.records = grid.records[:5]
    out = tmp_path / "bordered.pdf"
    grid.to_pdf(out)

    # border stroke color set once per cell, immediately followed by a
    # rectangle path + stroke ("re S")
    content = _page_content(out)
    assert content.count(".867 .867 .867 RG") == len(grid)
    assert content.count(" re S") == len(grid)


def _cell_left_edges(path) -> list[float]:
    # each cell's border is "<gray> RG\n.5 w\nn X Y W H re S" -- X is the
    # cell's left edge in PDF points
    return [float(m.group(1)) for m in re.finditer(r"n ([\d.]+) [\d.]+ [\d.]+ [\d.]+ re S", _page_content(path))]


def test_render_pdf_larger_cell_gap_pushes_columns_further_apart(tmp_path):
    narrow = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW"], mols_per_row=2, cell_gap=8)
    narrow.records = narrow.records[:2]
    wide = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW"], mols_per_row=2, cell_gap=60)
    wide.records = wide.records[:2]

    narrow_out, wide_out = tmp_path / "narrow_gap.pdf", tmp_path / "wide_gap.pdf"
    narrow.to_pdf(narrow_out)
    wide.to_pdf(wide_out)

    narrow_x = _cell_left_edges(narrow_out)
    wide_x = _cell_left_edges(wide_out)
    assert len(narrow_x) == 2 and len(wide_x) == 2
    # second column's left edge should sit further right with the bigger gap
    assert wide_x[1] > narrow_x[1]

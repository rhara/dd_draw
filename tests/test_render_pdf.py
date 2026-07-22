import re
from pathlib import Path

import pytest
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4

from dd_draw.layout import MoleculeGrid
from dd_draw.render_pdf import CELL_PADDING, MARGIN, _svg_native_size

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


def test_svg_native_size_is_smaller_than_declared_pixels():
    # svg2rlg converts a declared "Npx" using the standard 96dpi->72dpi
    # ratio, so the parsed Drawing is 75% of the pixel value, not equal to
    # it -- this is the exact discrepancy that caused molecules to render
    # undersized and flush to a cell's bottom-left corner (see render_pdf).
    native_w, native_h = _svg_native_size(250, 200)
    assert native_w == pytest.approx(250 * 0.75, rel=0.02)
    assert native_h == pytest.approx(200 * 0.75, rel=0.02)


def test_render_pdf_structure_fills_its_depiction_box(tmp_path):
    grid = MoleculeGrid.from_sdf(DATA_DIR / "sample_drugs.sdf", properties=["MW"])
    grid.records = grid.records[:1]
    grid.mols_per_row = 1
    out = tmp_path / "one.pdf"
    grid.to_pdf(out)

    # our own applied `scale` is a "N 0 0 N 0 0 cm" matrix immediately
    # followed by svg2rlg's own internal 0.75 px->pt matrix; skip the
    # page's leading "1 0 0 1 0 0 cm" identity transform, which matches
    # the same shape but isn't the one we're after
    applied_scale = None
    for match in re.finditer(r"([\d.]+) 0 0 \1 0 0 cm\s*q\s*\.75 0 0 -0\.75", _page_content(out)):
        applied_scale = float(match.group(1))
    assert applied_scale is not None

    native_w, _ = _svg_native_size(grid.cell_width, grid.cell_height)
    page_w, _ = A4
    cell_w = page_w - 2 * MARGIN  # single column, no gap term
    depiction_w = cell_w - 2 * CELL_PADDING
    expected_scale = depiction_w / native_w
    assert applied_scale == pytest.approx(expected_scale, rel=0.01)

    # regression guard: the original bug scaled against the *declared*
    # pixel size directly, which is ~33% smaller than the correct scale
    naive_scale = depiction_w / grid.cell_width
    assert applied_scale > naive_scale * 1.2

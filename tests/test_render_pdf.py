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

"""Renders a `MoleculeGrid` to a paginated PDF: pure Python (reportlab +
svglib), no system Cairo/Pango/GTK dependency, so it behaves identically on
Linux/macOS/Windows. Lays out its own grid directly from each molecule's SVG
depiction -- independent of `render_html`'s CSS grid, since PDF pagination
has no CSS-grid equivalent to reuse.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING, Tuple, Union

from rdkit import Chem
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg

from .depict import mol_to_svg
from .render_html import format_value

if TYPE_CHECKING:
    from .layout import MoleculeGrid

MARGIN = 15 * mm
CELL_PADDING = 6
TITLE_HEIGHT = 18


def _svg_native_size(width: int, height: int) -> Tuple[float, float]:
    """svg2rlg interprets an SVG's declared `width="Npx"`/`height="Mpx"`
    using the standard 96dpi (CSS px) -> 72dpi (PDF pt) conversion, so a
    `mol_to_svg(..., width=250, height=200)` canvas parses to a Drawing
    sized 187.5x150pt, not 250x200pt. Scaling against the *declared* pixel
    size (as if it were already in points) silently renders everything at
    75% of the intended size, flush to the depiction box's bottom-left
    corner instead of filling it. Probing with a trivial molecule -- built
    via the exact same `mol_to_svg` header -- gives the real native pt
    size to scale against instead of assuming px == pt."""
    probe_svg = mol_to_svg(Chem.MolFromSmiles("C"), width=width, height=height)
    probe = svg2rlg(io.StringIO(probe_svg))
    return probe.width, probe.height


def render_pdf(grid: "MoleculeGrid", path: Union[str, Path], page_size=A4) -> None:
    properties = grid.display_properties()
    prop_font_size = grid.font_size
    name_font_size = grid.font_size + 2
    line_height = prop_font_size + 2
    gap = grid.cell_gap

    native_w, native_h = _svg_native_size(grid.cell_width, grid.cell_height)

    page_w, page_h = page_size
    cols = max(1, grid.mols_per_row)
    cell_w = (page_w - 2 * MARGIN - (cols - 1) * gap) / cols
    depiction_w = cell_w - 2 * CELL_PADDING
    scale = depiction_w / native_w
    depiction_h = native_h * scale
    text_block_h = name_font_size + 4 + len(properties) * line_height
    cell_h = depiction_h + text_block_h + 2 * CELL_PADDING

    top_y = page_h - MARGIN - (TITLE_HEIGHT if grid.title else 0)
    rows_per_page = max(1, int((top_y - MARGIN + gap) // (cell_h + gap)))
    per_page = rows_per_page * cols

    c = canvas.Canvas(str(path), pagesize=page_size)

    def draw_title() -> None:
        if grid.title:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(MARGIN, page_h - MARGIN + 4, grid.title)

    draw_title()
    for i, rec in enumerate(grid.records):
        pos = i % per_page
        if i > 0 and pos == 0:
            c.showPage()
            draw_title()
        row, col = divmod(pos, cols)

        x0 = MARGIN + col * (cell_w + gap)
        y_top = top_y - row * (cell_h + gap)

        c.setStrokeColorRGB(0.867, 0.867, 0.867)
        c.setLineWidth(0.5)
        c.rect(x0, y_top - cell_h, cell_w, cell_h, stroke=1, fill=0)

        svg_text = mol_to_svg(
            rec.mol,
            width=grid.cell_width,
            height=grid.cell_height,
            orient_horizontal=grid.orient_horizontal,
            atom_indices=grid.atom_indices,
            bond_indices=grid.bond_indices,
        )
        drawing = svg2rlg(io.StringIO(svg_text))
        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)
        renderPDF.draw(drawing, c, x0 + CELL_PADDING, y_top - depiction_h)

        name_y = y_top - depiction_h - name_font_size - 2
        c.setFont("Helvetica-Bold", name_font_size)
        c.drawCentredString(x0 + cell_w / 2, name_y, rec.name)

        prop_y = name_y - line_height
        c.setFont("Helvetica", prop_font_size)
        for key in properties:
            c.drawCentredString(x0 + cell_w / 2, prop_y, f"{key}: {format_value(rec.props.get(key), key)}")
            prop_y -= line_height

    c.save()

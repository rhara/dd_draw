"""Renders a `MoleculeGrid` to one self-contained HTML string: every
structure is an inline `<svg>` (no external files, no CDN, opens offline).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader, select_autoescape

from .depict import mol_to_svg

if TYPE_CHECKING:
    from .layout import MoleculeGrid

_env = Environment(
    loader=PackageLoader("dd_draw", "templates"),
    autoescape=select_autoescape(["html"]),
)

MISSING = "—"  # em dash


def format_value(value) -> str:
    if value is None:
        return MISSING
    if isinstance(value, float):
        return f"{value:.3g}"
    return str(value)


def render_html(grid: "MoleculeGrid") -> str:
    properties = grid.display_properties()
    rows = []
    for rec in grid.records:
        rows.append(
            {
                "name": rec.name,
                "svg": mol_to_svg(rec.mol, width=grid.cell_width, height=grid.cell_height),
                "formatted": {key: format_value(rec.props.get(key)) for key in properties},
            }
        )
    template = _env.get_template("grid.html")
    return template.render(
        title=grid.title,
        records=rows,
        properties=properties,
        mols_per_row=grid.mols_per_row,
    )

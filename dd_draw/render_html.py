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

# Properties with a conventional fixed decimal precision, shown at that
# precision regardless of magnitude instead of the general 3-significant-
# figure default (which drops MW's usual 2 decimals for anything >= 100,
# e.g. 180.16 -> "180").
DECIMAL_PLACES = {"MW": 2}


def format_value(value, key: str = None) -> str:
    if value is None:
        return MISSING
    if isinstance(value, float):
        decimals = DECIMAL_PLACES.get(key)
        if decimals is not None:
            return f"{value:.{decimals}f}"
        return f"{value:.3g}"
    return str(value)


def render_html(grid: "MoleculeGrid") -> str:
    properties = grid.display_properties()
    rows = []
    for rec in grid.records:
        rows.append(
            {
                "name": rec.name,
                "svg": mol_to_svg(
                    rec.mol,
                    width=grid.cell_width,
                    height=grid.cell_height,
                    orient_horizontal=grid.orient_horizontal,
                    atom_indices=grid.atom_indices,
                    bond_indices=grid.bond_indices,
                ),
                "formatted": {key: format_value(rec.props.get(key), key) for key in properties},
            }
        )
    template = _env.get_template("grid.html")
    return template.render(
        title=grid.title,
        records=rows,
        properties=properties,
        mols_per_row=grid.mols_per_row,
        prop_font_size=grid.font_size,
        name_font_size=grid.font_size + 2,
        cell_gap=grid.cell_gap,
    )

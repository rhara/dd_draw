"""Command-line entry point:
  dd_draw compounds.sdf -o grid.html --props MW,LogP --sort-by MW
  dd_draw ligands.smi -o grid.pdf --compute-props MW,LogP,TPSA --sort-by LogP --descending
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .io_utils import DESCRIPTORS
from .layout import MoleculeGrid


def _csv_list(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Lay out a compound list (SMILES or SDF) as a sortable, "
        "property-annotated grid, rendered to self-contained HTML or paginated PDF.",
    )
    p.add_argument("input", type=Path, help="Input file: .smi/.smiles or .sdf/.sd/.mol")
    p.add_argument("-o", "--output", type=Path, required=True, help="Output path; format is chosen by extension (.html or .pdf)")
    p.add_argument(
        "--props",
        type=_csv_list,
        default=None,
        metavar="NAME,NAME,...",
        help="Comma-separated property names to display (default: every property found across the input)",
    )
    p.add_argument(
        "--compute-props",
        type=_csv_list,
        default=None,
        metavar="NAME,NAME,...",
        help=f"Comma-separated RDKit descriptors to compute and attach. Available: {', '.join(sorted(DESCRIPTORS))}. "
        "Pass 'all' to compute every available descriptor.",
    )
    p.add_argument("--props-csv", type=Path, default=None, help="External CSV to merge in as properties, keyed by molecule name (first column, or --props-csv-key)")
    p.add_argument("--props-csv-key", default=None, metavar="COLUMN", help="Key column name in --props-csv (default: its first column)")
    p.add_argument("--sort-by", default=None, metavar="NAME", help="Property name to sort by (records missing it always sort last)")
    p.add_argument("--descending", action="store_true", help="Sort --sort-by in descending order (default: ascending)")
    p.add_argument("--cols", type=int, default=4, help="Molecules per row (default: 4)")
    p.add_argument("--cell-width", type=int, default=250, help="Structure depiction width in pixels (default: 250)")
    p.add_argument("--cell-height", type=int, default=200, help="Structure depiction height in pixels (default: 200)")
    p.add_argument("--title", default=None, help="Page/document title")
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)

    compute_props = None
    if args.compute_props is not None:
        compute_props = sorted(DESCRIPTORS) if args.compute_props == ["all"] else args.compute_props

    grid = MoleculeGrid.from_file(
        args.input,
        properties=args.props,
        compute_props=compute_props,
        props_csv=args.props_csv,
        props_csv_key=args.props_csv_key,
        mols_per_row=args.cols,
        cell_width=args.cell_width,
        cell_height=args.cell_height,
        title=args.title,
    )

    if args.sort_by:
        grid.sort_by(args.sort_by, ascending=not args.descending)

    suffix = args.output.suffix.lower()
    if suffix in (".html", ".htm"):
        grid.to_html(args.output)
    elif suffix == ".pdf":
        grid.to_pdf(args.output)
    else:
        raise SystemExit(f"--output: unrecognized extension {suffix!r} (expected .html or .pdf)")

    print(f"[done] {len(grid)} compound(s) -> {args.output}")


if __name__ == "__main__":
    main()

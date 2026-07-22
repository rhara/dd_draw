[Japanese version](README.jp.md)

# dd_draw — lay out a compound list as a sortable, property-annotated grid

Takes a list of small molecules (`.smi` or `.sdf`), draws each one as a 2D
structure, arranges them in a grid with the compound name and any properties
you choose underneath, and writes the result to a self-contained HTML page
or a paginated PDF. That's the whole scope: dd_draw does not standardize,
filter, dock, or otherwise touch the molecules -- other `dd_*` projects
already own that ([dd_prep](https://github.com/rhara/dd_prep),
[dd_chembl](https://github.com/rhara/dd_chembl), ...); dd_draw is just the
last-mile "look at these compounds" step.

## Overview

- **Input**: `.smi`/`.smiles` (whitespace-separated `SMILES [name]` per line)
  or `.sdf`/`.sd`/`.mol` (every SD tag becomes a property automatically, no
  extra flags needed)
- **Output**: self-contained HTML (every structure is an inline `<svg>`, no
  CDN, no external files -- opens offline, emails/Slacks as one file) or a
  paginated PDF, chosen by the output path's extension
- **Properties**: show any subset of available properties per compound
  (`--props`), or let dd_draw show the union of everything it found;
  `.smi` input carries no properties of its own, so `--compute-props` fills
  in RDKit descriptors on demand (MW, LogP, TPSA, HBD, HBA, RotB, NumRings,
  HeavyAtoms, FractionCSP3, QED) and/or `--props-csv` merges in an external
  table keyed by compound name. Floats are shown to 3 significant figures by
  default, except `MW`, which always shows a fixed 2 decimal places (e.g.
  `180.16`, matching the conventional way molecular weight is reported)
- **Sorting**: `--sort-by NAME` reorders the whole grid by any one property,
  ascending or descending (`--descending`); compounds missing that property
  always sort last, regardless of direction
- **Orientation**: every structure is rotated to be as wide as possible by
  default (`--no-orient-horizontal` to keep each molecule's original 2D
  orientation instead) -- 2D depiction (freshly computed *or* already
  present in the input file) can come out taller than wide, which wastes
  most of a landscape-ish grid cell
- **Atom/bond indices**: `--atom-indices`/`--bond-indices` annotate every
  atom/bond with its RDKit index, for referring to a specific atom or bond
  (e.g. when reporting a docking/SAR finding, or picking a SMARTS anchor)
- **Font size**: `--font-size` (points; default 7, compound name is drawn
  2pt larger) controls the compound name/property text size, in both HTML
  and PDF
- **Jupyter API**: `MoleculeGrid` is the one object the CLI, HTML renderer,
  and PDF renderer all share -- build it, `sort_by(...)` (chainable), and
  either let it auto-display inline (`_repr_html_`) or write it out
  (`to_html`/`to_pdf`)

## Layout

```
data/
  build_sample_drugs.py  regenerates the sample data below
  sample_drugs.smi       29 well-known approved drugs, SMILES + name only
  sample_drugs.sdf       same 29, with MW/LogP/TPSA/HBD/HBA/RotB/QED/Score as SD tags

dd_draw/                    reusable package
  io_utils.py             Record, read_smi / read_sdf / load_molecules,
                           compute_descriptors (RDKit descriptor registry),
                           merge_properties_csv
  depict.py                mol_to_svg - one Mol -> one sized SVG, shared by both renderers
  layout.py                MoleculeGrid - records + display/sort/layout settings;
                           from_smiles / from_sdf / from_file, sort_by, to_html, to_pdf
  render_html.py           render_html - self-contained HTML (jinja2 + inline SVG)
  render_pdf.py            render_pdf - paginated PDF (reportlab + svglib, pure Python)
  templates/grid.html      the HTML grid's jinja2 template
  cli.py                   CLI argument parsing (console script: dd_draw)

tests/                     pytest suite covering every module above
```

## Installation

dd_draw targets its own dedicated environment, separate from any other
`dd_*` project (they are all independent, per this suite's convention) --
named `dd_draw`, Python 3.12. It is pure Python plus RDKit and runs the
same way on Linux, macOS, and Windows: no C++ compiler, no system
Cairo/Pango/GTK, no platform-specific code path anywhere in the package.

Package management is mamba(/conda)-first: every real dependency comes from
conda-forge. `pip` is only used for `dd_draw` itself (an editable,
local-source install), always with `--no-deps` so it never touches the
conda-forge-installed dependencies.

**Linux / macOS / Windows (identical commands):**

```bash
mamba create -n dd_draw -c conda-forge python=3.12 rdkit numpy jinja2 reportlab svglib pytest
mamba activate dd_draw
cd dd_draw
pip install --no-deps -e .   # editable install of dd_draw itself; drop -e for a fixed install
```

(`conda` works identically in place of `mamba` if you don't have mamba
installed.)

**No mamba/conda available (any platform):** RDKit, numpy, jinja2,
reportlab, and svglib all also ship as regular PyPI wheels, so a plain venv
works too:

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

Once installed, `import dd_draw` and the `dd_draw` CLI command work from any
directory.

### Why reportlab+svglib for PDF, not WeasyPrint/cairosvg?

Rendering the same HTML/CSS grid straight to PDF (e.g. via WeasyPrint) would
have been less code, but WeasyPrint and cairosvg both need system
Cairo/Pango/GDK-pixbuf libraries -- reliable on Linux/macOS via conda-forge,
but a known source of friction on Windows (a separate GTK3 runtime
install). `reportlab` + `svglib` are pure Python (svglib's only non-Python
dependency is `lxml`, which ships prebuilt wheels everywhere), so PDF
generation behaves identically on all three platforms with nothing beyond
`mamba create`. The trade-off: `render_pdf.py` lays out its own grid
directly from each molecule's SVG rather than reusing `render_html.py`'s
CSS grid, since plain PDF has no CSS-grid equivalent to share.

### Horizontal orientation

RDKit's 2D coordinate generation picks *a* valid, non-overlapping layout,
not necessarily a wide one -- and a molecule loaded from someone else's SDF
already carries whatever orientation that file's own coordinates happen to
be in, which is just as arbitrary. By default, `depict.py` runs a PCA over
each molecule's atom positions and rotates it so its longest extent is
horizontal (falling back to the perpendicular axis if that still comes out
taller than wide, e.g. cross-shaped layouts). Pass `--no-orient-horizontal`
(`orient_horizontal=False` in the API) to keep a molecule's original
orientation as-is -- useful if the input coordinates are meaningful on
their own, e.g. matching a docked pose's orientation in a pocket.

## Usage

```bash
# HTML: self-contained, opens in any browser offline
dd_draw data/sample_drugs.sdf -o grid.html --props MW,LogP,TPSA,Score --sort-by Score --descending --cols 5

# PDF: same grid, paginated
dd_draw data/sample_drugs.sdf -o grid.pdf --props MW,LogP --sort-by MW --cols 4

# .smi has no properties of its own -- compute RDKit descriptors on the fly
dd_draw data/sample_drugs.smi -o grid.html --compute-props MW,LogP,TPSA --sort-by MW

# merge in your own property table (CSV keyed by compound name, first column by default)
dd_draw hits.smi -o hits.html --props-csv docking_scores.csv --sort-by docking_score

# annotate atom/bond indices, and keep each molecule's original orientation instead of auto-rotating
dd_draw hits.sdf -o hits.html --atom-indices --bond-indices --no-orient-horizontal

# smaller/larger text (default is 7pt)
dd_draw data/sample_drugs.sdf -o grid.html --font-size 5
```

Full option list: `dd_draw --help`.

| Option | Description | Default |
|---|---|---|
| `-o`/`--output` | output path; format chosen by extension (`.html`/`.htm` or `.pdf`) | required |
| `--props` | comma-separated property names to display | every property found across the input |
| `--compute-props` | comma-separated RDKit descriptors to compute and attach (`all` for every one) | none |
| `--props-csv` | external CSV to merge in as properties, keyed by compound name | none |
| `--props-csv-key` | key column name in `--props-csv` | the CSV's first column |
| `--sort-by` | property name to sort the grid by; missing values always sort last | input order |
| `--descending` | sort `--sort-by` descending instead of ascending | ascending |
| `--cols` | molecules per row | 4 |
| `--cell-width` / `--cell-height` | structure depiction size in pixels | 250 / 200 |
| `--title` | page/document title | none |
| `--no-orient-horizontal` | keep each molecule's original 2D orientation instead of rotating it to be as wide as possible | rotate |
| `--atom-indices` | annotate each atom with its RDKit atom index | off |
| `--bond-indices` | annotate each bond with its RDKit bond index | off |
| `--font-size` | property text size in points (compound name is drawn 2pt larger); applies to both HTML and PDF | 7 |

Available `--compute-props` descriptors: `MW`, `LogP`, `TPSA`, `HBD`, `HBA`,
`RotB`, `NumRings`, `HeavyAtoms`, `FractionCSP3`, `QED`.

### Python / Jupyter API

```python
from dd_draw import MoleculeGrid

# SDF: SD tags become properties automatically
grid = MoleculeGrid.from_sdf("data/sample_drugs.sdf", properties=["MW", "LogP", "Score"])
grid.sort_by("Score", ascending=False)
grid  # last expression in a notebook cell -> renders the grid inline

grid.to_html("hits_grid.html")
grid.to_pdf("hits_grid.pdf")

# SMILES: no properties on their own, so compute or merge some in
grid2 = MoleculeGrid.from_smiles(
    "data/sample_drugs.smi",
    compute_props=["MW", "LogP", "TPSA"],
    mols_per_row=5,
    title="My library",
).sort_by("MW")

# atom/bond indices, original (non-rotated) orientation, smaller text
grid3 = MoleculeGrid.from_sdf(
    "hits.sdf",
    atom_indices=True,
    bond_indices=True,
    orient_horizontal=False,
    font_size=5,
)
```

`MoleculeGrid.from_file(path, ...)` dispatches to `from_smiles`/`from_sdf`
by extension automatically, same as the CLI.

## Sample data

`data/sample_drugs.smi`/`.sdf`: 29 well-known approved drugs (aspirin,
caffeine, ibuprofen, metformin, propranolol, fluoxetine, ...), chosen for
simple, easy-to-verify structures rather than breadth. Every SMILES parses
in RDKit, no two are duplicate structures, and every molecular formula and
molecular weight was checked by hand against known literature values before
committing. The `.sdf` also carries MW/LogP/TPSA/HBD/HBA/RotB/QED and a
synthetic `Score` (`QED * 100`, just to have something realistic to sort a
demo by) as SD tags. Regenerate with `python data/build_sample_drugs.py`
(needs the `dd_draw` env active).

## Dependencies

RDKit >= 2024.09.2 (2D depiction), numpy (horizontal-orientation PCA),
Jinja2 >= 3.1 (HTML templating), reportlab >= 4.0 + svglib >= 1.5 (PDF
rendering). No JavaScript, no CDN, no system Cairo/Pango/GTK.

## License

MIT — see [LICENSE](LICENSE).

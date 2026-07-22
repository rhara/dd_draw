"""2D structure depiction: one RDKit `Mol` -> one SVG string, sized for a
grid cell. Kept as its own module so the HTML/PDF renderers and any future
output format all draw molecules identically.
"""
from __future__ import annotations

import re

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

_XML_DECL_RE = re.compile(r"^<\?xml[^>]*\?>\s*")


def mol_to_svg(mol: Chem.Mol, width: int = 250, height: int = 200, inline: bool = True) -> str:
    """Renders `mol` as an SVG string of the given pixel size. Computes 2D
    coordinates if the molecule has none yet (does not mutate `mol`). With
    `inline=True` (default), strips the leading `<?xml ... ?>` declaration
    so the SVG can be embedded directly inside an HTML page's `<body>`."""
    mol = Chem.Mol(mol)
    if mol.GetNumConformers() == 0:
        AllChem.Compute2DCoords(mol)
    rdMolDraw2D.PrepareMolForDrawing(mol, addChiralHs=False)

    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    drawer.drawOptions().padding = 0.1
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()

    if inline:
        svg = _XML_DECL_RE.sub("", svg, count=1)
    return svg

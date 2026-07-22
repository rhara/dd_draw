"""2D structure depiction: one RDKit `Mol` -> one SVG string, sized for a
grid cell. Kept as its own module so the HTML/PDF renderers and any future
output format all draw molecules identically.
"""
from __future__ import annotations

import re

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Geometry import Point3D

_XML_DECL_RE = re.compile(r"^<\?xml[^>]*\?>\s*")


def _orient_horizontal(mol: Chem.Mol) -> None:
    """Rotates `mol`'s 2D conformer in place so its longest extent runs
    left-to-right. Needed regardless of whether coordinates were just
    computed or already present on the input (e.g. from an SDF written by
    some other tool) -- 2D depiction algorithms pick *a* valid layout, not
    necessarily a wide one, and a molecule's stored orientation is
    arbitrary. Aligns to the principal axis (PCA on atom positions), then
    swaps to the perpendicular axis if that still comes out taller than
    wide (e.g. cross-shaped layouts where the single largest-variance axis
    isn't the bounding-box-widest one)."""
    conf = mol.GetConformer()
    n = mol.GetNumAtoms()
    if n < 2:
        return

    pts = np.array([[conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y] for i in range(n)])
    centered = pts - pts.mean(axis=0)
    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    principal = eigvecs[:, np.argmax(eigvals)]
    angle = np.arctan2(principal[1], principal[0])
    c, s = np.cos(-angle), np.sin(-angle)
    rotated = centered @ np.array([[c, -s], [s, c]]).T

    width = rotated[:, 0].max() - rotated[:, 0].min()
    height = rotated[:, 1].max() - rotated[:, 1].min()
    if height > width:
        rotated = rotated[:, [1, 0]]
        rotated[:, 1] *= -1

    for i in range(n):
        conf.SetAtomPosition(i, Point3D(float(rotated[i, 0]), float(rotated[i, 1]), 0.0))


def mol_to_svg(
    mol: Chem.Mol,
    width: int = 250,
    height: int = 200,
    inline: bool = True,
    orient_horizontal: bool = True,
    atom_indices: bool = False,
    bond_indices: bool = False,
) -> str:
    """Renders `mol` as an SVG string of the given pixel size. Computes 2D
    coordinates if the molecule has none yet (does not mutate `mol`). With
    `orient_horizontal=True` (default), rotates the depiction to be as wide
    as possible -- see `_orient_horizontal`. `atom_indices`/`bond_indices`
    annotate each atom/bond with its RDKit index. With `inline=True`
    (default), strips the leading `<?xml ... ?>` declaration so the SVG can
    be embedded directly inside an HTML page's `<body>`."""
    mol = Chem.Mol(mol)
    if mol.GetNumConformers() == 0:
        AllChem.Compute2DCoords(mol)
    if orient_horizontal:
        _orient_horizontal(mol)
    rdMolDraw2D.PrepareMolForDrawing(mol, addChiralHs=False)

    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.padding = 0.1
    opts.addAtomIndices = atom_indices
    opts.addBondIndices = bond_indices
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()

    if inline:
        svg = _XML_DECL_RE.sub("", svg, count=1)
    return svg

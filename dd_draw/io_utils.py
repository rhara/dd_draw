"""Load a compound list (.smi or .sdf) into a flat list of `Record`s, each
carrying an RDKit `Mol`, a display name, and a dict of properties -- SD tags
for SDF input, external CSV columns and/or computed RDKit descriptors for
either input format.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from rdkit import Chem
from rdkit.Chem import Descriptors, QED


@dataclass
class Record:
    name: str
    mol: Chem.Mol
    props: Dict[str, Any] = field(default_factory=dict)


def read_smi(path: Union[str, Path]) -> List[Record]:
    """Reads whitespace-separated `SMILES [name]` lines (name defaults to
    `mol{i}` if omitted). No properties -- add them with `compute_descriptors`
    or `merge_properties_csv`."""
    records: List[Record] = []
    with open(path) as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            smiles = parts[0]
            name = parts[1].strip() if len(parts) > 1 else f"mol{i}"
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError(f"{path}:{i + 1}: could not parse SMILES {smiles!r}")
            records.append(Record(name=name, mol=mol, props={}))
    return records


def read_sdf(path: Union[str, Path]) -> List[Record]:
    """Reads an SDF; every SD tag becomes a property. The display name comes
    from the molecule title (`_Name`, the SDF's own first-line title field)
    if set, else falls back to `mol{i}`."""
    records: List[Record] = []
    supplier = Chem.SDMolSupplier(str(path))
    for i, mol in enumerate(supplier):
        if mol is None:
            raise ValueError(f"{path}: record {i + 1} could not be parsed")
        name = mol.GetProp("_Name").strip() if mol.HasProp("_Name") and mol.GetProp("_Name").strip() else f"mol{i}"
        props = {k: v for k, v in mol.GetPropsAsDict().items() if not k.startswith("_")}
        records.append(Record(name=name, mol=mol, props=props))
    return records


def load_molecules(path: Union[str, Path]) -> List[Record]:
    """Dispatches on file extension: `.smi`/`.smiles` -> `read_smi`,
    `.sdf`/`.mol`/`.sd` -> `read_sdf`."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".smi", ".smiles"):
        return read_smi(path)
    if suffix in (".sdf", ".sd", ".mol"):
        return read_sdf(path)
    raise ValueError(f"{path}: unrecognized extension {suffix!r} (expected .smi/.smiles or .sdf/.sd/.mol)")


# name -> callable(mol) -> value, for `--compute-props`/`compute_descriptors`.
# A small curated subset of RDKit's Descriptors module, not the full ~200,
# picked for what's actually useful to display/sort a hit-picking grid by.
DESCRIPTORS: Dict[str, Callable[[Chem.Mol], float]] = {
    "MW": Descriptors.MolWt,
    "LogP": Descriptors.MolLogP,
    "TPSA": Descriptors.TPSA,
    "HBD": Descriptors.NumHDonors,
    "HBA": Descriptors.NumHAcceptors,
    "RotB": Descriptors.NumRotatableBonds,
    "NumRings": Descriptors.RingCount,
    "HeavyAtoms": Descriptors.HeavyAtomCount,
    "FractionCSP3": Descriptors.FractionCSP3,
    "QED": QED.qed,
}


def compute_descriptors(records: Sequence[Record], names: Optional[Sequence[str]] = None) -> List[Record]:
    """Returns new `Record`s with the named descriptors from `DESCRIPTORS`
    added to `props` (existing keys of the same name are overwritten).
    `names=None` computes all of them."""
    names = list(DESCRIPTORS) if names is None else list(names)
    unknown = [n for n in names if n not in DESCRIPTORS]
    if unknown:
        raise ValueError(f"unknown descriptor(s) {unknown}; available: {sorted(DESCRIPTORS)}")
    out = []
    for rec in records:
        props = dict(rec.props)
        for n in names:
            props[n] = DESCRIPTORS[n](rec.mol)
        out.append(Record(name=rec.name, mol=rec.mol, props=props))
    return out


def merge_properties_csv(records: Sequence[Record], csv_path: Union[str, Path], key_column: Optional[str] = None) -> List[Record]:
    """Merges columns from an external CSV into each record's `props`,
    matched by name. `key_column` defaults to the CSV's first column. Values
    that parse as `float` are stored as `float`; everything else stays `str`.
    Records with no matching CSV row are left unchanged."""
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path}: no header row found")
        key = key_column or reader.fieldnames[0]
        if key not in reader.fieldnames:
            raise ValueError(f"{csv_path}: key column {key!r} not found (columns: {reader.fieldnames})")
        by_key = {row[key]: row for row in reader}

    out = []
    for rec in records:
        row = by_key.get(rec.name)
        props = dict(rec.props)
        if row is not None:
            for col, value in row.items():
                if col == key:
                    continue
                try:
                    props[col] = float(value)
                except (TypeError, ValueError):
                    props[col] = value
        out.append(Record(name=rec.name, mol=rec.mol, props=props))
    return out

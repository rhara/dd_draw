"""`MoleculeGrid` -- the one object the CLI, the Jupyter API, and both
renderers (`render_html`/`render_pdf`) all share: a list of `Record`s plus
the display/sort/layout settings, with no format-specific logic of its own.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Union

from .io_utils import Record, compute_descriptors, merge_properties_csv, read_sdf, read_smi


@dataclass
class MoleculeGrid:
    records: List[Record]
    properties: Optional[List[str]] = None
    mols_per_row: int = 4
    cell_width: int = 250
    cell_height: int = 200
    orient_horizontal: bool = True
    atom_indices: bool = False
    bond_indices: bool = False
    font_size: int = 7
    title: Optional[str] = None

    @classmethod
    def from_smiles(
        cls,
        path: Union[str, Path],
        properties: Optional[Sequence[str]] = None,
        compute_props: Optional[Sequence[str]] = None,
        props_csv: Optional[Union[str, Path]] = None,
        props_csv_key: Optional[str] = None,
        **kwargs,
    ) -> "MoleculeGrid":
        """Loads a `.smi` file. `.smi` carries no properties on its own --
        `compute_props` fills in RDKit descriptors (see `io_utils.DESCRIPTORS`
        for the available names) and/or `props_csv` merges columns from an
        external CSV keyed by molecule name."""
        records = read_smi(path)
        if compute_props:
            records = compute_descriptors(records, compute_props)
        if props_csv:
            records = merge_properties_csv(records, props_csv, key_column=props_csv_key)
        return cls(records=records, properties=list(properties) if properties else None, **kwargs)

    @classmethod
    def from_sdf(
        cls,
        path: Union[str, Path],
        properties: Optional[Sequence[str]] = None,
        compute_props: Optional[Sequence[str]] = None,
        props_csv: Optional[Union[str, Path]] = None,
        props_csv_key: Optional[str] = None,
        **kwargs,
    ) -> "MoleculeGrid":
        """Loads an `.sdf` file; every SD tag becomes a property automatically.
        `compute_props`/`props_csv` add to (or overwrite) those, same as
        `from_smiles`."""
        records = read_sdf(path)
        if compute_props:
            records = compute_descriptors(records, compute_props)
        if props_csv:
            records = merge_properties_csv(records, props_csv, key_column=props_csv_key)
        return cls(records=records, properties=list(properties) if properties else None, **kwargs)

    @classmethod
    def from_file(cls, path: Union[str, Path], **kwargs) -> "MoleculeGrid":
        """Dispatches to `from_smiles`/`from_sdf` by file extension."""
        suffix = Path(path).suffix.lower()
        if suffix in (".smi", ".smiles"):
            return cls.from_smiles(path, **kwargs)
        if suffix in (".sdf", ".sd", ".mol"):
            return cls.from_sdf(path, **kwargs)
        raise ValueError(f"{path}: unrecognized extension {suffix!r} (expected .smi/.smiles or .sdf/.sd/.mol)")

    def display_properties(self) -> List[str]:
        """The properties to show per cell: `self.properties` if set,
        otherwise every property key seen on any record, in first-seen
        order."""
        if self.properties is not None:
            return self.properties
        seen: List[str] = []
        for rec in self.records:
            for key in rec.props:
                if key not in seen:
                    seen.append(key)
        return seen

    def sort_by(self, prop: str, ascending: bool = True) -> "MoleculeGrid":
        """Sorts `self.records` in place by property `prop` (mutates and
        returns `self`, so calls chain: `grid.sort_by("MW").to_html(...)`).
        Records missing `prop` always sort to the end, regardless of
        `ascending`."""
        def has_value(rec: Record) -> bool:
            return prop in rec.props and rec.props[prop] is not None

        present = [r for r in self.records if has_value(r)]
        missing = [r for r in self.records if not has_value(r)]
        present.sort(key=lambda r: r.props[prop], reverse=not ascending)
        self.records = present + missing
        return self

    def to_html(self, path: Union[str, Path]) -> Path:
        from .render_html import render_html

        path = Path(path)
        path.write_text(render_html(self))
        return path

    def to_pdf(self, path: Union[str, Path]) -> Path:
        from .render_pdf import render_pdf

        path = Path(path)
        render_pdf(self, path)
        return path

    def _repr_html_(self) -> str:
        """Auto-display support: a bare `grid` as the last expression in a
        Jupyter cell renders the same grid `to_html` would write."""
        from .render_html import render_html

        return render_html(self)

    def __len__(self) -> int:
        return len(self.records)

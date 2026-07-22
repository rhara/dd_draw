#!/usr/bin/env python3
"""Regenerates data/sample_drugs.smi and data/sample_drugs.sdf from the
DRUGS list below: 29 well-known approved drugs (simple, non-stereo
structures, picked so their SMILES are easy to verify by eye) spanning
NSAIDs, CNS/psychiatric, cardiovascular, GI, antihistamine, and a few
endogenous signaling molecules for variety. Validates that every SMILES
parses and that there are no duplicate canonical structures before writing.

Run from the dd_draw env (needs rdkit): `python data/build_sample_drugs.py`
"""
from __future__ import annotations

from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors, QED

DRUGS = [
    ("aspirin", "CC(=O)OC1=CC=CC=C1C(=O)O"),
    ("caffeine", "Cn1cnc2c1c(=O)n(C)c(=O)n2C"),
    ("ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
    ("acetaminophen", "CC(=O)Nc1ccc(O)cc1"),
    ("naproxen", "COc1ccc2cc(ccc2c1)C(C)C(=O)O"),
    ("diclofenac", "OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl"),
    ("warfarin", "CC(=O)CC(c1ccccc1)c1c(O)c2ccccc2oc1=O"),
    ("metformin", "CN(C)C(=N)NC(N)=N"),
    ("propranolol", "CC(C)NCC(O)COc1cccc2ccccc12"),
    ("metoprolol", "COCCc1ccc(OCC(O)CNC(C)C)cc1"),
    ("diphenhydramine", "CN(C)CCOC(c1ccccc1)c1ccccc1"),
    ("loratadine", "CCOC(=O)N1CCC(=C2c3ccc(Cl)cc3CCc3cccnc23)CC1"),
    ("diazepam", "CN1c2ccc(Cl)cc2C(=NCC1=O)c1ccccc1"),
    ("omeprazole", "CC1=CN=C(CS(=O)c2nc3cc(OC)ccc3[nH]2)C(=C1OC)C"),
    ("ranitidine", "CNC(=C[N+](=O)[O-])NCCSCc1ccc(CN(C)C)o1"),
    ("famotidine", "NC(=N)Nc1nc(CSCCC(N)=NS(N)(=O)=O)cs1"),
    ("gabapentin", "NCC1(CC(=O)O)CCCCC1"),
    ("tramadol", "COc1cccc(C2(O)CCCCC2CN(C)C)c1"),
    ("lidocaine", "CCN(CC)CC(=O)Nc1c(C)cccc1C"),
    ("fluoxetine", "CNCCC(Oc1ccc(C(F)(F)F)cc1)c1ccccc1"),
    ("sertraline", "CNC1CCC(c2ccc(Cl)c(Cl)c2)c2ccccc21"),
    ("nicotine", "CN1CCCC1c1cccnc1"),
    ("melatonin", "COc1ccc2[nH]c(CCNC(C)=O)cc2c1"),
    ("theophylline", "Cn1c(=O)c2[nH]cnc2n(C)c1=O"),
    ("atenolol", "CC(C)NCC(O)COc1ccc(CC(N)=O)cc1"),
    ("salbutamol", "CC(C)(C)NCC(O)c1ccc(O)c(CO)c1"),
    ("dopamine", "NCCc1ccc(O)c(O)c1"),
    ("serotonin", "NCCc1c[nH]c2ccc(O)cc12"),
    ("histamine", "NCCc1c[nH]cn1"),
]


def main() -> None:
    out_dir = Path(__file__).parent
    mols = []
    canon_seen: dict[str, str] = {}
    for name, smi in DRUGS:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            raise ValueError(f"{name}: could not parse SMILES {smi!r}")
        canon = Chem.MolToSmiles(mol)
        if canon in canon_seen:
            raise ValueError(f"{name}: duplicate structure of {canon_seen[canon]}")
        canon_seen[canon] = name
        mols.append((name, mol))

    smi_path = out_dir / "sample_drugs.smi"
    with open(smi_path, "w") as fh:
        for name, mol in mols:
            fh.write(f"{Chem.MolToSmiles(mol)}\t{name}\n")

    sdf_path = out_dir / "sample_drugs.sdf"
    writer = Chem.SDWriter(str(sdf_path))
    for name, mol in mols:
        mol.SetProp("_Name", name)
        qed = QED.qed(mol)
        mol.SetDoubleProp("MW", round(Descriptors.MolWt(mol), 2))
        mol.SetDoubleProp("LogP", round(Descriptors.MolLogP(mol), 2))
        mol.SetDoubleProp("TPSA", round(Descriptors.TPSA(mol), 2))
        mol.SetIntProp("HBD", Descriptors.NumHDonors(mol))
        mol.SetIntProp("HBA", Descriptors.NumHAcceptors(mol))
        mol.SetIntProp("RotB", Descriptors.NumRotatableBonds(mol))
        mol.SetDoubleProp("QED", round(qed, 3))
        mol.SetDoubleProp("Score", round(qed * 100, 1))
        writer.write(mol)
    writer.close()

    print(f"[done] {len(mols)} drugs -> {smi_path.name}, {sdf_path.name}")


if __name__ == "__main__":
    main()

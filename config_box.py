import os
import numpy as np
from settings_loader import get_selected_proteins

WATER_RESIDUES = {"HOH", "WAT", "H2O", "DOD", "TIP"}

proteins_dir = "proteins"
selected_proteins = get_selected_proteins()
pdbqt_files = [f"{p['pdb_id']}_{p['chain_id']}chain.pdbqt" for p in selected_proteins]
pdbqt_files = [f for f in pdbqt_files if os.path.exists(os.path.join(proteins_dir, f))]

def find_pocket_center_from_pdb(pdb_path):
    """Use co-crystallized ligand HETATM coords as pocket center. Falls back to protein center."""
    ligand_coords = []
    protein_coords = []

    with open(pdb_path, 'r') as f:
        for line in f:
            record = line[:6].strip()
            if record == "HETATM":
                res_name = line[17:20].strip().upper()
                if res_name not in WATER_RESIDUES:
                    try:
                        x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
                        ligand_coords.append([x, y, z])
                    except ValueError:
                        pass
            elif record == "ATOM":
                try:
                    x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
                    protein_coords.append([x, y, z])
                except ValueError:
                    pass

    if ligand_coords:
        center = np.array(ligand_coords).mean(axis=0)
        print(f"  → Pocket center from co-crystallized ligand ({len(ligand_coords)} atoms)")
        return center
    elif protein_coords:
        center = np.array(protein_coords).mean(axis=0)
        print(f"  → No ligand found, falling back to protein geometric center")
        return center
    else:
        return np.array([0.0, 0.0, 0.0])

for pdbqt_file in pdbqt_files:
    base_name = os.path.splitext(pdbqt_file)[0]

    # Look for the corresponding chain PDB file
    pdb_id = selected_proteins[pdbqt_files.index(pdbqt_file)]["pdb_id"]
    chain_id = selected_proteins[pdbqt_files.index(pdbqt_file)]["chain_id"]
    pdb_path = os.path.join(proteins_dir, f"{pdb_id}_{chain_id}chain.pdb")

    if not os.path.exists(pdb_path):
        print(f"Warning: {pdb_path} not found, skipping {pdbqt_file}")
        continue

    print(f"Processing {base_name}...")
    center = find_pocket_center_from_pdb(pdb_path)

    config = f"""receptor = {pdbqt_file}
center_x = {center[0]:.3f}
center_y = {center[1]:.3f}
center_z = {center[2]:.3f}
size_x = 25
size_y = 25
size_z = 25
exhaustiveness = 32
"""

    with open(os.path.join(proteins_dir, f"{base_name}_vina_config.txt"), 'w') as f:
        f.write(config)

    print(f"  → Config saved: center=({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")

print("All pocket-centered config files generated")

import os
import json
import numpy as np
from settings_loader import get_selected_proteins

proteins_dir = "proteins"
selected_proteins = get_selected_proteins()
pdbqt_files = [f"{p['pdb_id']}_{p['chain_id']}chain.pdbqt" for p in selected_proteins]
pdbqt_files = [f for f in pdbqt_files if os.path.exists(os.path.join(proteins_dir, f))]

for pdbqt_file in pdbqt_files:
    coords = []
    with open(os.path.join(proteins_dir, pdbqt_file), 'r') as f:
        for line in f:
            if line.startswith('ATOM'):
                coords.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])

    if coords:
        coords_arr = np.array(coords)
        center = coords_arr.mean(axis=0)
        size = (coords_arr.max(axis=0) - coords_arr.min(axis=0)) + 10  # 5Å padding each side
    else:
        center, size = [0, 0, 0], [30, 30, 30]

    base_name = os.path.splitext(pdbqt_file)[0]

    config = f"""receptor = {pdbqt_file}
center_x = {center[0]:.3f}
center_y = {center[1]:.3f}
center_z = {center[2]:.3f}
size_x = {size[0]:.3f}
size_y = {size[1]:.3f}
size_z = {size[2]:.3f}
exhaustiveness = 32
"""

    with open(os.path.join(proteins_dir, f"{base_name}_vina_config.txt"), 'w') as f:
        f.write(config)

    print(f"Whole-protein box config created for {base_name}")

print("All whole-protein config files generated")

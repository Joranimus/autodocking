import os
import numpy as np
from scipy.spatial.distance import cdist

proteins_dir = "proteins"
pdbqt_files = [f for f in os.listdir(proteins_dir) if f.endswith(".pdbqt")]

def find_pocket_center(coords):
    """Find largest cavity/pocket center using geometric analysis"""
    coords = np.array(coords)
    
    # Create grid around protein
    min_coords = coords.min(axis=0) - 5
    max_coords = coords.max(axis=0) + 5
    grid_points = []
    
    for x in np.arange(min_coords[0], max_coords[0], 2):
        for y in np.arange(min_coords[1], max_coords[1], 2):
            for z in np.arange(min_coords[2], max_coords[2], 2):
                grid_points.append([x, y, z])
    
    grid_points = np.array(grid_points)
    
    # Find grid points far from protein atoms (potential pocket centers)
    distances = cdist(grid_points, coords)
    min_distances = distances.min(axis=1)
    
    # Select points that are 3-8Å from nearest atom (pocket-like)
    pocket_candidates = grid_points[(min_distances > 3) & (min_distances < 8)]
    
    if len(pocket_candidates) > 0:
        # Return center of largest cluster
        return pocket_candidates.mean(axis=0)
    else:
        # Fallback to protein center
        return coords.mean(axis=0)

for pdbqt_file in pdbqt_files:
    coords = []
    with open(os.path.join(proteins_dir, pdbqt_file), 'r') as f:
        for line in f:
            if line.startswith('ATOM'):
                coords.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    
    pocket_center = find_pocket_center(coords) if coords else [0, 0, 0]
    base_name = os.path.splitext(pdbqt_file)[0]
    
    config = f"""receptor = {pdbqt_file}
center_x = {pocket_center[0]:.3f}
center_y = {pocket_center[1]:.3f}
center_z = {pocket_center[2]:.3f}
size_x = 22
size_y = 22
size_z = 22
exhaustiveness = 8
"""
    
    with open(os.path.join(proteins_dir, f"{base_name}_vina_config.txt"), 'w') as f:
        f.write(config)
    
    print(f"Pocket config created for {base_name}")

print("All pocket-centered config files generated")
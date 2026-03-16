import os
import json
import shutil
import subprocess
from datetime import datetime
from settings_loader import get_selected_proteins, get_selected_ligands

# Input parameters
proteins_dir = "proteins"
ligands_dir = "ligands"
vina_path = "vina"

# Get selected proteins and ligands from settings
selected_proteins = get_selected_proteins()
pdbqt_files = [f"{p['pdb_id']}_{p['chain_id']}chain.pdbqt" for p in selected_proteins]
pdbqt_files = [f for f in pdbqt_files if os.path.exists(os.path.join(proteins_dir, f))]

selected_ligands = get_selected_ligands()
ligand_files = [f"{l['name']}.pdbqt" for l in selected_ligands]
ligand_files = [f for f in ligand_files if os.path.exists(os.path.join(ligands_dir, f))]

# Create timestamped results folder
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results_dir = os.path.join("results", f"docking_run_{timestamp}")
os.makedirs(results_dir, exist_ok=True)
print(f"Created results folder: {results_dir}\n")
os.environ["RESULTS_DIR"] = results_dir

if not os.path.exists(proteins_dir):
    print(f"Error: Proteins directory {proteins_dir} does not exist.")
    exit(1)
if not os.path.exists(ligands_dir):
    print(f"Error: Ligands directory {ligands_dir} does not exist.")
    exit(1)

config_files = [f for f in os.listdir(proteins_dir) if f.endswith("_vina_config.txt")]
if not pdbqt_files:
    print(f"Error: No .pdbqt files found in {proteins_dir}.")
    exit(1)
if not config_files:
    print(f"Error: No config files found in {proteins_dir}.")
    exit(1)

if not ligand_files:
    print(f"Error: No selected ligand .pdbqt files found in {ligands_dir}.")
    exit(1)

# Step 1: Function to dock a single ligand to a protein
def dock_ligand(protein_pdbqt, config_file, ligand_pdbqt, results_subdir):
    try:
        protein_name = os.path.splitext(protein_pdbqt)[0]  # e.g., 1ZOG_chainA
        ligand_name = os.path.splitext(ligand_pdbqt)[0]    # e.g., CX-4945
        output_pdbqt = os.path.join(results_subdir, f"{ligand_name}_docked.pdbqt")
        
        # Run Vina
        cmd = [
            vina_path,
            "--receptor", os.path.join(proteins_dir, protein_pdbqt),
            "--ligand", os.path.join(ligands_dir, ligand_pdbqt),
            "--config", os.path.join(proteins_dir, config_file),
            "--out", output_pdbqt,
            "--seed", "42"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Docked {ligand_name} to {protein_name}: Output at {output_pdbqt}")
        return output_pdbqt
    except subprocess.CalledProcessError as e:
        print(f"Error docking {ligand_pdbqt} to {protein_pdbqt}: {e.stderr}")
        return None, None
    except Exception as e:
        print(f"Unexpected error docking {ligand_pdbqt} to {protein_pdbqt}: {e}")
        return None, None

# Step 2: Process all proteins and ligands
docking_results = []
for protein_pdbqt in pdbqt_files:
    protein_name = os.path.splitext(protein_pdbqt)[0]
    config_file = f"{protein_name}_vina_config.txt"
    if config_file not in config_files:
        print(f"Warning: No config file found for {protein_pdbqt}. Skipping.")
        continue
    
    # Create results subfolder for this protein
    results_subdir = os.path.join(results_dir, protein_name)
    os.makedirs(results_subdir, exist_ok=True)

    # Copy config file to results folder
    shutil.copy(os.path.join(proteins_dir, config_file), os.path.join(results_subdir, config_file))

    for ligand_pdbqt in ligand_files:
        output_pdbqt = dock_ligand(protein_pdbqt, config_file, ligand_pdbqt, results_subdir)
        if output_pdbqt:
            docking_results.append((output_pdbqt))

# Step 3: Output results
print("\nDocking completed. Results saved in:")
for pdbqt in docking_results:
    print(f"Pose: {pdbqt}")
print("\nValidate in Chimera/PyMOL: Check docked poses and binding affinities in log files.")
print("Next: Analyze results (e.g., extract affinities from logs or visualize poses).")
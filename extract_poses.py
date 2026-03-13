import os
import subprocess

# Configuration
results_dir = "results"
obabel_path = r"C:\Users\Jora\Miniconda3\envs\docking_py3\Library\bin\obabel.exe"

# Find all docked PDBQT files
pdbqt_files = []
for root, dirs, files in os.walk(results_dir):
    for file in files:
        if file.endswith("_docked.pdbqt"):
            pdbqt_files.append(os.path.join(root, file))

if not pdbqt_files:
    print("No docked PDBQT files found")
    exit(1)

for pdbqt_file in pdbqt_files:
    base_name = os.path.splitext(os.path.basename(pdbqt_file))[0]
    ligand_name = base_name.replace('_docked', '')
    
    # Create folder for this ligand's poses
    poses_dir = os.path.join(os.path.dirname(pdbqt_file), ligand_name)
    os.makedirs(poses_dir, exist_ok=True)
    
    # Extract all poses to separate PDB files
    output_pattern = os.path.join(poses_dir, f"{ligand_name}_pose_.pdb")
    result = subprocess.run([
        obabel_path, "-ipdbqt", pdbqt_file, "-opdb", "-O", output_pattern, "-m"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"Extracted poses from {os.path.basename(pdbqt_file)} to {poses_dir}")
    else:
        print(f"Error extracting {pdbqt_file}: {result.stderr}")

print("\nAll poses extracted to PDB format")
print("Each ligand's poses saved in separate folders")

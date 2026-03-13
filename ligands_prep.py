from rdkit import Chem
from rdkit.Chem import AllChem
from openbabel import openbabel
import os
import subprocess
import sys
import json
import shutil


# Set default JSON file path (relative to c:\Users\Jora\Desktop\DOCKING\Programm)
DEFAULT_JSON = "temp_ligands.json"

# Read JSON input file
input_json = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
ligands = []

try:
    with open(input_json, "r") as f:
        ligands = json.load(f)
except FileNotFoundError:
    print(f"Error: JSON file '{input_json}' not found. Ensure it exists in {os.path.dirname(input_json)}.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in '{input_json}': {e}")
    sys.exit(1)

# Validate input
if not ligands:
    print("Error: No ligands found in input JSON.")
    sys.exit(1)

# Output directory (relative to Programm)
output_dir = "ligands"
os.makedirs(output_dir, exist_ok=True)

# Find OpenBabel executable dynamically
obabel_path = shutil.which("obabel")
if not obabel_path:
    print("Error: OpenBabel 'obabel' executable not found in PATH. Ensure openbabel-wheel is installed and PATH includes the environment's bin directory.")
    sys.exit(1)

# Path to OpenBabel executable in docking_py3 environment
obabel_path = r"C:\Users\Jora\Miniconda3\envs\docking_py3\Library\bin\obabel.exe"

# Verify OpenBabel
if not os.path.exists(obabel_path):
    print(f"Error: OpenBabel not found at '{obabel_path}'. Install openbabel-wheel or adjust path.")
    sys.exit(1)

# Ligand preparation function
def prepare_ligand(smiles, ligand_name, output_dir=output_dir):
    try:
        # Convert SMILES to 3D structure
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES for {ligand_name}: {smiles}")
        mol = Chem.AddHs(mol)  # Add hydrogens
        AllChem.EmbedMolecule(mol, randomSeed=42)  # Generate 3D coordinates
        AllChem.MMFFOptimizeMolecule(mol, maxIters=20000)  # Optimize with MMFF
        
        # Save as SDF (preserves bonds)
        sdf_file = os.path.join(output_dir, f"{ligand_name}.sdf")
        writer = Chem.SDWriter(sdf_file)
        writer.write(mol)
        writer.close()
        
        # Convert to PDBQT with OpenBabel
        pdbqt_file = os.path.join(output_dir, f"{ligand_name}.pdbqt")
        result = subprocess.run([
            obabel_path, "-isdf", sdf_file, "-opdbqt", "-O", pdbqt_file,
            "--partialcharge", "gasteiger"
        ], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"OpenBabel failed for {ligand_name}: {result.stderr}")
        
        os.remove(sdf_file)
        
        # Clean up PDB file
        #os.remove(pdb_file)
        print(f"Prepared ligand: {pdbqt_file}")
        return pdbqt_file
    except Exception as e:
        print(f"Error preparing ligand {ligand_name}: {e}")
        return None

# Process all ligands
output_ligands = []
for ligand in ligands:
    pdbqt_file = prepare_ligand(ligand["smiles"], ligand["name"])
    if pdbqt_file:
        output_ligands.append(pdbqt_file)

# Output results
print("\nLigands prepared:")
for pdbqt_file in output_ligands:
    print(pdbqt_file)
print("\nValidate in Chimera/PyMOL: Check 3D structure and protonation.")
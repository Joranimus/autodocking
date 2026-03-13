import Bio.PDB
from Bio.PDB import PDBList, PDBParser, PDBIO, Select
import pdbfixer
from openmm.app import PDBFile
import os
import subprocess
import sys
import json

"""
# Read JSON input file from command-line argument
if len(sys.argv) != 2:
    print("Usage: python batch_prepare_proteins.py <input_json>")
    sys.exit(1)

input_json = sys.argv[1]
with open(input_json, "r") as f:
    proteins = json.load(f)
"""

# Set default JSON file path (relative to c:\Users\Jora\Desktop\DOCKING\Programm)
DEFAULT_JSON = "temp_proteins.json"

# Read JSON input file
input_json = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
proteins = []

try:
    with open(input_json, "r") as f:
        proteins = json.load(f)
except FileNotFoundError:
    print(f"Error: JSON file '{input_json}' not found. Ensure it exists in {os.path.dirname(input_json)}.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in '{input_json}': {e}")
    sys.exit(1)

# Validate input
if not proteins:
    print("Error: No proteins found in input JSON.")
    sys.exit(1)

# Output directory
output_dir = "proteins"
os.makedirs(output_dir, exist_ok=True)

# Path to AutoDock Tools prepare_receptor4.py and Python 2.7
adt_script = r"C:\Program Files (x86)\MGLTools-1.5.7\Lib\site-packages\AutoDockTools\Utilities24\prepare_receptor4.py"
mgltools_lib = r"C:\Program Files (x86)\MGLTools-1.5.7\Lib\site-packages"
python2_path = r"C:\Users\Jora\Miniconda3\envs\docking_py2\python.exe"
python2_lib = r"C:\Users\Jora\Miniconda3\envs\docking_py2\Lib\site-packages"

# Verify paths
if not os.path.exists(adt_script):
    print(f"Error: {adt_script} not found. Install MGLTools or adjust path.")
    sys.exit(1)
if not os.path.exists(python2_path):
    print(f"Error: {python2_path} not found. Install Python 2.7.11 or adjust path.")
    sys.exit(1)
if not os.path.exists(mgltools_lib):
    print(f"Error: {mgltools_lib} not found. Verify MGLTools installation.")
    sys.exit(1)
if not os.path.exists(python2_lib):
    print(f"Error: {python2_lib} not found. Verify Python 2.7.11 installation.")
    sys.exit(1)

# Protein preparation function
def prepare_protein(pdb_id, chain_id, output_dir):
    try:
        # Download PDB file
        pdb_list = PDBList()
        pdb_file = pdb_list.retrieve_pdb_file(pdb_id, pdir=output_dir, file_format="pdb")
        print(f"Downloaded PDB file: {pdb_file}")
        
        # Isolate specific chain
        class ChainSelect(Select):
            def __init__(self, chain_id):
                self.chain_id = chain_id
            def accept_chain(self, chain):
                return chain.id == self.chain_id
        
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure(pdb_id, pdb_file)
        io = PDBIO()
        io.set_structure(structure)
        output_pdb = os.path.join(output_dir, f"{pdb_id}_{chain_id}chain.pdb")
        io.save(output_pdb, ChainSelect(chain_id))
        print(f"Isolated chain {chain_id}: {output_pdb}")
        
        # Clean and fix structure with PDBFixer
        fixer = pdbfixer.PDBFixer(filename=output_pdb)
        fixer.removeHeterogens(keepWater=False)
        fixer.findMissingResidues()
        fixer.findNonstandardResidues()
        fixer.replaceNonstandardResidues()
        fixer.findMissingAtoms()
        fixer.addMissingAtoms()
        fixer.addMissingHydrogens(pH=7.0)
        print(f"Fixed structure for {pdb_id}")

        # Save fixed PDB
        fixed_pdb = os.path.join(output_dir, f"{pdb_id}_fixed.pdb")
        with open(fixed_pdb, "w") as f:
            PDBFile.writeFile(fixer.topology, fixer.positions, f)
        print(f"Saved fixed PDB: {fixed_pdb}")

        # Convert to PDBQT with AutoDock Tools using Python 2.7
        output_pdbqt = os.path.join(output_dir, f"{pdb_id}_{chain_id}chain.pdbqt")
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{python2_lib};{mgltools_lib};{env.get('PYTHONPATH', '')}"
        result = subprocess.run([
            python2_path, adt_script, "-r", fixed_pdb, "-o", output_pdbqt, "-A", "hydrogens"
        ], env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ADT preparation failed for {pdb_id}: {result.stderr}")
        print(f"Generated rigid PDBQT: {output_pdbqt}")
        
        # Clean up intermediate files
        os.remove(pdb_file)
        #os.remove(output_pdb)
        #os.remove(fixed_pdb)
        print(f"Cleaned up intermediate files for {pdb_id}")
        
        return output_pdbqt
    except Exception as e:
        print(f"Error preparing protein {pdb_id}: {e}")
        return None

# Process all proteins
prepared_proteins = []
for protein in proteins:
    pdbqt_file = prepare_protein(protein["pdb_id"], protein["chain_id"], output_dir)
    if pdbqt_file:
        prepared_proteins.append(pdbqt_file)

# Output results
print("\nPrepared proteins:")
for pdbqt_file in prepared_proteins:
    print(pdbqt_file)
print("\nValidate in Chimera/PyMOL: Check chain, hydrogens, and no ligands/waters.")
print("Next: Generate grid box configs with generate_vina_gridbox_noligand.py.")
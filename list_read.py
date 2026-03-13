import os
import json
import subprocess

# Paths relative to script (c:\Users\Jora\Desktop\DOCKING\Programm)
protein_prep_script = "batch_prepare_proteins.py"
ligand_prep_script = "prepare_ligands.py"
input_file = "input_lists.txt"
proteins_dir = "proteins"
ligands_dir = "ligands"

# Create output directories
os.makedirs(proteins_dir, exist_ok=True)
os.makedirs(ligands_dir, exist_ok=True)

# Read input file
proteins = []
ligands = []
current_section = None

with open(input_file, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line == "[Proteins]":
            current_section = "proteins"
            continue
        if line == "[Ligands]":
            current_section = "ligands"
            continue
        if current_section == "proteins":
            pdb_id, chain_id = line.split()
            proteins.append({"pdb_id": pdb_id, "chain_id": chain_id})
        elif current_section == "ligands":
            smiles, name = line.rsplit(" ", 1)
            ligands.append({"smiles": smiles, "name": name})

# Validate inputs
if not proteins:
    print("Error: No proteins found in [Proteins] section.")
    exit(1)
if not ligands:
    print("Error: No ligands found in [Ligands] section.")
    exit(1)

# Save proteins to JSON
proteins_json = "temp_proteins.json"
with open(proteins_json, "w") as f:
    json.dump(proteins, f)

# Save ligands to JSON
ligands_json = "temp_ligands.json"
with open(ligands_json, "w") as f:
    json.dump(ligands, f)

print("List read successfully.")
import os
import json

input_file = "input_lists.txt"
proteins_dir = "proteins"
ligands_dir = "ligands"

os.makedirs(proteins_dir, exist_ok=True)
os.makedirs(ligands_dir, exist_ok=True)

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

if not proteins:
    print("Error: No proteins found in [Proteins] section.")
    exit(1)
if not ligands:
    print("Error: No ligands found in [Ligands] section.")
    exit(1)

# Save ligands into settings.json
settings_file = "settings.json"
with open(settings_file, "r") as f:
    settings = json.load(f)

settings["ligands"] = ligands

with open(settings_file, "w") as f:
    json.dump(settings, f, indent=4)

print(f"List read successfully: {len(proteins)} proteins, {len(ligands)} ligands saved to settings.json")

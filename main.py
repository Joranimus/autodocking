import os
import sys
import json
import subprocess
import questionary

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "steps": {
        "RUN_LIST_READ": True,
        "RUN_PROTEIN_PREP": True,
        "RUN_CONFIG_BOX": True,
        "RUN_LIGAND_PREP": True,
        "RUN_DOCKING": True,
        "RUN_EXTRACT_POSES": False,
        "RUN_EXTRACT_RESULTS": True
    },
    "box_mode": "pocket",
    "selected_proteins": [],
    "selected_ligands": []
}

STEP_LABELS = {
    "RUN_LIST_READ":       "List Reading",
    "RUN_PROTEIN_PREP":    "Protein Preparation",
    "RUN_CONFIG_BOX":      "Config Box Generation",
    "RUN_LIGAND_PREP":     "Ligand Preparation",
    "RUN_DOCKING":         "AutoDock Vina Docking",
    "RUN_EXTRACT_POSES":   "Extract Poses to PDB",
    "RUN_EXTRACT_RESULTS": "Extract Results Summary"
}

STEP_SCRIPTS = {
    "RUN_LIST_READ":       "list_read.py",
    "RUN_PROTEIN_PREP":    "proteins_prep.py",
    "RUN_CONFIG_BOX":      None,  # dynamic based on box_mode
    "RUN_LIGAND_PREP":     "ligands_prep.py",
    "RUN_DOCKING":         "dock_vina.py",
    "RUN_EXTRACT_POSES":   "extract_poses.py",
    "RUN_EXTRACT_RESULTS": "extract_results.py"
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def read_proteins_from_input():
    proteins = []
    with open("input_lists.txt", "r") as f:
        in_proteins = False
        for line in f:
            line = line.strip()
            if line == "[Proteins]":
                in_proteins = True
                continue
            if line.startswith("["):
                in_proteins = False
            if in_proteins and line:
                pdb_id, chain_id = line.split()
                proteins.append({"pdb_id": pdb_id, "chain_id": chain_id})
    return proteins

def read_ligands_from_settings(settings):
    return settings.get("ligands", [])

def ask_user_choices(settings):
    # Ask if user wants to reload input_lists.txt
    reload_input = questionary.confirm(
        "Reload proteins/ligands from input_lists.txt?",
        default=False
    ).ask()
    if reload_input is None:
        sys.exit(0)

    # Force list_read step on if reloading
    last_steps = settings.get("steps", DEFAULT_SETTINGS["steps"])
    if reload_input:
        last_steps["RUN_LIST_READ"] = True
    step_choices = [
        questionary.Choice(label, checked=last_steps.get(key, False))
        for key, label in STEP_LABELS.items()
    ]
    selected_labels = questionary.checkbox(
        "Select pipeline steps to run:",
        choices=step_choices
    ).ask()

    if selected_labels is None:
        sys.exit(0)

    steps = {key: (label in selected_labels) for key, label in STEP_LABELS.items()}
    if reload_input:
        steps["RUN_LIST_READ"] = True

    # Box mode
    box_mode = questionary.select(
        "Select box mode:",
        choices=["pocket", "whole"],
        default=settings.get("box_mode", "pocket")
    ).ask()

    # Protein selection
    all_proteins = read_proteins_from_input()
    protein_labels = [f"{p['pdb_id']} (chain {p['chain_id']})" for p in all_proteins]
    last_selected = [f"{p['pdb_id']} (chain {p['chain_id']})" for p in settings.get("selected_proteins", [])]

    protein_choices = [
        questionary.Choice(label, checked=(label in last_selected))
        for label in protein_labels
    ]
    selected_labels = questionary.checkbox(
        "Select proteins to dock:",
        choices=protein_choices
    ).ask()

    if not selected_labels:
        print("No proteins selected. Exiting.")
        sys.exit(0)

    selected_proteins = [p for p, label in zip(all_proteins, protein_labels) if label in selected_labels]

    # Ligand selection
    all_ligands = read_ligands_from_settings(settings)
    if not all_ligands:
        if reload_input:
            print("⚠ Ligands will be loaded from input_lists.txt — all ligands selected by default.")
            selected_ligands = []  # will be populated after list_read runs
        else:
            print("No ligands in settings.json. Please reload input_lists.txt first.")
            sys.exit(0)
    else:
        ligand_labels = [l["name"] for l in all_ligands]
        last_selected_ligands = [l["name"] for l in settings.get("selected_ligands", [])]

        ligand_choices = [
            questionary.Choice(label, checked=(label in last_selected_ligands or not last_selected_ligands))
            for label in ligand_labels
        ]
        selected_ligand_labels = questionary.checkbox(
            "Select ligands to dock:",
            choices=ligand_choices
        ).ask()

        if not selected_ligand_labels:
            print("No ligands selected. Exiting.")
            sys.exit(0)

        selected_ligands = [l for l in all_ligands if l["name"] in selected_ligand_labels]

    return steps, box_mode, selected_proteins, selected_ligands

def run_step(step_name, script_name):
    print(f"\n{'='*60}")
    print(f"Running: {step_name}")
    print(f"{'='*60}")
    try:
        subprocess.run([sys.executable, script_name], check=True, text=True)
        print(f"✓ {step_name} completed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ Error in {step_name}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error in {step_name}: {e}")
        return False

def main():
    print("="*60)
    print("MOLECULAR DOCKING PIPELINE")
    print("="*60)

    settings = load_settings()
    steps, box_mode, selected_proteins, selected_ligands = ask_user_choices(settings)

    # Save choices for next run
    save_settings({"steps": steps, "box_mode": box_mode, "selected_proteins": selected_proteins, "selected_ligands": selected_ligands, "ligands": settings.get("ligands", [])})
    print(f"\nSelected {len(selected_proteins)} protein(s), {len(selected_ligands)} ligand(s), box mode: {box_mode}")

    for key, label in STEP_LABELS.items():
        if not steps[key]:
            print(f"\n⊘ Skipping: {label}")
            continue

        # Determine script
        if key == "RUN_CONFIG_BOX":
            script = "config_box_whole.py" if box_mode == "whole" else "config_box.py"
        else:
            script = STEP_SCRIPTS[key]

        # After list_read, overwrite temp_proteins.json with selection
        if not run_step(label, script):
                print(f"\n✗ Pipeline stopped due to error in {label}")
                return
        # After list_read, if no ligands were selected (first reload), select all
        if key == "RUN_LIST_READ" and not selected_ligands:
            reloaded = load_settings()
            selected_ligands = reloaded.get("ligands", [])
            save_settings({**reloaded, "selected_ligands": selected_ligands})
            print(f"✓ Auto-selected all {len(selected_ligands)} ligands from input_lists.txt")

    print("\n" + "="*60)
    print("✓ PIPELINE COMPLETED SUCCESSFULLY")
    print("="*60)
    print("\nResults available in 'results' directory:")
    print("  - Docked poses in PDB format (organized by ligand folders)")
    print("  - Summary files with binding affinities (*_summary.txt)")
    print("\nValidate docked poses in Chimera/PyMOL")

if __name__ == "__main__":
    main()

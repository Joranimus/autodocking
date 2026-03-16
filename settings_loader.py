import json
import os

SETTINGS_FILE = "settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        raise FileNotFoundError(f"settings.json not found. Run main.py first.")
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def get_selected_proteins():
    return load_settings().get("selected_proteins", [])

def get_selected_ligands():
    return load_settings().get("selected_ligands", [])

def get_ligands():
    return load_settings().get("ligands", [])

def get_box_mode():
    return load_settings().get("box_mode", "pocket")

def get_steps():
    return load_settings().get("steps", {})

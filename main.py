import os
import sys
import subprocess

# ==================== SETUP SECTION ====================
# Choose which steps to run (True/False)
RUN_LIST_READ = True          # Read input_lists.txt and create JSON files
RUN_PROTEIN_PREP = True       # Prepare proteins (download, fix, convert to PDBQT)
RUN_CONFIG_BOX = True         # Generate Vina config files with grid boxes
RUN_LIGAND_PREP = True        # Prepare ligands (SMILES to PDBQT)
RUN_DOCKING = True            # Run AutoDock Vina docking
RUN_EXTRACT_POSES = True      # Extract docking poses to PDB files
RUN_EXTRACT_RESULTS = True    # Generate summary files with binding affinities

# ==================== PIPELINE EXECUTION ====================

def run_step(step_name, script_name):
    """Execute a pipeline step"""
    print(f"\n{'='*60}")
    print(f"Running: {step_name}")
    print(f"{'='*60}")
    try:
        result = subprocess.run([sys.executable, script_name], check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings/Errors:\n{result.stderr}")
        print(f"✓ {step_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error in {step_name}:")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"✗ Unexpected error in {step_name}: {e}")
        return False

def main():
    print("="*60)
    print("MOLECULAR DOCKING PIPELINE")
    print("="*60)
    
    # Step 1: Read input lists
    if RUN_LIST_READ:
        if not run_step("List Reading", "list_read.py"):
            print("\n✗ Pipeline stopped due to error in list reading")
            return
    else:
        print("\n⊘ Skipping: List Reading")
    
    # Step 2: Protein preparation
    if RUN_PROTEIN_PREP:
        if not run_step("Protein Preparation", "proteins_prep.py"):
            print("\n✗ Pipeline stopped due to error in protein preparation")
            return
    else:
        print("\n⊘ Skipping: Protein Preparation")
    
    # Step 3: Config box generation
    if RUN_CONFIG_BOX:
        if not run_step("Config Box Generation", "config_box.py"):
            print("\n✗ Pipeline stopped due to error in config box generation")
            return
    else:
        print("\n⊘ Skipping: Config Box Generation")
    
    # Step 4: Ligand preparation
    if RUN_LIGAND_PREP:
        if not run_step("Ligand Preparation", "ligands_prep.py"):
            print("\n✗ Pipeline stopped due to error in ligand preparation")
            return
    else:
        print("\n⊘ Skipping: Ligand Preparation")
    
    # Step 5: Docking
    if RUN_DOCKING:
        if not run_step("AutoDock Vina Docking", "dock_vina.py"):
            print("\n✗ Pipeline stopped due to error in docking")
            return
    else:
        print("\n⊘ Skipping: Docking")
    
    # Step 6: Extract poses
    if RUN_EXTRACT_POSES:
        if not run_step("Extract Poses to PDB", "extract_poses.py"):
            print("\n✗ Pipeline stopped due to error in pose extraction")
            return
    else:
        print("\n⊘ Skipping: Extract Poses")
    
    # Step 7: Extract results summary
    if RUN_EXTRACT_RESULTS:
        if not run_step("Extract Results Summary", "extract_results.py"):
            print("\n✗ Pipeline stopped due to error in results extraction")
            return
    else:
        print("\n⊘ Skipping: Extract Results")
    
    # Pipeline completed
    print("\n" + "="*60)
    print("✓ PIPELINE COMPLETED SUCCESSFULLY")
    print("="*60)
    print("\nResults available in 'results' directory:")
    print("  - Docked poses in PDB format (organized by ligand folders)")
    print("  - Summary files with binding affinities (*_summary.txt)")
    print("\nValidate docked poses in Chimera/PyMOL")

if __name__ == "__main__":
    main()

import os
import re
from datetime import datetime

# Process all docking runs in results folder
base_results_dir = "results"

if not os.path.exists(base_results_dir):
    print(f"Error: Results directory '{base_results_dir}' does not exist.")
    exit(1)

# Find all docking run folders
docking_runs = [f for f in os.listdir(base_results_dir) 
                if os.path.isdir(os.path.join(base_results_dir, f)) and f.startswith("docking_run_")]

if not docking_runs:
    print(f"Error: No docking run folders found in '{base_results_dir}'.")
    exit(1)

print(f"Found {len(docking_runs)} docking run(s) to process\n")

total_summaries = 0

# Process each docking run
for docking_run in sorted(docking_runs):
    results_dir = os.path.join(base_results_dir, docking_run)
    print(f"Processing docking run: {docking_run}")
    
    # Find protein folders inside this docking run
    protein_folders = [f for f in os.listdir(results_dir) 
                      if os.path.isdir(os.path.join(results_dir, f))]
    
    if not protein_folders:
        print(f"  No protein folders found in {docking_run}")
        continue
    
    # Process each protein folder in this docking run
    for protein_folder in protein_folders:
        protein_path = os.path.join(results_dir, protein_folder)
        
        print(f"  Processing protein folder: {protein_folder}")
        
        # Find all docked PDBQT files
        pdbqt_files = [f for f in os.listdir(protein_path) if f.endswith("_docked.pdbqt")]
        
        print(f"    Found {len(pdbqt_files)} docked PDBQT files")
        
        if not pdbqt_files:
            print(f"    Skipping {protein_folder} - no docked files found")
            continue
        
        # Create summary file
        summary_file = os.path.join(protein_path, f"{protein_folder}_summary.txt")
        
        with open(summary_file, 'w') as out:
            out.write(f"DOCKING RESULTS SUMMARY FOR {protein_folder}\n")
            out.write("="*80 + "\n\n")
            
            all_results = []
            
            for pdbqt_file in sorted(pdbqt_files):
                ligand_name = pdbqt_file.replace("_docked.pdbqt", "")
                pdbqt_path = os.path.join(protein_path, pdbqt_file)
                
                poses = []
                with open(pdbqt_path, 'r') as f:
                    for line in f:
                        if 'REMARK VINA RESULT:' in line:
                            parts = line.split()
                            affinity = float(parts[3])
                            rmsd_lb = float(parts[4])
                            rmsd_ub = float(parts[5])
                            poses.append((affinity, rmsd_lb, rmsd_ub))
                
                if poses:
                    best_affinity = poses[0][0]
                    all_results.append((ligand_name, best_affinity, len(poses), poses))
            
            # Sort by best affinity
            all_results.sort(key=lambda x: x[1])
            
            # Write summary table
            out.write(f"{'Ligand':<20} {'Best Affinity':<15} {'Poses':<10}\n")
            out.write("-"*80 + "\n")
            
            for ligand_name, best_affinity, num_poses, poses in all_results:
                out.write(f"{ligand_name:<20} {best_affinity:<15.2f} {num_poses:<10}\n")
            
            out.write("\n" + "="*80 + "\n\n")
            
            # Write detailed results
            out.write("DETAILED RESULTS\n")
            out.write("="*80 + "\n\n")
            
            for ligand_name, best_affinity, num_poses, poses in all_results:
                out.write(f"Ligand: {ligand_name}\n")
                out.write(f"  Best Affinity: {best_affinity:.2f} kcal/mol\n")
                out.write(f"  Number of Poses: {num_poses}\n")
                out.write(f"  All Poses:\n")
                for i, (aff, rmsd_lb, rmsd_ub) in enumerate(poses, 1):
                    out.write(f"    Pose {i}: Affinity={aff:.2f} kcal/mol, RMSD_lb={rmsd_lb:.2f}, RMSD_ub={rmsd_ub:.2f}\n")
                out.write("\n")
        
        print(f"    Summary created: {summary_file}")
        total_summaries += 1
    
    print()  # Empty line between docking runs

if total_summaries == 0:
    print("Warning: No summaries were created. Check if docked PDBQT files exist.")
else:
    print(f"All summaries generated ({total_summaries} files total)")

"""
Robustness Check Orchestrator

This script runs the biofuel policy optimization model with configurable input/output folders.
It handles the complete workflow: generating intermediate files and running the optimization.

Usage:
    # Run baseline only (k=0, uses range(1))
    python print_results.py
    
    # Run full robustness check (k=0-4, uses range(5))
    python print_results.py --k-range 5
    
    # Run with specific scenario folders and full robustness
    python print_results.py --input-folder data_input_baseline --output-folder results_baseline --k-range 5
    
    # Run with scenario name (automatically maps to data_input_<scenario> and results_<scenario>)
    python print_results.py --scenario baseline
    python print_results.py --scenario baseline --k-range 5
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def validate_input_folder(input_folder: str, script_dir: Path) -> bool:
    """
    Validate that the input folder exists and contains required files.
    
    Args:
        input_folder: Name of the input folder
        script_dir: Path to the script directory
        
    Returns:
        True if valid, False otherwise
    """
    input_path = script_dir / input_folder
    
    if not input_path.exists():
        print(f"ERROR: Input folder '{input_folder}' does not exist!")
        print(f"Expected path: {input_path}")
        return False
    
    # Check for required input files
    required_files = [
        "biofuel_input.xlsx",
        "feedstock_supply.xlsx",
        "fuel_demand.xlsx",
        "Policy_constraints.xlsx",
        "state_tax.xlsx"
    ]
    
    missing_files = []
    for file in required_files:
        if not (input_path / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"ERROR: Missing required input files in '{input_folder}':")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    return True


def cleanup_unnecessary_files(output_folder: str, script_dir: Path) -> None:
    """
    Delete unnecessary output files that are not needed for analysis.
    
    Args:
        output_folder: Name of the output folder
        script_dir: Path to the script directory
    """
    output_path = script_dir / output_folder
    
    # Files to delete
    unnecessary_files = [
        "objective_values.xlsx",
        "variables_best.xlsx",
        "variables_best.txt",
        "demand_quantity_best.xlsx",
        "terms_breakdown_best.xlsx"
    ]
    
    deleted_count = 0
    for file_name in unnecessary_files:
        file_path = output_path / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                deleted_count += 1
                print(f"  Deleted: {file_name}")
            except Exception as e:
                print(f"  Warning: Could not delete {file_name}: {e}")
    
    if deleted_count > 0:
        print(f"✓ Cleaned up {deleted_count} unnecessary file(s)\n")


def run_robustness_check(input_folder: str, output_folder: str, script_dir: Path, k_range: int = 1) -> int:
    """
    Run complete robustness check workflow.
    
    Args:
        input_folder: Name of the input folder
        output_folder: Name of the output folder
        script_dir: Path to the script directory
        k_range: Number of robustness iterations (1 for baseline, 5 for full robustness check)
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print(f"\n{'='*60}")
    print(f"BIOFUEL POLICY OPTIMIZATION")
    print(f"{'='*60}")
    print(f"Input folder:  {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"Robustness iterations: {k_range}")
    print(f"{'='*60}\n")
    
    # Validate input folder
    if not validate_input_folder(input_folder, script_dir):
        return 1
    
    print("✓ All required input files found\n")
    
    # Step 1: Generate intermediate files
    print("Step 1: Generating intermediate input files...")
    print("-" * 60)
    try:
        subprocess.run(
            [sys.executable, "generate_outputs.py", "--input-folder", input_folder],
            cwd=script_dir,
            check=True
        )
        print("-" * 60)
        print("✓ Intermediate files generated successfully\n")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to generate intermediate files: {e}")
        return 1
    
    # Step 2: Run all optimization models in policy_python folder
    print("Step 2: Running optimization models...")
    print("-" * 60)
    
    # Get all Python files in policy_python folder
    policy_python_dir = script_dir / "policy_python"
    if not policy_python_dir.exists():
        print(f"ERROR: policy_python folder not found at {policy_python_dir}")
        return 1
    
    python_files = sorted([f for f in policy_python_dir.glob("*.py")])
    
    if not python_files:
        print(f"ERROR: No Python files found in policy_python folder")
        return 1
    
    print(f"Found {len(python_files)} model(s) to run:")
    for py_file in python_files:
        print(f"  - {py_file.name}")
    print()
    
    # Run each Python file
    failed_models = []
    for py_file in python_files:
        print(f"Running {py_file.name}...")
        try:
            subprocess.run(
                [sys.executable, str(py_file), 
                 "--input-folder", input_folder,
                 "--output-folder", output_folder,
                 "--k-range", str(k_range)],
                cwd=script_dir,
                check=True
            )
            print(f"✓ {py_file.name} completed successfully\n")
        except subprocess.CalledProcessError as e:
            print(f"✗ {py_file.name} failed: {e}\n")
            failed_models.append(py_file.name)
    
    print("-" * 60)
    
    if failed_models:
        print(f"\n✗ {len(failed_models)} model(s) failed:")
        for model in failed_models:
            print(f"  - {model}")
        print(f"\n✓ {len(python_files) - len(failed_models)}/{len(python_files)} model(s) completed successfully")
        print(f"✓ Results saved to: {output_folder}/\n")
        return 1
    else:
        print(f"\n✓ All {len(python_files)} model(s) completed successfully")
        print(f"\nStep 3: Cleaning up unnecessary files...")
        print("-" * 60)
        cleanup_unnecessary_files(output_folder, script_dir)
        print(f"✓ Results saved to: {output_folder}/\n")
        return 0
    
    print(f"{'='*60}")
    print(f"COMPLETED SUCCESSFULLY")
    print(f"{'='*60}\n")
    
    return 0


def main():
    """Main entry point for the robustness check orchestrator"""
    
    script_dir = Path(__file__).parent
    
    parser = argparse.ArgumentParser(
        description='Run biofuel policy optimization with configurable input/output folders.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run baseline only (default, k=0)
  python print_results.py
  
  # Run full robustness check (k=0-4, all 5 iterations)
  python print_results.py --k-range 5
  
  # Run with explicit folder names
  python print_results.py --input-folder data_input_baseline --output-folder results_baseline
  
  # Run with explicit folders and full robustness
  python print_results.py --input-folder data_input_baseline --output-folder results_baseline --k-range 5
  
  # Run with scenario name (auto-maps to data_input_<scenario> and results_<scenario>)
  python print_results.py --scenario baseline
  
  # Run with scenario and full robustness
  python print_results.py --scenario baseline --k-range 5
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--scenario',
        type=str,
        help='Scenario name (e.g., baseline, high_cost). Auto-maps to data_input_<scenario> and results_<scenario>'
    )
    group.add_argument(
        '--input-folder',
        type=str,
        default='data_input',
        help='Name of the input folder (default: data_input)'
    )
    
    parser.add_argument(
        '--output-folder',
        type=str,
        help='Name of the output folder (default: results, or results_<scenario> if --scenario is used)'
    )
    
    parser.add_argument(
        '--k-range',
        type=int,
        default=1,
        choices=[1, 5],
        help='Number of robustness iterations: 1 for baseline only, 5 for full robustness check (default: 1)'
    )
    
    args = parser.parse_args()
    
    # Determine input and output folders
    if args.scenario:
        # Scenario mode: auto-map folder names
        if args.scenario == "default":
            input_folder = "data_input"
            output_folder = "results"
        else:
            input_folder = f"data_input_{args.scenario}"
            output_folder = f"results_{args.scenario}"
    else:
        # Manual mode: use specified folders
        input_folder = args.input_folder
        output_folder = args.output_folder if args.output_folder else "results"
    
    # Run the robustness check
    exit_code = run_robustness_check(input_folder, output_folder, script_dir, args.k_range)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
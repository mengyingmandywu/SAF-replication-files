"""
Run all plotting scripts in `plot_python/` using a specified results folder and write outputs to a single results_plot file.

Usage:
        python plot_output.py [--results-suffix SUFFIX] [--columns COL1,COL2] [--dry-run]

This meta-script controls where plotting scripts read data from and write output to by:
    - Passing --results-dir to specify the input folder (e.g., results, results_baseline)
    - Passing --output-file to specify the output Excel file (e.g., results_plot.xlsx, results_plot_baseline.xlsx)

The meta-script has full control over these parameters and overrides any defaults in individual plotting scripts.

Examples:
        python plot_output.py
        -> Uses results/ folder, writes to results_plot.xlsx

        python plot_output.py --results-suffix _baseline
        -> Uses results_baseline/ folder, writes to results_plot_baseline.xlsx

        python plot_output.py --results-suffix _sensitivity --dry-run
        -> Dry-run mode: prints commands without executing

        python plot_output.py --columns Mean,Q_10th
        python plot_output.py --columns Mean,Q_10th,Q_33th,Q_67th,Q_90th
        -> Produces separate workbooks for the listed columns (results_plot_Mean.xlsx, results_plot_Q_10th.xlsx)

The meta-script ensures:
    1. Results folder exists before running scripts
    2. All scripts receive the same --results-dir and --output-file parameters
    3. Scripts are executed sequentially, stopping on first failure
"""
import argparse
import subprocess
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PLOT_DIR = os.path.join(ROOT, 'plot_python')


def collect_plot_scripts():
    """Collect all Python scripts from plot_python/ directory"""
    files = [f for f in os.listdir(PLOT_DIR) if f.endswith('.py')]
    files.sort()
    return files


def main():
    parser = argparse.ArgumentParser(
        description='Meta-script to run all plotting scripts with controlled parameters',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--results-suffix', type=str, default='', 
                       help='Suffix to append to results folder and output file (e.g., "_baseline")')
    parser.add_argument('--columns', type=str, default='',
                       help='Comma-separated list of columns/quantiles to produce separate xlsx files (e.g., Mean,Q_10th). If provided, one workbook per column will be created; otherwise a single workbook is produced.')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Print commands without executing them')
    args = parser.parse_args()

    suffix = args.results_suffix
    results_folder = f'results{suffix}' if suffix else 'results'
    output_file = f'results_plot{suffix}.xlsx' if suffix else 'results_plot.xlsx'
    # Parse requested columns
    requested_columns = [c.strip() for c in args.columns.split(',') if c.strip()] if args.columns else []
    
    # Full path to results folder
    results_path = os.path.join(ROOT, results_folder)

    scripts = collect_plot_scripts()
    if not scripts:
        print('ERROR: No plotting scripts found in plot_python/')
        sys.exit(1)

    print("=" * 80)
    print("PLOT OUTPUT META-SCRIPT")
    print("=" * 80)
    print(f"Found {len(scripts)} script(s) to run in plot_python/:")
    for script in scripts:
        print(f"  - {script}")
    print()
    print("META-SCRIPT CONTROLS:")
    print(f"  Results folder (input):  {results_folder}")
    print(f"  Output file:             {output_file}")
    print(f"  Mode:                    {'DRY-RUN' if args.dry_run else 'EXECUTE'}")
    print("=" * 80)
    
    # Validate results folder exists (unless dry-run)
    if not args.dry_run and not os.path.exists(results_path):
        print(f"\nERROR: Results folder does not exist: {results_path}")
        print("Please run the policy models first to generate results.")
        sys.exit(1)
    elif args.dry_run and not os.path.exists(results_path):
        print(f"\nWARNING: Results folder does not exist: {results_path}")
        print("(Continuing in dry-run mode)")
    
    print()
    
    print()

    # If user requested multiple columns, run the plotting scripts once per column and write per-column workbook
    if requested_columns:
        for col in requested_columns:
            out_file = f"results_plot_{col}{suffix}.xlsx" if suffix else f"results_plot_{col}.xlsx"
            print(f"\n*** Producing workbook for column: {col} -> {out_file} ***")
            for i, script in enumerate(scripts, 1):
                script_path = os.path.join(PLOT_DIR, script)
                cmd = [
                    sys.executable,
                    script_path,
                    '--results-dir', results_folder,
                    '--output-file', out_file,
                    '--columns', col
                ]
                print(f"[{i}/{len(scripts)}] Running: {script}")
                print(f"         --results-dir {results_folder}")
                print(f"         --output-file {out_file}")
                print(f"         --columns {col}")

                if args.dry_run:
                    print(f"         DRY-RUN: {' '.join(cmd)}")
                    print()
                    continue

                proc = subprocess.run(cmd, cwd=ROOT)
                if proc.returncode != 0:
                    print(f"\n✗ ERROR: Script {script} failed with exit code {proc.returncode}")
                    print(f"Meta-script stopping execution.")
                    sys.exit(proc.returncode)

                print(f"✓ Completed successfully")
                print()

        print("\nAll requested column workbooks created.")
        return
    # If no specific columns requested, run each plotting script once and write to a single workbook
    print("=" * 80)
    print("Running all plotting scripts and writing to a single workbook")
    for i, script in enumerate(scripts, 1):
        script_path = os.path.join(PLOT_DIR, script)
        cmd = [
            sys.executable,
            script_path,
            '--results-dir', results_folder,
            '--output-file', output_file
        ]

        print(f"[{i}/{len(scripts)}] Running: {script}")
        print(f"         --results-dir {results_folder}")
        print(f"         --output-file {output_file}")

        if args.dry_run:
            print(f"         DRY-RUN: {' '.join(cmd)}")
            print()
            continue

        proc = subprocess.run(cmd, cwd=ROOT)
        if proc.returncode != 0:
            print(f"\n✗ ERROR: Script {script} failed with exit code {proc.returncode}")
            print(f"Meta-script stopping execution.")
            sys.exit(proc.returncode)

        print(f"✓ Completed successfully")
        print()

    if args.dry_run:
        print("DRY-RUN COMPLETE - No scripts were executed")
    else:
        print("✓ ALL PLOTTING SCRIPTS COMPLETED SUCCESSFULLY")
        print(f"Output written to: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()

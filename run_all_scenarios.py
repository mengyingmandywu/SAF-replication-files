"""
Meta Script: Run Robustness Check Across All Scenarios

This meta script automatically discovers all data_input_XX folders and runs
print_results.py for each scenario, storing results in corresponding results_XX folders.
It also automatically generates quantile-specific plot Excel files for each scenario.

PURPOSE:
  Orchestrate robustness checks across multiple scenarios without manual intervention.
  Automatically maps data_input_XX folders to results_XX output folders.
  Generates results_plot_XX_*.xlsx files for each quantile and saves to results_XX folder.
  Supports different k-range values for different scenarios.

WORKFLOW:
  For each scenario:
    1. Run print_results.py (optimization & analysis)
    2. Run plot_output.py (generate quantile-specific plot workbooks)
    3. Move plot files to corresponding results_XX folder

USAGE:
    # Run all scenarios with baseline only (k-range=1, default)
    python run_all_scenarios.py
    # (also works with the flag present but no values)
    python run_all_scenarios.py --scenarios
    
    # Run all scenarios with full robustness check (k-range=5)
    python run_all_scenarios.py --k-range 5
    # (also works with the flag present but no values)
    python run_all_scenarios.py --scenarios --k-range 5
    
    # Run specific scenarios only
    python run_all_scenarios.py --scenarios baseline conversion
    
    # Run specific scenarios with full robustness
    python run_all_scenarios.py --scenarios baseline conversion --k-range 5
    
    # Run scenarios with DIFFERENT k-ranges per scenario
    python run_all_scenarios.py --scenario-config baseline:5 conversion:1
    python run_all_scenarios.py --scenario-config baseline:5 conversion:1 sensitivity:5
    
    # Run selected scenarios with different k-ranges
    python run_all_scenarios.py --scenarios baseline conversion --scenario-config baseline:5 conversion:1
    
    # Skip plotting step (optimization only)
    python run_all_scenarios.py --k-range 5 --no-plotting
    
    # Combine custom k-ranges with no plotting
    python run_all_scenarios.py --scenario-config baseline:5 conversion:1 --no-plotting

SCENARIOS DISCOVERED:
    - data_input_baseline    → results_baseline
    - data_input_conversion  → results_conversion
    (automatically discovers any data_input_XX folder)

OUTPUT:
    Optimization results in results_XX/ folders
    Plot workbooks in results_XX/ folders:
        If k-range=1:
            - results_plot_XX_Mean.xlsx (1 file)
        If k-range=5:
            - results_plot_XX_Mean.xlsx
            - results_plot_XX_Q_10th.xlsx
            - results_plot_XX_Q_33th.xlsx
            - results_plot_XX_Q_67th.xlsx
            - results_plot_XX_Q_90th.xlsx (5 files total)
    Log file: run_all_scenarios.log
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime


class ScenarioRunner:
    """Manages running robustness checks across multiple scenarios"""
    
    def __init__(self, script_dir: Path, k_range: int = 1, skip_plotting: bool = False, scenario_config: dict = None):
        """
        Initialize the scenario runner.
        
        Args:
            script_dir: Path to the script directory
            k_range: Default number of robustness iterations (1 or 5)
            skip_plotting: If True, skip the plot_output.py step
            scenario_config: Dict mapping scenario names to k-range values
                           e.g., {'baseline': 5, 'conversion': 1}
        """
        self.script_dir = script_dir
        self.k_range = k_range
        self.skip_plotting = skip_plotting
        self.scenario_config = scenario_config or {}  # Maps scenario name to k-range
        self.results = {
            'successful': [],
            'failed': [],
            'skipped': []
        }
        self.start_time = datetime.now()
        
    def discover_scenarios(self) -> list:
        """
        Discover all data_input_XX folders in the script directory.
        
        Returns:
            List of tuples: [(scenario_name, input_folder, output_folder), ...]
        """
        scenarios = []
        
        # Find all data_input_* folders
        for folder in self.script_dir.glob("data_input_*"):
            if folder.is_dir():
                # Extract scenario name (remove 'data_input_' prefix)
                scenario_name = folder.name.replace("data_input_", "")
                input_folder = folder.name
                output_folder = f"results_{scenario_name}"
                
                scenarios.append((scenario_name, input_folder, output_folder))
        
        return sorted(scenarios)
    
    def validate_scenario(self, input_folder: str) -> bool:
        """
        Validate that the input folder exists and contains required files.
        
        Args:
            input_folder: Name of the input folder
            
        Returns:
            True if valid, False otherwise
        """
        input_path = self.script_dir / input_folder
        
        if not input_path.exists():
            print(f"  ✗ Input folder '{input_folder}' does not exist!")
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
            print(f"  ✗ Missing required input files in '{input_folder}':")
            for file in missing_files:
                print(f"     - {file}")
            return False
        
        return True
    
    def run_plotting(self, scenario_name: str, output_folder: str, scenario_k_range: int) -> bool:
        """
        Run plot_output.py to generate quantile-specific plot workbooks.
        
        Args:
            scenario_name: Name of the scenario (e.g., 'baseline', 'conversion')
            output_folder: Name of the output folder (e.g., 'results_baseline')
            scenario_k_range: K-range for this scenario (1 or 5)
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\nRunning plot_output.py to generate plot workbooks...")
        print("-" * 60)
        
        # Determine the suffix for the output folder
        # If output_folder is 'results_baseline', suffix should be '_baseline'
        suffix = output_folder.replace('results', '')
        
        # Determine which quantiles to generate based on k_range
        if scenario_k_range == 1:
            # k-range 1: only Mean
            quantiles = ['Mean']
        else:  # scenario_k_range == 5
            # k-range 5: all quantiles
            quantiles = ['Mean', 'Q_10th', 'Q_33th', 'Q_67th', 'Q_90th']
        
        try:
            # Run plot_output.py with --columns to generate per-quantile workbooks
            columns_arg = ','.join(quantiles)
            
            cmd = [
                sys.executable, 
                "plot_output.py",
                "--results-suffix", suffix,
                "--columns", columns_arg
            ]
            
            print(f"Command: python plot_output.py --results-suffix {suffix} --columns {columns_arg}")
            
            result = subprocess.run(
                cmd,
                cwd=self.script_dir,
                check=True,
                capture_output=False
            )
            
            # Verify plot files were created
            expected_files = [f"results_plot_{q}{suffix}.xlsx" for q in quantiles]
            created_files = []
            
            for plot_file in expected_files:
                file_path = self.script_dir / plot_file
                if file_path.exists():
                    created_files.append(plot_file)
                    # Move to results folder
                    dest_path = self.script_dir / output_folder / plot_file
                    file_path.rename(dest_path)
                    print(f"  ✓ Moved {plot_file} to {output_folder}/")
            
            if len(created_files) == len(expected_files):
                print(f"✓ All {len(created_files)} plot workbook(s) generated and moved to {output_folder}/")
                return True
            else:
                print(f"⚠ Only {len(created_files)}/{len(expected_files)} plot workbooks were created")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"✗ plot_output.py failed: {e}")
            return False
    
    def run_scenario(self, scenario_name: str, input_folder: str, output_folder: str) -> bool:
        """
        Run robustness check for a single scenario.
        
        Args:
            scenario_name: Name of the scenario
            input_folder: Name of the input folder
            output_folder: Name of the output folder
            
        Returns:
            True if successful, False otherwise
        """
        # Determine k-range for this scenario
        scenario_k_range = self.scenario_config.get(scenario_name, self.k_range)
        
        print(f"\n{'='*70}")
        print(f"SCENARIO: {scenario_name.upper()}")
        print(f"{'='*70}")
        print(f"Input:  {input_folder}")
        print(f"Output: {output_folder}")
        print(f"K-range: {scenario_k_range}")
        print(f"{'='*70}")
        
        # Validate input folder
        if not self.validate_scenario(input_folder):
            return False
        
        print(f"✓ All required input files found")
        
        # Step 1: Run print_results.py with this scenario
        print(f"\n[STEP 1] Running print_results.py...")
        print("-" * 60)
        try:
            result = subprocess.run(
                [sys.executable, "print_results.py",
                 "--input-folder", input_folder,
                 "--output-folder", output_folder,
                 "--k-range", str(scenario_k_range)],
                cwd=self.script_dir,
                check=True,
                capture_output=False
            )
            
            # Verify output folder was created
            output_path = self.script_dir / output_folder
            if output_path.exists():
                num_files = len(list(output_path.glob("*")))
                print(f"✓ Optimization completed: {output_folder}/ ({num_files} files)")
            else:
                print(f"✗ Output folder '{output_folder}' was not created")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"✗ print_results.py failed: {e}")
            return False
        
        # Step 2: Run plot_output.py (unless skipped)
        if not self.skip_plotting:
            print(f"\n[STEP 2] Generating plot workbooks...")
            if not self.run_plotting(scenario_name, output_folder, scenario_k_range):
                # Plotting failure is not critical - still mark scenario as successful
                print(f"⚠ Plotting step had issues, but scenario data is ready")
        else:
            print(f"\n[STEP 2] Skipping plot generation (--no-plotting flag)")
        
        print(f"\n✓ Scenario '{scenario_name}' processing completed")
        return True
    
    def run_all_scenarios(self, selected_scenarios: list = None) -> int:
        """
        Run robustness check for all discovered scenarios (or selected ones).
        
        Args:
            selected_scenarios: List of scenario names to run. If None, run all.
            
        Returns:
            Exit code (0 for all success, 1 if any failed)
        """
        # Discover all scenarios
        all_scenarios = self.discover_scenarios()
        
        if not all_scenarios:
            print("ERROR: No data_input_* folders found in the script directory!")
            print(f"Expected folders like: data_input_baseline, data_input_conversion, etc.")
            return 1
        
        # Filter by selected scenarios if provided
        if selected_scenarios:
            scenarios = [s for s in all_scenarios if s[0] in selected_scenarios]
            if not scenarios:
                print(f"ERROR: None of the selected scenarios were found!")
                print(f"Available scenarios: {[s[0] for s in all_scenarios]}")
                return 1
        else:
            scenarios = all_scenarios
        
        print(f"\n{'#'*70}")
        print(f"# META SCRIPT: RUN ALL SCENARIOS")
        print(f"{'#'*70}")
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total scenarios to run: {len(scenarios)}")
        print(f"Default k-range: {self.k_range}")
        if self.scenario_config:
            print(f"Custom k-ranges: {self.scenario_config}")
        print(f"\nScenarios:")
        for scenario_name, input_folder, output_folder in scenarios:
            scenario_k_range = self.scenario_config.get(scenario_name, self.k_range)
            print(f"  - {scenario_name}: {input_folder} → {output_folder} (k-range: {scenario_k_range})")
        print(f"\n{'#'*70}\n")
        
        # Run each scenario
        for scenario_name, input_folder, output_folder in scenarios:
            success = self.run_scenario(scenario_name, input_folder, output_folder)
            
            if success:
                self.results['successful'].append(scenario_name)
            else:
                self.results['failed'].append(scenario_name)
        
        # Print summary
        self.print_summary()
        
        # Return exit code (0 if all successful, 1 if any failed)
        return 0 if not self.results['failed'] else 1
    
    def print_summary(self):
        """Print summary of all scenario runs"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        total_run = len(self.results['successful']) + len(self.results['failed'])
        
        print(f"\n{'#'*70}")
        print(f"# SUMMARY")
        print(f"{'#'*70}")
        print(f"Start time:  {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time:    {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration:    {int(duration.total_seconds() // 60)} minutes {int(duration.total_seconds() % 60)} seconds")
        print(f"\nResults:")
        print(f"  ✓ Successful: {len(self.results['successful'])}/{total_run}")
        if self.results['successful']:
            for scenario in self.results['successful']:
                print(f"    - {scenario}")
        
        if self.results['failed']:
            print(f"\n  ✗ Failed: {len(self.results['failed'])}/{total_run}")
            for scenario in self.results['failed']:
                print(f"    - {scenario}")
        
        if self.results['skipped']:
            print(f"\n  ⊘ Skipped: {len(self.results['skipped'])}/{total_run}")
            for scenario in self.results['skipped']:
                print(f"    - {scenario}")
        
        print(f"\n{'#'*70}\n")
        
        # Return overall status
        if self.results['failed']:
            print(f"✗ {len(self.results['failed'])} scenario(s) failed")
            return 1
        else:
            print(f"✓ All scenarios completed successfully!")
            return 0


def main():
    """Main entry point for the meta script"""
    
    script_dir = Path(__file__).parent
    
    parser = argparse.ArgumentParser(
        description='Run robustness checks across all scenarios with flexible k-range per scenario',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
See the USAGE section at the top of this file for complete examples.
        """
    )
    
    parser.add_argument(
        '--scenarios',
        nargs='*',
        help='Specific scenarios to run (e.g., baseline conversion). If omitted or provided without values, runs all discovered scenarios.'
    )
    
    parser.add_argument(
        '--k-range',
        type=int,
        default=1,
        choices=[1, 5],
        help='Default number of robustness iterations: 1 for baseline only, 5 for full robustness check (default: 1). Can be overridden per scenario with --scenario-config.'
    )
    
    parser.add_argument(
        '--scenario-config',
        nargs='+',
        help='Specify k-range per scenario as scenario:k-range pairs. E.g., baseline:5 conversion:1. Overrides --k-range for specified scenarios.'
    )
    
    parser.add_argument(
        '--no-plotting',
        action='store_true',
        help='Skip the plot_output.py step (optimization only, no quantile plots generated)'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Generate detailed summary report'
    )
    
    args = parser.parse_args()
    
    # Parse scenario config
    scenario_config = {}
    if args.scenario_config:
        for config_pair in args.scenario_config:
            if ':' not in config_pair:
                print(f"ERROR: Invalid scenario config format: '{config_pair}'")
                print(f"Expected format: scenario:k-range (e.g., baseline:5)")
                sys.exit(1)
            
            scenario_name, k_range_str = config_pair.split(':', 1)
            try:
                k_range_val = int(k_range_str)
                if k_range_val not in [1, 5]:
                    print(f"ERROR: Invalid k-range value: {k_range_val} (must be 1 or 5)")
                    sys.exit(1)
                scenario_config[scenario_name] = k_range_val
            except ValueError:
                print(f"ERROR: k-range must be an integer: '{k_range_str}'")
                sys.exit(1)
    
    # Create runner and execute
    runner = ScenarioRunner(
        script_dir, 
        args.k_range, 
        skip_plotting=args.no_plotting,
        scenario_config=scenario_config
    )
    exit_code = runner.run_all_scenarios(args.scenarios)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

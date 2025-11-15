/*
================================================================================
MASTER BATCH FILE - Generate Figures for Multiple Scenarios and Quantiles
================================================================================

PURPOSE:
  This master batch file orchestrates figure generation for specified scenarios
  and quantiles by calling create_figures.do for each combination.
  Reads plot data from results_plot_XX_YY.xlsx files stored in results_YY/ folders.

FEATURES:
  - Generate figures for multiple scenarios (baseline, conversion, etc.)
  - Generate all 5 quantiles or specific subset (Mean, Q_10th, Q_33th, Q_67th, Q_90th)
  - Choose output format: PNG or EPS
  - Generates 18 figures per quantile per scenario (90 total for all quantiles)
  - Organizes output by scenario and quantile into Plot_XX_YY/ folders

DATA SOURCE:
  Requires results_plot_XX_YY.xlsx files in results_YY/ folders:
    - results_baseline/results_plot_Mean_baseline.xlsx
    - results_baseline/results_plot_Q_10th_baseline.xlsx
    - results_conversion/results_plot_Mean_conversion.xlsx
    - etc.

OUTPUT FILES:
  - 18 PNG/EPS files per quantile per scenario
  - Saved to Plot_XX_YY/ folders (e.g., Plot_Mean_baseline/, Plot_Q_10th_conversion/)
  - Each folder contains: volumes, subsidy stacks, AAC scatter, policy costs, fuel prices, feedstock

USAGE - Run from Stata (requires StataNow):

This .do now auto-discovers scenario folders and available quantiles so you
do not need to set `global scenarios` manually. Behavior:

        - If you do not set `global scenarios`, the script will search for
            directories matching `results_*` and use their suffixes as scenario names.
        - For each scenario, the script probes the quantiles listed in `$quantiles`
            (default: Mean, Q_10th, Q_33th, Q_67th, Q_90th) and will only process
            quantiles that have corresponding workbook files
            `results_<scenario>/results_plot_<quantile>_<scenario>.xlsx`.
        - If no quantile workbooks are present for a scenario, that scenario is
            skipped with a warning.

New option - AUTO_DISCOVER:

        - The new global `AUTO_DISCOVER` controls whether discovery should force-
            override any pre-existing `$scenarios` value.
                - `global AUTO_DISCOVER "0"` (default): preserve an explicitly set
                    `$scenarios`; otherwise auto-discover only when `$scenarios` is
                    missing or equal to the original default `baseline`.
                - `global AUTO_DISCOVER "1"`: always override whatever `$scenarios`
                    is currently set to and use the discovered `results_*` folders.

Examples (recommended):

    # Auto-discover all scenarios and available quantiles (PNG, default):
    /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do run_figures.do

    # Force a specific subset of scenarios (overrides auto-discovery):
    global scenarios "baseline conversion"
    /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do run_figures.do

    # Request specific quantiles (will be skipped if workbook missing):
    global quantiles "Mean Q_90th"
    /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do run_figures.do

    # Change output figure format to EPS (optional):
    global figtype "eps"
    /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do run_figures.do

    # Force discovery to override user-specified scenarios (AUTO_DISCOVER=1):
    # In Stata:
    global AUTO_DISCOVER "1"
    do run_figures.do

    # Or from bash (create a small preamble .do then run Stata):
    # cat > /tmp/p.do <<'EOF'
    # global AUTO_DISCOVER "1"
    # do run_figures.do
    # EOF
    # /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do /tmp/p.do

Notes:
    - To ensure a particular ordering of scenarios, set `global scenarios` before
        running; otherwise the script uses the directory discovery order.
    - If you want the script to always probe the full 5-quantile set regardless
        of `$quantiles`, tell me and I can update the probe list.
    - New option: `global AUTO_DISCOVER "1"` forces the script to override any
      pre-existing `$scenarios` with the discovered `results_*` folders. Default
      is `0` (do not override user-specified `$scenarios`).

EXAMPLES (from Terminal/bash):

    # Default: all 5 quantiles for baseline in PNG
    /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do run_figures.do
    Result: Plot_Mean_baseline/, Plot_Q_10th_baseline/, ... (90 figures total)
    
    # Generate only Mean for baseline
    /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do run_figures.do 2>&1 &
    (then in Stata: global quantiles "Mean" and global scenarios "baseline")
    
    # Generate Mean and Q_90th for both scenarios in EPS
    /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do run_figures.do 2>&1 &
    Result: Plot_Mean_baseline/, Plot_Q_90th_baseline/, Plot_Mean_conversion/, Plot_Q_90th_conversion/
    
    # Background execution with logging
    /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do run_figures.do 2>&1 &
    sleep 120 && tail run_figures.log

EXECUTION TIME:
    - Single quantile: ~20-30 seconds
    - All 5 quantiles per scenario: ~2-3 minutes
    - Both scenarios (all quantiles): ~5-6 minutes

OUTPUT LOG:
    run_figures.log - Contains progress messages and any errors

CONFIGURATION VARIABLES (optional, defaults shown):
    $scenarios    = "baseline"                    (space-separated scenario names)
    $quantiles    = "Mean Q_10th Q_33th Q_67th Q_90th"  (space-separated quantile names)
    $figtype      = "png"                         (png or eps)

REQUIREMENTS:
    - Stata installed at /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp
    - results_plot_XX_YY.xlsx files in corresponding results_YY/ folders
    - Plot_XX_YY/ output folders created automatically if needed
    - create_figures.do in same directory

================================================================================
*/

* Set defaults if not specified
* Auto-discover results_* folders and set $scenarios when appropriate.
* If the user explicitly set $scenarios to something other than the default
* 'baseline', do not override it.

* Collect entries matching results_* in the current directory
local dirlist : dir . files "results_*"
local scenlist ""
* Diagnostic: print current working directory and discovered entries for debugging
di as txt "DEBUG: Stata working directory: " c(pwd)
di as txt "DEBUG: raw dirlist: `dirlist'"
foreach d of local dirlist {
    * remove the 'results_' prefix to get scenario name
    local scen = subinstr("`d'", "results_", "", .)
    * Only include if the directory actually exists
    if isdir("results_`scen'") {
        local scenlist "`scenlist' `scen'"
    }
}

if "`scenlist'" != "" {
    * We discovered scenario folders. Respect user preference unless AUTO_DISCOVER=1
    if missing("$AUTO_DISCOVER") {
        global AUTO_DISCOVER "0"
    }

    if "$AUTO_DISCOVER" == "1" {
        * Force override of any existing $scenarios with discovered list
        global scenarios "`scenlist'"
        di "AUTO_DISCOVER=1 -> Overriding scenarios with discovered list: $scenarios"
    }
    else {
        * AUTO_DISCOVER is 0 (default). Only set scenarios if user didn't set them
        if missing("$scenarios") {
            global scenarios "`scenlist'"
            di "Auto-discovered scenarios: $scenarios"
        }
        else if "$scenarios" == "baseline" {
            * If the only default was 'baseline', replace with discovered list
            global scenarios "`scenlist'"
            di "Auto-discovered scenarios (replacing default 'baseline'): $scenarios"
        }
        else {
            di "Using user-specified scenarios: $scenarios"
        }
    }
}
else {
    * No results_* folders found; fall back to baseline if user didn't set scenarios
    if missing("$scenarios") {
        global scenarios "baseline"
        di "No results_* folders found; defaulting to: baseline"
    }
}

if missing("$quantiles") {
    global quantiles "Mean Q_10th Q_33th Q_67th Q_90th"
}

if missing("$figtype") {
    global figtype "png"
}

di ""
di "================================================================================"
di "MASTER FIGURE GENERATION BATCH FILE"
di "================================================================================"
di "Scenarios: $scenarios"
di "Quantiles: $quantiles"
di "Format: $figtype"
di "================================================================================"
di ""

* Process each scenario
foreach s in $scenarios {
    di ""
    di "================================================================================"
    di "SCENARIO: `s'"
    di "================================================================================"
    di ""
    
    * Determine which quantiles are actually available for this scenario and skip missing ones
    local _orig_quantiles "$quantiles"
    local _avail_qs ""
    foreach q in $quantiles {
        * Check for expected input workbook in results_<scenario>/
        capture confirm file "results_`s'/results_plot_`q'_`s'.xlsx"
        if _rc == 0 {
            local _avail_qs "`_avail_qs' `q'"
        }
    }

    if "`_avail_qs'" == "" {
        di "WARNING: No plot workbooks found for scenario `s' in results_`s'/ - skipping"
        continue
    }

    /*
    Temporarily set the global quantiles to the available subset so the inner loop
    only processes quantiles that have workbooks present. Restore original at end.
    */
    global quantiles "`_avail_qs'"

    * Process each quantile for this scenario
    foreach q in $quantiles {
        di ""
        di "Processing: `q' for scenario `s' in $figtype format"
        di "---"
        di ""
        
        * Set global variables for this run
        global current_quantile "`q'"
        global current_scenario "`s'"
        global input_data "results_plot_`q'_`s'.xlsx"
        global results_folder "results_`s'"
        global output_folder "Plot_`q'_`s'"
        
        * Call the unified figure generation script
        do create_figures.do
    }
    * Restore the original quantiles global
    global quantiles "`_orig_quantiles'"
    
    di ""
    di "Completed: Scenario `s' ($figtype format)"
    di ""
}

di ""
di "================================================================================"
di "ALL SCENARIOS PROCESSED SUCCESSFULLY!"
di "================================================================================"
di ""

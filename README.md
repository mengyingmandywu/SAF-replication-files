# Aviation SI Policy Projection - Python Workflow Documentation

## Overview

This Python project analyzes policy scenarios for aviation sustainability through a comprehensive analysis framework.

## Project Structure

```
code/
├── policy_python/              # Policy model implementation scripts
│   ├── Current_policy.py
│   ├── Pure_quantity.py
│   ├── Carbon_tax.py
│   ├── Nested_D2_RV1.py
│   ├── Nested_D2_RV2.py
│   ├── Nonnested_D2_RV1.py
│   ├── Nonnested_D2_RV2.py
│   ├── Aviation_intensity_standard.py
│   ├── Current_policy_noLCFS.py
│   ├── Carbon_tax_noSAF_floor.py
│   └── No_policy_floor.py
│
├── plot_python/                # Output generation scripts
│   ├── generate_aac_sheet.py
│   ├── generate_allowance_prices_sheet.py
│   ├── generate_feedstock_sheet.py
│   ├── generate_fuel_prices_sheet.py
│   ├── generate_subsidy_sheet.py
│   ├── generate_subsidy_stack_figs_sheet.py
│   ├── generate_volumes_sheet.py
│   └── plot_output.py          # Meta-script orchestrator
│
├── data_input/                 # Input data directory
├── results/                    # Policy model outputs
│   ├── Total.xlsx
│   ├── Fuel_price.xlsx
│   ├── Fitted_quantity.xlsx
│   ├── Solution.xlsx
│   └── Intermediate_results/
│       └── Mean.xlsx
│
├── intermediate/               # Processing cache
├── plot_python/               # Generated outputs directory
├── generate_outputs.py        # Main execution script
├── print_results.py           # Results reporting
└── README.md                  # This file
```

## Workflow Architecture

### Phase 1: Policy Model Execution
# Baseline only (default, k=0)
python print_results.py

# Full robustness check (k=0-4, all 5 iterations)
python print_results.py --k-range 5

# With custom scenario and full robustness
python print_results.py --scenario baseline --k-range 5

# With explicit folders and robustness - default
python print_results.py --input-folder data_input --output-folder results --k-range 5

python print_results.py --input-folder data_input_baseline --output-folder results_baseline --k-range 5
read all input_parameters from data_input_XX folder; input_generate.py will create 

### Phase 2: Output Generation & Analysis

**Uses results/ folder, writes to results_plot.xlsx**
python plot_output.py

**Uses results_baseline/ folder, writes to results_plot_baseline.xlsx**    
python plot_output.py --results-suffix _baseline

### Phase 3: Generate plots

```

## Data Models & Policy Mapping

### Policy Scenarios

All scripts use consistent policy name mapping:

| Sheet Name | Display Name |
|-----------|--------------|
| Current_policy | Current Policy |
| Pure_quantity | Q mandate |
| Nested_D2_RV1 | Nested D2 |
| Nested_D2_RV2 | Nested D2 + stricter RFS |
| Nonnested_D2 | Non-nested D2 |
| Nonnested_D2_RV2 | Non-nested + stricter RFS |
| Carbon_tax | Carbon Tax |
| Aviation_intensity_standard | Aviation Intensity Std |
| Current_policy_no_LCFS | Current Policy + No LCFS |
| Carbon_tax_noSAF_floor | Carbon tax+no SAF |
| No_policy_floor | No policy |

### Key Data Structures

**Regional Fuel Demand Percentages (CA allocation):**
- Diesel (D): 9.90027%
- Gasoline (G): 9.04482%
- Jet (J): 17%

**Feedstock Unit Conversions:**
- Corn: 1 bushel ≈ 1/56 gallons → ×56 for display
- Sugarcane: 1 ton ≈ 1/2000 gallons → ×2000 for display

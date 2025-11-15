import pandas as pd
import numpy as np
import gurobipy as gp
from gurobipy import GRB, nlfunc
from gurobipy import quicksum
import os
import argparse
from typing import Optional

# Generate versioned input tables (V1/V2/V3/V4/D2)
try:
    # Local import; both files live in the same folder
    from generate_outputs import main as _generate_outputs_main
except Exception:
    _generate_outputs_main = None  # Fallback if generator isn't importable

# Get the directory where this script is located (policy_python folder)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (code folder) where intermediate/ and data_input/ are located
parent_dir = os.path.dirname(script_dir)

# Parse command-line arguments for configurable input/output folders
parser = argparse.ArgumentParser(description='Run biofuel policy optimization model (carbon_tax) with configurable input/output folders.')
parser.add_argument('--input-folder', type=str, default='data_input',
                    help='Name of the input folder (default: data_input)')
parser.add_argument('--output-folder', type=str, default='results',
                    help='Name of the output folder (default: results)')
parser.add_argument('--k-range', type=int, default=1,
                    help='Number of robustness iterations (default: 1, max: 5)')
args = parser.parse_args()

# Construct full paths using the specified folder names (relative to parent_dir)
DATA_INPUT_FOLDER = os.path.join(parent_dir, args.input_folder)
OUTPUT_FOLDER = os.path.join(parent_dir, args.output_folder)
K_RANGE = args.k_range

# Create the solution DataFrame
solution = pd.DataFrame(
    np.zeros((77, 6)),  # 70 rows and 6 columns filled with zeros
    columns=['Name', 'Mean', 'Q_10th', 'Q_33th', 'Q_67th', 'Q_90th']
)
# Assign the 'Name' column
solution['Name'] = [
    'Biofuel quantity', 'Q_B100-soyoil-CA', 'Q_B100-animalfat-CA', 'Q_RD-soyoil-CA', 'Q_RD-animalfat-CA', 'Q_SAF-animalfat-CA', 'Q_gasE100-corn-CA',
                 'Q_B100-soyoil-NC', 'Q_B100-animalfat-NC', 'Q_RD-soyoil-NC', 'Q_RD-animalfat-NC', 'Q_SAF-animalfat-NC', 'Q_gasE100-corn-NC',
                 'Q_gasE100-sugarcane-CA', 'Q_gasE100-sugarcane-NC', 'Q_SAF-soyoil-CA', 'Q_SAF-soyoil-NC', 'Q_SAF-sugarcane-ETJ-CA', 'Q_SAF-sugarcane-ETJCCS-CA',
                 'Q_SAF-corn-ETJ-CA', 'Q_SAF-corn-ETJCCS-CA', 'Q_SAF-sugarcane-ETJ-NC', 'Q_SAF-sugarcane-ETJCCS-NC', 'Q_SAF-corn-ETJ-NC', 'Q_SAF-corn-ETJCCS-NC',
                 'Prices', 'State_tax_credit', 'Additional_tax_credit','P_D2', 'P_D4', 'P_D6', 'P_LCFS', 'P_SAF', 'P_B100_CA', 'P_RD_CA', 'P_SAF_CA', 'P_gasE100_CA', 'P_B100_NC', 'P_RD_NC', 'P_SAF_NC', 'P_gasE100_NC',
                 'P_B0_CA', 'P_E0_CA', 'P_J0_CA', 'P_B0_NC', 'P_E0_NC', 'P_J0_NC', 'Feedstock', 'P_soyoil', 'P_animal fat', 'P_corn', 'P_sugarcane', 'Q_soyoil', 'Q_animal fat', 'Q_corn', 'Q_sugarcane',
                 'Conventional fuel quantity', 'Q_B0', 'Q_E0', 'Q_J0',
                 'Blended-Fuel', 'D_CA', 'G_CA', 'J_CA', 'D_NC', 'G_NC', 'J_NC','P_carbon_tax',
                 'DGE_price',
                 'P_B100_CA_DGE','P_RD_CA_DGE', 'P_SAF_CA_DGE', 'P_gasE100_CA_DGE', 'P_B100_NC_DGE', 'P_RD_NC_DGE', 'P_SAF_NC_DGE', 'P_gasE100_NC_DGE'
]

# Fitted_quantity DataFrame
Fitted_quantity = pd.DataFrame(
    np.zeros((29, 6)),
    columns=['Name', 'Mean', 'Q_10th', 'Q_33th', 'Q_67th', 'Q_90th']
)
Fitted_quantity['Name'] = [
    'RVO_D2', 'RVO_BBD', 'RVO_RF', 'RV_BBD', 'RV_RF', 'Fitted_BBD', 'Fitted_RF', 'Fitted_LCFS_deficit-credits','Fitted_SAF_LCFS_deficit-credits',
    'Total', 'BD_all', 'RD_all', 'BBD_all', 'B0_all', 'E100_all', 'E0_all', 'SAF_HEFA_all', 'SAF_ETJ_all', 'SAF_all', 'J0_all',
    'Feedstock', 'soyoil', 'animal fat', 'corn', 'sugarcane', 'Demand_all', 'D', 'G', 'J'
]

# Fuel_price DataFrame
Fuel_price = pd.DataFrame(
    np.zeros((30, 6)),
    columns=['Name', 'Mean', 'Q_10th', 'Q_33th', 'Q_67th', 'Q_90th']
)
Fuel_price['Name'] = [
    'Blended fuel', 'Blended-diesel', 'Blended-gasoline', 'Aviation','E100', 'E10',
    'Finished biofuel', 'B100', 'RD', 'E100', 'SAF',
    'Conventional fuel', 'B0','E0','J0',
    'Implicit tax', 'RFS_RVO_road','RFS_RVO_jet', 'LCFS_CA_road', 'LCFS_CA_jet','Aviation_intensity_standard',
    'Carbon_tax', 'Carbon_tax_B0', 'Carbon_tax_E0', 'Carbon_tax_J0',
    'Finished biofuel DGE per gallon', 'B100', 'RD', 'E100', 'SAF'
]

# Fuel_CI DataFrame
Fuel_CI = pd.DataFrame(
    np.zeros((5, 6)),
    columns=['Name', 'Mean', 'Q_10th', 'Q_33th', 'Q_67th', 'Q_90th']
)
Fuel_CI['Name'] = [
    'Total', 'Blended fuel', 'Blended-diesel', 'Blended-gasoline', 'Blended-jet'
]

# Total DataFrame
Total = pd.DataFrame(
    np.zeros((40, 6)),
    columns=['Name', 'Mean', 'Q_10th', 'Q_33th', 'Q_67th', 'Q_90th']
)
Total['Name'] = [
    'Total', 'Emissions_D', 'Emissions_G', 'Emissions_J', 'Emissions_total', 'Costs_D', 'Costs_G', 'Costs_J', 'Costs_total',
    'Subsidy', 'Taxpayer', 'IRA', '45Z', '45Q', 'State_tax_credit', 'Additional_SAF_tax',
    'RFS_credits_road_CA', 'RFS_credits_road_NC', 'RFS_credits_jet_CA', 'RFS_credits_jet_NC',
    'RFS_deficits_road_CA', 'RFS_deficits_road_NC', 'RFS_deficits_jet_CA', 'RFS_deficits_jet_NC',
    'LCFS_CA_biofuel_credits', 'LCFS_CA_other_credits', 'LCFS_CA_all_credits', 'LCFS_all_jet', 'LCFS_all_credits_jet_CA', 'LCFS_all_credits_jet_NC',
    'LCFS_all_deficits_jet_CA', 'LCFS_all_deficits_jet_NC', 'Subsidy_total', 
    'Taxpayer_D', 'Taxpayer_G', 'Taxpayer_J','Carbon_tax_total','Carbon_tax_D','Carbon_tax_G','Carbon_tax_J',
    #'Carbon_tax_D_CA','Carbon_tax_D_NC','Carbon_tax_G_CA','Carbon_tax_G_NC','Carbon_tax_J_CA','Carbon_tax_J_NC'
]

# Feedstock_source DataFrame
Feedstock_source = pd.DataFrame(
    np.zeros((12, 6)),
    columns=['Name', 'Mean', 'Q_10th', 'Q_33th', 'Q_67th', 'Q_90th']
)
Feedstock_source['Name'] = [
    'B100-soyoil', 'B100-animalfat', 'RD-soyoil', 'RD-animalfat', 'SAF-soyoil', 'SAF-animalfat', 'SAF-corn', 'SAF-sugarcane',
    'SAF-corn-CCS', 'SAF-sugarcane-CCS', 'gasE100-corn', 'gasE100-sugarcane'
]

for k in range(K_RANGE):
    # Read input_biofuel from generated V3 (OLD rules, NC-zeroed CI columns)
    intermediate_dir = os.path.join(parent_dir, 'intermediate')
    v3_path = os.path.join(intermediate_dir, 'input_biofuel_V3.xlsx')
    if not os.path.exists(v3_path):
        # Attempt to generate all outputs if missing
        if _generate_outputs_main is not None:
            try:
                _generate_outputs_main()
            except Exception as e:
                raise RuntimeError(f"Failed to generate input_biofuel_V3.xlsx via generate_outputs.py: {e}")
        else:
            raise FileNotFoundError(
                "input_biofuel_V3.xlsx not found and generate_outputs.py unavailable to build it."
            )
    if not os.path.exists(v3_path):
        raise FileNotFoundError(f"Expected generated file is missing: {v3_path}")

    input_biofuel = pd.read_excel(v3_path, index_col=0)
    
    # # Drop old CI_std_LCFS and rename CI_std_LCFS_new to CI_std_LCFS (using 30% reduction)
    # if 'CI_std_LCFS' in input_biofuel.columns:
    #     input_biofuel.drop(columns=['CI_std_LCFS'], inplace=True)
    # if 'CI_std_LCFS_new' in input_biofuel.columns:
    #     input_biofuel.rename(columns={'CI_std_LCFS_new': 'CI_std_LCFS'}, inplace=True)

    # Reorder columns and rename the 8th column
    input_biofuel = input_biofuel.iloc[:, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15,19,20]]
    input_biofuel.columns.values[7] = 'CI_LCFS'

    pd.set_option('display.max_columns', None)
    print(input_biofuel.head(10))
    
    # Ensure results folder exists for outputs later
    results_dir = OUTPUT_FOLDER  # Already has full path from parent_dir
    os.makedirs(results_dir, exist_ok=True)
    
    # Read feedstock supply parameters from data_input folder
    data_input_dir = DATA_INPUT_FOLDER  # Already has full path from parent_dir
    feedstock_path = os.path.join(data_input_dir, 'feedstock_supply.xlsx')
    input_feedstock = pd.read_excel(feedstock_path, index_col=0)
    
    demand_path = os.path.join(data_input_dir, 'fuel_demand.xlsx')
    input_demand = pd.read_excel(demand_path, sheet_name='V2', index_col=0)
    input_demand = input_demand.iloc[:, [0, 1, 2, k+3, 8, 9]]
    input_demand.columns = ['F', 'j', 'PC_F0', 'alpha', 'beta', 'ETJ_percent']

    compliance_path = os.path.join(data_input_dir, 'Policy_constraints.xlsx')
    input_compliance = pd.read_excel(compliance_path, sheet_name='V2', index_col=0)
    input_compliance = input_compliance.iloc[:, [0, k+1, 6, 7]]
    input_compliance.columns = ['mandate', 'Q', 'CI_LCFS', 'ED_LCFS']
    print(input_compliance)

    state_tax_path = os.path.join(data_input_dir, 'state_tax.xlsx')
    state_level_tax = pd.read_excel(state_tax_path)

    # Read jet fuel percentage from the new spreadsheet
    jet_volume = state_level_tax.iloc[:, k+1]
    print(jet_volume)
    state_tax_credit = state_level_tax['State tax credit'].values
    
    # # # Assign to breaks, add 0 at front and 1 at end
    breaks = list(jet_volume)
    vals = list(state_tax_credit) + [0.0]
    print("Breaks:", breaks)
    print("Values:", vals)

    # Define constants
    alpha_eth_d = 1.5
    beta_eth_d = 0.2
    P_cap = 250
    duty_e100sugarcane = 0.125 
    M= 50
    epsilon = 1e-4
    Sigma = 1e-6 #Should be ≳ feasibility tol
    iteration = 0
    P_carbon_tax = 15
    max_total_profit = -float('inf')
    best_df = None
    best_break_idx = None
    state_tax_profit = 0.0
    
    # Initialize list to track objective values for each break
    objective_values = []

    for break_idx, break_val in enumerate(breaks):
        val = vals[break_idx]
        val_pre = vals[break_idx - 1] if break_idx > 0 else 0.0
        break_val_pre = breaks[break_idx - 1] if break_idx > 0 else 0.0
        break_val_step = break_val_pre - breaks[break_idx-2] if break_idx > 1 else break_val_pre
        print(f"Break {break_idx}: break = {break_val}, val = {val},val_pre = {val_pre},break_val_pre = {break_val_pre},break_val_step = {break_val_step}")
        state_tax_profit_step = (-val + val_pre) * break_val_step if break_idx > 0 else 0.0
        state_tax_profit = state_tax_profit + state_tax_profit_step

        print(f"State tax profit step: {state_tax_profit_step}, Cumulative state tax profit: {state_tax_profit}")
        #print(f"Break {break_idx}: break = {break_val}, val = {val}")
        # Set up your model here, using break_val as needed
        # Create a new model
        m = gp.Model("carbon_tax")

        # Create variables for biofuel quantity
        biofuel_quantity_Q = m.addVars(24, vtype=GRB.CONTINUOUS, name="Q")
        biofuel_quantity_Q_equiv = m.addVars(24, vtype=GRB.CONTINUOUS, name="Q_equiv")
        # Set row names for biofuel_quantity
        biofuel_quantity = pd.DataFrame({
            'Q': [biofuel_quantity_Q[i] for i in range(24)],
            'Q_equiv': [biofuel_quantity_Q_equiv[i] for i in range(24)]
        }, index=input_biofuel.index)

        # Create multipliers mu
        mu_value = m.addVars(24, vtype=GRB.CONTINUOUS, name="mu_value")
        # Set row names for mu
        mu = pd.DataFrame({
            'value': [mu_value[i] for i in range(24)]
        }, index=input_biofuel.index)

        muzeta_value = m.addVars(24, vtype=GRB.BINARY, name="muzeta_value")
        muzeta = pd.DataFrame({
            'value': [muzeta_value[i] for i in range(24)]
        }, index=input_biofuel.index)

        # Create multipliers nu
        nu_value = m.addVars(4, vtype=GRB.CONTINUOUS, name="nu_value")
        nuzeta_value = m.addVars(4, vtype=GRB.BINARY, name="nuzeta_value")
        # Set row names for nu
        nu_index = ['B100', 'RD', 'SAF', 'gasE100']
        nu = pd.DataFrame({
            'value': [nu_value[i] for i in range(4)],
            'f': ['B100', 'RD', 'SAF', 'gasE100']
        }, index=nu_index)
        nuzeta = pd.DataFrame({
            'value': [nuzeta_value[i] for i in range(4)],
            'f': ['B100', 'RD', 'SAF', 'gasE100']
        }, index=nu_index)

        # Create multipliers for HEFA constraints
        hefa_value = m.addVars(2, vtype=GRB.CONTINUOUS, name="hefa_value")
        hefazeta_value = m.addVars(2, vtype=GRB.BINARY, name="hefazeta_value")

        # # RIN prices
        # RIN_prices_P = m.addVars(2, vtype=GRB.CONTINUOUS, name="RIN_prices_P")
        # RIN_prices = pd.DataFrame({
        #     'P': [RIN_prices_P[i] for i in range(2)],
        #     'fueltype': ['B100,RD,SAF', 'gasE100'],
        #     'code': ['D4', 'D6']
        # }, index=['D4', 'D6'])

        # # RVO percent
        # RVO_percent_P = m.addVars(2, vtype=GRB.CONTINUOUS, name="RVO_percent_P")
        # RVO_percent = pd.DataFrame({
        #     'P': [RVO_percent_P[i] for i in range(2)],
        #     'mandate': ['BBD', 'RF']
        # }, index=['BBD', 'RF'])

        # # LCFS prices
        # LCFS_prices_P = m.addVar(vtype=GRB.CONTINUOUS, name="LCFS_prices_P")
        # LCFS_prices = pd.DataFrame({
        #     'P': [LCFS_prices_P],
        #     'type': ['LCFS']
        # }, index=['LCFS'])

        # SAF credit prices
        SAFcredit_prices_P = m.addVar(vtype=GRB.CONTINUOUS, name="SAFcredit_prices_P")
        SAFcredit_prices = pd.DataFrame({
            'P': [SAFcredit_prices_P],
            'type': ['SAF']
        }, index=['SAF'])

        # Feedstock prices
        feedstock_prices_P = m.addVars(4, vtype=GRB.CONTINUOUS, name="feedstock_prices_P")
        feedstock_prices = pd.DataFrame({
            'P': [feedstock_prices_P[i] for i in range(4)],
            's': ['soyoil', 'animalfat', 'corn', 'sugarcane']
        }, index=['soyoil', 'animalfat', 'corn', 'sugarcane'])

        # # Biofuel prices
        # biofuel_prices_P = m.addVars(8, vtype=GRB.CONTINUOUS, name="biofuel_prices_P")
        # biofuel_prices = pd.DataFrame({
        #     'P': [biofuel_prices_P[i] for i in range(8)],
        #     'f': ['B100', 'RD', 'SAF', 'gasE100', 'B100', 'RD', 'SAF', 'gasE100'],
        #     'j': ['CA', 'CA', 'CA', 'CA', 'NC', 'NC', 'NC', 'NC']
        # }, index=['B100_CA', 'RD_CA', 'SAF_CA', 'gasE100_CA', 'B100_NC', 'RD_NC', 'SAF_NC', 'gasE100_NC'])

        biofuel_prices_P = m.addVars(4, vtype=GRB.CONTINUOUS, name="biofuel_prices_P")
        biofuel_prices = pd.DataFrame({
            'P': [biofuel_prices_P[i] for i in range(4)],
            'f': ['B100', 'RD', 'SAF', 'gasE100'],
        }, index=['B100', 'RD', 'SAF', 'gasE100'])


        # Conventional fuel prices
        # conventionalfuel_prices_P = m.addVars(6, vtype=GRB.CONTINUOUS, name="conventionalfuel_prices_P")
        # conventionalfuel_prices = pd.DataFrame({
        #     'P': [conventionalfuel_prices_P[i] for i in range(6)],
        #     'F': ['D', 'G', 'J', 'D', 'G', 'J'],
        #     'j': ['CA', 'CA', 'CA', 'NC', 'NC', 'NC']
        # }, index=['D_CA', 'G_CA', 'J_CA', 'D_NC', 'G_NC', 'J_NC'])

        conventionalfuel_prices_P = m.addVars(3, vtype=GRB.CONTINUOUS, name="conventionalfuel_prices_P")
        conventionalfuel_prices = pd.DataFrame({
            'P': [conventionalfuel_prices_P[i] for i in range(3)],
            'F': ['D', 'G', 'J'],
        }, index=['D', 'G', 'J'])


        # Feedstock quantity
        feedstock_quantity_Q = m.addVars(4, vtype=GRB.CONTINUOUS, name="feedstock_quantity_Q")
        feedstock_quantity = pd.DataFrame({
            'Q': [feedstock_quantity_Q[i] for i in range(4)],
            's': ['soyoil', 'animalfat', 'corn', 'sugarcane']
        }, index=['soyoil', 'animalfat', 'corn', 'sugarcane'])

        demand_quantity_Q = m.addVars(3, vtype=GRB.CONTINUOUS, name="demand_quantity_Q")
        demand_quantity_Q_actual = m.addVars(3, vtype=GRB.CONTINUOUS, name="demand_quantity_Q_actual")
        demand_quantity = pd.DataFrame({
            'F': ['D', 'G', 'J'],
            'Q': [demand_quantity_Q[i] for i in range(3)],
            'Q_actual': [demand_quantity_Q_actual[i] for i in range(3)]
        }, index=['D', 'G', 'J'])

        # Blended fuel price
        demand_price_P = m.addVars(3, vtype=GRB.CONTINUOUS, name="demand_price_P")
        demand_price = pd.DataFrame({
            'F': ['D', 'G', 'J'],
            'P': [demand_price_P[i] for i in range(3)]
        }, index=['D', 'G', 'J'])

        # Conventional fuel quantity
        # conventionalfuel_quantity_Q = m.addVars(6, vtype=GRB.CONTINUOUS, name="conventionalfuel_quantity_Q")
        # conventionalfuel_quantity = pd.DataFrame({
        #     'Q': [conventionalfuel_quantity_Q[i] for i in range(6)],
        #     'j': ['CA', 'CA', 'CA', 'NC', 'NC', 'NC'],
        #     'F': ['D', 'G', 'J', 'D', 'G', 'J'],
        #     'CI_LCFS': [0, 0, 0, 0, 0, 0],
        #     'CI_std_LCFS': [0, 0, 0, 0, 0, 0],
        #     'ED_LCFS': [0, 0, 0, 0, 0, 0]
        # }, index=['B0_CA', 'E0_CA', 'J0_CA', 'B0_NC', 'E0_NC', 'J0_NC'])

        conventionalfuel_quantity_Q = m.addVars(3, vtype=GRB.CONTINUOUS, name="conventionalfuel_quantity_Q")
        conventionalfuel_quantity = pd.DataFrame({
            'Q': [conventionalfuel_quantity_Q[i] for i in range(3)],
            'F': ['D', 'G', 'J'],
            'CI_LCFS': [0, 0, 0],
            'CI_std_LCFS': [0, 0, 0],
            'ED_LCFS': [0, 0, 0]
        }, index=['B0', 'E0', 'J0'])

        # Assign values to the conventionalfuel_quantity DataFrame
        conventionalfuel_quantity.loc[:, 'CI_LCFS'] = input_compliance.loc[input_compliance['mandate'] == 'LCFS', 'CI_LCFS'].values
        conventionalfuel_quantity.loc['B0', 'CI_std_LCFS'] = input_biofuel.loc[input_biofuel['F'] == 'D', 'CI_std_LCFS'].unique()[0]
        conventionalfuel_quantity.loc['E0', 'CI_std_LCFS'] = input_biofuel.loc[input_biofuel['F'] == 'G', 'CI_std_LCFS'].unique()[0]
        conventionalfuel_quantity.loc['J0', 'CI_std_LCFS'] = input_biofuel.loc[input_biofuel['F'] == 'J', 'CI_std_LCFS'].unique()[0]
        conventionalfuel_quantity.loc[:, 'ED_LCFS'] = input_compliance.loc[input_compliance['mandate'] == 'LCFS', 'ED_LCFS'].values

        # Price break up: RIN/LCFS obligation
        Price_bio = pd.DataFrame({
            'f': input_biofuel['f'],
            's': input_biofuel['s'],
            'j': input_biofuel['j'],
            'F': input_biofuel['F'],
            'RIN_obligation': [m.addVar(vtype=GRB.CONTINUOUS, name=f"RIN_obligation_{i}") for i in range(len(input_biofuel))],
            'LCFS_CA_obligation': [m.addVar(vtype=GRB.CONTINUOUS, name=f"LCFS_CA_obligation_{i}") for i in range(len(input_biofuel))],
            'Tax': [m.addVar(vtype=GRB.CONTINUOUS, name=f"Tax_{i}") for i in range(len(input_biofuel))],
            'Carbon_tax_obligation': [m.addVar(vtype=GRB.CONTINUOUS, name=f"Carbon_tax_obligation_{i}") for i in range(len(input_biofuel))],
            'P_all': [m.addVar(vtype=GRB.CONTINUOUS, name=f"P_all_{i}") for i in range(len(input_biofuel))],
            'PC_F0': [m.addVar(vtype=GRB.CONTINUOUS, name=f"PC_F0_{i}") for i in range(len(input_biofuel))],
            'P_RIN_LCFS_detach': [m.addVar(vtype=GRB.CONTINUOUS, name=f"P_RIN_LCFS_detach_{i}") for i in range(len(input_biofuel))],
            'P_RIN_detach': [m.addVar(vtype=GRB.CONTINUOUS, name=f"P_RIN_detach_{i}") for i in range(len(input_biofuel))],
            'Q_actual': [m.addVar(vtype=GRB.CONTINUOUS, name=f"Q_actual_{i}") for i in range(len(input_biofuel))],
            'Q_equiv': [m.addVar(vtype=GRB.CONTINUOUS, name=f"Q_equiv_{i}") for i in range(len(input_biofuel))]
        }, index=input_biofuel.index)

        Price_conventional = pd.DataFrame({
            'f': ['B0', 'E0', 'J0'],
            's': ['', '', ''],
            'F': ['D', 'G', 'J'],
            'RIN_obligation': [m.addVar(vtype=GRB.CONTINUOUS, name=f"RIN_obligation_{i+len(input_biofuel)}") for i in range(3)],
            'LCFS_CA_obligation': [m.addVar(vtype=GRB.CONTINUOUS, name=f"LCFS_CA_obligation_{i+len(input_biofuel)}") for i in range(3)],
            'Tax': [m.addVar(vtype=GRB.CONTINUOUS, name=f"Tax_{i+len(input_biofuel)}") for i in range(3)],
            'Carbon_tax_obligation': [m.addVar(vtype=GRB.CONTINUOUS, name=f"Carbon_tax_obligation_{i+len(input_biofuel)}") for i in range(3)],
            'P_all': [m.addVar(vtype=GRB.CONTINUOUS, name=f"P_all_{i+len(input_biofuel)}") for i in range(3)],
            'PC_F0': [m.addVar(vtype=GRB.CONTINUOUS, name=f"PC_F0_{i+len(input_biofuel)}") for i in range(3)],
            'P_RIN_LCFS_detach': [m.addVar(vtype=GRB.CONTINUOUS, name=f"P_RIN_LCFS_detach_{i+len(input_biofuel)}") for i in range(3)],
            'P_RIN_detach': [m.addVar(vtype=GRB.CONTINUOUS, name=f"P_RIN_detach_{i+len(input_biofuel)}") for i in range(3)],
            'Q_actual': [m.addVar(vtype=GRB.CONTINUOUS, name=f"Q_actual_{i+len(input_biofuel)}") for i in range(3)],
            'Q_equiv': [m.addVar(vtype=GRB.CONTINUOUS, name=f"Q_equiv_{i+len(input_biofuel)}") for i in range(3)]
        }, index=conventionalfuel_quantity.index)

        # Combine the biofuel and conventional fuel price DataFrames
        Price = pd.concat([Price_bio, Price_conventional])

        # Define an objective
        # We do not actually need an objective function
        m.setObjective(0, GRB.MAXIMIZE)

        # Define constraints
        Constraints = []

        # Biofuel supply curves
        output = biofuel_quantity.join(input_biofuel)
        biofuel_quantity = biofuel_quantity.join(input_biofuel)


        # Add the new constraints
        for i in range(24):
            Constraints.append(
                biofuel_prices.loc[biofuel_prices['f'] == output['f'][i], 'P'].item() -
                (output['PC'][i] + output['Conversion'][i] * feedstock_prices.loc[feedstock_prices['s'] == output['s'][i], 'P'].item()*
                 (1+duty_e100sugarcane*(output['s'][i] == 'sugarcane'))) + (output['f'][i] == 'SAF') * SAFcredit_prices['P'].item() * output.iloc[i]['SAFcreditheaviside']
                #- (P_carbon_tax * output['CI_LCFS'][i] * output['ED_LCFS'][i] / 1000000) 
                + mu['value'][i] - nu.loc[nu['f'] == output['f'][i], 'value'].item() -
                    hefa_value[0] * ((output['f'][i] == 'SAF') & (output['s'][i] == 'soyoil')) +
                    hefa_value[0] * 5.5/2.5 * ((output['f'][i] == 'RD') & (output['s'][i] == 'soyoil')) 
                    - hefa_value[1] * ((output['f'][i] == 'SAF') & (output['s'][i] == 'animalfat')) +
                    hefa_value[1] * 5.5/2.5 * ((output['f'][i] == 'RD') & (output['s'][i] == 'animalfat')) == 0
            )
            

        # Biofuel supply curves - multipliers mu
        for j in range(24):
            Constraints.append(mu_value[j] >= 0)
            Constraints.append(mu_value[j] <= muzeta_value[j] * M)
            Constraints.append(output['Q'][j] >= 0)
            Constraints.append(output['Q'][j] <= (1 - muzeta_value[j]) * M)

        # Biofuel supply curves - multipliers nu
        # Blending wall constraints
        fuel_types = ['B100', 'RD']
        for fuel in fuel_types:
            Constraints.append(nu_value[nu_index.index(f'{fuel}')] >= 0)
            Constraints.append(nu_value[nu_index.index(f'{fuel}')] <= (1 - nuzeta_value[nu_index.index(f'{fuel}')]) * M)
            Constraints.append(-(biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'Q'].sum() -
                                        biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'BW_constraints'].unique()[0] *
                                        demand_quantity.loc[(demand_quantity['F'] == 'D'), 'Q_actual'].item()) >= 0)
            Constraints.append(-(biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'Q'].sum() -
                                biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'BW_constraints'].unique()[0] *
                                demand_quantity.loc[(demand_quantity['F'] == 'D'), 'Q_actual'].item()) <=
                                nuzeta_value[nu_index.index(f'{fuel}')] * M)
                
        fuel_types = ['gasE100']
        for fuel in fuel_types:
            Constraints.append(nu_value[nu_index.index(f'{fuel}')] >= 0)
            Constraints.append(nu_value[nu_index.index(f'{fuel}')] <= (1 - nuzeta_value[nu_index.index(f'{fuel}')]) * M)
            Constraints.append(-(biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'Q'].sum() -
                                        biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'BW_constraints'].unique()[0] *
                                        demand_quantity.loc[(demand_quantity['F'] == 'G'), 'Q_actual'].item()) >= 0)
            Constraints.append(-(biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'Q'].sum() -
                                biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'BW_constraints'].unique()[0] *
                                demand_quantity.loc[(demand_quantity['F'] == 'G'), 'Q_actual'].item()) <=
                                nuzeta_value[nu_index.index(f'{fuel}')] * M)
                
        fuel_types = ['SAF']
        for fuel in fuel_types:
            Constraints.append(nu_value[nu_index.index(f'{fuel}')] >= 0)
            Constraints.append(nu_value[nu_index.index(f'{fuel}')] <= (1 - nuzeta_value[nu_index.index(f'{fuel}')]) * M)
            Constraints.append(-(biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'Q'].sum() -
                                        biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'BW_constraints'].unique()[0] *
                                        demand_quantity.loc[(demand_quantity['F'] == 'J'), 'Q_actual'].item())>= 0)
            Constraints.append(-(biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'Q'].sum() -
                                biofuel_quantity.loc[(biofuel_quantity['f'] == fuel), 'BW_constraints'].unique()[0] *
                                demand_quantity.loc[(demand_quantity['F'] == 'J'), 'Q_actual'].item()) <=
                                nuzeta_value[nu_index.index(f'{fuel}')] * M)        
            
         # # # HEFA constraints
        M1_0 = 10
        Constraints.append(hefa_value[0] >= 0)
        Constraints.append(hefa_value[0] <= hefazeta_value[0] * M1_0)
        Constraints.append(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'soyoil'), 'Q'].sum() -
               5.5/2.5*biofuel_quantity.loc[(biofuel_quantity['f'] == 'RD') & (biofuel_quantity['s'] == 'soyoil'), 'Q'].sum() <=0)
        Constraints.append(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'soyoil'), 'Q'].sum() -
               5.5/2.5*biofuel_quantity.loc[(biofuel_quantity['f'] == 'RD') & (biofuel_quantity['s'] == 'soyoil'), 'Q'].sum() >= - (1 - hefazeta_value[0]) * M1_0)
        Constraints.append(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'soyoil'), 'Q'].sum() -
               5.5/2.5*biofuel_quantity.loc[(biofuel_quantity['f'] == 'RD') & (biofuel_quantity['s'] == 'soyoil'), 'Q'].sum() <= (1 - hefazeta_value[0]) * M1_0)
        
        M1_1 = 10
        Constraints.append(hefa_value[1] >= 0)
        Constraints.append(hefa_value[1] <= hefazeta_value[1] * M1_1)
        Constraints.append(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'animalfat'), 'Q'].sum() -
               5.5/2.5*biofuel_quantity.loc[(biofuel_quantity['f'] == 'RD') & (biofuel_quantity['s'] == 'animalfat'), 'Q'].sum() <= 0)
        Constraints.append(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'animalfat'), 'Q'].sum() -
               5.5/2.5*biofuel_quantity.loc[(biofuel_quantity['f'] == 'RD') & (biofuel_quantity['s'] == 'animalfat'), 'Q'].sum() >= - (1 - hefazeta_value[1]) * M1_1)
        Constraints.append(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'animalfat'), 'Q'].sum() -
               5.5/2.5*biofuel_quantity.loc[(biofuel_quantity['f'] == 'RD') & (biofuel_quantity['s'] == 'animalfat'), 'Q'].sum() <= (1 - hefazeta_value[1]) * M1_1)
    
                

        # Biofuel quantity - get diesel equivalent and gasoline equivalent
        for i in range(24):
            Constraints.append(biofuel_quantity_Q_equiv[i] - biofuel_quantity_Q[i] * output['phi_ed'][i] == 0)
        
        # # Constraint: Disallow sugarcane as feedstock - set all sugarcane-based biofuel quantities to zero
        # for i in range(24):
        #     if output['s'][i] == 'sugarcane':
        #         Constraints.append(biofuel_quantity_Q[i] == 0)
        
        # # Constraint: Set sugarcane feedstock quantity to zero (no sugarcane allowed)
        # Constraints.append(feedstock_quantity.loc[feedstock_quantity['s'] == 'sugarcane', 'Q'].item() == 0)



        # Conventional fuel prices
        Fconventionalfuel_pricesD = (
            conventionalfuel_prices.loc[conventionalfuel_prices['F'] == 'D', 'P'].item() -
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'ED_LCFS'].unique()[0] / 1000000) -
            input_demand.loc[input_demand['F'] == 'D', 'PC_F0'].unique()[0]
        )
        Fconventionalfuel_pricesG = (
            conventionalfuel_prices.loc[conventionalfuel_prices['F'] == 'G', 'P'].item() -
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'ED_LCFS'].unique()[0] / 1000000) -
            input_demand.loc[input_demand['F'] == 'G', 'PC_F0'].unique()[0]
        )
        Fconventionalfuel_pricesJ = (
            conventionalfuel_prices.loc[conventionalfuel_prices['F'] == 'J', 'P'].item() -
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'ED_LCFS'].unique()[0] / 1000000) -
            input_demand.loc[input_demand['F'] == 'J', 'PC_F0'].unique()[0]
        )

        Constraints.append(Fconventionalfuel_pricesD == 0)
        Constraints.append(Fconventionalfuel_pricesG == 0)
        Constraints.append(Fconventionalfuel_pricesJ == 0)

        # # Biofuel demand
        # FbiofueldemandB100 = (input_biofuel.loc[input_biofuel['f'] == 'B100', 'phi'].unique()[0] * 
        #                         input_demand.loc[input_demand['F'] == 'D', 'PC_F0'].unique()[0] - 
        #                         biofuel_prices.loc[(biofuel_prices['f'] == 'B100'), 'P'].item())
        # FbiofueldemandRD = (input_biofuel.loc[input_biofuel['f'] == 'RD', 'phi'].unique()[0] * 
        #                     input_demand.loc[input_demand['F'] == 'D', 'PC_F0'].unique()[0] - 
        #                     biofuel_prices.loc[(biofuel_prices['f'] == 'RD'), 'P'].item())
        # FbiofueldemandSAF = (input_biofuel.loc[input_biofuel['f'] == 'SAF', 'phi'].unique()[0] * 
        #                     input_demand.loc[input_demand['F'] == 'J', 'PC_F0'].unique()[0] - 
        #                     biofuel_prices.loc[(biofuel_prices['f'] == 'SAF'), 'P'].item())

        FbiofueldemandB100 = (input_biofuel.loc[input_biofuel['f'] == 'B100', 'phi'].unique()[0] * 
                                conventionalfuel_prices.loc[(conventionalfuel_prices['F'] == 'D'), 'P'].item() - 
                                biofuel_prices.loc[(biofuel_prices['f'] == 'B100'), 'P'].item())
        FbiofueldemandRD = (input_biofuel.loc[input_biofuel['f'] == 'RD', 'phi'].unique()[0] * 
                            conventionalfuel_prices.loc[(conventionalfuel_prices['F'] == 'D'), 'P'].item() - 
                            biofuel_prices.loc[(biofuel_prices['f'] == 'RD'), 'P'].item())
        FbiofueldemandSAF = (input_biofuel.loc[input_biofuel['f'] == 'SAF', 'phi'].unique()[0] * 
                            conventionalfuel_prices.loc[(conventionalfuel_prices['F'] == 'J'), 'P'].item() - 
                            biofuel_prices.loc[(biofuel_prices['f'] == 'SAF'), 'P'].item())

        Constraints.append(FbiofueldemandB100 == 0)
        Constraints.append(FbiofueldemandRD == 0)
        Constraints.append(FbiofueldemandSAF == 0)

        # Biofuel demand for gasE100
        blending_ratio = m.addVar(vtype=GRB.CONTINUOUS, name="blending_ratio")
        m.addConstr(blending_ratio == sum(biofuel_quantity.loc[(biofuel_quantity['f'] == 'gasE100'), 'Q']) / demand_quantity.loc[(demand_quantity['F'] == 'G'), 'Q_actual'].item())

        indicator_var = m.addVar(vtype=GRB.BINARY, name="indicator_var")
        m.addConstr(blending_ratio >= 0.1 + Sigma - M * (1 - indicator_var), name="indicator_var_constr1")
        m.addConstr(blending_ratio <= 0.1 + M * indicator_var, name="indicator_var_constr2")

        # # Modify the constraint to include the indicator variable
        # Constraints.append((input_biofuel.loc[input_biofuel['f'] == 'gasE100', 'phi'].unique()[0] * 
        #                     input_demand.loc[input_demand['F'] == 'G', 'PC_F0'].unique()[0] * 
        #                     (1 - indicator_var * (nlfunc.exp(((sum(biofuel_quantity.loc[(biofuel_quantity['f'] == 'gasE100'), 'Q']) / 
        #                                         demand_quantity.loc[(demand_quantity['F'] == 'G'), 'Q_actual'].item() - 0.1) / 0.02) * 
        #                                         np.log(2)) - 1)) == 
        #                     biofuel_prices.loc[(biofuel_prices['f'] == 'gasE100'), 'P'].item()))

        # # Modify the constraint to include the indicator variable
        # Constraints.append(((input_biofuel.loc[input_biofuel['f'] == 'gasE100', 'phi'].unique()[0] * 
        #                     input_demand.loc[input_demand['F'] == 'G', 'PC_F0'].unique()[0] + 
        #                     P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'CI_LCFS'].unique()[0] *
        #                     conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'ED_LCFS'].unique()[0] / 1000000)) * 
        #                     (1 - indicator_var * (nlfunc.exp(((sum(biofuel_quantity.loc[(biofuel_quantity['f'] == 'gasE100'), 'Q']) / 
        #                                         demand_quantity.loc[(demand_quantity['F'] == 'G'), 'Q_actual'].item() - 0.1) / 0.02) * 
        #                                         np.log(2)) - 1)) == 
        #                     biofuel_prices.loc[(biofuel_prices['f'] == 'gasE100'), 'P'].item()))


        # # Modify the constraint to include the indicator variable
        Constraints.append((input_biofuel.loc[input_biofuel['f'] == 'gasE100', 'phi'].unique()[0] * 
                            conventionalfuel_prices.loc[(conventionalfuel_prices['F'] == 'G'), 'P'].item() * 
                            (1 - indicator_var * (nlfunc.exp(((sum(biofuel_quantity.loc[(biofuel_quantity['f'] == 'gasE100'), 'Q']) / 
                                                demand_quantity.loc[(demand_quantity['F'] == 'G'), 'Q_actual'].item() - 0.1) / 0.02) * 
                                                np.log(2)) - 1)) == 
                            biofuel_prices.loc[(biofuel_prices['f'] == 'gasE100'), 'P'].item()))

        # Add constraints for blend prices
        Constraints.append(sum(Price.loc[(Price['F'] == 'D'), 'P_RIN_LCFS_detach'] * Price.loc[(Price['F'] == 'D'), 'Q_actual']) / 
                            (demand_quantity.loc[(demand_quantity['F'] == 'D'), 'Q'].sum()) == 
                            demand_price.loc[(demand_price['F'] == 'D'), 'P'].item())
        Constraints.append(sum(Price.loc[(Price['F'] == 'G'), 'P_RIN_LCFS_detach'] * Price.loc[(Price['F'] == 'G'), 'Q_actual'])/
                            (demand_quantity.loc[(demand_quantity['F'] == 'G'), 'Q'].sum()) == 
                            demand_price.loc[(demand_price['F'] == 'G'), 'P'].item())
        Constraints.append(sum(Price.loc[(Price['F'] == 'J'), 'P_RIN_LCFS_detach'] * Price.loc[(Price['F'] == 'J'), 'Q_actual'])/
                            (demand_quantity.loc[(demand_quantity['F'] == 'J'), 'Q'].sum()) == 
                            demand_price.loc[(demand_price['F'] == 'J'), 'P'].item())


        # Total demand elasticity
        for fuel in ['D', 'G', 'J']:
            alpha = input_demand.loc[(input_demand['F'] == fuel), 'alpha'].item()
            beta = input_demand.loc[(input_demand['F'] == fuel), 'beta'].item()
            price = demand_price.loc[(demand_price['F'] == fuel), 'P'].item()
            quantity = demand_quantity.loc[(demand_quantity['F'] == fuel), 'Q'].item()
            
            # Create an auxiliary variable for the power term
            power_term = m.addVar(vtype=GRB.CONTINUOUS, name=f"power_term_{fuel}")
            
            # Add the power constraint
            m.addGenConstrPow(price, power_term, beta, name=f"power_constraint_{fuel}")
            
            # Add the elasticity constraint
            Constraints.append(alpha * power_term == quantity)


        # Market clearing - demand equation
        Ddemand = (
            sum(biofuel_quantity.loc[(biofuel_quantity['F'] == 'D') , 'Q_equiv']) +
            conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'D'), 'Q'].sum() -
            demand_quantity.loc[(demand_quantity['F'] == 'D'), 'Q'].item()
        )
        Gdemand = (
            sum(biofuel_quantity.loc[(biofuel_quantity['F'] == 'G'), 'Q_equiv']) +
            conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'G'), 'Q'].sum() -
            demand_quantity.loc[(demand_quantity['F'] == 'G'), 'Q'].item()
        )
        Jdemand = (
            sum(biofuel_quantity.loc[(biofuel_quantity['F'] == 'J'), 'Q_equiv']) +
            conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'J'), 'Q'].sum() -
            demand_quantity.loc[(demand_quantity['F'] == 'J'), 'Q'].item()
        )

        Constraints.append(Ddemand == 0)
        Constraints.append(Gdemand == 0)
        Constraints.append(Jdemand == 0)

        Constraints.append(
            demand_quantity.loc[(demand_quantity['F'] == 'D'), 'Q_actual'].item() -
            (biofuel_quantity.loc[(biofuel_quantity['F'] == 'D'), 'Q'].sum() +
                conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'D'), 'Q'].sum()
            ) == 0
        )
        Constraints.append(
            demand_quantity.loc[(demand_quantity['F'] == 'G'), 'Q_actual'].item() -
            (biofuel_quantity.loc[(biofuel_quantity['F'] == 'G'), 'Q'].sum() +
                conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'G'), 'Q'].sum()
            ) == 0
        )
        Constraints.append(
            demand_quantity.loc[(demand_quantity['F'] == 'J'), 'Q_actual'].item() -
            (biofuel_quantity.loc[(biofuel_quantity['F'] == 'J'), 'Q'].sum() +
                conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'J'), 'Q'].sum()
            ) == 0
        )

        # Price breakup - get obligations
        for i in range(24):
            Constraints.append(
                Price.iloc[i]['RIN_obligation']  == 0
            )

        Constraints.append(
            Price.loc[(Price['f'] == 'B0'), 'RIN_obligation'].item() == 0
        )

        Constraints.append(
            Price.loc[(Price['f'] == 'E0'), 'RIN_obligation'].item() == 0
        )

        for i in range(24):
            Constraints.append(
                Price.iloc[i]['LCFS_CA_obligation']  == 0
            )

        Constraints.append(
            Price.loc[(Price['f'] == 'B0'), 'LCFS_CA_obligation'].item()  == 0
        )

        Constraints.append(
            Price.loc[(Price['f'] == 'E0'), 'LCFS_CA_obligation'].item()  == 0
        )

        # Add the new constraints
        for i in range(24):
            Constraints.append(
                Price.loc[Price.index[i], 'Tax'] - 
                (output['f'][i] == 'SAF') * SAFcredit_prices['P'].item() * output.iloc[i]['SAFcreditheaviside'] == 0
            )

        # Add the new constraints
        for i in range(24):
            Constraints.append(
                Price.loc[Price.index[i], 'Carbon_tax_obligation'] 
                #- (P_carbon_tax * output.loc[output.index[i], 'CI_LCFS'] * output.loc[output.index[i], 'ED_LCFS'] / 1000000) 
                == 0
            )    

        # Add the new constraints
        Constraints.append(
            Price.loc[Price['f'] == 'B0', 'Carbon_tax_obligation'].item() - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        Constraints.append(
            Price.loc[Price['f'] == 'E0', 'Carbon_tax_obligation'].item() - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        Constraints.append(
            Price.loc[Price['f'] == 'J0', 'Carbon_tax_obligation'].item() - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        # Add the new constraints
        # for i in range(24):
        #     Constraints.append(
        #         Price.loc[Price.index[i], 'P_all'] - 
        #         (biofuel_prices.loc[biofuel_prices['f'] == output.loc[output.index[i], 'f'], 'P'].item() + 
        #         (output['f'][i] == 'SAF') * SAFcredit_prices['P'].item() + 
        #         (P_carbon_tax * output.loc[output.index[i], 'CI_LCFS'] * output.loc[output.index[i], 'ED_LCFS'] / 1000000)) == 0
        #     )

        for i in range(24):
            Constraints.append(
                Price.loc[Price.index[i], 'P_all'] - 
                (biofuel_prices.loc[biofuel_prices['f'] == output.loc[output.index[i], 'f'], 'P'].item() + 
                (output['f'][i] == 'SAF') * SAFcredit_prices['P'].item()* output.iloc[i]['SAFcreditheaviside']) == 0
            )

        Constraints.append(
            Price.loc[Price['f'] == 'B0', 'P_all'].item() - 
            input_demand.loc[input_demand['F'] == 'D', 'PC_F0'].unique()[0] - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        Constraints.append(
            Price.loc[Price['f'] == 'E0', 'P_all'].item() - 
            input_demand.loc[input_demand['F'] == 'G', 'PC_F0'].unique()[0] - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        Constraints.append(
            Price.loc[Price['f'] == 'J0', 'P_all'].item() - 
            input_demand.loc[input_demand['F'] == 'J', 'PC_F0'].unique()[0] - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        # for i in range(24):
        #     Constraints.append(
        #         Price.iloc[i]['PC_F0'] - biofuel_prices.loc[(biofuel_prices['f'] == output.iloc[i]['f']), 'P'].item() == 0
        #     )

        for i in range(24):
            Constraints.append(
                Price.iloc[i]['PC_F0'] - (biofuel_prices.loc[(biofuel_prices['f'] == output.iloc[i]['f']), 'P'].item() 
                                          #-(P_carbon_tax * output.loc[output.index[i], 'CI_LCFS'] * output.loc[output.index[i], 'ED_LCFS'] / 1000000)
                                          ) == 0
            )

        Constraints.append(
            Price.loc[(Price['f'] == 'B0'), 'PC_F0'].values[0] -
            input_demand.loc[input_demand['F'] == 'D', 'PC_F0'].values[0] == 0
        )
        Constraints.append(
            Price.loc[(Price['f'] == 'E0'), 'PC_F0'].values[0] -
            input_demand.loc[input_demand['F'] == 'G', 'PC_F0'].values[0] == 0
        )
        Constraints.append(
            Price.loc[(Price['f'] == 'J0'), 'PC_F0'].values[0] -
            input_demand.loc[input_demand['F'] == 'J', 'PC_F0'].values[0] == 0
        )

        # Add the new constraints
        # for i in range(24):
        #     Constraints.append(
        #         Price.loc[Price.index[i], 'P_RIN_LCFS_detach'] - 
        #         (biofuel_prices.loc[biofuel_prices['f'] == output.loc[output.index[i], 'f'], 'P'].item() + 
        #         (P_carbon_tax * output.loc[output.index[i], 'CI_LCFS'] * output.loc[output.index[i], 'ED_LCFS'] / 1000000)) == 0
        #     )

        for i in range(24):
            Constraints.append(
                Price.loc[Price.index[i], 'P_RIN_LCFS_detach'] - 
                (biofuel_prices.loc[biofuel_prices['f'] == output.loc[output.index[i], 'f'], 'P'].item()) == 0
            )
        
        Constraints.append(
            Price.loc[Price['f'] == 'B0', 'P_RIN_LCFS_detach'].item() - 
            input_demand.loc[input_demand['F'] == 'D', 'PC_F0'].unique()[0] - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        Constraints.append(
            Price.loc[Price['f'] == 'E0', 'P_RIN_LCFS_detach'].item() - 
            input_demand.loc[input_demand['F'] == 'G', 'PC_F0'].unique()[0] - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        Constraints.append(
            Price.loc[Price['f'] == 'J0', 'P_RIN_LCFS_detach'].item() - 
            input_demand.loc[input_demand['F'] == 'J', 'PC_F0'].unique()[0] - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        # for i in range(24):
        #     Constraints.append(
        #         Price.loc[Price.index[i], 'P_RIN_detach'] - 
        #         (biofuel_prices.loc[biofuel_prices['f'] == output.loc[output.index[i], 'f'], 'P'].item() + 
        #         (P_carbon_tax * output.loc[output.index[i], 'CI_LCFS'] * output.loc[output.index[i], 'ED_LCFS'] / 1000000)) == 0
        #     )

        for i in range(24):
            Constraints.append(
                Price.loc[Price.index[i], 'P_RIN_detach'] - 
                (biofuel_prices.loc[biofuel_prices['f'] == output.loc[output.index[i], 'f'], 'P'].item() ) == 0
            )

        Constraints.append(
            Price.loc[Price['f'] == 'B0', 'P_RIN_detach'].item() - 
            input_demand.loc[input_demand['F'] == 'D', 'PC_F0'].unique()[0] - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        Constraints.append(
            Price.loc[Price['f'] == 'E0', 'P_RIN_detach'].item() - 
            input_demand.loc[input_demand['F'] == 'G', 'PC_F0'].unique()[0] - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )

        Constraints.append(
            Price.loc[Price['f'] == 'J0', 'P_RIN_detach'].item() - 
            input_demand.loc[input_demand['F'] == 'J', 'PC_F0'].unique()[0] - 
            P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'CI_LCFS'].unique()[0] *
                            conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'ED_LCFS'].unique()[0] / 1000000) == 0
        )


        for i in range(24):
            Constraints.append(
                Price.iloc[i]['Q_actual'] - biofuel_quantity.iloc[i]['Q'] == 0
            )

        Constraints.append(
            Price.loc[(Price['f'] == 'B0'), 'Q_actual'].item() -
            conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'D'), 'Q'].item() == 0
        )
        Constraints.append(
            Price.loc[(Price['f'] == 'E0'), 'Q_actual'].item() -
            conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'G'), 'Q'].item() == 0
        )
        Constraints.append(
            Price.loc[(Price['f'] == 'J0'), 'Q_actual'].item() -
            conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'J'), 'Q'].item() == 0
        )

        # Price breakup - get obligations
        for i in range(24):
            Constraints.append(
                Price.iloc[i]['Q_equiv'] - biofuel_quantity.iloc[i]['Q_equiv'] == 0
            )

        Constraints.append(
            Price.loc[(Price['f'] == 'B0'), 'Q_equiv'].item() -
            conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'D'), 'Q'].item() == 0
        )
        Constraints.append(
            Price.loc[(Price['f'] == 'E0'), 'Q_equiv'].item() -
            conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'G'), 'Q'].item() == 0
        )
        Constraints.append(
            Price.loc[(Price['f'] == 'J0'), 'Q_equiv'].item() -
            conventionalfuel_quantity.loc[(conventionalfuel_quantity['F'] == 'J'), 'Q'].item() == 0
        )


        # Define the feedstocks
        feedstocks = ['soyoil', 'animalfat', 'corn', 'sugarcane']
        #feedstocks = ['soyoil', 'animalfat', 'corn']

        # Loop through each feedstock and add the corresponding constraint
        for feedstock in feedstocks:
            Constraints.append(
                feedstock_quantity.loc[feedstock_quantity['s'] == feedstock, 'Q'].item() ==
                input_feedstock.loc[input_feedstock['s'] == feedstock, 'alpha'].item() *
                feedstock_prices.loc[feedstock_prices['s'] == feedstock, 'P'].item() **
                input_feedstock.loc[input_feedstock['s'] == feedstock, 'beta'].item()
            )

        # Calculate the demand for each feedstock
        for feedstock in feedstocks:
            demand = (
                sum(biofuel_quantity.loc[biofuel_quantity['s'] == feedstock, 'Conversion_demand'] * 
                    biofuel_quantity.loc[biofuel_quantity['s'] == feedstock, 'Q']) - 
                feedstock_quantity.loc[feedstock_quantity['s'] == feedstock, 'Q'].item()
            )
            Constraints.append(demand == 0)

        # SAF goal

        # Create binary variable for SAFCreditzeta
        SAFCreditzeta = m.addVar(vtype=GRB.BINARY, name="SAFCreditzeta")

        # Add constraints for SAF credit prices and biofuel quantities
        Constraints.append(SAFcredit_prices.loc['SAF', 'P'] >= 0)
        Constraints.append(SAFcredit_prices.loc['SAF', 'P'] <= (1 - SAFCreditzeta) * M)

        # Calculate the sum of SAF biofuel quantities
        #sum_SAF_biofuel_quantity = biofuel_quantity.loc[biofuel_quantity['f'] == 'SAF', 'Q'].sum()
        sum_SAF_biofuel_quantity = biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['SAFcreditheaviside'] == 1), 'Q'].sum()


        # Add constraints for SAF biofuel quantities
        Constraints.append(sum_SAF_biofuel_quantity - input_compliance.loc[input_compliance['mandate'] == 'SAF', 'Q'].item() >= 0)
        Constraints.append(sum_SAF_biofuel_quantity - input_compliance.loc[input_compliance['mandate'] == 'SAF', 'Q'].item() <= SAFCreditzeta * M)

        # # Create binary variables for PD4zeta and PD6zeta
        # PD4zeta = m.addVar(vtype=GRB.BINARY, name="PD4zeta")
        # PD6zeta = m.addVar(vtype=GRB.BINARY, name="PD6zeta")

        # # Add constraints for RIN prices and biofuel quantities
        # Constraints.append((RIN_prices.loc['D4', 'P'] - RIN_prices.loc['D6', 'P']) >= 0)
        # Constraints.append((RIN_prices.loc['D4', 'P'] - RIN_prices.loc['D6', 'P']) <= (1 - PD4zeta) * M)

        # Constraints.append((biofuel_quantity.loc[biofuel_quantity['f'].isin(['B100', 'RD', 'SAF']), 'Q'].sum() -
        #     RVO_percent.loc['BBD', 'P'] / 1.6 * conventionalfuel_quantity.loc[conventionalfuel_quantity['F'].isin(['G', 'D']), 'Q'].sum()) >= 0)
        # Constraints.append((biofuel_quantity.loc[biofuel_quantity['f'].isin(['B100', 'RD', 'SAF']), 'Q'].sum() -
        #     RVO_percent.loc['BBD', 'P'] / 1.6 * conventionalfuel_quantity.loc[conventionalfuel_quantity['F'].isin(['G', 'D']), 'Q'].sum()) <= PD4zeta * M)

        # Constraints.append(RIN_prices.loc['D6', 'P'] >= 0)
        # Constraints.append(RIN_prices.loc['D6', 'P'] <= (1 - PD6zeta) * M)

        # Constraints.append((sum((biofuel_quantity.loc[biofuel_quantity['f'] == 'B100', 'kappa_RFS'] * biofuel_quantity.loc[biofuel_quantity['f'] == 'B100', 'Q'])) + sum(biofuel_quantity.loc[biofuel_quantity['f'] == 'RD', 'kappa_RFS'] * biofuel_quantity.loc[biofuel_quantity['f'] == 'RD', 'Q']) + sum(biofuel_quantity.loc[biofuel_quantity['f'] == 'SAF', 'kappa_RFS'] * biofuel_quantity.loc[biofuel_quantity['f'] == 'SAF', 'Q']) + sum(biofuel_quantity.loc[biofuel_quantity['f'] == 'gasE100', 'kappa_RFS'] * biofuel_quantity.loc[biofuel_quantity['f'] == 'gasE100', 'Q']) - RVO_percent.loc['RF', 'P'] * conventionalfuel_quantity.loc[conventionalfuel_quantity['F'].isin(['G', 'D']), 'Q'].sum()) >= 0)
        # Constraints.append((sum((biofuel_quantity.loc[biofuel_quantity['f'] == 'B100', 'kappa_RFS'] * biofuel_quantity.loc[biofuel_quantity['f'] == 'B100', 'Q'])) + sum(biofuel_quantity.loc[biofuel_quantity['f'] == 'RD', 'kappa_RFS'] * biofuel_quantity.loc[biofuel_quantity['f'] == 'RD', 'Q']) +sum(biofuel_quantity.loc[biofuel_quantity['f'] == 'SAF', 'kappa_RFS'] * biofuel_quantity.loc[biofuel_quantity['f'] == 'SAF', 'Q']) +sum(biofuel_quantity.loc[biofuel_quantity['f'] == 'gasE100', 'kappa_RFS'] * biofuel_quantity.loc[biofuel_quantity['f'] == 'gasE100', 'Q']) - RVO_percent.loc['RF', 'P'] * conventionalfuel_quantity.loc[conventionalfuel_quantity['F'].isin(['G', 'D']), 'Q'].sum()) <= PD6zeta * M)


        # # Define variables
        # AlphaLCFS = m.addVar(vtype=GRB.CONTINUOUS, name="AlphaLCFS")
        # Alpha2LCFS = m.addVar(vtype=GRB.CONTINUOUS, name="Alpha2LCFS")

        # # LCFS clearance constraints
        # Constraints.append(LCFS_prices_P - AlphaLCFS * P_cap == 0)
        # Constraints.append(AlphaLCFS >= 0)
        # Constraints.append(AlphaLCFS <= 1)

        # # Calculate DeltaCI
        # DeltaCI_expr = (
        #     sum(biofuel_quantity.loc[biofuel_quantity['j'] == 'CA', 'Q'] *
        #         (biofuel_quantity.loc[biofuel_quantity['j'] == 'CA', 'CI_std_LCFS'] - biofuel_quantity.loc[biofuel_quantity['j'] == 'CA', 'CI_LCFS']) *
        #         biofuel_quantity.loc[biofuel_quantity['j'] == 'CA', 'ED_LCFS']) +
        #     sum(input_compliance.loc[input_compliance['mandate'] == 'LCFS_Q', 'Q']) -
        #     sum(conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'D'), 'Q'] *
        #         (-conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'D'), 'CI_std_LCFS'] +
        #          conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'D'), 'CI_LCFS']) *
        #         conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'D'), 'ED_LCFS']) -
        #     sum(conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'G'), 'Q'] *
        #         (-conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'G'), 'CI_std_LCFS'] +
        #          conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'G'), 'CI_LCFS']) *
        #         conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'G'), 'ED_LCFS'])
        # )

        # Constraints.append(LCFS_prices_P * DeltaCI_expr <= 0)
        # Constraints.append((LCFS_prices_P - P_cap) * DeltaCI_expr <= 0)

        # # Alpha2LCFS constraints
        # Constraints.append(Alpha2LCFS - AlphaLCFS * (1 - AlphaLCFS) == 0)
        # Constraints.append(Alpha2LCFS * DeltaCI_expr == 0)


        # Add constraints to the model
        for constraint in Constraints:
            m.addConstr(constraint)


        #m.Params.FeasibilityTol = 2e-7
        m.Params.FeasibilityTol = 2e-7
        m.Params.OptimalityTol = 1e-7
        m.Params.NumericFocus = 1       
        # # Add these parameters before m.optimize()
        # m.Params.NumericFocus = 3  # Maximum focus on numerical stability
        # m.Params.FeasibilityTol = 2e-7  # Relax feasibility tolerance
        # m.Params.OptimalityTol = 1e-7   # Relax optimality tolerance
        # m.Params.ScaleFlag = 2          # Aggressive scaling
        # m.Params.Quad = 1               # Use quad precision


        m.optimize()

        if m.status == GRB.OPTIMAL:
            print(f"Solution found for break {break_idx}")
            print(f"Break {break_idx}: break = {break_val}, val = {val}")
            
            # Store objective value for this break
            objective_values.append({
                'Break': break_idx,
                'Break_Value': break_val,
                'Val': val,
                'Objective_Value': m.ObjVal,
                'Total_Profit': 0,  # Will be updated after total_profit calculation
                'State_tax': state_tax_profit
                #'Denominator': denominator.X  # Add denominator value
            })

            # with open(f'results/variables_break{break_idx}.txt', 'w') as f:
            #     f.write(f"Objective value: {m.ObjVal}\n")  # <-- Add this line
            #     DeltaCI_value = DeltaCI_expr.getValue()
            #     f.write(f"DeltaCI_expr value: {DeltaCI_value:g}\n")
            #     for v in m.getVars():
            #         f.write(f"{v.VarName} {v.X:g}\n")

            # # After m.optimize() and if m.status == GRB.OPTIMAL:
            # with open(f'results/hefa_value_break{break_idx}1.txt', 'w') as f:
            #     for i in range(2):
            #         f.write(f"hefa_value[{i}] = {hefa_value[i].X}\n")

            names = [
                'B100-soyoil-CA', 'B100-animalfat-CA', 'RD-soyoil-CA', 'RD-animalfat-CA', 'SAF-animalfat-CA', 'gasE100-corn-CA',
                'B100-soyoil-NC', 'B100-animalfat-NC', 'RD-soyoil-NC', 'RD-animalfat-NC', 'SAF-animalfat-NC', 'gasE100-corn-NC',
                'gasE100-sugarcane-CA', 'gasE100-sugarcane-NC', 'SAF-soyoil-CA', 'SAF-soyoil-NC', 'SAF-sugarcane-ETJ-CA', 'SAF-sugarcane-ETJCCS-CA',
                'SAF-corn-ETJ-CA', 'SAF-corn-ETJCCS-CA', 'SAF-sugarcane-ETJ-NC', 'SAF-sugarcane-ETJCCS-NC', 'SAF-corn-ETJ-NC', 'SAF-corn-ETJCCS-NC'
            ]
            
            # Collect results for each term in a list of dicts
            results = []
            for i in range(24):
                # v1 = biofuel_prices.loc[(biofuel_prices['f'] == output['f'][i]) & (biofuel_prices['j'] == output['j'][i]), 'P'].item().X
                v1 = biofuel_prices.loc[(biofuel_prices['f'] == output['f'][i]), 'P'].item().X
                #v2 = output['PC'][i] + output['Conversion'][i] * feedstock_prices.loc[feedstock_prices['s'] == output['s'][i], 'P'].item().X
                v2 = (output['PC'][i] + output['Conversion'][i] * feedstock_prices.loc[feedstock_prices['s'] == output['s'][i], 'P'].item().X*(1+duty_e100sugarcane*(output['s'][i] == 'sugarcane')))
                #v3 = output['kappa_RFS'][i] * RIN_prices.loc[RIN_prices['fueltype'].str.contains(output['f'][i]), 'P'].item().X
                # v4 = 1 * ((output['f'][i] == 'B100') | (output['f'][i] == 'RD') | (output['f'][i] == 'gasE100')) * ((47.39 - output['CI_Tax'][i]) / 47.39) * output['Taxheavyside'][i] +  max([
                #     1 * (output['f'][i] == 'SAF') * ((47.39 - output['CI_Tax'][i]) / 47.39) * output['Taxheavyside'][i],
                #     85 * 30 * output['ED_LCFS'][i] / (10**6) * output['CCS_tech'][i]
                # ])
                v3 = 0
                v4 = 0
                #v5 = 0
                v5 = (output['f'][i] == 'SAF') * SAFcredit_prices['P'].item().X * output.iloc[i]['SAFcreditheaviside']
                # v6 = LCFS_prices['P'][0].X * (output['CI_std_LCFS'][i] - output['CI_LCFS'][i]) * output['ED_LCFS'][i] * (output['j'][i] == 'CA') / 1000000
                v6 = 0
                #v7 = ((output['f'][i] == 'SAF') & (output['j'][i] == 'NC')) * output['Taxheavyside'][i] * val
                v7 = 0
                v8 = mu['value'][i].X
                #v9 = nu.loc[(nu['f'] == output['f'][i]) & (nu['j'] == output['j'][i]), 'value'].item().X
                v9 = nu.loc[(nu['f'] == output['f'][i]), 'value'].item().X
                # v10 = - ((output['f'][i] == 'SAF') & (output['j'][i] == 'NC')) * output['Taxheavyside'][i]* diracdeltalb_value.X + ((output['f'][i] == 'SAF') & (output['j'][i] == 'NC')) * output['Taxheavyside'][i]* diracdeltaub_value.X
                v10 = 0
                v11 = biofuel_quantity_Q[i].X
                v12 = v1 - v2 + v3 + v4 + v5 + v6 + v7
                v13 =  - hefa_value[0].X * ((output['f'][i] == 'SAF') & (output['s'][i] == 'soyoil')) + hefa_value[0].X * 5.5/2.5 * ((output['f'][i] == 'RD') & (output['s'][i] == 'soyoil')) - hefa_value[1].X * ((output['f'][i] == 'SAF') & (output['s'][i] == 'animalfat')) + hefa_value[1].X * 5.5/2.5 * ((output['f'][i] == 'RD') & (output['s'][i] == 'animalfat'))
                #v14 = P_carbon_tax * output['CI_LCFS'][i] * output['ED_LCFS'][i] / 1000000
                v14 = 0
                total = v1 - v2 + v3 + v4 + v5 + v6 + v7 + v8  - v9 - v10 + v13 + v14
                # ... calculate v1, v2, ..., v11 ...
                results.append({
                    'i': i,
                    'Name': names[i],
                    'fuel': output['f'][i],
                    'state': output['j'][i],
                    'biofuel_price': v1,
                    'production_cost': v2,
                    'RIN': v3,
                    '45Z_tax': v4,
                    'SAF_credit': v5,
                    'LCFS_CA': v6,
                    'state_tax': v7,
                    'mu': v8,
                    'nu': v9,
                    'dirac_delta': v10,
                    'hefa':v13,
                    'FOC': total,
                    'quantity': v11,
                    'break_idx': break_idx,
                    'break_val': break_val,
                    'val': val,
                    'profit':v12,
                    'Carbon_tax':v14
                })
        
            # Save to spreadsheet for this break
            df_results = pd.DataFrame(results)
            #df_results = df_results.sort_values(by=['state','fuel'])
            #total_profit = (df_results['profit'] * df_results['quantity']).sum()
            total_profit = (df_results['profit'] * df_results['quantity']).sum() + state_tax_profit

            # for step function - state tax, total profit is not just marginal, but also need to include the previous fixed amount part
            
            # Update objective values to include total profit
            objective_values[-1]['Total_Profit'] = total_profit

            
            if total_profit > max_total_profit:
                max_total_profit = total_profit
                best_df = df_results.copy()
                best_break_idx = break_idx
                best_demand_quantity = demand_quantity.copy()
                best_model = m  # Save the best model
                best_val = val  # <-- Add this line

            # # Instead of comparing total_profit, update best result if solution exists
            # max_total_profit = total_profit
            # best_df = df_results.copy()
            # best_break_idx = break_idx
            # best_demand_quantity = demand_quantity.copy()
            # best_model = m  # Save the best model
            # best_val = val  # <-- Add this line

            
            #df_results.to_excel(f'results/terms_breakdown_break{break_idx}.xlsx', index=False)
            
            # Save demand_quantity DataFrame to spreadsheet for this break
            demand_quantity_out = demand_quantity.copy()
            demand_quantity_out['Q'] = [q.X if hasattr(q, 'X') else q for q in demand_quantity_out['Q']]
            demand_quantity_out['Q_actual'] = [q.X if hasattr(q, 'X') else q for q in demand_quantity_out['Q_actual']]
            #demand_quantity_out.to_excel(f'results/demand_quantity_break{break_idx}.xlsx', index=False)

        else:
            print(f"No solution for break {break_idx}, status: {m.status}")
            # Store result even for infeasible solutions
            objective_values.append({
                'Break': break_idx,
                'Break_Value': break_val,
                'Val': val,
                'Objective_Value': None if m.status != GRB.OPTIMAL else m.ObjVal,
                'Total_Profit': None
            })
            continue  # Skip to next break

    # After the loop
    if best_df is not None:
        best_df.to_excel(os.path.join(results_dir, 'terms_breakdown_best.xlsx'), index=False)
        print(f"Best break_idx: {best_break_idx}, max total profit: {max_total_profit}")

        # Save demand_quantity DataFrame for the best solution
        demand_quantity_out = best_demand_quantity.copy()
        demand_quantity_out['Q'] = [q.X if hasattr(q, 'X') else q for q in demand_quantity_out['Q']]
        demand_quantity_out['Q_actual'] = [q.X if hasattr(q, 'X') else q for q in demand_quantity_out['Q_actual']]
        demand_quantity_out.to_excel(os.path.join(results_dir, 'demand_quantity_best.xlsx'), index=False)
        
    # Save objective values to Excel file (regardless of whether best solution exists)
    if objective_values:
        objective_df = pd.DataFrame(objective_values)
        # Add a column to indicate which is the best solution
        if best_break_idx is not None:
            objective_df['Is_Best'] = objective_df['Break'] == best_break_idx
        else:
            objective_df['Is_Best'] = False
        
        objective_df.to_excel(os.path.join(results_dir, 'objective_values.xlsx'), index=False)
        print(f"Objective values saved to {os.path.join(results_dir, 'objective_values.xlsx')}")
        
        # Display summary
        print("\nObjective Values Summary:")
        for _, row in objective_df.iterrows():
            status = " (BEST)" if row['Is_Best'] else ""
            if row['Objective_Value'] is not None:
                profit_str = f", Total Profit: {row['Total_Profit']:.6f}" if row['Total_Profit'] is not None else ""
                print(f"Break {row['Break']}: Objective: {row['Objective_Value']:.6f}{profit_str}{status}")
            else:
                print(f"Break {row['Break']}: No solution{status}")
    
    if best_df is not None:
        # Print and save variable values for the best model
        variables_data = []
        
        with open(os.path.join(results_dir, 'variables_best.txt'), 'w') as f:
            for v in best_model.getVars():
                var_name = v.VarName
                var_value = v.X
                
                print(f"{var_name} {var_value:g}")
                f.write(f"{var_name} {var_value:g}\n")
                
                # Collect data for Excel file
                variables_data.append({
                    'Variable_Name': var_name,
                    'Value': var_value
                })
        
        # Create and save Excel file for variables
        variables_df = pd.DataFrame(variables_data)
        variables_df.to_excel(os.path.join(results_dir, 'variables_best.xlsx'), index=False)
        
        print(f"Best solution variables saved to {os.path.join(results_dir, 'variables_best.xlsx')}")

        # # Define the Intermediate_var DataFrame
        Intermediate_var = pd.DataFrame({
            'Name': ['B100-soyoil-CA', 'B100-animalfat-CA', 'RD-soyoil-CA', 'RD-animalfat-CA', 'SAF-animalfat-CA', 'gasE100-corn-CA',
                    'B100-soyoil-NC', 'B100-animalfat-NC', 'RD-soyoil-NC', 'RD-animalfat-NC', 'SAF-animalfat-NC', 'gasE100-corn-NC',
                    'gasE100-sugarcane-CA', 'gasE100-sugarcane-NC', 'SAF-soyoil-CA', 'SAF-soyoil-NC', 'SAF-sugarcane-ETJ-CA', 'SAF-sugarcane-ETJCCS-CA',
                    'SAF-corn-ETJ-CA', 'SAF-corn-ETJCCS-CA', 'SAF-sugarcane-ETJ-NC', 'SAF-sugarcane-ETJCCS-NC', 'SAF-corn-ETJ-NC', 'SAF-corn-ETJCCS-NC',
                    'B0', 'E0', 'J0'],
            'RIN_obligation': [0]*27,
            'LCFS_CA_obligation': [0]*27,
            'Tax': [0]*27,
            'Carbon_tax_obligation': [0]*27,
            'P_all': [0]*27,
            'PC_F0': [0]*27,
            'P_RIN_LCFS_detach': [0]*27,
            'P_RIN_detach': [0]*27,
            'Q_actual': [0]*27,
            'Q_equiv': [0]*27,
            'RFS_road': [0]*27,
            'RFS_jet': [0]*27,
            'LCFS': [0]*27,
            'TC': [0]*27,
            'TC_IRA': [0]*27,
            'TC_45Z': [0]*27,
            'TC_45Q': [0]*27,
            'TC_state': [0]*27,
            'TC_SAF': [0]*27,
            'Subsidy': [0]*27,
            'Production_cost': [0]*27,
            'Fixed_production_cost': [0]*27,
            'Feedstock_cost': [0]*27,
            'mu_value': [0]*27,
            'nu_value': [0]*27,
            'etj_value': [0]*27,
            'foc': [0]*27
        })

        # Calculate the values for each row using best_model
        for i in range(24):
            # Intermediate_var.at[i, 'RFS_road'] = (
            #     (output['f'][i] in ['B100', 'RD', 'gasE100'])
            #     * output['kappa_RFS'][i]
            #     * best_model.getVarByName(RIN_prices.loc[RIN_prices['fueltype'].str.contains(output['f'][i]), 'P'].item().VarName).X
            # )
            # Intermediate_var.at[i, 'RFS_jet'] = (
            #     (output['f'][i] == 'SAF')
            #     * output['kappa_RFS'][i]
            #     * best_model.getVarByName(RIN_prices.loc[RIN_prices['fueltype'].str.contains(output['f'][i]), 'P'].item().VarName).X
            # )
            # Intermediate_var.at[i, 'LCFS'] = (
            #     best_model.getVarByName(LCFS_prices['P'][0].VarName).X
            #     * (output['CI_std_LCFS'][i] - output['CI_LCFS'][i])
            #     * (output['j'][i] == 'CA')
            #     * output['ED_LCFS'][i] / 1000000
            # )
            #Intermediate_var.at[i, 'LCFS'] = 0
            Intermediate_var.at[i, 'TC'] = (output['f'][i] == 'SAF') * best_model.getVarByName(SAFcredit_prices['P'].item().VarName).X * output.iloc[i]['SAFcreditheaviside']
            # Intermediate_var.at[i, 'TC_IRA'] = (
            #     1 * (output['f'][i] in ['B100', 'RD', 'gasE100'])
            #     * ((47.39 - output['CI_Tax'][i]) / 47.39)
            #     * output['Taxheavyside'][i]
            #     + max(
            #         1 * (output['f'][i] == 'SAF')
            #         * ((47.39 - output['CI_Tax'][i]) / 47.39)
            #         * output['Taxheavyside'][i],
            #         85 * 30 * output['ED_LCFS'][i] / (10**6) * output['CCS_tech'][i]
            #     )
            # )
            # Intermediate_var.at[i, 'TC_45Z'] = (
            #     1 * (output['f'][i] in ['B100', 'RD', 'gasE100'])
            #     * ((47.39 - output['CI_Tax'][i]) / 47.39)
            #     * output['Taxheavyside'][i]
            #     + (
            #         1 * (output['f'][i] == 'SAF')
            #         * ((47.39 - output['CI_Tax'][i]) / 47.39)
            #         * output['Taxheavyside'][i]
            #         > 85 * 30 * output['ED_LCFS'][i] / (10**6) * output['CCS_tech'][i]
            #     )
            #     * 1 * (output['f'][i] == 'SAF')
            #     * ((47.39 - output['CI_Tax'][i]) / 47.39)
            #     * output['Taxheavyside'][i]
            # )
            # Intermediate_var.at[i, 'TC_45Q'] = (
            #     (
            #         85 * 30 * output['ED_LCFS'][i] / (10**6) * output['CCS_tech'][i]
            #         > 1 * (output['f'][i] == 'SAF')
            #         * ((47.39 - output['CI_Tax'][i]) / 47.39)
            #         * output['Taxheavyside'][i]
            #     )
            #     * 85 * 30 * output['ED_LCFS'][i] / (10**6) * output['CCS_tech'][i]
            # )
            # Intermediate_var.at[i, 'TC_state'] = best_val * (output['f'][i] == 'SAF') * (output['j'][i] == 'NC') * output['Taxheavyside'][i]
            Intermediate_var.at[i, 'TC_SAF'] = (output['f'][i] == 'SAF') * best_model.getVarByName(SAFcredit_prices['P'].item().VarName).X * output.iloc[i]['SAFcreditheaviside']
            #Intermediate_var.at[i, 'TC_SAF'] = 0
            #Intermediate_var.at[i, 'Carbon_tax'] = P_carbon_tax * output['CI_LCFS'][i] * output['ED_LCFS'][i] / 1000000
            Intermediate_var.at[i, 'Carbon_tax'] = 0
            Intermediate_var.at[i, 'Subsidy'] = (
                Intermediate_var.at[i, 'RFS_road']
                + Intermediate_var.at[i, 'RFS_jet']
                + Intermediate_var.at[i, 'LCFS']
                + Intermediate_var.at[i, 'TC']
            )
            Intermediate_var.at[i, 'Production_cost'] = (
                output['PC'][i]
                + output['Conversion'][i]
                * best_model.getVarByName(feedstock_prices.loc[feedstock_prices['s'] == output['s'][i], 'P'].item().VarName).X *(1+duty_e100sugarcane*(output['s'][i] == 'sugarcane'))
            )
            Intermediate_var.at[i, 'Fixed_production_cost'] = output['PC'][i]
            Intermediate_var.at[i, 'Feedstock_cost'] = (
                output['Conversion'][i]
                * best_model.getVarByName(feedstock_prices.loc[feedstock_prices['s'] == output['s'][i], 'P'].item().VarName).X *(1+duty_e100sugarcane*(output['s'][i] == 'sugarcane'))
            )
            Intermediate_var.at[i, 'mu_value'] = best_model.getVarByName(mu['value'][i].VarName).X
            # Intermediate_var.at[i, 'nu_value'] = best_model.getVarByName(
            #     nu.loc[(nu['f'] == output['f'][i]) & (nu['j'] == output['j'][i]), 'value'].item().VarName
            # ).X
            Intermediate_var.at[i, 'nu_value'] = best_model.getVarByName(
                nu.loc[(nu['f'] == output['f'][i]), 'value'].item().VarName
            ).X
            # Intermediate_var.at[i, 'etj_value'] = - ((output['f'][i] == 'SAF') & (output['j'][i] == 'NC')) * output['Taxheavyside'][i]* best_model.getVarByName('diracdeltalb_value').X + ((output['f'][i] == 'SAF') & (output['j'][i] == 'NC')) * output['Taxheavyside'][i]* best_model.getVarByName('diracdeltaub_value').X
            Intermediate_var.at[i, 'foc'] = (
                best_model.getVarByName(biofuel_prices.loc[(biofuel_prices['f'] == output['f'][i]), 'P'].item().VarName).X
                - (output['PC'][i]
                + output['Conversion'][i]
                * best_model.getVarByName(feedstock_prices.loc[feedstock_prices['s'] == output['s'][i], 'P'].item().VarName).X*(1+duty_e100sugarcane*(output['s'][i] == 'sugarcane')))
                + (output['f'][i] == 'SAF') * best_model.getVarByName(SAFcredit_prices['P'].item().VarName).X * output.iloc[i]['SAFcreditheaviside']
                #- P_carbon_tax * output['CI_LCFS'][i] * output['ED_LCFS'][i] / 1000000
                # + output['kappa_RFS'][i] * best_model.getVarByName(RIN_prices.loc[RIN_prices['fueltype'].str.contains(output['f'][i]), 'P'].item().VarName).X
                # + 1 * ((output['f'][i] == 'B100') | (output['f'][i] == 'RD') | (output['f'][i] == 'gasE100'))
                # * ((47.39 - output['CI_Tax'][i]) / 47.39)
                # * output['Taxheavyside'][i]
                # + max([
                #     1 * (output['f'][i] == 'SAF')
                #     * ((47.39 - output['CI_Tax'][i]) / 47.39)
                #     * output['Taxheavyside'][i],
                #     85 * 30 * output['ED_LCFS'][i] / (10**6) * output['CCS_tech'][i]
                # ])
                # + (best_model.getVarByName(LCFS_prices['P'][0].VarName).X
                # * (output['CI_std_LCFS'][i] - output['CI_LCFS'][i])
                # * output['ED_LCFS'][i]
                # * (output['j'][i] == 'CA') / 1000000)
                + best_model.getVarByName(mu['value'][i].VarName).X
                # - best_model.getVarByName(
                #     nu.loc[(nu['f'] == output['f'][i]) & (nu['j'] == output['j'][i]), 'value'].item().VarName
                # ).X
                - best_model.getVarByName(
                    nu.loc[(nu['f'] == output['f'][i]), 'value'].item().VarName
                ).X
                # + ((output['f'][i] == 'SAF') & (output['j'][i] == 'NC')) * output['Taxheavyside'][i] * best_val
                # - ((output['f'][i] == 'SAF') & (output['j'][i] == 'NC')) * output['Taxheavyside'][i]* best_model.getVarByName('diracdeltalb_value').X + ((output['f'][i] == 'SAF') & (output['j'][i] == 'NC')) * output['Taxheavyside'][i]* best_model.getVarByName('diracdeltaub_value').X 
                - best_model.getVarByName('hefa_value[0]').X * ((output['f'][i] == 'SAF') & (output['s'][i] == 'soyoil')) 
                + best_model.getVarByName('hefa_value[0]').X * 5.5/2.5 * ((output['f'][i] == 'RD') & (output['s'][i] == 'soyoil')) 
                - best_model.getVarByName('hefa_value[1]').X * ((output['f'][i] == 'SAF') & (output['s'][i] == 'animalfat')) 
                + best_model.getVarByName('hefa_value[1]').X * 5.5/2.5 * ((output['f'][i] == 'RD') & (output['s'][i] == 'animalfat'))
            )
        
        # # Assign values from the Price DataFrame to Intermediate_var
        # for col in ['RIN_obligation', 'LCFS_CA_obligation', 'Tax', 'P_all', 'PC_F0', 'P_RIN_LCFS_detach', 'P_RIN_detach', 'Q_actual', 'Q_equiv']:
        #     Intermediate_var[col] = [Price.at[i, col].X for i in Price.index]

        # Assign values from the Price DataFrame to Intermediate_var using best_model
        for col in ['RIN_obligation', 'LCFS_CA_obligation']:
            Intermediate_var.loc[:23, col] = [
                best_model.getVarByName(Price.at[i, col].VarName).X for i in Price.index[:24]
            ]
            Intermediate_var.loc[24:, col] = [
                -best_model.getVarByName(Price.at[i, col].VarName).X for i in Price.index[24:]
            ]

        for col in ['Tax','Carbon_tax_obligation', 'P_all', 'PC_F0', 'P_RIN_LCFS_detach', 'P_RIN_detach', 'Q_actual', 'Q_equiv']:
            Intermediate_var[col] = [
                best_model.getVarByName(Price.at[i, col].VarName).X for i in Price.index
            ]

        # Update the Carbon_Tax column for specific rows
        Intermediate_var.loc[24:26, 'Carbon_tax'] = Intermediate_var.loc[24:26, 'Carbon_tax_obligation']
    
        output_dir1 = os.path.join(results_dir, 'Intermediate_results')
        os.makedirs(output_dir1, exist_ok=True)

        # Function to append data to an existing Excel file
        def append_to_excel(file_path, df, sheet_name):
            try:
                # Load the existing workbook
                with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    # Write the DataFrame to the specified sheet
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
            except FileNotFoundError:
                # If the file does not exist, create a new one
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name=sheet_name)

        if k == 0:
            append_to_excel(os.path.join(output_dir1, 'Mean.xlsx'), Intermediate_var, 'Carbon_tax')

        if k == 1:
            append_to_excel(os.path.join(output_dir1, '10th.xlsx'), Intermediate_var, 'Carbon_tax')

        if k == 2:
            append_to_excel(os.path.join(output_dir1, '33th.xlsx'), Intermediate_var, 'Carbon_tax')

        if k == 3:
            append_to_excel(os.path.join(output_dir1, '67th.xlsx'), Intermediate_var, 'Carbon_tax') 

        if k == 4:
            append_to_excel(os.path.join(output_dir1, '90th.xlsx'), Intermediate_var, 'Carbon_tax')
                               
                                    

        # # Read the external file into a DataFrame
        # Intermediate_input = pd.read_excel(
        #     '/Users/Mandywu/Dropbox/Aviation-SI project/Spreadsheets/Policy_projection/code/main_paper/code/Input_intermediate.xlsx'
        # )

         # New automatic path resolution:
        intermediate_input_path = os.path.join(parent_dir, 'intermediate', 'Input_intermediate_V2.xlsx')
        
        # Verify the file exists
        if not os.path.exists(intermediate_input_path):
            raise FileNotFoundError(f"Input_intermediate_V2.xlsx not found at: {intermediate_input_path}")
        
        print(f"Using Input_intermediate_V2.xlsx: {intermediate_input_path}")
        
        # Read the external file into a DataFrame
        Intermediate_input = pd.read_excel(intermediate_input_path)

        
        # Join the existing Intermediate_var with the new data
        Intermediate_var = Intermediate_var.join(Intermediate_input)

        # Update the solution DataFrame using best_model
        solution.iloc[:, k+1] = (
            [0]
            + [best_model.getVarByName(biofuel_quantity_Q[i].VarName).X for i in range(24)]
            + [0]
            #+ [best_val]
            + [0]
            + [best_model.getVarByName(SAFcredit_prices_P.VarName).X]
            + [0]
            + [0]
            + [0]
            #+ [best_model.getVarByName(RIN_prices_P[i].VarName).X for i in range(2)]
            #+ [best_model.getVarByName(LCFS_prices_P.VarName).X]
            + [0]
            + [0]
            + [best_model.getVarByName(biofuel_prices_P[i].VarName).X for i in range(4)]
            + [best_model.getVarByName(biofuel_prices_P[i].VarName).X for i in range(4)]
            + [best_model.getVarByName(conventionalfuel_prices_P[i].VarName).X for i in range(3)]
            + [best_model.getVarByName(conventionalfuel_prices_P[i].VarName).X for i in range(3)]
            + [0]
            + [best_model.getVarByName(feedstock_prices_P[i].VarName).X for i in range(4)]
            + [best_model.getVarByName(feedstock_quantity_Q[i].VarName).X for i in range(4)]
            + [0]
            + [best_model.getVarByName(conventionalfuel_quantity_Q[i].VarName).X for i in range(3)]
            + [0]
            + [best_model.getVarByName(demand_price_P[i].VarName).X for i in range(3)]
            + [best_model.getVarByName(demand_price_P[i].VarName).X for i in range(3)]
            +[P_carbon_tax]
            +[0]
            + [best_model.getVarByName(biofuel_prices_P[i].VarName).X/input_biofuel.loc[input_biofuel['f'] == ['B100', 'RD', 'SAF', 'gasE100'][i], 'phi'].unique()[0] for i in range(4)]
            + [best_model.getVarByName(biofuel_prices_P[i].VarName).X/input_biofuel.loc[input_biofuel['f'] == ['B100', 'RD', 'SAF', 'gasE100'][i], 'phi'].unique()[0] for i in range(4)] 
        )

        # Helper function to get .X from a Gurobi variable or a pandas Series of variables
        def get_x(val):
            if hasattr(val, 'VarName'):
                return best_model.getVarByName(val.VarName).X
            elif hasattr(val, 'X'):
                return val.X
            elif hasattr(val, '__iter__'):
                return sum(get_x(v) for v in val)
            else:
                return val

        Fitted_quantity.iloc[5:20, k+1] = [
            # best_model.getVarByName(RVO_percent.loc[RVO_percent['mandate'] == 'BBD', 'P'].values[0].VarName).X,
            # best_model.getVarByName(RVO_percent.loc[RVO_percent['mandate'] == 'RF', 'P'].values[0].VarName).X,
            # input_compliance.loc[input_compliance['mandate'] == 'BBD', 'Q'].values[0] *
            #     get_x(denominator) / 1.6,
            # input_compliance.loc[input_compliance['mandate'] == 'RF', 'Q'].values[0] *
            #     get_x(denominator),
            get_x(biofuel_quantity.loc[biofuel_quantity['f'].isin(['B100', 'RD', 'SAF']), 'Q']),
            sum(
                biofuel_quantity.loc[biofuel_quantity['f'] == 'B100', 'kappa_RFS'].values[i] *
                best_model.getVarByName(q.VarName).X
                for i, q in enumerate(biofuel_quantity.loc[biofuel_quantity['f'] == 'B100', 'Q'])
            ) +
            sum(
                biofuel_quantity.loc[biofuel_quantity['f'] == 'RD', 'kappa_RFS'].values[i] *
                best_model.getVarByName(q.VarName).X
                for i, q in enumerate(biofuel_quantity.loc[biofuel_quantity['f'] == 'RD', 'Q'])
            ) +
            sum(
                biofuel_quantity.loc[biofuel_quantity['f'] == 'SAF', 'kappa_RFS'].values[i] *
                best_model.getVarByName(q.VarName).X
                for i, q in enumerate(biofuel_quantity.loc[biofuel_quantity['f'] == 'SAF', 'Q'])
            ) +
            sum(
                biofuel_quantity.loc[biofuel_quantity['f'] == 'gasE100', 'kappa_RFS'].values[i] *
                best_model.getVarByName(q.VarName).X
                for i, q in enumerate(biofuel_quantity.loc[biofuel_quantity['f'] == 'gasE100', 'Q'])
            ),
            0,
            0, 0,
            get_x(biofuel_quantity.loc[biofuel_quantity['f'] == 'B100', 'Q']),
            get_x(biofuel_quantity.loc[biofuel_quantity['f'] == 'RD', 'Q']),
            get_x(biofuel_quantity.loc[biofuel_quantity['f'].isin(['B100', 'RD']), 'Q']),
            get_x(conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'Q']),
            get_x(biofuel_quantity.loc[biofuel_quantity['f'] == 'gasE100', 'Q']),
            get_x(conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'Q']),
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'].isin(['soyoil', 'animalfat'])), 'Q']),
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'].isin(['corn', 'sugarcane'])), 'Q']),
            get_x(biofuel_quantity.loc[biofuel_quantity['f'] == 'SAF', 'Q']),
            get_x(conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'Q'])
        ]

        # Fitted_quantity.iloc[20:28, k+1] = [
        #     0,
        #     get_x(biofuel_quantity.loc[(biofuel_quantity['j'] == 'CA') & (biofuel_quantity['f'] == 'B100'), 'Q']),
        #     get_x(biofuel_quantity.loc[(biofuel_quantity['j'] == 'CA') & (biofuel_quantity['f'] == 'RD'), 'Q']),
        #     get_x(conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'D'), 'Q']),
        #     get_x(biofuel_quantity.loc[(biofuel_quantity['j'] == 'CA') & (biofuel_quantity['f'] == 'gasE100'), 'Q']),
        #     get_x(conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'G'), 'Q']),
        #     get_x(biofuel_quantity.loc[(biofuel_quantity['j'] == 'CA') & (biofuel_quantity['f'] == 'SAF'), 'Q']),
        #     get_x(conventionalfuel_quantity.loc[(conventionalfuel_quantity['j'] == 'CA') & (conventionalfuel_quantity['F'] == 'J'), 'Q'])
        # ]

        Fitted_quantity.iloc[21:25, k+1] = [
            best_model.getVarByName(feedstock_quantity_Q[i].VarName).X for i in range(4)
        ]
        Fitted_quantity.iloc[26:29, k+1] = [
            best_model.getVarByName(demand_quantity_Q[i].VarName).X for i in range(3)
        ]
        
        # Calculate and assign values to Fuel_price DataFrame
        Fuel_price.iloc[1:5, k+1] = [
        sum(Intermediate_var.loc[(Intermediate_var['F'] == 'D'), 'P_RIN_LCFS_detach']*Intermediate_var.loc[(Intermediate_var['F'] == 'D'), 'Q_actual']) /sum(Intermediate_var.loc[(Intermediate_var['F'] == 'D'), 'Q_equiv']),
        sum(Intermediate_var.loc[(Intermediate_var['F'] == 'G'), 'P_RIN_LCFS_detach']*Intermediate_var.loc[(Intermediate_var['F'] == 'G'), 'Q_actual']) /sum(Intermediate_var.loc[(Intermediate_var['F'] == 'G'), 'Q_equiv']),
        sum(Intermediate_var.loc[(Intermediate_var['F'] == 'J'), 'P_RIN_LCFS_detach']*Intermediate_var.loc[(Intermediate_var['F'] == 'J'), 'Q_actual']) /sum(Intermediate_var.loc[(Intermediate_var['F'] == 'J'), 'Q_equiv']),
        sum(Intermediate_var.loc[Intermediate_var['f'] == 'gasE100', 'P_RIN_LCFS_detach'] *
        Intermediate_var.loc[Intermediate_var['f'] == 'gasE100', 'Q_actual']) / sum(Intermediate_var.loc[Intermediate_var['f'] == 'gasE100', 'Q_actual'])]

        Fuel_price.iloc[5, k+1] = ((Fuel_price.iloc[4, k+1] * 0.1 + Intermediate_var.loc[(Intermediate_var['f'] == 'E0'), 'P_RIN_LCFS_detach'].values[0] * 0.9) /(0.1 * input_biofuel.loc[input_biofuel['f'] == 'gasE100', 'phi_ed'].unique()[0] + 0.9))

        Fuel_price.iloc[7:11, k+1] = [
        sum(Intermediate_var.loc[Intermediate_var['f'] == 'B100', 'P_all'] *Intermediate_var.loc[Intermediate_var['f'] == 'B100', 'Q_actual']) /sum(Intermediate_var.loc[Intermediate_var['f'] == 'B100', 'Q_actual']) if sum(Intermediate_var.loc[Intermediate_var['f'] == 'B100', 'Q_actual']) != 0 else 0,
        sum(Intermediate_var.loc[Intermediate_var['f'] == 'RD', 'P_all'] * Intermediate_var.loc[Intermediate_var['f'] == 'RD', 'Q_actual']) /sum(Intermediate_var.loc[Intermediate_var['f'] == 'RD', 'Q_actual']) if sum(Intermediate_var.loc[Intermediate_var['f'] == 'RD', 'Q_actual']) != 0 else 0,
        sum(Intermediate_var.loc[Intermediate_var['f'] == 'gasE100', 'P_all'] *Intermediate_var.loc[Intermediate_var['f'] == 'gasE100', 'Q_actual'])/sum(Intermediate_var.loc[Intermediate_var['f'] == 'gasE100', 'Q_actual']),
        (sum(Intermediate_var.loc[Intermediate_var['f'] == 'SAF', 'P_all'] *Intermediate_var.loc[Intermediate_var['f'] == 'SAF', 'Q_actual']) /sum(Intermediate_var.loc[Intermediate_var['f'] == 'SAF', 'Q_actual'])) if sum(Intermediate_var.loc[Intermediate_var['f'] == 'SAF', 'Q_actual']) != 0 else 0
        ]

        # Example for conventionalfuel_prices['P']
        Fuel_price.iloc[12:15, k+1] = [
            best_model.getVarByName(conventionalfuel_prices_P[i].VarName).X for i in range(3)
        ]

        # Fuel_price.iloc[16, k+1] = [
        #     best_model.getVarByName(RVO_percent_P[0].VarName).X * best_model.getVarByName(RIN_prices_P[0].VarName).X +
        #     (best_model.getVarByName(RVO_percent_P[1].VarName).X - best_model.getVarByName(RVO_percent_P[0].VarName).X) * best_model.getVarByName(RIN_prices_P[1].VarName).X
        # ]

        Fuel_price.iloc[22, k+1] = [P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'CI_LCFS'].unique()[0] *conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'D', 'ED_LCFS'].unique()[0] / 1000000) ]
    

        Fuel_price.iloc[23, k+1] = [P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'CI_LCFS'].unique()[0] *conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'G', 'ED_LCFS'].unique()[0] / 1000000) ]

        Fuel_price.iloc[24, k+1] = [P_carbon_tax * (conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'CI_LCFS'].unique()[0] *conventionalfuel_quantity.loc[conventionalfuel_quantity['F'] == 'J', 'ED_LCFS'].unique()[0] / 1000000) ]


        Fuel_price.iloc[26:30, k+1] = [
            sum(Intermediate_var.loc[Intermediate_var['f'] == 'B100', 'P_all'] *Intermediate_var.loc[Intermediate_var['f'] == 'B100', 'Q_actual']) /sum(Intermediate_var.loc[Intermediate_var['f'] == 'B100', 'Q_equiv']) if sum(Intermediate_var.loc[Intermediate_var['f'] == 'B100', 'Q_equiv']) != 0 else np.nan,   
            sum(Intermediate_var.loc[Intermediate_var['f'] == 'RD', 'P_all'] * Intermediate_var.loc[Intermediate_var['f'] == 'RD', 'Q_actual']) /sum(Intermediate_var.loc[Intermediate_var['f'] == 'RD', 'Q_equiv']),  
            sum(Intermediate_var.loc[Intermediate_var['f'] == 'gasE100', 'P_all'] *Intermediate_var.loc[Intermediate_var['f'] == 'gasE100', 'Q_actual'])/sum(Intermediate_var.loc[Intermediate_var['f'] == 'gasE100', 'Q_equiv']),
            sum(Intermediate_var.loc[Intermediate_var['f'] == 'SAF', 'P_all'] *Intermediate_var.loc[Intermediate_var['f'] == 'SAF', 'Q_actual']) /sum(Intermediate_var.loc[Intermediate_var['f'] == 'SAF', 'Q_equiv'])
        ]
        
        # # Calculate and assign values to Fuel_CI DataFrame
        # Fuel_CI.iloc[1:5, k+1] = [
        #     sum(Intermediate_var['CI_Tax'] * Intermediate_var['Q_actual']) / sum(Intermediate_var['Q_actual']),
        #     sum(Intermediate_var.loc[Intermediate_var['F'] == 'D', 'CI_Tax'] * Intermediate_var.loc[Intermediate_var['F'] == 'D', 'Q_actual']) /
        #     sum(Intermediate_var.loc[Intermediate_var['F'] == 'D', 'Q_actual']),
        #     sum(Intermediate_var.loc[Intermediate_var['F'] == 'G', 'CI_Tax'] * Intermediate_var.loc[Intermediate_var['F'] == 'G', 'Q_actual']) /
        #     sum(Intermediate_var.loc[Intermediate_var['F'] == 'G', 'Q_actual']),
        #     sum(Intermediate_var.loc[Intermediate_var['F'] == 'J', 'CI_Tax'] * Intermediate_var.loc[Intermediate_var['F'] == 'J', 'Q_actual']) /
        #     sum(Intermediate_var.loc[Intermediate_var['F'] == 'J', 'Q_actual'])
        # ]

        # Calculate and assign values to Fuel_CI DataFrame
        Fuel_CI.iloc[1:5, k+1] = [
            sum(Intermediate_var['CI_Emissions'] * Intermediate_var['Q_actual']) / sum(Intermediate_var['Q_actual']),
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'D', 'CI_Emissions'] * Intermediate_var.loc[Intermediate_var['F'] == 'D', 'Q_actual']) /
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'D', 'Q_actual']),
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'G', 'CI_Emissions'] * Intermediate_var.loc[Intermediate_var['F'] == 'G', 'Q_actual']) /
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'G', 'Q_actual']),
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'J', 'CI_Emissions'] * Intermediate_var.loc[Intermediate_var['F'] == 'J', 'Q_actual']) /
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'J', 'Q_actual'])
        ]
        
            
        # Rows 2 to 5 (Emissions for D, G, J, and total)
        # Total.iloc[1:5, k+1] = [
        #     sum(Intermediate_var.loc[Intermediate_var['F'] == 'D', 'Q_actual'] *
        #         Intermediate_var.loc[Intermediate_var['F'] == 'D', 'CI_Tax'] *
        #         Intermediate_var.loc[Intermediate_var['F'] == 'D', 'ED_LCFS']) / 10**6,
        #     sum(Intermediate_var.loc[Intermediate_var['F'] == 'G', 'Q_actual'] *
        #         Intermediate_var.loc[Intermediate_var['F'] == 'G', 'CI_Tax'] *
        #         Intermediate_var.loc[Intermediate_var['F'] == 'G', 'ED_LCFS']) / 10**6,
        #     sum(Intermediate_var.loc[Intermediate_var['F'] == 'J', 'Q_actual'] *
        #         Intermediate_var.loc[Intermediate_var['F'] == 'J', 'CI_Tax'] *
        #         Intermediate_var.loc[Intermediate_var['F'] == 'J', 'ED_LCFS']) / 10**6,
        #     sum(Intermediate_var['Q_actual'] * Intermediate_var['CI_Tax'] * Intermediate_var['ED_LCFS']) / 10**6
        # ]

        Total.iloc[1:5, k+1] = [
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'D', 'Q_actual'] *
                Intermediate_var.loc[Intermediate_var['F'] == 'D', 'CI_Emissions'] *
                Intermediate_var.loc[Intermediate_var['F'] == 'D', 'ED_LCFS']) / 10**6,
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'G', 'Q_actual'] *
                Intermediate_var.loc[Intermediate_var['F'] == 'G', 'CI_Emissions'] *
                Intermediate_var.loc[Intermediate_var['F'] == 'G', 'ED_LCFS']) / 10**6,
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'J', 'Q_actual'] *
                Intermediate_var.loc[Intermediate_var['F'] == 'J', 'CI_Emissions'] *
                Intermediate_var.loc[Intermediate_var['F'] == 'J', 'ED_LCFS']) / 10**6,
            sum(Intermediate_var['Q_actual'] * Intermediate_var['CI_Emissions'] * Intermediate_var['ED_LCFS']) / 10**6
        ]
        
        # Rows 6 to 9 (Costs for D, G, J, and total)
        Total.iloc[5:9, k+1] = [
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'D', 'Q_actual'] *
                Intermediate_var.loc[Intermediate_var['F'] == 'D', 'P_RIN_LCFS_detach']),
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'G', 'Q_actual'] *
                Intermediate_var.loc[Intermediate_var['F'] == 'G', 'P_RIN_LCFS_detach']),
            sum(Intermediate_var.loc[Intermediate_var['F'] == 'J', 'Q_actual'] *
                Intermediate_var.loc[Intermediate_var['F'] == 'J', 'P_RIN_LCFS_detach']),
            sum(Intermediate_var['Q_actual'] * Intermediate_var['P_RIN_LCFS_detach'])
        ]

        # Filter Intermediate_var for rows 1 to 24
        Intermediate_var_subsidy = Intermediate_var.iloc[:24, :]
        
        # Rows 11 to 20 in the Total DataFrame
        Total.iloc[10, k+1] = sum(Intermediate_var_subsidy['TC'] * Intermediate_var_subsidy['Q_actual'])
        Total.iloc[11, k+1] = sum(Intermediate_var_subsidy['TC_IRA'] * Intermediate_var_subsidy['Q_actual'])
        Total.iloc[12, k+1] = sum(Intermediate_var_subsidy['TC_45Z'] * Intermediate_var_subsidy['Q_actual'])
        Total.iloc[13, k+1] = sum(Intermediate_var_subsidy['TC_45Q'] * Intermediate_var_subsidy['Q_actual'])
        Total.iloc[14, k+1] = sum(Intermediate_var_subsidy['TC_state'] * Intermediate_var_subsidy['Q_actual'])
        Total.iloc[15, k+1] = sum(Intermediate_var_subsidy['TC_SAF'] * Intermediate_var_subsidy['Q_actual'])
        
        # RFS road and jet credits for CA and NC
        Total.iloc[16, k+1] = sum(
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['j'] == 'CA', 'RFS_road'] *
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['j'] == 'CA', 'Q_actual']
        )
        Total.iloc[17, k+1] = sum(
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['j'] == 'NC', 'RFS_road'] *
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['j'] == 'NC', 'Q_actual']
        )
        Total.iloc[18, k+1] = sum(
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['j'] == 'CA', 'RFS_jet'] *
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['j'] == 'CA', 'Q_actual']
        )
        Total.iloc[19, k+1] = sum(
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['j'] == 'NC', 'RFS_jet'] *
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['j'] == 'NC', 'Q_actual']
        )

        Total.iloc[20, k+1] = sum(
            Intermediate_var.loc[
                (Intermediate_var['f'].isin(['B0', 'E0'])),
                'RIN_obligation'
            ] * Intermediate_var.loc[
                (Intermediate_var['f'].isin(['B0', 'E0'])),
                'Q_actual'
            ]
        )
        
        # Total.iloc[21, k+1] = sum(
        #     Intermediate_var.loc[
        #         (Intermediate_var['j'] == 'NC') & (Intermediate_var['f'].isin(['B0', 'E0'])),
        #         'RIN_obligation'
        #     ] * Intermediate_var.loc[
        #         (Intermediate_var['j'] == 'NC') & (Intermediate_var['f'].isin(['B0', 'E0'])),
        #         'Q_actual'
        #     ]
        # )

        Total.iloc[24, k+1] = sum(
            Intermediate_var_subsidy['LCFS'] * Intermediate_var_subsidy['Q_actual']
        )

        # Total.iloc[25, k+1] = (
        #     LCFS_prices.loc['LCFS', 'P'].X *
        #     sum(input_compliance.loc[input_compliance['mandate'] == 'LCFS_Q', 'Q'])
        # )

        Total.iloc[26, k+1] = (
            sum(Intermediate_var_subsidy['LCFS'] * Intermediate_var_subsidy['Q_actual']) 
        )

        Total.iloc[32, k+1] = (
            sum(Intermediate_var_subsidy['Subsidy'] * Intermediate_var_subsidy['Q_actual'])
        )
        
            
        Total.iloc[33, k+1] = sum(
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['F'] == 'D', 'TC'] *
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['F'] == 'D', 'Q_actual']
        )
        
        Total.iloc[34, k+1] = sum(
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['F'] == 'G', 'TC'] *
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['F'] == 'G', 'Q_actual']
        )
        
        Total.iloc[35, k+1] = sum(
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['F'] == 'J', 'TC'] *
            Intermediate_var_subsidy.loc[Intermediate_var_subsidy['F'] == 'J', 'Q_actual']
        )

        Total.iloc[36, k+1] = sum(
            Intermediate_var['Carbon_tax'] * Intermediate_var['Q_actual']
        )

        Total.iloc[37, k+1] = sum(
            Intermediate_var.loc[Intermediate_var['F'] == 'D', 'Carbon_tax'] *
            Intermediate_var.loc[Intermediate_var['F'] == 'D', 'Q_actual']
        )
        
        Total.iloc[38, k+1] = sum(
            Intermediate_var.loc[Intermediate_var['F'] == 'G', 'Carbon_tax'] *
            Intermediate_var.loc[Intermediate_var['F'] == 'G', 'Q_actual']
        )
        
        Total.iloc[39, k+1] = sum(
            Intermediate_var.loc[Intermediate_var['F'] == 'J', 'Carbon_tax'] *
            Intermediate_var.loc[Intermediate_var['F'] == 'J', 'Q_actual']
        )

            
        # Rows 1 to 4 in the Feedstock_source DataFrame
        Feedstock_source.iloc[0:4, k+1] = [
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'B100') & (biofuel_quantity['s'] == 'soyoil'), 'Q']),
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'B100') & (biofuel_quantity['s'] == 'animalfat'), 'Q']),
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'RD') & (biofuel_quantity['s'] == 'soyoil'), 'Q']),
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'RD') & (biofuel_quantity['s'] == 'animalfat'), 'Q'])
        ]

        # Rows 5 to 8 in the Feedstock_source DataFrame
        Feedstock_source.iloc[4:8, k+1] = [
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'soyoil'), 'Q']),
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'animalfat'), 'Q']),
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'corn'), 'Q']),
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'sugarcane'), 'Q'])
        ]

        # Rows 9 to 10 in the Feedstock_source DataFrame
        # SAF-corn-CCS (row 8)
        mask_corn = (biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'corn')
        Feedstock_source.iloc[8, k+1] = sum(
            best_model.getVarByName(q.VarName).X * ccs
            for q, ccs in zip(
                biofuel_quantity.loc[mask_corn, 'Q'],
                biofuel_quantity.loc[mask_corn, 'CCS_tech']
            )
        )
        
        # SAF-sugarcane-CCS (row 9)
        mask_sugarcane = (biofuel_quantity['f'] == 'SAF') & (biofuel_quantity['s'] == 'sugarcane')
        Feedstock_source.iloc[9, k+1] = sum(
            best_model.getVarByName(q.VarName).X * ccs
            for q, ccs in zip(
                biofuel_quantity.loc[mask_sugarcane, 'Q'],
                biofuel_quantity.loc[mask_sugarcane, 'CCS_tech']
            )
        )

        # Rows 11 to 12 in the Feedstock_source DataFrame
        Feedstock_source.iloc[10:12, k+1] = [
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'gasE100') & (biofuel_quantity['s'] == 'corn'), 'Q']),
            get_x(biofuel_quantity.loc[(biofuel_quantity['f'] == 'gasE100') & (biofuel_quantity['s'] == 'sugarcane'), 'Q'])
        ]

        
# Function to append data to an existing Excel file
def append_to_excel(file_path, df, sheet_name):
    try:
        # Load the existing workbook
        with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            # Write the DataFrame to the specified sheet
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    except FileNotFoundError:
        # If the file does not exist, create a new one
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)

# Append data to the Excel file using results_dir
append_to_excel(os.path.join(results_dir, 'Solution.xlsx'), solution, 'Carbon_tax')
append_to_excel(os.path.join(results_dir, 'Fitted_quantity.xlsx'), Fitted_quantity, 'Carbon_tax')
append_to_excel(os.path.join(results_dir, 'Fuel_price.xlsx'), Fuel_price, 'Carbon_tax')
append_to_excel(os.path.join(results_dir, 'Fuel_CI.xlsx'), Fuel_CI, 'Carbon_tax')
append_to_excel(os.path.join(results_dir, 'Total.xlsx'), Total, 'Carbon_tax')
append_to_excel(os.path.join(results_dir, 'Feedstock_source.xlsx'), Feedstock_source, 'Carbon_tax')


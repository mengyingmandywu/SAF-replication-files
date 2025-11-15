from __future__ import annotations

import os
import argparse
from pathlib import Path
import pandas as pd

import input_generate as gen

BASE_DIR = Path(__file__).parent


def main(input_folder: str = "data_input") -> None:
    """
    Generate all output files from biofuel_input.xlsx.
    
    Args:
        input_folder: Name of the input folder (default: "data_input")
    """
    XLSX_IN = BASE_DIR / input_folder / "biofuel_input.xlsx"
    # Write all generated inputs to the 'intermediate' folder
    INTERMEDIATE_DIR = BASE_DIR / "intermediate"
    OUT_OLD = INTERMEDIATE_DIR / "input_biofuel_V3.xlsx"
    OUT_V1 = INTERMEDIATE_DIR / "input_biofuel_V1.xlsx"
    OUT_V2 = INTERMEDIATE_DIR / "input_biofuel_V2.xlsx"
    OUT_D2 = INTERMEDIATE_DIR / "input_biofuel_D2.xlsx"
    OUT_V4 = INTERMEDIATE_DIR / "input_biofuel_V4.xlsx"
    
    if not XLSX_IN.exists():
        raise FileNotFoundError(f"Missing input file: {XLSX_IN}")

    # Ensure the intermediate directory exists
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

    # Build merged (NEW rules frame is built in build_table_from_biofuel_input)
    merged = gen.build_table_from_biofuel_input(XLSX_IN)

    # Create Input_intermediate_V1.xlsx from the NEW rules merged dataframe
    # This preserves CI_Tax_PreOBBBA which is lost in OLD version transformations
    OUT_INTERMEDIATE_V1 = INTERMEDIATE_DIR / "Input_intermediate_V1.xlsx"
    intermediate_v1_df = gen.make_intermediate_v1(merged, XLSX_IN)
    intermediate_v1_df.to_excel(OUT_INTERMEDIATE_V1, index=False)

    # Create Input_intermediate_V2.xlsx with consolidated baseline rows (j='ALL')
    OUT_INTERMEDIATE_V2 = INTERMEDIATE_DIR / "Input_intermediate_V2.xlsx"
    intermediate_v2_df = gen.make_intermediate_v2(merged, XLSX_IN)
    intermediate_v2_df.to_excel(OUT_INTERMEDIATE_V2, index=False)

    # Write NEW (D2) version
    OUT_D2.parent.mkdir(parents=True, exist_ok=True)
    d2_df = merged.copy()
    # Also zero CI_* for j == 'NC' as requested
    mask_nc = d2_df["j"].astype(str).str.upper() == "NC"
    for col in ["CI_LCFS", "CI_std_LCFS", "CI_std_LCFS_new"]:
        if col in d2_df.columns:
            d2_df.loc[mask_nc, col] = 0
    d2_df.to_excel(OUT_D2, index=False)

    # OLD version (no D2; D4/D6 via CI_EPA)
    old_df = gen._make_old_version(merged)
    # Build V3 from OLD with adjustments:
    # - Remove CI_std_LCFS_new column
    # - Set BW_constraints for f=B100 & j=CA to match f=B100 & j=NC by 's'
    v3_df = old_df.copy()
    if "CI_std_LCFS_new" in v3_df.columns:
        v3_df = v3_df.drop(columns=["CI_std_LCFS_new"])
    try:
        if {"f", "j", "s", "BW_constraints"}.issubset(v3_df.columns):
            src_map_v3 = (
                v3_df.loc[(v3_df["f"] == "B100") & (v3_df["j"] == "NC"), ["s", "BW_constraints"]]
                .set_index("s")["BW_constraints"]
            )
            ca_mask_v3 = (v3_df["f"] == "B100") & (v3_df["j"] == "CA")
            v3_df.loc[ca_mask_v3, "BW_constraints"] = v3_df.loc[ca_mask_v3, "s"].map(src_map_v3).combine_first(v3_df.loc[ca_mask_v3, "BW_constraints"])  # keep original if no match
    except Exception:
        pass
    v3_df.to_excel(OUT_OLD, index=False)

    # Build V4 from OLD: keep BW_constraints exactly as in OLD (no overrides)
    v4_df = old_df.copy()
    # Rename std columns as requested
    rename_map = {}
    if "CI_std_LCFS" in v4_df.columns:
        rename_map["CI_std_LCFS"] = "CI_std_LCFS_CA"
    if "CI_std_LCFS_new" in v4_df.columns:
        rename_map["CI_std_LCFS_new"] = "CI_std_LCFS_CA_new"
    if rename_map:
        v4_df = v4_df.rename(columns=rename_map)
    # Create new CI_std_LCFS column: 82.01 for SAF, 0 otherwise
    v4_df["CI_std_LCFS"] = (v4_df["f"].astype(str).eq("SAF")).astype(int) * 82.01
    # Ensure CI_std_LCFS appears before CI_std_LCFS_CA in the column order
    cols = list(v4_df.columns)
    if "CI_std_LCFS" in cols and "CI_std_LCFS_CA" in cols:
        cols.remove("CI_std_LCFS")
        idx = cols.index("CI_std_LCFS_CA")
        cols.insert(idx, "CI_std_LCFS")
        v4_df = v4_df[cols]
    # Add SAFLCFSside and CALCFSSide, then place them after Taxheavyside and before CCS_tech
    v4_df["SAFLCFSside"] = v4_df["f"].astype(str).eq("SAF").astype(int)
    v4_df["CALCFSSide"] = v4_df["j"].astype(str).eq("CA").astype(int)
    cols = list(v4_df.columns)
    # Remove if present to reinsert in correct position
    for c in ["SAFLCFSside", "CALCFSSide"]:
        if c in cols:
            cols.remove(c)
    try:
        tax_idx = cols.index("Taxheavyside") + 1
    except ValueError:
        tax_idx = len(cols)
    # Insert in requested order: SAFLCFSside then CALCFSSide
    cols.insert(tax_idx, "SAFLCFSside")
    cols.insert(tax_idx + 1, "CALCFSSide")
    v4_df = v4_df[cols]
    # Zero CI_std_LCFS_CA and CI_std_LCFS_CA_new when j == 'NC'
    mask_nc_v4 = v4_df["j"].astype(str).str.upper() == "NC"
    for col in ("CI_std_LCFS_CA", "CI_std_LCFS_CA_new"):
        if col in v4_df.columns:
            v4_df.loc[mask_nc_v4, col] = 0
    v4_df.to_excel(OUT_V4, index=False)

    # OLD NC-zeroed base (V2): zero CI_* for j == 'NC'
    nc0_df = gen._make_nc_zeroed(old_df)
    nc0_df.to_excel(OUT_V2, index=False)

    # V1: Start from NC-zeroed base then set BW_constraints for f=B100 & j=CA
    # to equal the corresponding values for f=B100 & j=NC, matched by s.
    v1_df = nc0_df.copy()
    try:
        if {"f", "j", "s", "BW_constraints"}.issubset(v1_df.columns):
            src_map = (
                v1_df.loc[(v1_df["f"] == "B100") & (v1_df["j"] == "NC"), ["s", "BW_constraints"]]
                .set_index("s")["BW_constraints"]
            )
            ca_mask = (v1_df["f"] == "B100") & (v1_df["j"] == "CA")
            v1_df.loc[ca_mask, "BW_constraints"] = v1_df.loc[ca_mask, "s"].map(src_map).combine_first(v1_df.loc[ca_mask, "BW_constraints"])  # keep original if no match
    except Exception:
        # If anything unexpected happens, keep v1_df unchanged to avoid breaking the run
        pass
    v1_df.to_excel(OUT_V1, index=False)

    print(f"Wrote:\n  - {OUT_D2}\n  - {OUT_OLD}\n  - {OUT_V2}\n  - {OUT_V1}\n  - {OUT_V4}\n  - {OUT_INTERMEDIATE_V1}\n  - {OUT_INTERMEDIATE_V2}")

    # Quick sanity summary: presence of D2 and D4/D6 sums
    for path in (OUT_OLD, OUT_V2, OUT_V1, OUT_V4, OUT_D2, OUT_INTERMEDIATE_V1, OUT_INTERMEDIATE_V2):
        df = pd.read_excel(path)
        cols = list(df.columns)
        has_d2 = 'D2' in cols
        d4_sum = int(pd.to_numeric(df.get('D4'), errors='coerce').fillna(0).sum()) if 'D4' in cols else 0
        d6_sum = int(pd.to_numeric(df.get('D6'), errors='coerce').fillna(0).sum()) if 'D6' in cols else 0
        print(f"FILE: {path.name} | has_D2={has_d2} | D4_sum={d4_sum} | D6_sum={d6_sum} | rows={len(df)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate biofuel input files from biofuel_input.xlsx.')
    parser.add_argument('--input-folder', type=str, default='data_input',
                        help='Name of the input folder (default: data_input)')
    args = parser.parse_args()
    
    main(input_folder=args.input_folder)

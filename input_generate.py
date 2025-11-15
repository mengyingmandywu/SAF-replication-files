from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


def build_basic_rows_table() -> pd.DataFrame:
	"""Build the base table and include a CCS indicator column.

	Columns returned: Row, f, s, j, F, CCS
	- CCS is 1 if the Row name contains 'CCS' (e.g., ETJCCS rows), otherwise 0.
	"""
	columns = ["Row", "f", "s", "j", "F", "CCS_tech"]
	rows: List[Dict[str, Any]] = [
		{"Row": "B100-soyoil-CA", "f": "B100", "s": "soyoil", "j": "CA", "F": "D"},
		{"Row": "B100-animalfat-CA", "f": "B100", "s": "animalfat", "j": "CA", "F": "D"},
		{"Row": "RD-soyoil-CA", "f": "RD", "s": "soyoil", "j": "CA", "F": "D"},
		{"Row": "RD-animalfat-CA", "f": "RD", "s": "animalfat", "j": "CA", "F": "D"},
		{"Row": "SAF-animalfat-CA", "f": "SAF", "s": "animalfat", "j": "CA", "F": "J"},
		{"Row": "gasE100-corn-CA", "f": "gasE100", "s": "corn", "j": "CA", "F": "G"},
		{"Row": "B100-soyoil-NC", "f": "B100", "s": "soyoil", "j": "NC", "F": "D"},
		{"Row": "B100-animalfat-NC", "f": "B100", "s": "animalfat", "j": "NC", "F": "D"},
		{"Row": "RD-soyoil-NC", "f": "RD", "s": "soyoil", "j": "NC", "F": "D"},
		{"Row": "RD-animalfat-NC", "f": "RD", "s": "animalfat", "j": "NC", "F": "D"},
		{"Row": "SAF-animalfat-NC", "f": "SAF", "s": "animalfat", "j": "NC", "F": "J"},
		{"Row": "gasE100-corn-NC", "f": "gasE100", "s": "corn", "j": "NC", "F": "G"},
		{"Row": "gasE100-sugarcane-CA", "f": "gasE100", "s": "sugarcane", "j": "CA", "F": "G"},
		{"Row": "gasE100-sugarcane-NC", "f": "gasE100", "s": "sugarcane", "j": "NC", "F": "G"},
		{"Row": "SAF-soyoil-CA", "f": "SAF", "s": "soyoil", "j": "CA", "F": "J"},
		{"Row": "SAF-soyoil-NC", "f": "SAF", "s": "soyoil", "j": "NC", "F": "J"},
		{"Row": "SAF-sugarcane-ETJ-CA", "f": "SAF", "s": "sugarcane", "j": "CA", "F": "J"},
		{"Row": "SAF-sugarcane-ETJCCS-CA", "f": "SAF", "s": "sugarcane", "j": "CA", "F": "J"},
		{"Row": "SAF-corn-ETJ-CA", "f": "SAF", "s": "corn", "j": "CA", "F": "J"},
		{"Row": "SAF-corn-ETJCCS-CA", "f": "SAF", "s": "corn", "j": "CA", "F": "J"},
		{"Row": "SAF-sugarcane-ETJ-NC", "f": "SAF", "s": "sugarcane", "j": "NC", "F": "J"},
		{"Row": "SAF-sugarcane-ETJCCS-NC", "f": "SAF", "s": "sugarcane", "j": "NC", "F": "J"},
		{"Row": "SAF-corn-ETJ-NC", "f": "SAF", "s": "corn", "j": "NC", "F": "J"},
		{"Row": "SAF-corn-ETJCCS-NC", "f": "SAF", "s": "corn", "j": "NC", "F": "J"},
	]
	df = pd.DataFrame(rows, columns=columns)

	# Add CCS indicator based on Row name
	df["CCS_tech"] = df["Row"].str.contains("CCS", case=False, na=False).astype(int)

	# Ensure CCS is included in the output order
	return df[["Row", "f", "s", "j", "F", "CCS_tech"]]


def build_table_from_biofuel_input(xlsx_path: Path) -> pd.DataFrame:
	"""
	Read all sheets from biofuel_input.xlsx and merge values into the
	base 5-column table by matching on available keys among ['Row','f','s','j','F'].

	The function brings over any columns whose names match the expected
	value columns listed in `target_value_columns`. If multiple sheets contain
	the same value column, later sheets will overwrite earlier ones (last-wins).

	Args:
		xlsx_path: Path to biofuel_input.xlsx

	Returns:
		DataFrame: base rows augmented with any matched value columns.
	"""

	base = build_basic_rows_table()

	# Known value columns we expect to populate if present in any sheet
	target_value_columns = [
		"phi",
		"PC",
		"Conversion",
		"CI_LCFS",
		"CI_LCFS_actual",
		"ED_LCFS",
		"CI_std_LCFS",
		"CI_std_LCFS_new",
		"BW_constraints",
		"kappa_RFS",
		"CI_Tax",
		"CI_Tax_PreOBBBA",
		"CI_EPA",
		"Taxheavyside",
		"CCS_tech",
		"phi_ed",
		"D4",
		"D6",
		"D2",
		"Statetaxheaviside",
		"SAFcreditheaviside",
		"Conversion_demand",
		"CI_Emissions"
	]

	key_candidates = ["Row", "f", "s", "j", "F","CCS_tech"]

	# Load all sheets
	xlsx = pd.ExcelFile(xlsx_path)
	merged = base.copy()

	for sheet_name in xlsx.sheet_names:
		try:
			sdf = pd.read_excel(xlsx, sheet_name=sheet_name)
		except Exception:
			continue

		# Normalize column names (strip whitespace)
		sdf.columns = [str(c).strip() for c in sdf.columns]

		# Determine usable keys present in this sheet
		join_keys = [k for k in key_candidates if k in sdf.columns]
		if not join_keys:
			# If no explicit keys, try to construct from components if present
			# e.g., if f,s,j present but not Row, we can still join on those
			pass  # already handled by join_keys logic

		# Restrict to only keys + target columns that exist in the sheet
		# Exclude any join keys from value columns (e.g., avoid updating 'CCS_tech' if it's also a key)
		value_cols_here = [c for c in target_value_columns if c in sdf.columns and c not in join_keys]
		use_cols = list(dict.fromkeys(join_keys + value_cols_here))  # preserve order, dedupe
		if not join_keys or not value_cols_here:
			# Nothing to merge from this sheet
			continue

		sdf_use = sdf[use_cols].copy()

		# Keep last per key combo
		sdf_use = sdf_use.drop_duplicates(subset=join_keys, keep="last")

		# Align on keys using index; prefer values from the sheet (last-wins) without creating _x/_y columns
		merged_idx = merged.set_index(join_keys)
		sdf_idx = sdf_use.set_index(join_keys)

		# Ensure columns exist in merged before update
		for c in value_cols_here:
			if c not in merged_idx.columns:
				merged_idx[c] = pd.NA

		# Update with non-null values from sheet
		merged_idx.update(sdf_idx[value_cols_here])

		# Bring back to row form
		merged = merged_idx.reset_index()

	# ---- Derivations AFTER all sheets are merged ----
	# 1) Taxheavyside from CI_Tax: 1 if CI_Tax <= 47.39, else 0
	if "CI_Tax" in merged.columns:
		ci_tax_num = pd.to_numeric(merged["CI_Tax"], errors="coerce")
		merged["Taxheavyside"] = ci_tax_num.le(47.39).fillna(False).astype(int)
	else:
		merged["Taxheavyside"] = 0

	# 2) D4 per rule using CI_EPA (UPDATED):
	# - Only for F == 'D': D4 = 1 if CI_EPA <= 45.97
	ci_epa_num = pd.to_numeric(merged.get("CI_EPA"), errors="coerce") if "CI_EPA" in merged.columns else None
	if ci_epa_num is not None:
		cond_D_only = (merged["F"] == "D") & ci_epa_num.le(45.97)
		merged["D4"] = (cond_D_only.fillna(False)).astype(int)
	else:
		merged["D4"] = 0

	# 3) Statetaxheaviside and SAFcreditheaviside using CI_Tax_PreOBBBA; fallback to CI_Tax if needed
	if "CI_Tax_PreOBBBA" in merged.columns:
		ci_base = pd.to_numeric(merged["CI_Tax_PreOBBBA"], errors="coerce")
	elif "CI_Tax" in merged.columns:
		ci_base = pd.to_numeric(merged["CI_Tax"], errors="coerce")
	else:
		ci_base = None

	if ci_base is not None:
		merged["Statetaxheaviside"] = (
			(ci_base.le(44.50) & (merged["f"] == "SAF") & (merged["j"] == "NC")).fillna(False)
		).astype(int)
		merged["SAFcreditheaviside"] = (
			(ci_base.le(47.39) & (merged["f"] == "SAF")).fillna(False)
		).astype(int)
	else:
		merged["Statetaxheaviside"] = 0
		merged["SAFcreditheaviside"] = 0

	# 4) D6 (UPDATED rules):
	# - For F == 'D': 45.97 < CI_EPA <= 74.46
	# - For F == 'G': CI_EPA <= 74.46
	# - For F == 'J': 44.50 < CI_EPA <= 74.46
	if ci_epa_num is not None:
		cond_DD6 = (merged["F"] == "D") & ci_epa_num.le(74.46) & ci_epa_num.gt(45.97)
		cond_GD6 = (merged["F"] == "G") & ci_epa_num.le(74.46)
		cond_JD6 = (merged["F"] == "J") & ci_epa_num.le(74.46) & ci_epa_num.gt(44.50)
		merged["D6"] = ((cond_DD6 | cond_GD6 | cond_JD6).fillna(False)).astype(int)
	else:
		merged["D6"] = 0

	# 5) D2 (NEW): D2 = 1 if F == 'J' and CI_EPA <= 44.50, else 0
	if ci_epa_num is not None:
		merged["D2"] = ((merged["F"] == "J") & ci_epa_num.le(44.50)).fillna(False).astype(int)
	else:
		merged["D2"] = 0

	# Enforce final output order requested by user
	output_order = [
		"Row",
		"f",
		"s",
		"j",
		"F",
		"phi",
		"PC",
		"Conversion",
		"CI_LCFS",
		"ED_LCFS",
		"CI_std_LCFS",
		"CI_std_LCFS_new",
		"BW_constraints",
		"kappa_RFS",
		"CI_Tax",
		"Taxheavyside",
		"CCS_tech",
		"phi_ed",
		"D2",
		"D4",
		"D6",
		"Statetaxheaviside",
		"SAFcreditheaviside",
		"Conversion_demand",
		"CI_EPA",
		"CI_LCFS_actual",
		"CI_Tax_PreOBBBA",
		"CI_Emissions"
	]

	for col in output_order:
		if col not in merged.columns:
			merged[col] = pd.NA

	merged = merged[output_order]

	return merged


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
	p = argparse.ArgumentParser(description="Generate the 5-column (Row,f,s,j,F) table or merge values from biofuel_input.xlsx")
	p.add_argument("--preview", action="store_true", help="Print the full 5-column table")
	p.add_argument("--write-to", type=Path, help="Write the 5-column table to an Excel file")
	p.add_argument("--from-biofuel-input", type=Path, help="Path to biofuel_input.xlsx to merge value columns into the table")
	p.add_argument("--preview-merged", action="store_true", help="Print the merged table created from biofuel_input.xlsx")
	p.add_argument("--write-merged-to", type=Path, help="Write the merged table to an Excel file")
	# New explicit outputs
	p.add_argument("--write-old-to", type=Path, help="Write OLD rules version (no D2; D4 via CI_LCFS for F in {D,J}; D6 via CI_EPA)")
	p.add_argument("--write-d2-to", type=Path, help="Write NEW rules version with D2 and updated D4/D6")
	p.add_argument("--write-nc0-to", type=Path, help="Write OLD rules version with CI_* zeroed for j=='NC'")
	return p.parse_args(argv)


def _make_old_version(df: pd.DataFrame) -> pd.DataFrame:
	"""Return a copy of df with OLD rules applied:
	- No D2 column
	- D4 = 1 if (F in {D, J}) and CI_EPA <= 45.97 else 0
	- D6 = 1 if (F=='D' and 45.97<CI_EPA<=74.46) or (F=='G' and CI_EPA<=74.46) or (F=='J' and 45.97<CI_EPA<=74.46)
	"""
	old = df.copy()
	# Drop D2 if present
	if "D2" in old.columns:
		old = old.drop(columns=["D2"]) 
	# D4 old uses CI_EPA
	if "CI_EPA" in old.columns:
		ci_epa = pd.to_numeric(old["CI_EPA"], errors="coerce")
	else:
		# vector of NaNs to safely evaluate conditions (use float NaN for numeric ops)
		ci_epa = pd.Series([float("nan")] * len(old), index=old.index)
	old["D4"] = ((old["F"].isin(["D", "J"]) & ci_epa.le(45.97)).fillna(False)).astype(int)
	# D6 old uses CI_EPA
	cond_D = (old["F"] == "D") & ci_epa.le(74.46) & ci_epa.gt(45.97)
	cond_G = (old["F"] == "G") & ci_epa.le(74.46)
	cond_J = (old["F"] == "J") & ci_epa.le(74.46) & ci_epa.gt(45.97)
	old["D6"] = ((cond_D | cond_G | cond_J).fillna(False)).astype(int)
	return old


def _make_nc_zeroed(df_old: pd.DataFrame) -> pd.DataFrame:
	"""Return copy of df_old with CI columns zeroed for rows where j == 'NC'.
	Assumes OLD rules frame; does not create D2."""
	nc = df_old.copy()
	mask_nc = nc["j"].astype(str).str.upper() == "NC"
	for col in ["CI_LCFS", "CI_std_LCFS", "CI_std_LCFS_new"]:
		if col in nc.columns:
			nc.loc[mask_nc, col] = 0
	return nc


def make_intermediate_v1(df: pd.DataFrame, xlsx_path: Path) -> pd.DataFrame:
	"""Create intermediate V1 file with selected columns for analysis.
	
	Returns a dataframe with columns: Row, f, s, j, F, CI_LCFS, ED_LCFS, 
	CI_Tax, CI_45Z, CI_EPA
	
	This uses the NEW rules merged dataframe (with D2) before any OLD version transformations.
	Also adds baseline rows (B0, E0, J0 for CA and NC) from the 'baseline' sheet in biofuel_input.xlsx.
	
	Args:
		df: The merged dataframe from build_table_from_biofuel_input()
		xlsx_path: Path to the biofuel_input.xlsx file
	"""
	intermediate_cols = ["Row", "f", "s", "j", "F", "CI_LCFS", "ED_LCFS", "CI_Tax", "CI_Tax_PreOBBBA", "CI_EPA", "CI_Emissions"]

	# Select only columns that exist in the input dataframe
	available_cols = [col for col in intermediate_cols if col in df.columns]
	result_df = df[available_cols].copy()
	
	# Rename CI_Tax_PreOBBBA to CI_45Z
	if 'CI_Tax_PreOBBBA' in result_df.columns:
		result_df = result_df.rename(columns={'CI_Tax_PreOBBBA': 'CI_45Z'})
	
	# Replace CI_LCFS with CI_LCFS_actual for gasE100-corn rows
	if 'CI_LCFS_actual' in df.columns and 'f' in result_df.columns and 's' in result_df.columns:
		mask_gase100_corn = (result_df['f'] == 'gasE100') & (result_df['s'] == 'corn')
		if mask_gase100_corn.any():
			result_df.loc[mask_gase100_corn, 'CI_LCFS'] = df.loc[mask_gase100_corn, 'CI_LCFS_actual'].values
	
	# Read baseline rows from the 'baseline' sheet in biofuel_input.xlsx
	try:
		baseline_source = pd.read_excel(xlsx_path, sheet_name='baseline')
		# Normalize column names
		baseline_source.columns = [str(c).strip() for c in baseline_source.columns]
		
		# Get Row column (might be in 'Unnamed: 0' or 'Row')
		if 'Unnamed: 0' in baseline_source.columns:
			baseline_source['Row'] = baseline_source['Unnamed: 0']
		
		# For baseline rows, set CI_Tax and CI_Tax_PreOBBBA equal to CI_LCFS
		if 'CI_LCFS' in baseline_source.columns:
			baseline_source['CI_Tax'] = baseline_source['CI_LCFS']
			baseline_source['CI_Tax_PreOBBBA'] = baseline_source['CI_LCFS']
			# Also set CI_Emissions for baseline rows when not present explicitly
			if 'CI_Emissions' not in baseline_source.columns:
				baseline_source['CI_Emissions'] = baseline_source['CI_LCFS']
		
		# Set CI_EPA to NA for baseline rows
		baseline_source['CI_EPA'] = pd.NA
		
		# Select only the columns we need
		baseline_cols = [c for c in intermediate_cols if c in baseline_source.columns]
		baseline_df = baseline_source[baseline_cols].copy()
		
		# Rename CI_Tax_PreOBBBA to CI_45Z in baseline rows
		if 'CI_Tax_PreOBBBA' in baseline_df.columns:
			baseline_df = baseline_df.rename(columns={'CI_Tax_PreOBBBA': 'CI_45Z'})
		
		# Concatenate with the main dataframe
		result_df = pd.concat([result_df, baseline_df], ignore_index=True)
	except Exception as e:
		# If baseline sheet doesn't exist or has issues, continue without it
		print(f"Warning: Could not read baseline sheet from {xlsx_path}: {e}")
	
	return result_df


def make_intermediate_v2(df: pd.DataFrame, xlsx_path: Path) -> pd.DataFrame:
	"""Create intermediate V2 file with selected columns for analysis.
	
	Returns a dataframe with columns: Row, f, s, j, F, CI_LCFS, ED_LCFS, 
	CI_Tax, CI_45Z, CI_EPA
	
	This uses the NEW rules merged dataframe (with D2) before any OLD version transformations.
	Also adds baseline rows (B0, E0, J0) with j='ALL' (consolidated from CA and NC).
	
	Args:
		df: The merged dataframe from build_table_from_biofuel_input()
		xlsx_path: Path to the biofuel_input.xlsx file
	"""
	intermediate_cols = ["Row", "f", "s", "j", "F", "CI_LCFS", "ED_LCFS", "CI_Tax", "CI_Tax_PreOBBBA", "CI_EPA", "CI_Emissions"]
	# Select only columns that exist in the input dataframe
	available_cols = [col for col in intermediate_cols if col in df.columns]
	result_df = df[available_cols].copy()
	
	# Rename CI_Tax_PreOBBBA to CI_45Z
	if 'CI_Tax_PreOBBBA' in result_df.columns:
		result_df = result_df.rename(columns={'CI_Tax_PreOBBBA': 'CI_45Z'})
	
	# Replace CI_LCFS with CI_LCFS_actual for gasE100-corn rows
	if 'CI_LCFS_actual' in df.columns and 'f' in result_df.columns and 's' in result_df.columns:
		mask_gase100_corn = (result_df['f'] == 'gasE100') & (result_df['s'] == 'corn')
		if mask_gase100_corn.any():
			result_df.loc[mask_gase100_corn, 'CI_LCFS'] = df.loc[mask_gase100_corn, 'CI_LCFS_actual'].values
	
	# Read baseline rows from the 'baseline' sheet in biofuel_input.xlsx
	# For V2, consolidate CA and NC rows into single rows with j='ALL'
	try:
		baseline_source = pd.read_excel(xlsx_path, sheet_name='baseline')
		# Normalize column names
		baseline_source.columns = [str(c).strip() for c in baseline_source.columns]
		
		# Get Row column (might be in 'Unnamed: 0' or 'Row')
		if 'Unnamed: 0' in baseline_source.columns:
			baseline_source['Row'] = baseline_source['Unnamed: 0']
		
		# For baseline rows, set CI_Tax and CI_Tax_PreOBBBA equal to CI_LCFS
		if 'CI_LCFS' in baseline_source.columns:
			baseline_source['CI_Tax'] = baseline_source['CI_LCFS']
			baseline_source['CI_Tax_PreOBBBA'] = baseline_source['CI_LCFS']
			# Also set CI_Emissions for baseline rows when not present explicitly
			if 'CI_Emissions' not in baseline_source.columns:
				baseline_source['CI_Emissions'] = baseline_source['CI_LCFS']
		
		# Set CI_EPA to NA for baseline rows
		baseline_source['CI_EPA'] = pd.NA
		
		# Group by fuel type (f) to consolidate CA and NC rows
		# Keep only one row per fuel type (B0, E0, J0) and set j='ALL'
		baseline_grouped = baseline_source.groupby('f', as_index=False).first()
		baseline_grouped['j'] = 'ALL'
		# Update Row names to remove _CA or _NC suffix
		baseline_grouped['Row'] = baseline_grouped['f']  # B0, E0, J0
		
		# Select only the columns we need
		baseline_cols = [c for c in intermediate_cols if c in baseline_grouped.columns]
		baseline_df = baseline_grouped[baseline_cols].copy()
		
		# Rename CI_Tax_PreOBBBA to CI_45Z in baseline rows
		if 'CI_Tax_PreOBBBA' in baseline_df.columns:
			baseline_df = baseline_df.rename(columns={'CI_Tax_PreOBBBA': 'CI_45Z'})
		
		# Concatenate with the main dataframe
		result_df = pd.concat([result_df, baseline_df], ignore_index=True)
	except Exception as e:
		# If baseline sheet doesn't exist or has issues, continue without it
		print(f"Warning: Could not read baseline sheet from {xlsx_path}: {e}")
	
	return result_df


def main(argv: List[str] | None = None) -> None:
	args = _parse_args(argv)
	df = build_basic_rows_table()

	if args.preview or (not args.write_to and not args.from_biofuel_input):
		print(df.to_string(index=False))
		print(f"Shape: {df.shape}")

	if args.write_to:
		out_path: Path = args.write_to
		out_path.parent.mkdir(parents=True, exist_ok=True)
		df.to_excel(out_path, index=False)
		print(f"Wrote 5-column table to: {out_path}")

	if args.from_biofuel_input:
		merged = build_table_from_biofuel_input(args.from_biofuel_input)
		if args.preview_merged or not args.write_merged_to:
			print("\n[Merged table]")
			print(merged.head(25).to_string(index=False))
			print(f"Shape: {merged.shape}")
		if args.write_merged_to:
			outm: Path = args.write_merged_to
			outm.parent.mkdir(parents=True, exist_ok=True)
			merged.to_excel(outm, index=False)
			print(f"Wrote merged table to: {outm}")

			# Also optionally write NC-zeroed variant if requested via environment variable or inferred path
			# If the user provides an environment var OUTPUT_NC0 or a sibling path ending with _NC0.xlsx, create that file.
			# To keep changes minimal, infer NC0 path by appending _NC0 before suffix when env OUTPUT_NC0 is set to '1'.
			import os
			if os.environ.get('WRITE_NC0', '').lower() in ('1','true','yes'):
				variant_path = outm.with_name(outm.stem + '_NC0' + outm.suffix)
				# Create NC-zeroed copy
				df_nc0 = merged.copy()
				mask_nc = df_nc0['j'].astype(str).str.upper() == 'NC'
				for _col in [
					'CI_LCFS',
					'CI_std_LCFS',
					'CI_std_LCFS_new',
				]:
					if _col in df_nc0.columns:
						df_nc0.loc[mask_nc, _col] = 0
				variant_path.parent.mkdir(parents=True, exist_ok=True)
				df_nc0.to_excel(variant_path, index=False)
				print(f"Wrote NC-zeroed variant to: {variant_path}")

		# Explicit multi-output support
		if args.write_d2_to:
			args.write_d2_to.parent.mkdir(parents=True, exist_ok=True)
			merged.to_excel(args.write_d2_to, index=False)
			print(f"Wrote NEW (D2) version to: {args.write_d2_to}")
		if args.write_old_to or args.write_nc0_to:
			old_df = _make_old_version(merged)
			if args.write_old_to:
				args.write_old_to.parent.mkdir(parents=True, exist_ok=True)
				old_df.to_excel(args.write_old_to, index=False)
				print(f"Wrote OLD version to: {args.write_old_to}")
			if args.write_nc0_to:
				nc0_df = _make_nc_zeroed(old_df)
				args.write_nc0_to.parent.mkdir(parents=True, exist_ok=True)
				nc0_df.to_excel(args.write_nc0_to, index=False)
				print(f"Wrote OLD (NC-zeroed) version to: {args.write_nc0_to}")


if __name__ == "__main__":
	main()
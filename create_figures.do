/*
================================================================================
WORKER SCRIPT - Generate Figures for Single Quantile/Scenario/Format Combination
================================================================================

PURPOSE:
  This worker script generates 18 publication-quality figures
  for a SINGLE quantile of a SINGLE scenario in specified format (PNG or EPS).
  Reads data from scenario-specific results_plot_XX_YY.xlsx workbooks.
  Called by run_figures.do for each quantile-scenario combination.

ROLE IN PIPELINE:
  - Tier 4 (bottom) of 4-tier orchestration pipeline
  - Called by: run_figures.do (master batch orchestrator)
  - Handles: Single quantile × single scenario × single format combination
  - Repeats: Once per quantile per scenario (e.g., 5 times for 5 quantiles)

CALLED BY: run_figures.do (master batch file)

PREREQUISITES - REQUIRED GLOBALS (Set by run_figures.do):
  Global variables MUST be set before calling this script:
    
    $current_quantile
      - Description: Quantile identifier
      - Valid values: Mean, Q_10th, Q_33th, Q_67th, Q_90th
      - Example: Mean (for mean value quantile)
      - Example: Q_90th (for 90th percentile)
    
    $current_scenario
      - Description: Scenario identifier
      - Valid values: baseline, conversion (or other scenario names)
      - Example: baseline
      - Used to construct input/output folder names
    
    $figtype
      - Description: Output figure format
      - Valid values: png, eps
      - Example: png
    
    $input_data
      - Description: Input Excel workbook filename
      - Format: results_plot_XX_YY.xlsx
      - Example: results_plot_Mean_baseline.xlsx
      - Example: results_plot_Q_10th_conversion.xlsx
      - Stored in: $results_folder directory
    
    $results_folder
      - Description: Path to folder containing input data files
      - Format: results_XX (results_baseline, results_conversion, etc.)
      - Example: results_baseline
      - Full path constructed as: {current_dir}/$results_folder
    
    $output_folder
      - Description: Path to folder for saving generated figures
      - Format: Plot_XX_YY (Plot_Mean_baseline, Plot_Q_10th_conversion, etc.)
      - Example: Plot_Mean_baseline
      - Created automatically if not present

DO NOT RUN DIRECTLY:
  This script is designed to be called by run_figures.do only.
  Running it directly will fail with global variable validation errors.
  All globals MUST be pre-set by the calling script.

DATA SOURCE:
  Input Excel workbooks stored in results_XX/ folders:
    Location: $results_folder/$input_data
    Examples:
      - results_baseline/results_plot_Mean_baseline.xlsx
      - results_baseline/results_plot_Q_10th_baseline.xlsx
      - results_baseline/results_plot_Q_33th_baseline.xlsx
      - results_baseline/results_plot_Q_67th_baseline.xlsx
      - results_baseline/results_plot_Q_90th_baseline.xlsx
      - results_conversion/results_plot_Mean_conversion.xlsx
  
  Full path constructed as: {working_dir}/$results_folder/$input_data
  Stored globally as: $input_file (created in validation section)
  Existence verified before processing begins

FIGURES GENERATED (18 total per quantile per scenario):
  
  Figure 2: Volume Analysis (4 PNG/EPS files)
    - vol_jet_gal.{png|eps}        (Jet volume by feedstock)
    - vol_diesel_gal.{png|eps}     (Diesel volume by feedstock)
    - vol_gas_gal.{png|eps}        (Gas volume by feedstock)
    - vol_legend.{png|eps}         (Legend for volume figures)
  
  Figure 3: Subsidy Stacks (7 PNG/EPS files)
    - stack_fatrdca.{png|eps}      (Fat-based RD credit subsidy stack CA)
    - stack_soyrdca.{png|eps}      (Soy-based RD credit subsidy stack CA)
    - stack_fatsafca.{png|eps}     (Fat-based SAF credit subsidy stack CA)
    - stack_soysafca.{png|eps}     (Soy-based SAF credit subsidy stack CA)
    - stack_fatsafrous.{png|eps}   (Fat-based SAF credit subsidy stack RoUS)
    - stack_soysafrous.{png|eps}   (Soy-based SAF credit subsidy stack RoUS)
    - stack_etjsafrous.{png|eps}   (ETJ SAF credit subsidy stack RoUS)
  
  Figure 4: Average Abatement Cost (1 PNG/EPS file)
    - scatter.{png|eps}            (AAC scatter plot by feedstock region)
  
  Figure 5: Policy Cost Breakdown (1 PNG/EPS file)
    - policycost_breakdown.{png|eps} (Policy cost components by category)
  
  Figure 6: Policy Cost Share (1 PNG/EPS file)
    - policycost_share.{png|eps}   (Policy cost share by feedstock)
  
  Figure 7: Fuel Prices (3 PNG/EPS files)
    - fuelprices_rous.{png|eps}    (Fuel prices Rest of US by fuel type)
    - fuelprices_ca.{png|eps}      (Fuel prices California by fuel type)
    - fuelprices_legend.{png|eps}  (Legend for fuel price figures)
  
  Figure 8: Feedstock Demand (1 PNG/EPS file)
    - feedstock_demand.{png|eps}   (Feedstock demand by source)
  
  TOTAL OUTPUT: 18 figures per quantile per scenario

OUTPUT LOCATION:
  Directory: $output_folder
  Examples:
    - Plot_Mean_baseline/          (18 figures for mean baseline)
    - Plot_Q_10th_baseline/        (18 figures for 10th percentile baseline)
    - Plot_Q_90th_baseline/        (18 figures for 90th percentile baseline)
    - Plot_Mean_conversion/        (18 figures for mean conversion scenario)
  
  Output folders created automatically if they don't exist.
  All .png or .eps files saved directly to output folder.

VALIDATION & ERROR HANDLING:
  1. Checks all 6 required global variables are set
  2. Constructs full input file path: $input_file = $results_folder/$input_data
  3. Verifies input file exists before processing
  4. Creates output folder if not present
  5. Exits with descriptive error if any validation fails
  
  Validation errors are fatal (script exits with code 1).

EXECUTION EXAMPLE (via run_figures.do):
  
  For baseline Mean quantile in PNG:
    global current_quantile "Mean"
    global current_scenario "baseline"
    global figtype "png"
    global input_data "results_plot_Mean_baseline.xlsx"
    global results_folder "results_baseline"
    global output_folder "Plot_Mean_baseline"
    do create_figures.do
    
    Result: 18 PNG files in Plot_Mean_baseline/ folder

================================================================================
*/

* Verify required globals are set
if "$current_quantile" == "" {
	di as error "ERROR: $current_quantile is not set"
	exit 1
}
if "$current_scenario" == "" {
	di as error "ERROR: $current_scenario is not set"
	exit 1
}
if "$figtype" == "" {
	di as error "ERROR: $figtype is not set"
	exit 1
}
if "$input_data" == "" {
	di as error "ERROR: $input_data is not set"
	exit 1
}
if "$results_folder" == "" {
	di as error "ERROR: $results_folder is not set"
	exit 1
}
if "$output_folder" == "" {
	di as error "ERROR: $output_folder is not set"
	exit 1
}

* Construct full path to input file in results folder
global input_file "$results_folder/$input_data"

* Verify input file exists
capture confirm file "$input_file"
if _rc {
	di as error "ERROR: Input file not found: $input_file"
	exit 1
}

di ""
di "================================================================================"
di "Processing: $current_quantile for scenario $current_scenario ($figtype format)"
di "Input file: $input_file"
di "Output folder: $output_folder"
di "================================================================================"

* Create output folder if it doesn't exist
cap mkdir "$output_folder"

* Define colors
	global mydarkblue "0 87 124"
	global myblue "13 149 208"
	global mylightblue "223 234 246"
	global mypurple "154 97 127"
	global mylightrose "221 108 109"
	global myrosealt "231 47 82"
	global myrose "196 59 96"
	global mydarkrose "173 0 79"
	global myteal "0 150 158"
	global mutedteal "24 138 145"
	global mylightteal "113 201 198"
	global mygreen "125 196 98"
	global myrust "212 70 39"
	global mygold "239 183 67"
	global myyellow "224 177 101"
	global mydarkyellow "186 129 38"

* ============================================================================
* Figure 2 - Volumes
* ============================================================================

	*bring in data
	import excel using "$input_file", cellrange(n2:v10) firstrow clear ///
		sheet("Volumes")
	rename Policy Scenario
	rename (Ethanol Gasoline Diesel RenewableDiesel Biodiesel JetFuel SAFHEFA SAFATJ) ///
	(eth gas diesel rd biodiesel jet SAFhefa SAFatj)
	replace Scenario="Aviation Intensity Standard" if Scenario=="Aviation intensity standard"
	
	*create custum order and labels for scenarios 
	gen ord = 1 if Scenario=="No Policy"
	replace ord = 2 if Scenario=="Current Policy"
	replace ord = 3 if Scenario=="SAF Credit"
	replace ord = 4 if Scenario=="Nested D2"
	replace ord = 5 if Scenario=="D2 with Aviation Obligation"
	replace ord = 6 if Scenario=="Nested D2 + Stricter RFS"
	replace ord = 7 if Scenario=="Carbon Tax + SAF Credit"
	replace ord = 8 if Scenario=="Aviation Intensity Standard"
	label define ordlbl 1 "No Policy" 2 "Current Policy" 3 "SAF Credit" ///
		 4 "Nested D2" 5 "D2 with Aviation Obligation" 6 "Nested D2 + Stricter RFS" ///
		 7 "Carbon Tax + SAF Credit" 8 "Aviation Intensity Standard"
	label values ord ordlbl
	
	*examine how total fuel volume varies by scenario 
	gen sum_diesel = diesel + rd + biodiesel
	gen sum_jet = jet + SAFhefa + SAFatj
	gen sum_gas = eth + gas
	
	qui sum sum_diesel 
	local diesel_var = 100*(`r(max)'-`r(min)')/`r(min)'
	qui sum sum_jet 
	local jet_var = 100*(`r(max)'-`r(min)')/`r(min)	'
	qui sum sum_gas 
	local gas_var = 100*(`r(max)'-`r(min)')/`r(min)'
	
	di "`diesel_var'"
	di "`jet_var'"
	di "`gas_var'"
	
 	*create figure (totals)
	sum SAFatj if Scenario=="Current Policy"
	local SAFatj_current = round(r(max)*100,.1)/100
	graph hbar SAFhefa SAFatj, over(ord, label(angle(0))) stack name(g3, replace) ///
		title("Aviation (bil. gallons)") ytitle("Aviation (bil. gallons)") /// 
		bar(1, color("${mydarkyellow}")) bar(2, color("${myyellow}")) ///
		yscale(range(0 15)) ylab(0(5)10) legend(off)  aspect(.8) ///
		text(0.1 82 "{bf:`SAFatj_current' (ATJ)}", place(e) color("${myyellow}") size(3.7))
		graph export "$output_folder/vol_jet_gal.$figtype", replace
	graph hbar rd biodiesel,  over(ord, label(angle(0))) stack name(g2, replace) ///
		title("Diesel (bil. gallons)") ytitle("Diesel (bil. gallons)") legend(off) ///
		bar(1, color("${mydarkrose}")) bar(2, color("${mylightrose}")) ///
		yscale(range(0 15))	ylab(0(5)10) aspect(.8)
		graph export "$output_folder/vol_diesel_gal.$figtype", replace
	graph hbar eth, over(ord, label(angle(0))) stack name(g1, replace)  ///
		title("Gasoline (bil. gallons)") ytitle("Gasoline (bil. gallons)") /// 
		bar(1, color("${mydarkblue}")) aspect(.8) ///
		yscale(range(0 15)) ylab(0(5)10)
		graph export "$output_folder/vol_gas_gal.$figtype", replace
	
	*express each renewable fuel as a percent of total renewable + fossil fuel
	replace eth = eth/sum_gas*100
	drop gas sum_gas
	
	replace rd = rd/sum_diesel*100
	replace biodiesel = biodiesel/sum_diesel*100
	drop diesel sum_diesel
	
	replace SAFhefa = SAFhefa/sum_jet*100
	replace SAFatj = SAFatj/sum_jet*100
	drop jet sum_jet
		
	graph hbar SAFhefa SAFatj rd biodiesel eth, ///
		over(ord, label(labcolor(white))) stack name(g1, replace)  ///
		title("Gasoline") ytitle("") ///
		bar(1, color("${mydarkyellow}")) bar(2, color("${myyellow}")) ///
		bar(3, color("${mydarkrose}")) bar(4, color("${mylightrose}")) ///
		bar(5, color("${mydarkblue}")) xsize(10) ///
		legend(pos(6) col(6) ///
		order(1 "SAF (HEFA)" 2 "SAF (ATJ)" 3 "Renewable Diesel" 4 "Biodiesel" 5 "Ethanol"))
		graph export "$output_folder/vol_legend.$figtype", replace

* ============================================================================
* Figure 3 - Subsidy Stacks
* ============================================================================

	*bring in data
	import excel using "$input_file", cellrange(o2:y32) firstrow clear ///
		sheet("Subsidy_stack_figs")
	rename Name pathway
	keep pathway Production_cost RIN LCFS Z Q Statetaxcredits NetPrice FossilPrice
	rename (Production_cost RIN LCFS Z Q Statetaxcredits NetPrice FossilPrice) ///
	(cost rin lcfs z q state netprice fossilprice)
	
	*keep relevant pathways 
	keep if inlist(pathway, ///
		"RD-soyoil-CA", "RD-animalfat-CA", "SAF-soyoil-CA", "SAF-animalfat-CA", ///
		"SAF-animalfat-NC", "SAF-soyoil-NC", "SAF-corn-ETJCCS-NC")
		
	*make all credit values positive (for figure)
	foreach v of varlist rin-state{
		replace `v'=`v'*-1
	}
	
	*create blank spaces for figure 
	gen blank_rin = cost-rin 
	gen blank_lcfs = cost-rin-lcfs 
	gen blank_z = cost-rin-lcfs-z 
	gen blank_q = cost-rin-lcfs-z-q 
	gen blank_state = cost-rin-lcfs-z-q-state 
	
	*reshape data 
	rename (cost rin lcfs z q state netprice fossilprice) ///
		(type_cost type_rin type_lcfs type_z type_q type_state type_netprice type_fossilprice)
	reshape long type_ blank_, i(pathway) j(cost_price) string
	rename (type_ blank_)(value blank)
	replace pathway="Fats and Waste Oils Renewable Diesel (CA)" if pathway=="RD-animalfat-CA"
	replace pathway="Crop-based Vegetable oils Renewable Diesel (CA)" if pathway=="RD-soyoil-CA"
	replace pathway="Fats and Waste Oils SAF (CA)" if pathway=="SAF-animalfat-CA"
	replace pathway="Crop-based Vegetable oils SAF (CA)" if pathway=="SAF-soyoil-CA"
	replace pathway="Crop-based Vegetable oils SAF (Rest of US)" if pathway=="SAF-soyoil-NC"
	replace pathway="Fats and Waste Oils SAF (Rest of US)" if pathway=="SAF-animalfat-NC"
	replace pathway="Corn EJT with CCS (Rest of US)" if pathway=="SAF-corn-ETJCCS-NC"

	*create bar chart 
	gen ord = 1 if cost_price=="cost"
	replace ord = 2 if cost_price=="rin"
	replace ord = 3 if cost_price=="lcfs"
	replace ord = 4 if cost_price=="z"
	replace ord = 5 if cost_price=="q"
	replace ord = 6 if cost_price=="state"
	replace ord = 7 if cost_price=="netprice"
	replace ord = 8 if cost_price=="fossilprice"
	
	label define ordlbl 1 "Prod. cost" 2 "RIN" 3 "LCFS" ///
		 4 "45Z" 5 "45Q" 6 "State credits" ///
		 7 "Net price" 8 "Fossil price"
	label values ord ordlbl
	
	gen cost = value if cost_price=="cost"
	replace value =. if cost~=.
	gen price = value if cost_price=="netprice" | cost_price=="fossilprice"
	replace value =. if price~=.
	rename value credit
	
	gen barlabel = cost 
	replace barlabel = . if blank
	
	* Fats and Waste Oils Renewable Diesel (CA) 
	forval o=1/8 {
		foreach v of varlist cost credit price { 
			sum `v' if pathway=="Fats and Waste Oils Renewable Diesel (CA)" & ord==`o'
			local `v'`o' = r(mean)
			
			sum blank if pathway=="Fats and Waste Oils Renewable Diesel (CA)" & ord==`o'
			local `v'`o'h = ``v'`o'' + r(mean) + .2 
			
			if "`v'" ~="credit" {
				local `v'`o'h = ``v'`o'' + .2 
			}
			local `v'`o' = round(``v'`o''*100)/100
		}
	} 
	graph bar (sum) blank cost credit price if pathway=="Fats and Waste Oils Renewable Diesel (CA)", ///
		stack ytitle("Dollars per gallon", size(medium)) bar(1, color(none)) bar(2, color("${mydarkblue}")) bar(3, color("${myblue}")) ///
		bar(4, color("${mydarkrose}")) title("Fats and Waste Oils Renewable Diesel (CA)" " ") over(ord, label(angle(0) labsize(medium)) ///
		relabel(1 `""Production" "cost""' 6 `""State tax" "credits""' 7 `""Net" "price""' 8 `""Fossil" "price""')) ///
		legend(off) ylab(, labsize(medium)) ///
		text(`cost1h' 5 "`cost1'", size(3.5)) text(`credit2h' 18 "`credit2'", size(3.5)) text(`credit3h' 31 "`credit3'", size(3.5)) text(`credit4h' 43.5 "`credit4'", size(3.5)) ///
		text(`price7h' 82 "`price7'", size(3.5)) text(`price8h' 94.5 "`price8'", size(3.5))
	graph export "$output_folder/stack_fatrdca.$figtype", replace
	
* Crop-based Vegetable oils Renewable Diesel (CA)
	forval o=1/8 {
		foreach v of varlist cost credit price { 
			sum `v' if pathway=="Crop-based Vegetable oils Renewable Diesel (CA)" & ord==`o'
			local `v'`o' = r(mean)
			
			sum blank if pathway=="Crop-based Vegetable oils Renewable Diesel (CA)" & ord==`o'
			local `v'`o'h = ``v'`o'' + r(mean) + .2 
			
			if "`v'" ~="credit" {
				local `v'`o'h = ``v'`o'' + .2 
			}
			local `v'`o' = round(``v'`o''*100)/100
		}
	}
	graph bar (sum) blank cost credit price if pathway=="Crop-based Vegetable oils Renewable Diesel (CA)", ///
		stack ytitle("Dollars per gallon", size(medium)) bar(1, color(none)) bar(2, color("${mydarkblue}")) bar(3, color("${myblue}")) ///
		bar(4, color("${mydarkrose}")) title("Crop-based Vegetable oils Renewable Diesel (CA)") ylab(, labsize(medium)) over(ord, label(angle(0) labsize(medium)) ///
		relabel(1 `""Production" "cost""' 6 `""State tax" "credits""' 7 `""Net" "price""' 8 `""Fossil" "price""')) ///
		legend(off) ///
		text(`cost1h' 5 "`cost1'", size(3.5)) text(`credit2h' 18 "`credit2'", size(3.5)) text(`credit3h' 31 "`credit3'", size(3.5)) text(`credit4h' 43.5 "`credit4'", size(3.5)) ///
		text(`price7h' 82 "`price7'", size(3.5)) text(`price8h' 94.5 "`price8'", size(3.5))
	graph export "$output_folder/stack_soyrdca.$figtype", replace
	
	* Fats and Waste Oils SAF (CA)
	forval o=1/8 {
		foreach v of varlist cost credit price { 
			sum `v' if pathway=="Fats and Waste Oils SAF (CA)" & ord==`o'
			local `v'`o' = r(mean)
			
			sum blank if pathway=="Fats and Waste Oils SAF (CA)" & ord==`o'
			local `v'`o'h = ``v'`o'' + r(mean) + .2 
			
			if "`v'" ~="credit" {
				local `v'`o'h = ``v'`o'' + .2 
			}
			local `v'`o' = round(``v'`o''*100)/100
		}
	}
	graph bar (sum) blank cost credit price if pathway=="Fats and Waste Oils SAF (CA)", ///
		stack ytitle("Dollars per gallon", size(medium)) bar(1, color(none)) bar(2, color("${mydarkblue}")) bar(3, color("${myblue}")) ///
		bar(4, color("${mydarkrose}")) title("Fats and Waste Oils SAF (CA)") over(ord, label(angle(0) labsize(medium)) ///
		relabel(1 `""Production" "cost""' 6 `""State tax" "credits""' 7 `""Net" "price""' 8 `""Fossil" "price""')) ///
		legend(off) ylab(, labsize(medium)) ///
		text(`cost1h' 5 "`cost1'", size(3.5)) text(`credit2h' 18 "`credit2'", size(3.5)) text(`credit4h' 43.5 "`credit4'", size(3.5)) text(`credit6h' 69 "`credit6'", size(3.5)) ///
		text(`price7h' 82 "`price7'", size(3.5)) text(`price8h' 94.5 "`price8'", size(3.5))
	graph export "$output_folder/stack_fatsafca.$figtype", replace
	
	* Crop-based Vegetable oils SAF (CA)
	forval o=1/8 {
		foreach v of varlist cost credit price { 
			sum `v' if pathway=="Crop-based Vegetable oils SAF (CA)" & ord==`o'
			local `v'`o' = r(mean)
			
			sum blank if pathway=="Crop-based Vegetable oils SAF (CA)" & ord==`o'
			local `v'`o'h = ``v'`o'' + r(mean) + .2 
			
			if "`v'" ~="credit" {
				local `v'`o'h = ``v'`o'' + .2 
			}
			local `v'`o' = round(``v'`o''*100)/100
		}
	}
	graph bar (sum) blank cost credit price if pathway=="Crop-based Vegetable oils SAF (CA)", ///
		stack ytitle("Dollars per gallon", size(medium)) bar(1, color(none)) bar(2, color("${mydarkblue}")) bar(3, color("${myblue}")) ///
		bar(4, color("${mydarkrose}")) title("Crop-based Vegetable oils SAF (CA)") over(ord, label(angle(0) labsize(medium)) ///
		relabel(1 `""Production" "cost""' 6 `""State tax" "credits""' 7 `""Net" "price""' 8 `""Fossil" "price""')) ///
		legend(off) ylab(, labsize(medium))  ///
		text(`cost1h' 5 "`cost1'", size(3.5)) text(`credit2h' 18 "`credit2'", size(3.5)) text(`credit4h' 43.5 "`credit4'", size(3.5)) text(`credit6h' 69 "`credit6'", size(3.5)) ///
		text(`price7h' 82 "`price7'", size(3.5)) text(`price8h' 94.5 "`price8'", size(3.5))
	graph export "$output_folder/stack_soysafca.$figtype", replace
	
	* Fats and Waste Oils SAF (Rest of US)
	forval o=1/8 {
		foreach v of varlist cost credit price { 
			sum `v' if pathway=="Fats and Waste Oils SAF (Rest of US)" & ord==`o'
			local `v'`o' = r(mean)
			
			sum blank if pathway=="Fats and Waste Oils SAF (Rest of US)" & ord==`o'
			local `v'`o'h = ``v'`o'' + r(mean) + .2 
			
			if "`v'" ~="credit" {
				local `v'`o'h = ``v'`o'' + .2 
			}
			local `v'`o' = round(``v'`o''*100)/100
		}
	}
	graph bar (sum) blank cost credit price if pathway=="Fats and Waste Oils SAF (Rest of US)", ///
		stack ytitle("Dollars per gallon", size(medium)) bar(1, color(none)) bar(2, color("${mydarkblue}")) bar(3, color("${myblue}")) ///
		bar(4, color("${mydarkrose}")) title("Fats and Waste Oils SAF (Rest of US)") over(ord, label(angle(0) labsize(medium)) ///
		relabel(1 `""Production" "cost""' 6 `""State tax" "credits""' 7 `""Net" "price""' 8 `""Fossil" "price""')) ///
		legend(off) ylab(, labsize(medium)) ///
		text(`cost1h' 5 "`cost1'", size(3.5)) text(`credit2h' 18 "`credit2'", size(3.5)) text(`credit4h' 43.5 "`credit4'", size(3.5)) text(`credit6h' 69 "`credit6'", size(3.5)) ///
		text(`price7h' 82 "`price7'", size(3.5)) text(`price8h' 94.5 "`price8'", size(3.5))
	graph export "$output_folder/stack_fatsafrous.$figtype", replace
	
	* Crop-based Vegetable oils SAF (Rest of US)
	forval o=1/8 {
		foreach v of varlist cost credit price { 
			sum `v' if pathway=="Crop-based Vegetable oils SAF (Rest of US)" & ord==`o'
			local `v'`o' = r(mean)
			
			sum blank if pathway=="Crop-based Vegetable oils SAF (Rest of US)" & ord==`o'
			local `v'`o'h = ``v'`o'' + r(mean) + .2 
			
			if "`v'" ~="credit" {
				local `v'`o'h = ``v'`o'' + .2 
			}
			local `v'`o' = round(``v'`o''*100)/100
		}
	}
	graph bar (sum) blank cost credit price if pathway=="Crop-based Vegetable oils SAF (Rest of US)", ///
		stack ytitle("Dollars per gallon", size(medium)) bar(1, color(none)) bar(2, color("${mydarkblue}")) bar(3, color("${myblue}")) ///
		bar(4, color("${mydarkrose}")) title("Crop-based Vegetable oils SAF (Rest of US)") over(ord, label(angle(0) labsize(medium)) ///
		relabel(1 `""Production" "cost""' 6 `""State tax" "credits""' 7 `""Net" "price""' 8 `""Fossil" "price""')) ///
		legend(off) ylab(, labsize(medium))  ///
		text(`cost1h' 5 "`cost1'", size(3.5)) text(`credit2h' 18 "`credit2'", size(3.5)) text(`credit4h' 43.5 "`credit4'", size(3.5)) text(`credit6h' 69 "`credit6'", size(3.5)) ///
		text(`price7h' 82 "`price7'", size(3.5)) text(`price8h' 94.5 "`price8'", size(3.5))
	graph export "$output_folder/stack_soysafrous.$figtype", replace
	
	* Corn EJT with CCS (Rest of US)
	forval o=1/8 {
		foreach v of varlist cost credit price { 
			sum `v' if pathway=="Corn EJT with CCS (Rest of US)" & ord==`o'
			local `v'`o' = r(mean)
			
			sum blank if pathway=="Corn EJT with CCS (Rest of US)" & ord==`o'
			local `v'`o'h = ``v'`o'' + r(mean) + .2 
			
			if "`v'" ~="credit" {
				local `v'`o'h = ``v'`o'' + .2 
			}
			local `v'`o' = round(``v'`o''*100)/100
		}
	}
	graph bar (sum) blank cost credit price if pathway=="Corn EJT with CCS (Rest of US)", ///
		stack ytitle("Dollars per gallon", size(medium)) bar(1, color(none)) bar(2, color("${mydarkblue}")) bar(3, color("${myblue}")) ///
		bar(4, color("${mydarkrose}")) title("Corn EJT with CCS (Rest of US)") over(ord, label(angle(0) labsize(medium)) ///
		relabel(1 `""Production" "cost""' 6 `""State tax" "credits""' 7 `""Net" "price""' 8 `""Fossil" "price""')) ///
		legend(off) ylab(, labsize(medium))  ///
		text(`cost1h' 5 "`cost1'", size(3.5)) text(`credit2h' 18 "`credit2'", size(3.5)) text(`credit4h' 43.5 "`credit4'", size(3.5)) text(`credit6h' 69 "`credit6'", size(3.5)) ///
		text(`price7h' 82 "`price7'", size(3.5)) text(`price8h' 94.5 "`price8'", size(3.5))
	graph export "$output_folder/stack_etjsafrous.$figtype", replace

* ============================================================================
* Figure 4 - Average Abatement Cost (AAC)
* ============================================================================
	
	*bring in data
	import excel using "$input_file", cellrange(n1:v3) firstrow clear ///
		sheet("AAC")
	rename N outcome
	keep outcome SAFCredit NestedD2 D2withaviationobligation NestedD2stricterRFS ///
		CarbonTaxSAFcredit AviationIntensityStd CurrentPolicy
	rename (SAFCredit NestedD2 D2withaviationobligation NestedD2stricterRFS ///
	CarbonTaxSAFcredit AviationIntensityStd CurrentPolicy) ///
	(scenario_SAFCredit scenario_NestedD2 scenario_D2aviation ///
	scenario_NestedD2RFS scenario_CarbonTaxSAF ///
	scenario_AviationIntensityStd scenario_CurrentPolicy)
	
	*reshape data
	reshape long scenario_, i(outcome) j(name) string
	rename scenario_ value
	rename name scenario
	replace outcome = "avg_abate_cost" if strpos(outcome, "Abate")>0
	replace outcome = "emis_red" if strpos(outcome, "Reduction")>0
	reshape wide value, i(scenario) j(outcome) string
	rename value* *
	
	*rename scenarios 
	replace scenario = "Current Policy"  if strpos(scenario, "Current") >0
	replace scenario = "Carbon Tax + SAF Credit"  if strpos(scenario, "CarbonTaxSAF") >0
	replace scenario = "Nested D2"  if scenario =="NestedD2"
	replace scenario = "D2 w/ Aviation Obligation"  if strpos(scenario, "D2aviat") >0
	replace scenario = "Nested D2 + Stricter RFS"  if strpos(scenario, "D2RFS") >0
	replace scenario = "SAF Credit"  if scenario== "SAFCredit"
	replace scenario = "Aviation Intensity Standard" if scenario=="AviationIntensityStd"
	
	*make emissions reductions percents 
	replace emis_red = emis_red*100
	
	*generate custum callout lines 
	cap drop avg_line emis_line
	gen avg_line = avg_abate_cost +20
	gen emis_line = emis_red + .2
	
	replace avg_line = avg_abate_cost -50 if scenario=="Current Policy"
	replace emis_line = emis_red - .6 if scenario=="Current Policy"
	
	replace avg_line = avg_abate_cost-40 if scenario=="Carbon Tax + SAF Credit"
	replace emis_line = emis_red + 0 if scenario=="Carbon Tax + SAF Credit"
	
	replace avg_line = avg_abate_cost -80 if scenario=="Aviation Intensity Standard"
	replace emis_line = emis_red + 0 if scenario=="Aviation Intensity Standard"
	
	replace avg_line = avg_abate_cost +50 if scenario=="D2 w/ Aviation Obligation"
	replace emis_line = emis_red + .1 if scenario=="D2 w/ Aviation Obligation"
	
	replace avg_line = avg_abate_cost -0 if scenario=="Nested D2"
	replace emis_line = emis_red + .2 if scenario=="Nested D2"
	
	replace avg_line = avg_abate_cost -80 if scenario=="Nested D2 + Stricter RFS"
	replace emis_line = emis_red + 0 if scenario=="Nested D2 + Stricter RFS"
	
	*make labels span two lines 
	gen avg_line2 = avg_line-30
	gen scenario2 = "Standard" if scenario=="Aviation Intensity Standard"
	replace scenario = "Aviation Intensity" if scenario=="Aviation Intensity Standard"
	replace scenario2 = "Stricter RFS" if scenario=="Nested D2 + Stricter RFS"
	replace scenario = "Nested D2 +" if scenario=="Nested D2 + Stricter RFS"
	replace scenario2 = "SAF Credit" if scenario=="Carbon Tax + SAF Credit"
	replace scenario = "Carbon Tax +" if scenario=="Carbon Tax + SAF Credit"
	
	*plot
	generate pos = 3
	replace pos = 6 if inlist(scenario, "Current Policy", "Carbon Tax +", ///
		"Aviation Intensity", "Nested D2 +")
	replace pos = 12 if inlist(scenario, "SAF Credit")
	
	qui sum avg_abate_cost if scenario=="Current Policy"
	local xdot = `r(mean)'
	qui sum emis_red if scenario=="Current Policy"
	local ydot = `r(mean)'
	twoway (pcspike avg_abate_cost emis_red avg_line emis_line, lcolor(gray) legend(off)) ///
		(scatter avg_abate_cost emis_red, ytitle("Average Abatement Cost ($/ton)", size(medsmall)) ///
		xtitle("Transportation Emissions Reduction (%)", size(medsmall)) mcolor("${mydarkblue}")  ///
		xscale(range(0 5)) msize(medium) xlab(0(.5)5, labsize(medsmall)) yscale(range(0 600)) ylab(0(100)600, ///
		labsize(medsmall))) ///
		(scatter avg_line2 emis_line, ///
		mlabel(scenario2) mlabsize(medsmall) mlabv(pos) ///
		mlabcolor(black) msymbol(i) xline(`ydot', lcolor(gray)) yline(`xdot', lcolor(gray))) ///
		(scatter avg_line emis_line, ///
		mlabel(scenario) mlabsize(medsmall) mlabv(pos) ///
		mlabcolor(black) msymbol(i) xline(`ydot', lcolor(gray)) yline(`xdot', lcolor(gray))) 	
	graph export "$output_folder/scatter.$figtype", replace	
	
	*calculate in-text values 
	gen ord =1 if scenario=="Current Policy"
	sort ord
	gen emis_red_perc = round((emis_red-emis_red[1])/emis_red[1]*100, 1)
	gen avg_cost_perc = round((avg_abat-avg_abat[1])/avg_abat[1]*100, 1)

* ============================================================================
* Figure 5 - Policy Cost Breakdown
* ============================================================================
	
	*bring in data
	import excel using "$input_file", cellrange(a1:l8) firstrow clear ///
		sheet("AAC")
	rename Metric party
	keep if inlist(party, "Fuel Expenditure at current prices, no policy quantities" , ///
	"Government spending (Tax subsidies)", "Carbon tax revenue")
	drop CurrentPolicyNoLCFS CarbontaxnoSAF NonnestedstricterRFS
	rename (Qmandate NestedD2 NonnestedD2 NestedD2stricterRFS ///
		Aviationintensitystandard CurrentPolicy CarbonTax) ///
		(scenario_SAFCredit scenario_NestedD2 scenario_D2aviation scenario_NestedD2RFS ///
		scenario_AviationIntensityStd scenario_CurrentPolicy scenario_CarbonTaxSAFcredit) 
	foreach v of varlist scenario* {
		replace `v' = `v'-Nopolicy
		replace `v' = `v'*-1 if party=="Carbon tax revenue"
	}
	drop Nopolicy
	
	*simplify categories 
	replace party = "Government Spending" if party=="Government spending (Tax subsidies)"
	replace party = "Additional Fuel Costs" if party=="Fuel Expenditure at current prices, no policy quantities"
	replace party = "Carbon Tax Revenue" if party=="Carbon tax revenue"

	*reshape data
	replace party = "spend" if party=="Government Spending"
	replace party = "fuel" if party=="Additional Fuel Costs"
	replace party = "rev" if party=="Carbon Tax Revenue"
	
	reshape long scenario_, i(party) j(name) string
	rename scenario_ value
	rename name scenario
	reshape wide value, i(scenario) j(party) string
	rename value* *
	
	*calculate sums 
	gen tot_cost = spend + fuel + rev
	
	*create custum order and labels for scenarios 
	gen ord = 1 if scenario=="CurrentPolicy"
	replace ord = 2 if scenario=="SAFCredit"
	replace ord = 3 if scenario=="NestedD2"
	replace ord = 4 if scenario=="D2aviation"
	replace ord = 5 if scenario=="NestedD2RFS"
	replace ord = 6 if scenario=="CarbonTaxSAFcredit"
	replace ord = 7 if scenario=="AviationIntensityStd"
	label define ordlbl 1 "Current Policy" 2 "SAF Credit" ///
		 3 "Nested D2" 4 "D2 with Aviation Obligation" 5 "Nested D2 + Stricter RFS" ///
		 6 "Carbon Tax + SAF Credit" 7 "Aviation Intensity Standard"
	label values ord ordlbl
	
	gen tall_spend = fuel + spend
	gen ord_gap = ord*2 
	twoway ///
		(bar tall_spend ord_gap, color("${mylightblue}") lcolor("${mylightblue}") fintensity(100)) ///
		(bar tall_spend ord_gap, color("${myblue}") lcolor(none) fintensity(100)) ///
		(bar fuel ord_gap, color("${mylightblue}") lcolor("${mylightblue}") fintensity(100)) ///
		(bar rev ord_gap, fcolor("${mydarkblue}") lcolor("${mydarkblue}") fintensity(100)) ///
		(scatter tot_cost ord_gap, msymbol(D) msize(medium) mcolor("${mydarkrose}")), ///
		legend(pos(6) col(4) order(1 "Additional Fuel Costs" 2 ///
		"Gov Spending" 4 "Carbon Tax Revenue" 5 "Total Policy Cost")) ///
		xlabel(2 `""Current" "Policy""' 4 "SAF Credit" ///
		6 "Nested D2" 8 `""D2 w/Aviation" "Obligation""' ///
		10 `""Nested D2 +" "Stricter RFS""' 12 `""Carbon Tax +" "SAF Credit""' ///
		14 `""Aviation" "Intensity" "Standard""', angle(0) nogrid) xtitle("") ///
		ytitle("Total policy costs, excluding" "revenue (billions of dollars)") xsize(8) 
	graph export "$output_folder/policycost_breakdown.$figtype", replace

* ============================================================================
* Figure 6 - Policy Cost Share
* ============================================================================

	*bring in data
	import excel using "$input_file", cellrange(n1:u8) firstrow clear ///
		sheet("Subsidy breakup")
	rename N party
	rename (AviationIntensityStd CarbonTaxSAFcredit NestedD2stricterRFS ///
		D2withaviationobligation NestedD2 SAFCredit CurrentPolicy) ///
		(scenario_AviationIntensityStd scenario_CarbonTaxSAFcredit scenario_NestedD2RFS ///
		scenario_D2aviation scenario_NestedD2 scenario_SAFCredit ///
		scenario_CurrentPolicy)
	drop if party==""
	
	*reshape data
	replace party = "air_ca" if party=="Air passengers (CA)"
	replace party = "air_nc" if party=="Air passengers (NC)"
	replace party = "d_ca" if party=="Diesel (CA)"
	replace party = "d_nc" if party=="Diesel (ROUS)"
	replace party = "gas_ca" if party=="Gasoline (CA)"
	replace party = "gas_nc" if party=="Gasoline (ROUS)"
	replace party = "tax" if party=="Taxpayers"
	
	reshape long scenario_, i(party) j(name) string
	rename scenario_ value
	rename name scenario
	reshape wide value, i(scenario) j(party) string
	rename value* *
	
	*calculate totals and convert to percentages 
	egen tot_cost = rowtotal(air_ca-tax)
	foreach v of varlist air_ca-tax {
			replace `v'=`v'/tot_cost*100
	}
	
	*create custum order and labels for scenarios 
	gen ord = 1 if scenario=="CurrentPolicy"
	replace ord = 3 if scenario=="SAFCredit"
	replace ord = 4 if scenario=="NestedD2"
	replace ord = 5 if scenario=="D2aviation"
	replace ord = 6 if scenario=="NestedD2RFS"
	replace ord = 7 if scenario=="CarbonTaxSAFcredit"
	replace ord = 8 if scenario=="AviationIntensityStd"
	label define ordlbl 1 "Current Policy" 3 "SAF Credit" ///
		 4 "Nested D2" 5 "D2 with Aviation Obligation" 6 "Nested D2 + Stricter RFS" ///
		 7 "Carbon Tax + SAF Credit" 8 "Aviation Intensity Standard"
	label values ord ordlbl
	
	graph bar (sum) tax d_nc d_ca gas_nc gas_ca air_nc air_ca, stack name(g3, replace) ///
	over(ord, gap(100) label(angle(0)) relabel(1 `""Current" "Policy""' 4 `""D2 w/Aviation" "Obligation""' 5 ///
	`""Nested D2 +" "Stricter RFS""' 6 `""Carbon Tax +" "SAF Credit""' 7 `""Aviation" "Intensity" "Standard""')) ///
	title("") bar(1, color("${mutedteal}")) bar(2, color("${mydarkrose}")) bar(3, color("${mylightrose}")) ///
	bar(4, color("${mydarkblue}")) bar(5, color("${myblue}")) ///
	bar(6, color("${mydarkyellow}")) bar(7, color("${myyellow}")) ///
	legend(pos(6) col(3) order(1 "Taypayers" 2 "Diesel (Rest of US) *" 3 "Diesel (CA)" ///
	4 "Gasoline (Rest of US) *" 5 "Gasoline (CA)" 6 "Air Passengers (Rest of US) *" 7 "Air Passengers (CA)")) ///
	ytitle("Share of total policy costs," "excluding revenue (%)") xsize(8)
	
	graph export "$output_folder/policycost_share.$figtype", replace	

* ============================================================================
* Figure 7 - Fuel Prices
* ============================================================================

	*bring in data
	import excel using "$input_file", cellrange(n1:t7) firstrow clear ///
		sheet("Fuel prices")
	rename (Metric SAFCredit NestedD2 NonnestedD2 NestedD2stricterRFS ///
		CarbonTax Aviationintensitystandard) ///
		(fuel scenario_SAFCredit scenario_NestedD2 scenario_D2aviation scenario_NestedD2RFS ///
		scenario_CarbonTaxSAFcredit scenario_aviation)

	
	*reshape data
	replace fuel = "air_ca" if fuel=="Aviation (CA)"
	replace fuel = "air_nc" if fuel=="Aviation (ROUS)"
	replace fuel = "d_ca" if fuel=="Blended diesel (CA)"
	replace fuel = "d_nc" if fuel=="Blended diesel (ROUS)"
	replace fuel = "gas_ca" if fuel=="E10 (CA)"
	replace fuel = "gas_nc" if fuel=="E10 (ROUS)"
	
	reshape long scenario_, i(fuel) j(name) string
	rename scenario_ value
	rename name scenario
	reshape wide value, i(scenario) j(fuel) string
	rename value* *
	
	*create custum order and labels for scenarios 
	gen ord = 1 if scenario=="SAFCredit"
	replace ord = 4 if scenario=="NestedD2"
	replace ord = 5 if scenario=="D2aviation"
	replace ord = 6 if scenario=="NestedD2RFS"
	replace ord = 7 if scenario=="CarbonTaxSAFcredit"
	replace ord = 8 if scenario=="aviation"
	label define ordlbl 1 "SAF Credit" ///
		 4 "Nested D2" 5 "D2 with Aviation Obligation" 6 "Nested D2 + Stricter RFS" ///
		 7 "Carbon Tax + SAF Credit" 8 "Aviation Intensity Standard"
	label values ord ordlbl
	
	graph hbar (sum) d_nc gas_nc air_nc, name(g3, replace) ///
		over(ord, gap(100) label(angle(0) labsize(medlarge))) title("")  ///
		bar(1, color("${mydarkrose}")) bar(2, color("${mydarkblue}"))  ///
		bar(3, color("${mydarkyellow}")) yline(0) ///
		legend(off) ///
		ytitle("Rest of U.S. *", size(medlarge)) xsize(9) ///
		yscale(range(-.1 .5)) ylab(-0.1(.1).5, labsize(medlarge))
		graph export "$output_folder/fuelprices_rous.$figtype", replace
		
	graph hbar (sum) d_ca gas_ca air_ca, name(g3, replace) ///
		over(ord, gap(100) label(angle(0) labsize(medlarge))) title("")  ///
		bar(1, color("${mydarkrose}")) bar(2, color("${mydarkblue}"))  ///
		bar(3, color("${mydarkyellow}")) yline(0) ///
		legend(off) ///
		ytitle("California", size(medlarge)) xsize(9) ///
		yscale(range(-.1 .5)) ylab(-0.1(.1).5, labsize(medlarge))
		graph export "$output_folder/fuelprices_ca.$figtype", replace
		
	graph hbar d_ca gas_ca air_ca, ///
		over(ord, label(labcolor(white))) stack name(g1, replace)  ///
		title("Gasoline") ytitle("") ///
		bar(1, color("${mydarkrose}")) ///
		bar(2, color("${mydarkblue}")) bar(3, color("${mydarkyellow}")) xsize(10) ///
		ytitle("Change in blended fuel costs (dollars per gallon)", size(medium)) ///
		legend(pos(6) col(6) size(medium) ///
		order(1 "Blended Diesel" 2 "E10" 3 "Aviation"))
		graph export "$output_folder/fuelprices_legend.$figtype", replace	

* ============================================================================
* Figure 8 - Feedstock Demand
* ============================================================================

	*bring in data
	import excel using "$input_file", cellrange(n8:t12) firstrow clear ///
		sheet("Feedstock")
	rename (ChangeinFeedstockDemandbill SAFCredit NestedD2 NonnestedD2 ///
		NestedD2stricterRFS CarbonTax Aviationintensitystandard) ///
		(fuel scenario_SAFCredit scenario_NestedD2 scenario_D2aviation scenario_NestedD2RFS ///
		scenario_CarbonTaxSAFcredit scenario_aviation)
	
	*reshape data
	replace fuel = "soybean" if fuel=="Soybean Oil"
	replace fuel = "fat" if fuel=="Fats, oils, greases"
	replace fuel = "corn" if fuel=="Corn"
	replace fuel = "sugar" if fuel=="Sugarcane"
	
	reshape long scenario_, i(fuel) j(name) string
	rename scenario_ value
	rename name scenario
	reshape wide value, i(scenario) j(fuel) string
	rename value* *
	
	*create custum order and labels for scenarios 
	gen ord = 1 if scenario=="SAFCredit"
	replace ord = 4 if scenario=="NestedD2"
	replace ord = 5 if scenario=="D2aviation"
	replace ord = 6 if scenario=="NestedD2RFS"
	replace ord = 7 if scenario=="CarbonTaxSAFcredit"
	replace ord = 8 if scenario=="aviation"
	label define ordlbl 1 "SAF Credit" ///
		 4 "Nested D2" 5 "D2 with Aviation Obligation" 6 "Nested D2 + Stricter RFS" ///
		 7 "Carbon Tax + SAF Credit" 8 "Aviation Intensity Standard"
	label values ord ordlbl
	
	graph bar (sum) soybean fat corn sugar, stack name(g3, replace) ///
		over(ord, gap(100) label(angle(0)) relabel(3 `""D2 w/Aviation" "Obligation""' 4 ///
		`""Nested D2 +" "Stricter RFS""' 5 `""Carbon Tax +" "SAF Credit""' 6 ///
		`""Aviation" "Intensity" "Standard""'))  ///
		title("")  bar(1, color("${mydarkrose}")) bar(2, color("${mylightrose}")) ///
		bar(3, color("${myyellow}")) bar(4, color("${myblue}")) ///
		legend(pos(6) col(4) order(1 "Vegetable Oil" 2 "Fats, oils, greases" ///
		3 "Corn" 4 "Sugarcane")) ytitle("Feedstock demand (billion pounds)") xsize(8)
	graph export "$output_folder/feedstock_demand.$figtype", replace

di ""
di "================================================================================"
di "Completed: $current_quantile ($figtype format)"
di "Figures saved to: $output_folder"
di "================================================================================"

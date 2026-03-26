********************************************************************************
* ROBUSTNESS CHECKS FOR BASELINE REGRESSION
* Baseline: gdp_growth ~ export_vol_growth + import_vol_growth +
*           real_credit_growth + energy_consumption_growth + real_tax_growth + india
*
* Checks:
* (1) Drop energy consumption
* (2) Drop tax revenues
* (3) Export only (drop import)
* (4) Import only (drop export)
* (5) Add GCF growth
* (6) Replace energy with electricity consumption
********************************************************************************



*─── SPEC 1: Baseline - credit ─────────────────────────────────────────────────
use "panel 1995 onwards.dta", clear
preserve
gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, import_vol_growth, real_tax_growth, energy_consumption_growth)
keep if oil_producer==0 & small_1995==0 & fragile_state==0
keep if inrange(year, 1995, 2011)
keep if complete_data==1
collapse (mean) gdp_growth export_vol_growth import_vol_growth real_tax_growth energy_consumption_growth india, by(country_name)
reg gdp_growth export_vol_growth import_vol_growth real_tax_growth energy_consumption_growth india, robust
restore

*─── SPEC 2: Baseline - Import ─────────────────────────────────────────
use "panel 1995 onwards.dta", clear
preserve
gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, real_credit_growth, energy_consumption_growth, real_tax_growth)
keep if oil_producer==0 & small_1995==0 & fragile_state==0
keep if inrange(year, 1995, 2011)
keep if complete_data==1
collapse (mean) gdp_growth export_vol_growth real_credit_growth energy_consumption_growth real_tax_growth india, by(country_name)
reg gdp_growth export_vol_growth real_credit_growth energy_consumption_growth real_tax_growth india, robust
restore


*─── SPEC 3: Baseline + GCF growth ─────────────────────────────────────────────
use "panel 1995 onwards.dta", clear
preserve
gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, import_vol_growth, real_credit_growth, energy_consumption_growth, real_tax_growth, gcf_growth)
keep if oil_producer==0 & small_1995==0 & fragile_state==0
keep if inrange(year, 1995, 2011)
keep if complete_data==1
collapse (mean) gdp_growth export_vol_growth import_vol_growth real_credit_growth energy_consumption_growth real_tax_growth gcf_growth india, by(country_name)
reg gdp_growth export_vol_growth import_vol_growth real_credit_growth energy_consumption_growth real_tax_growth gcf_growth india, robust
restore


*─── SPEC 4: Baseline - Import + GCF + Govt expenditure ─────────────────────────────────────────────
use "panel 1995 onwards.dta", clear
preserve
gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, real_credit_growth, energy_consumption_growth, real_tax_growth, govt_exp_growth, gcf_growth)
keep if oil_producer==0 & small_1995==0 & fragile_state==0
keep if inrange(year, 1995, 2011)
keep if complete_data==1
collapse (mean) gdp_growth export_vol_growth real_credit_growth energy_consumption_growth real_tax_growth govt_exp_growth gcf_growth india, by(country_name)
reg gdp_growth export_vol_growth real_credit_growth energy_consumption_growth real_tax_growth govt_exp_growth gcf_growth india, robust
restore

*─── SPEC 5: Baseline - Import + GCF + Govt expenditure (Replacing energy with electricity)─────────────────────────────────────────────
use "panel 1995 onwards.dta", clear
preserve
gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, real_credit_growth, elec_consumption, real_tax_growth, govt_exp_growth, gcf_growth)
keep if oil_producer==0 & small_1995==0 & fragile_state==0
keep if inrange(year, 1995, 2011)
keep if complete_data==1
collapse (mean) gdp_growth export_vol_growth real_credit_growth elec_consumption real_tax_growth govt_exp_growth gcf_growth india, by(country_name)
reg gdp_growth export_vol_growth real_credit_growth elec_consumption real_tax_growth govt_exp_growth gcf_growth india, robust
restore


********************************************************************************
* SECTION 2: 2012–2024
********************************************************************************

*─── SPEC 1: Baseline - credit ─────────────────────────────────────────────────
use "panel 1995 onwards.dta", clear
preserve
gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, import_vol_growth, real_tax_growth, energy_consumption_growth)
keep if oil_producer==0 & small_2011==0 & fragile_state==0
keep if inrange(year, 2012, 2024)
drop if year==2020 | year==2021
keep if complete_data==1
collapse (mean) gdp_growth export_vol_growth import_vol_growth real_tax_growth energy_consumption_growth india, by(country_name)
reg gdp_growth export_vol_growth import_vol_growth real_tax_growth energy_consumption_growth india, robust
restore

*─── SPEC 2: Baseline - Import ─────────────────────────────────────────
use "panel 1995 onwards.dta", clear
preserve
gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, real_credit_growth, energy_consumption_growth, real_tax_growth)
keep if oil_producer==0 & small_2011==0 & fragile_state==0
keep if inrange(year, 2012, 2024)
drop if year==2020 | year==2021
keep if complete_data==1
collapse (mean) gdp_growth export_vol_growth real_credit_growth energy_consumption_growth real_tax_growth india, by(country_name)
reg gdp_growth export_vol_growth real_credit_growth energy_consumption_growth real_tax_growth india, robust
restore


*─── SPEC 3: Baseline + GCF growth ─────────────────────────────────────────────
use "panel 1995 onwards.dta", clear
preserve
gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, import_vol_growth, real_credit_growth, energy_consumption_growth, real_tax_growth, gcf_growth)
keep if oil_producer==0 & small_2011==0 & fragile_state==0
keep if inrange(year, 2012, 2024)
drop if year==2020 | year==2021
keep if complete_data==1
collapse (mean) gdp_growth export_vol_growth import_vol_growth real_credit_growth energy_consumption_growth real_tax_growth gcf_growth india, by(country_name)
reg gdp_growth export_vol_growth import_vol_growth real_credit_growth energy_consumption_growth real_tax_growth gcf_growth india, robust
restore


*─── SPEC 4: Baseline - Import + GCF + Govt expenditure ─────────────────────────────────────────────
use "panel 1995 onwards.dta", clear
preserve
gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, real_credit_growth, energy_consumption_growth, real_tax_growth, govt_exp_growth, gcf_growth)
keep if oil_producer==0 & small_2011==0 & fragile_state==0
keep if inrange(year, 2012, 2024)
drop if year==2020 | year==2021
keep if complete_data==1
collapse (mean) gdp_growth export_vol_growth real_credit_growth energy_consumption_growth real_tax_growth govt_exp_growth gcf_growth india, by(country_name)
reg gdp_growth export_vol_growth real_credit_growth energy_consumption_growth real_tax_growth govt_exp_growth gcf_growth india, robust
restore

*─── SPEC 5: Baseline - Import + GCF + Govt expenditure (Replacing energy with electricity)─────────────────────────────────────────────
use "panel 1995 onwards.dta", clear
preserve
gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, real_credit_growth, elec_consumption, real_tax_growth, govt_exp_growth, gcf_growth)
keep if oil_producer==0 & small_2011==0 & fragile_state==0
keep if inrange(year, 2012, 2024)
drop if year==2020 | year==2021
keep if complete_data==1
collapse (mean) gdp_growth export_vol_growth real_credit_growth elec_consumption real_tax_growth govt_exp_growth gcf_growth india, by(country_name)
reg gdp_growth export_vol_growth real_credit_growth elec_consumption real_tax_growth govt_exp_growth gcf_growth india, robust
restore







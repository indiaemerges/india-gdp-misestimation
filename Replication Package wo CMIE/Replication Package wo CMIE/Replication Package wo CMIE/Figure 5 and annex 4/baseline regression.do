cd "."
*use "panel regression data with gcf.dta", clear

*import excel "panel regression 1995-2024.xlsx", sheet("Panel Data") firstrow clear


*gen india=0
*replace india=1 if country_name=="India"

*save ".\panel 1995 onwards.dta"

use "panel 1995 onwards.dta", clear

*******Baseline Regression*******
**** Cross section 1995-2011*****
preserve

gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, import_vol_growth, energy_consumption_growth, real_credit_growth, real_tax_growth)


keep if oil_producer == 0 & small_1995 == 0 & fragile_state == 0
keep if inrange(year, 1995, 2011)
keep if complete_data == 1

collapse (mean) gdp_growth export_vol_growth import_vol_growth real_credit_growth energy_consumption_growth real_tax_growth india, by(country_name)
reg gdp_growth export_vol_growth import_vol_growth real_credit_growth energy_consumption_growth real_tax_growth india, robust


* Predicted values (includes india effect)
predict double yhat, xb

* Predicted values based only on indicators (exclude india dummy contribution)
gen double yhat_noindia = yhat - _b[india]*india
label var yhat_noindia "Predicted Growth"

* Relationship between actual and predicted for the baseline sample
reg gdp_growth yhat_noindia, robust

predict double fit, xb
predict double sefit, stdp
gen double ub = fit + invnormal(0.975)*sefit
gen double lb = fit - invnormal(0.975)*sefit

capture drop country_label
gen str10 country_label = ""
replace country_label = "India" if india == 1


twoway ///
    (rarea ub lb yhat_noindia, sort ///
	fcolor("186 181 213") lcolor("186 181 213")) ///
	    (line fit yhat_noindia, sort ///
        lcolor("70 55 183") lwidth(medthick)) ///
    (scatter gdp_growth yhat_noindia if india==1, ///
        msymbol(O) msize(large) mcolor(blue) ///
        mlabel(country_label) mlabcolor(black) mlabsize(medlarge) ///
        mlabposition(e)) ///
    , ///
    xtitle("Predicted Growth") ///
    ytitle("Actual Growth") ///
    legend(off) ///
    graphregion(color("242 242 242")) ///
    plotregion(color(white))

restore


**** Cross section 2012-2024*****

use "panel 1995 onwards.dta", clear

preserve

gen byte complete_data = ///
    !missing(gdp_growth, export_vol_growth, import_vol_growth, energy_consumption_growth, real_credit_growth, real_tax_growth)

keep if oil_producer == 0 & small_2011 == 0 & fragile_state == 0
drop if year==2020|year==2021
keep if complete_data == 1
keep if inrange(year, 2012, 2024)

collapse (mean) gdp_growth export_vol_growth import_vol_growth real_credit_growth energy_consumption_growth real_tax_growth india, by(country_name)
reg gdp_growth export_vol_growth import_vol_growth real_credit_growth energy_consumption_growth real_tax_growth india, robust

* Predicted values (includes india effect)
predict double yhat, xb

* Predicted values based only on indicators (exclude india dummy contribution)
gen double yhat_noindia = yhat - _b[india]*india
label var yhat_noindia "Predicted Growth"

* Relationship between actual and predicted for the baseline sample
reg gdp_growth yhat_noindia, robust

predict double fit, xb
predict double sefit, stdp
gen double ub = fit + invnormal(0.975)*sefit
gen double lb = fit - invnormal(0.975)*sefit

capture drop country_label
gen str10 country_label = ""
replace country_label = "India" if india == 1


twoway ///
    (rarea ub lb yhat_noindia, sort ///
	fcolor("186 181 213") lcolor("186 181 213")) ///
	    (line fit yhat_noindia, sort ///
        lcolor("70 55 183") lwidth(medthick)) ///
    (scatter gdp_growth yhat_noindia if india==1, ///
        msymbol(O) msize(large) mcolor(blue) ///
        mlabel(country_label) mlabcolor(black) mlabsize(medlarge) ///
        mlabposition(e)) ///
    , ///
    xtitle("Predicted Growth") ///
    ytitle("Actual Growth") ///
    legend(off) ///
    graphregion(color("242 242 242")) ///
    plotregion(color(white))
	
restore

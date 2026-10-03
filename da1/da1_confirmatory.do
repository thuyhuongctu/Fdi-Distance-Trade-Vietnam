* =============================================================================
* DA1 – Distance and FDI into Vietnam: confirmatory and robustness analyses
* © 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.
*
* Follows Part 5 of the OSF secondary-data preregistration for DA1 exactly.
* Run ONLY after the preregistration has been submitted.
* Requires: ppmlhdfe, reghdfe, ftools  (ssc install ppmlhdfe; ssc install reghdfe; ssc install ftools)
* Input:    da1_panel.csv produced by build_panel.py
* =============================================================================
version 17
clear all
set more off
capture log close
log using "da1_results.log", replace text

import delimited "da1_panel.csv", clear varnames(1) encoding(utf-8)
encode iso3, gen(cid)

* Main sample (column `main` from build_panel.py, preregistered rule 2): exclude the
* FSF offshore financial centres listed by the IMF (2000), except Singapore and Hong Kong
assert main == ((ofc == 0) | inlist(iso3, "SGP", "HKG"))

* ---------------------------------------------------------------------------
* Model 1 – tests H1, H2a, H2b (PPML, year FE, SE clustered by source economy)
* ---------------------------------------------------------------------------
ppmlhdfe fdi_usd_m ln_dist cult_dist inst_dist econ_dist ln_gdp fta if main, ///
    absorb(year) vce(cluster cid) d
estimates store M1

* ---------------------------------------------------------------------------
* Model 2 – tests H3: (a) year FE; (b) source-economy and year FE
* ---------------------------------------------------------------------------
ppmlhdfe fdi_usd_m ln_dist cult_dist inst_dist_c econ_dist ln_gdp fta fta_x_inst if main, ///
    absorb(year) vce(cluster cid)
estimates store M2a
ppmlhdfe fdi_usd_m inst_dist_c econ_dist ln_gdp fta fta_x_inst if main, ///
    absorb(cid year) vce(cluster cid)
estimates store M2b

* ---------------------------------------------------------------------------
* Confirmatory tests with Holm correction (4 tests: H1, H2a, H2b, H3)
* H3 counts as supported only if it passes in BOTH M2a and M2b; the larger
* of the two p-values enters the Holm procedure.
* ---------------------------------------------------------------------------
tempname P
matrix `P' = J(4, 3, .)
estimates restore M1
foreach k in 1 2 3 {
    local v : word `k' of ln_dist cult_dist inst_dist
    matrix `P'[`k', 1] = _b[`v']
    matrix `P'[`k', 2] = 2 * normal(-abs(_b[`v'] / _se[`v']))
}
estimates restore M2a
local p2a = 2 * normal(-abs(_b[fta_x_inst] / _se[fta_x_inst]))
local b2a = _b[fta_x_inst]
estimates restore M2b
local p2b = 2 * normal(-abs(_b[fta_x_inst] / _se[fta_x_inst]))
local b2b = _b[fta_x_inst]
matrix `P'[4, 1] = min(`b2a', `b2b') * (sign(`b2a') == sign(`b2b'))
matrix `P'[4, 2] = max(`p2a', `p2b')

* Holm step-down
preserve
clear
svmat `P', names(c)
rename (c1 c2) (beta p)
gen hyp = _n
label define hyp 1 "H1 geo (<0)" 2 "H2a cult (<0)" 3 "H2b inst (<0)" 4 "H3 FTAxinst (>0)"
label values hyp hyp
gen expected = cond(hyp == 4, 1, -1)
sort p
gen rank = _n
gen p_holm = min(1, p * (4 - rank + 1))
replace p_holm = max(p_holm, p_holm[_n-1]) if _n > 1
gen supported = (sign(beta) == expected) & (p_holm < 0.05)
sort hyp
list hyp beta p p_holm supported, noobs sep(0)
restore

* ---------------------------------------------------------------------------
* Effect sizes: % change in expected FDI for +1 SD of each distance, and FTA = 1
* ---------------------------------------------------------------------------
estimates restore M1
foreach v in ln_dist cult_dist inst_dist econ_dist {
    quietly summarize `v' if e(sample)
    display "`v': +1 SD -> " %6.1f 100 * (exp(_b[`v'] * r(sd)) - 1) "%"
}
display "fta: 0 -> 1   -> " %6.1f 100 * (exp(_b[fta]) - 1) "%"

* ---------------------------------------------------------------------------
* Robustness checks (preregistered list)
* ---------------------------------------------------------------------------
* R1  Outcome = IMF CDIS positions (2009–2024)
ppmlhdfe position_usd_m ln_dist cult_dist inst_dist econ_dist ln_gdp fta if main & year >= 2009, absorb(year) vce(cluster cid)
estimates store R1
* R2a Include offshore financial centres
ppmlhdfe fdi_usd_m ln_dist cult_dist inst_dist econ_dist ln_gdp fta, absorb(year) vce(cluster cid)
estimates store R2a
* R2b Exclude Singapore and Hong Kong as well (possible conduit investors)
ppmlhdfe fdi_usd_m ln_dist cult_dist inst_dist econ_dist ln_gdp fta if main & !inlist(iso3, "SGP", "HKG"), absorb(year) vce(cluster cid)
estimates store R2b
* R3  Kogut–Singh indices instead of Mahalanobis
ppmlhdfe fdi_usd_m ln_dist cult_dist_ks inst_dist_ks econ_dist ln_gdp fta if main, absorb(year) vce(cluster cid)
estimates store R3
* R4  Time-varying regressors lagged one year
xtset cid year
ppmlhdfe fdi_usd_m ln_dist cult_dist L.inst_dist L.econ_dist L.ln_gdp L.fta if main, absorb(year) vce(cluster cid)
estimates store R4
* R5  Bridge to Phan & Đỗ (2019): 16 countries, 2006–2015
*     (a) original random-effects log-linear form on positive flows; (b) PPML
gen ln_fdi = ln(fdi_usd_m) if fdi_usd_m > 0
xtreg ln_fdi ln_dist cult_dist inst_dist econ_dist ln_gdp fta if in_2019_sample & year <= 2015, re vce(robust)
estimates store R5a
ppmlhdfe fdi_usd_m ln_dist cult_dist inst_dist econ_dist ln_gdp fta if in_2019_sample & year <= 2015, absorb(year) vce(cluster cid)
estimates store R5b
* R6  Hausman–Taylor on positive flows (time-invariant distances treated as exogenous)
xthtaylor ln_fdi ln_dist cult_dist inst_dist econ_dist ln_gdp fta if main, endog(inst_dist econ_dist ln_gdp)
estimates store R6

estimates table M1 M2a M2b R1 R2a R2b R3 R4 R5a R5b R6, b(%9.3f) se(%9.3f) stats(N) varwidth(14)

log close

# DA1 – Disclosures and open decisions for the OSF preregistration

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương. Licence: CC BY 4.0.

*Mục đích (tiếng Việt):* Tệp này ghi lại trung thực những gì đã làm và đã thấy trên dữ liệu DA1 trước khi nộp tiền đăng ký, và các quyết định còn chờ thầy duyệt. Phần 1–3 viết sẵn bằng tiếng Anh để dán vào mẫu tiền đăng ký dữ liệu thứ cấp của OSF (mục "Prior knowledge of the data" và "Data collection"). Phần 4 cần chốt trước khi nộp.

## 1. Deviation from the original plan

The OSF wiki stated that DA1 would be preregistered **before** the extended dataset was assembled. This did not happen. All inputs were collected and the panel was built between 3 and 5 October 2026, before submission. The steps below were taken; no model in `da1_confirmatory.do` has been estimated, and no association between FDI and any distance measure, FTA status or GDP has been computed, tabulated or plotted.

| Date (UTC) | Step | Commit |
| --- | --- | --- |
| 2026-10-03 | Covariates downloaded: WGI 2026, CEPII GeoDist, WTO RTA, IMF OFC list, IMF WEO GDP for Taiwan (`fetch_inputs.py`) | 4e7ec59 |
| 2026-10-04 | Covariate-only panel built (FDI column empty) | 02b17bc |
| 2026-10-05 | IMF DIP (CDIS) positions downloaded | ee85dfc |
| 2026-10-05 | Registered FDI by partner extracted from GSO Statistical Yearbooks 2006–2025 | 22b305e |
| 2026-10-05 | Full panel built with `build_panel.py`; panel file not committed | f0dc69d |

## 2. What the authors have seen in the data (prior knowledge)

Only univariate and coverage statistics, all reported here:

- **Registered FDI table.** For each year 2006–2025, the listed partners cover 98.7–100.0% of the printed total (checked by `build_fdi_registered.py`). Two source errors were found and logged (`inputs/gso/README.md`).
- **Panel size.** 106 source economies × 19 years = 2,014 observations. The main sample (OFCs excluded except Singapore and Hong Kong) has 84 economies and 1,596 observations.
- **Zero flows.** 55.5% of all observations and 55.6% of main-sample observations have FDI = 0.
- **Complete cases.** 47 main-sample economies (893 observations) have all five regressors. Among these, 38.1% of observations are zeros.
- **Missing regressors (main sample, economies with no value in any year).** Cultural distance 37, geographic distance 3, institutional distance 2, economic distance 2, GDP 2.
- **CDIS.** 954 partner-year positions for 79 counterparts, 2009–2024. 153 are confidential and 19 are negative.
- **Bridge sample.** All 16 economies of Phan & Đỗ (2019) have complete regressors for 2006–2024, including Taiwan.

The authors also know the results of Phan & Đỗ (2019), which used an overlapping sample (16 economies, 2006–2015).

## 3. Data sources and coding decisions already taken

| Variable | Source and coding | Documentation |
| --- | --- | --- |
| Registered FDI (primary outcome) | GSO Statistical Yearbooks, table "FDI projects licensed in year Y by main counterpart", total registered capital, USD million. Economies not listed in a year are coded 0 (omitted partners hold ≤ 1.3% of the yearly total). | `inputs/gso/README.md` |
| — definition break | To 2015: new + supplementary capital. From 2016: also capital contributions and share purchases. Recorded per row in `capital_definition`. | same |
| CDIS (R1) | IMF DIP, inward positions derived from counterpart reports (Viet Nam does not report). Confidential cells are missing. | `inputs/sources_c.md` |
| Geographic distance | CEPII GeoDist `distw` (population-weighted), km. | `inputs/sources_c.md` |
| Cultural distance | Mahalanobis distance on Hofstede's six dimensions (time-invariant). | `build_panel.py` |
| Institutional distance | Mahalanobis distance on the six WGI estimates, by year (WGI 2026 release). | same |
| Economic distance | \|ln GDP per capita_j − ln GDP per capita_VN\|, WDI; Taiwan from IMF WEO April 2026 (second source for one economy). | `inputs/sources_c.md` |
| FTA | WTO RTA database; goods agreements with Viet Nam as a party; first year in force per partner. RCEP is not in the database and does not change any first-in-force year. | same |
| Main sample | IMF (2000) FSF list of OFCs excluded, except Singapore and Hong Kong (design decision of 3 Oct 2026). R2a includes all OFCs; R2b also excludes Singapore and Hong Kong. | same |

## 4. Decisions to settle before submission (cần thầy duyệt)

1. **Missing Hofstede scores (37 main-sample economies).** Listwise deletion removes mostly small investors and lowers the share of zeros from 55.6% to 38.1%. Options:
   - (a) keep listwise deletion as the main analysis and declare it;
   - (b) add a robustness check that drops cultural distance and uses the full sample;
   - (c) impute from regional Hofstede scores (not recommended: the source's regional rows are not countries).
   *Proposal: (a) + (b), with (b) added as R7.*
2. **Negative CDIS positions (19 cells) in R1.** PPML requires y ≥ 0. *Proposal: set negatives to missing in R1 and report how many were dropped; state this in the plan.*
3. **2016 definition break in registered capital.** Year fixed effects absorb a common level shift but not partner-specific changes in M&A share. *Proposal: add R8, estimating 2006–2015 and 2016–2024 separately and reporting both; no change to the confirmatory model.*
4. **Codes without ISO equivalents.** XBWI (British West Indies), XCHI (Channel Islands) and VIR (US Virgin Islands) have no covariates and drop out automatically; their FDI stays in the national total. *Proposal: declare.*
5. **Taiwan GDP from IMF WEO.** *Proposal: declare as a second source for one economy; keep in the main sample.*
6. **Statement on prior knowledge.** *Proposal: paste sections 1–2 of this file into the preregistration unchanged.*

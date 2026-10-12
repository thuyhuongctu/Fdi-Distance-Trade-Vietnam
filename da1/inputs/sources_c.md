# Sources for wgi.csv, cepii_dist.csv, fta.csv, ofc_list.csv, wdi_supplement.csv (fetched 2026-10-03)

All files are produced by `../fetch_inputs.py`. The script downloads directly from each provider into `raw/`, which is not committed. No value was invented, estimated or interpolated. Missing values are left blank.

## wgi.csv — 216 economies, 2005–2024, 4,263 rows
- Source: World Bank, Worldwide Governance Indicators, 2026 release, `wgidataset_with_sourcedata-2026.dta`, https://www.worldbank.org/content/dam/sites/govindicators/doc/wgidataset_with_sourcedata-2026.dta. Variable: `estimate` for the six dimensions va, pv, ge, rq, rl, cc.
- Check against the WDI API (source 3, last updated 2026-09-25). All 4,104 economy-years present in both sources are identical (maximum difference 4e-16).
- The bulk file covers 9 economies that the API leaves without an ISO3 code: AIA, ANT, COK, GUF, JEY, MTQ, NIU, REU, TWN. This brings Taiwan into the panel.
- Licence: CC BY 4.0 (World Bank).

## cepii_dist.csv — 224 origin economies (distance to Viet Nam)
- Source: CEPII GeoDist, `dist_cepii.zip` → `dist_cepii.xls`, https://www.cepii.fr/distance/dist_cepii.zip. Rows with iso_d = VNM. Citation: Mayer, T. & Zignago, S. (2011), CEPII Working Paper 2011-25.
- Columns kept: distw (population-weighted distance, km), dist (great-circle distance between the main cities, km), contig, comlang_off, colony.
- CEPII legacy codes were recoded to current ISO3:
  - ROM → ROU, ZAR → COD, TMP → TLS, PAL → PSE.
  - YUG is assigned to both SRB and MNE with the same value. `cepii_code` keeps the original code.
- distw is "." (missing) in the source for CCK, CXR, MAC, MSR and PCN. It is left blank.
  - Macao therefore has no `ln_dist` in the main specification.
  - `dist_km` is available for Macao and could be used only in a robustness check that is declared in the preregistration.
- The repository holds only this extract of 224 rows. For the full database, cite and download from CEPII.

## fta.csv — 74 agreement–partner rows, 54 partners
- Source: WTO Regional Trade Agreements Database, "Export all RTAs" (`AllRTAs.xlsx`, 662 RTAs), https://rtais.wto.org/UI/ExportAllRTAList.aspx.
- **Inclusion rule.** An agreement is included when Viet Nam is a party, directly or through ASEAN, and the agreement covers goods (type FTA, or FTA & EIA).
  - Excluded: the GSTP, which is a partial-scope agreement (PSA), and ATISA, which covers services only.
- **Date.** The date is the WTO goods entry-into-force date (G), except where the WTO Remarks give party-specific dates.
  - For CPTPP, the date for a pair is the later of Viet Nam's date (14 Jan 2019) and the partner's date.
  - For the United Kingdom, the date is EVFTA during the Brexit transition (from 1 Aug 2020), then UKVFTA (from 1 Jan 2021).
- **Partners through blocs:**
  - EU – Viet Nam is expanded to the EU-27.
  - EAEU – Viet Nam is expanded to ARM, BLR, KAZ, KGZ and RUS.
  - ASEAN+1 agreements are mapped to their partner: CHN, JPN, KOR, AUS/NZL, IND, HKG.
- **RCEP is not in the WTO database**, because it has not been notified to the WTO. It is therefore not listed. Every RCEP partner already had an earlier agreement with Viet Nam, so leaving RCEP out does not change any first-in-force year.
- `build_panel.py` uses the earliest `in_force_year` per partner. The FTA dummy equals 1 from the year of entry into force onwards.
- Taiwan and the United States have no agreement with Viet Nam.

## ofc_list.csv — 42 rows
- Source: IMF (2000), "Offshore Financial Centers – IMF Background Paper", 23 June 2000, Table 2 ("Basic Facts on OFCs Considered by the Financial Stability Forum"): https://www.imf.org/external/np/mae/oshore/2000/eng/back.htm. The script checks that each name appears in Table 2.
- The FSF list has 42 entries in Groups I–III. Two of them are sub-national and are not mapped to their country:
  - Dublin (Ireland);
  - Labuan (Malaysia).
- The Netherlands Antilles (ANT) are kept. Their successors since 2010, CUW and SXM, are added and marked in `note`.
- **Main-sample rule (design decision, 3 Oct 2026):** all listed OFCs are excluded from the main sample except Singapore and Hong Kong. Both are Group I centres with substantial real economic activity and complete covariates, and they are among the largest investors in Viet Nam. `build_panel.py` writes this as the column `main`. Robustness check R2a includes all OFCs; R2b also excludes Singapore and Hong Kong.
- Table 1 of the same paper, the broader Errico–Musalem list, also names facilities in Japan, the United States, Thailand and the Philippines. It is not used.

## wdi_supplement.csv — Taiwan, 2005–2024
- WDI does not cover Taiwan. GDP (NGDPD, billions of current USD × 1e9) and GDP per capita (NGDPDPC, current USD) come from the IMF World Economic Outlook DataMapper:
  - https://www.imf.org/external/datamapper/api/v1/NGDPD/TWN
  - https://www.imf.org/external/datamapper/api/v1/NGDPDPC/TWN
- WEO and WDI levels differ slightly. For Viet Nam in 2024, GDP is 459.4 bn USD in WEO and 476.3 bn USD in WDI. Only Taiwan is taken from WEO, and every other economy, including Viet Nam, stays on WDI.

## Coverage check (covariates only; FDI not yet collected)
- Economies with all of ln_dist, cult_dist, inst_dist, econ_dist and ln_gdp for all of 2006–2024: 61. Of these, 58 are in the main sample; CHE, LUX and MLT drop out as OFCs.
- Hofstede is the binding constraint. Without the cultural-distance requirement, 186 economies are complete.
- All 16 economies of the Phan & Do (2019) sample are complete, including Taiwan.

## imf_cdis.csv (iso3, year, position_usd_m, confidential) — added 2026-10-05
- IMF Direct Investment Positions by Counterpart Economy (DIP, formerly CDIS), dataflow `IMF.STA:DIP(12.0.1)`, release 2025-12-10:
  `https://api.imf.org/external/sdmx/2.1/data/IMF.STA,DIP,12.0.1/VNM.SCC.INWD_D_NETLA_FALL_ALL..A?startPeriod=2009`.
- Viet Nam does not report to the survey: the same query with `DV_TYPE = O` (reported official data) returns no series. All values are **derived from counterpart economies' outward positions** (`DV_TYPE = SCC`), as the preregistration allows.
- Indicator: inward direct investment, net (liabilities less assets), all instruments, all entities; end-year positions 2009–2024. `OBS_VALUE` is in US dollars (the `SCALE="6"` attribute is a display hint); converted to USD million.
- World and regional aggregates dropped. 954 rows, 79 counterparts. 153 cells are confidential (`STATUS = C`, no value; `confidential = 1`). 19 values are negative (net disinvestment); PPML needs y ≥ 0, so robustness check R1 must state how negatives are treated before it is run.
- Singapore and Taiwan do not publish bilateral outward positions, so they have no CDIS rows.

## fdi_registered.csv — added 2026-10-05
- GSO Statistical Yearbooks 2006–2025, table of FDI projects licensed in the year by main counterpart. Method, checks and source issues: `gso/README.md`.

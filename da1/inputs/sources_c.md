# Sources for wgi.csv, cepii_dist.csv, ofc_list.csv, fta.csv, wdi_supplement.csv (fetched 2026-10-04)

Network access to the data sites was opened for this environment on 2026-10-04. All files were downloaded directly with `curl`. Raw downloads are kept locally in `raw/` (not committed; rebuildable from the URLs below). SHA-256 checksums are listed so a re-download can be checked. No values were invented, estimated or interpolated; missing values are blank.

## wgi.csv (iso3, year, va, pv, ge, rq, rl, cc) — FILLED, replaces wgi_va_partial.csv
- World Bank API, source 3 (Worldwide Governance Indicators), lastupdated 2026-09-25, 2005–2024, estimate series `GOV_WGI_{VA,PV,GE,RQ,RL,CC}.EST`:
  `https://api.worldbank.org/v2/country/all/indicator/GOV_WGI_PV.EST?source=3&date=2005:2024&format=json&per_page=20000` (same pattern for each code).
- 216 entities × 20 years = 4,320 rows; 525 blank cells out of 25,920.
- Nine entities have no ISO3 code in the API response. They are mapped by name (the earlier file dropped them): Anguilla→AIA, Cook Islands→COK, French Guiana→GUF, Jersey→JEY, Martinique→MTQ, Netherlands Antilles→ANT, Niue→NIU, Reunion→REU, **Taiwan, China→TWN**. Taiwan is a main investor and is in the 2019 sample, so dropping it would remove it from the institutional-distance models.
- Checksums: VA 54d61268…, PV 0fe8ffb0…, GE be57fdfd…, RQ c7aae7fc…, RL 63b6443f…, CC 892637ac….

## cepii_dist.csv (iso3, distw_km, dist_km, contig, comlang_off, colony) — FILLED
- CEPII GeoDist, `dist_cepii.xls` in https://www.cepii.fr/distance/dist_cepii.zip (SHA-256 1854825b…). Mayer & Zignago (2011).
- Rows with `iso_d == VNM`, 223 origin economies. `distw_km` = population-weighted distance (`distw`), `dist_km` = distance between main cities.
- CEPII codes recoded to ISO3: ROM→ROU, ZAR→COD, TMP→TLS, PAL→PSE. `YUG` is left as is (no single successor).
- `distw` is blank for CCK, CXR, MAC, MSR, PCN. `contig = 1` for CHN, KHM, LAO.

## ofc_list.csv (iso3, entry, basis) — FILLED, coding rule needs supervisor approval
- IMF (2000), *Offshore Financial Centers – IMF Background Paper*, Table 1: https://www.imf.org/external/np/mae/oshore/2000/eng/back.htm (SHA-256 1e016d83…). All 64 entries are copied in `raw/imf_ofc_table1.csv` with the decision for each.
- Rule (script `build_ofc_list.py`): flag whole jurisdictions; do not flag entries that are a city, region or banking facility inside an onshore economy (Dublin, London, Labuan, Madeira, Campione, Tangier; Japan JOM, Singapore ACU, Thailand BIBF, US IBF). Hong Kong and Singapore stay in the main sample because preregistered robustness check R2b removes them separately. CUW and SXM are added as successors of the Netherlands Antilles.
- Result: 54 codes. **Note:** the Netherlands (NLD), Switzerland, Luxembourg, Cyprus, Malta, Philippines, Israel, Costa Rica, Panama and Uruguay are flagged because Table 1 lists them as whole economies. The Netherlands is in the 16-country 2019 sample. If the supervisor prefers a narrower list (for example, only small-island and FSF jurisdictions), change the table in `build_ofc_list.py` and rerun before submitting the DA1 preregistration.

## fta.csv (iso3, fta_name, rta_id, in_force_date, in_force_year, type) — FILLED
- WTO RTA database, export of all RTAs: https://rtais.wto.org/UI/ExportAllRTAList.aspx (SHA-256 c42505d5…), script `build_fta.py`.
- Kept: goods agreements of type FTA, FTA & EIA or CU with Viet Nam as a party. Dropped: GSTP (partial-scope, PSA), ATISA (services only), ATIGA (same partners as AFTA/CEPT), EFTA – Viet Nam (under negotiation).
- Pair date = the later of Viet Nam's and the partner's entry into force (party-specific dates where the database gives them; otherwise the goods date).
- 66 rows, 54 partners. AFTA (CEPT) is coded from the WTO record (1993); Viet Nam actually joined in 1996, which does not affect the 2006–2024 sample.
- RCEP is **not** in the WTO export. All RCEP partners already have an ASEAN+1 or bilateral FTA with Viet Nam in force before RCEP (2022), so the FTA dummy is unaffected.

## wdi_supplement.csv — Taiwan GDP (WDI has no Taiwan)
- IMF World Economic Outlook, April 2026, DataMapper API: `https://www.imf.org/external/datamapper/api/v1/NGDPD/TWN` and `/NGDPDPC/TWN` (USD bn and USD per capita, current prices). 2005–2024.
- `build_panel.py` adds these rows only for economies absent from `wdi.csv`. This is a second source for one economy; it should be declared in the preregistration (Section 2).

## imf_cdis.csv (iso3, year, position_usd_m, confidential) — FILLED from counterpart data
- IMF Direct Investment Positions by Counterpart Economy (DIP, formerly CDIS), dataflow `IMF.STA:DIP(12.0.1)`, release 2025-12-10:
  `https://api.imf.org/external/sdmx/2.1/data/IMF.STA,DIP,12.0.1/VNM.SCC.INWD_D_NETLA_FALL_ALL..A?startPeriod=2009` (SHA-256 13413030…).
- Viet Nam does not report to the survey: the same query with `DV_TYPE = O` (reported official data) returns no series. All values are **derived from counterpart economies' outward positions** (`DV_TYPE = SCC`), as the preregistration allows.
- Indicator: inward direct investment, net (liabilities less assets), all instruments, all entities; end-year positions 2009–2024.
- `OBS_VALUE` is in US dollars (the `SCALE="6"` attribute is a display hint: Japan 2024 = 28,671,060,923 USD); converted to USD million.
- World and regional aggregates (G001, GX…, U…) dropped. 954 rows, 79 counterparts. 153 cells are confidential (`STATUS = C`, no value; `confidential = 1`). 19 values are negative (net disinvestment); PPML needs y ≥ 0, so robustness check R1 must state how negatives are treated before it is run.
- Singapore and Taiwan do not publish bilateral outward positions, so they have no CDIS rows.

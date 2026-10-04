# Sources for covariate inputs (collected 2026-10-02)

Direct `curl` to api.worldbank.org and www.cepii.fr was refused by the session egress proxy (HTTP 403 on CONNECT, organization policy). Data were fetched through the Firecrawl scrape tool (`formats: ["rawHtml"]`, HTTP 200, `application/json`). Raw API responses are saved in `raw/`. No values were invented, estimated or interpolated. Missing values are left blank.

## wdi.csv (iso3, year, gdp_usd, gdppc_usd)
- gdp_usd = NY.GDP.MKTP.CD (GDP, current US$): https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.CD?date=2005:2024&format=json&per_page=20000 (WDI source 2, lastupdated 2026-07-13, 5300 records)
- gdppc_usd = NY.GDP.PCAP.CD (GDP per capita, current US$): https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.CD?date=2005:2024&format=json&per_page=20000 (lastupdated 2026-07-13, 5300 records)
- Aggregate filter uses country metadata from https://api.worldbank.org/v2/country?format=json&per_page=1000 (295 entries). The 78 entries with region.id == "NA" are aggregates and were dropped. 217 economies were kept.
- Coverage: 217 economies x 2005-2024 = 4340 rows. 134 blank gdp_usd and 134 blank gdppc_usd. VNM is included.

## wgi.csv: NOT PRODUCED (incomplete) — superseded 2026-10-04, see sources_c.md
- Only GOV_WGI_VA.EST was retrieved: https://api.worldbank.org/v2/country/all/indicator/GOV_WGI_VA.EST?source=3&date=2005:2024&format=json&per_page=20000 (source 3, lastupdated 2026-09-25, 4320 records, years 2005-2024)
- That series is saved as `wgi_va_partial.csv` (iso3, year, va): 207 economies x 2005-2024 = 4140 rows, 52 blank.
- 9 WGI entities have no ISO3 code in the API response, so they were excluded rather than assigned a code by hand: Anguilla, Cook Islands, French Guiana, Jersey, Martinique, Netherlands Antilles, Niue, Reunion, Taiwan, China.
- GOV_WGI_PV.EST, GOV_WGI_GE.EST, GOV_WGI_RQ.EST, GOV_WGI_RL.EST and GOV_WGI_CC.EST failed: Firecrawl returned "Insufficient credits", and direct curl is blocked by the proxy. To complete the file, use the same URL pattern with each code, e.g. https://api.worldbank.org/v2/country/all/indicator/GOV_WGI_PV.EST?source=3&date=2005:2024&format=json&per_page=20000

## cepii_dist.csv: NOT PRODUCED — superseded 2026-10-04, see sources_c.md
- CEPII GeoDist (dist_cepii, distw and contig): https://www.cepii.fr/distance/dist_cepii.zip and the landing page https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=6
- Direct curl to www.cepii.fr was denied by the proxy (403). Firecrawl cannot open zip files, and its credits were exhausted. Distances were NOT computed from any other source.

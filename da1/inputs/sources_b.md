# Sources for hofstede.csv, fta.csv, ofc_list.csv (fetched 2026-10-02)

## hofstede.csv — FILLED (111 rows)
- Landing page (fetched with Firecrawl, links format): https://geerthofstede.com/research-and-vsm/dimension-data-matrix/
- Data file (fetched with Firecrawl, parsed as a table): https://geerthofstede.com/wp-content/uploads/2016/08/6-dimensions-for-website-2015-08-16.xls
  - The .csv twin (same name, .csv) was blocked by Firecrawl anti-bot. Direct curl to geerthofstede.com got a 403 from the proxy.
- All 111 rows of the file are kept in file order. `#NULL!` becomes blank. The source column `ltowvs` is renamed `lto`. The values are the raw scores, not the 0–100 rescaled 2015-12-08 version.
- `country` is the source's own label. Hofstede's 3-letter `ctr` codes are NOT ISO3 (for example, VIE, GER, AUL). I mapped ISO3 by hand from the country name.
  - Name choices: Bosnia→BIH, Macedonia Rep→MKD, Great Britain→GBR, Korea South→KOR, Hong Kong→HKG, Taiwan→TWN, Puerto Rico→PRI.
- 10 rows have a blank iso3 because they are regional, sub-national or ethnic groups:
  - Africa East (AFE), Africa West (AFW), Arab countries (ARA)
  - Belgium French (BEF), Belgium Netherl (BEN), Canada French (CAF), Germany East (GEE)
  - South Africa white (SAW), Switzerland French (SWF), Switzerland German (SWG)
- Vietnam (VIE→VNM): pdi 70, idv 20, mas 40, uai 30, lto 57, ivr 35.

## fta.csv — NOT FILLED (header only)
Tried and failed:
- curl and WebFetch to rtais.wto.org, data.wto.org, www.wto.org and trungtamwto.vn: egress proxy blocked (CONNECT 403 / EGRESS_BLOCKED).
- Firecrawl scrape and search: HTTP 402, out of credits, after the Hofstede fetches.
- Google-translate proxy, web.archive.org and government FTA sites (DFAT, MFAT, gov.uk, EC, ASEAN, RCEP Secretariat, MOIT): all blocked.
- WebSearch (allowed_domains=rtais.wto.org) returns only model-written summaries, not page text. These summaries were self-contradictory. For example, one gave "Israel – Viet Nam entry into force 1 Sep 2026" and gave the CPTPP UK-accession date (15 Dec 2024) as if it applied to all CPTPP members. I did not use them as data.
Leads to fetch when access is available (RTA ID cards):
- EU – Viet Nam: https://rtais.wto.org/UI/PublicShowRTAIDCard.aspx?rtaid=872
- CPTPP – Accession of the United Kingdom: https://rtais.wto.org/UI/PublicShowRTAIDCard.aspx?rtaid=1218
- Member cards: https://rtais.wto.org/UI/PublicShowMemberRTAIDCard.aspx?rtaid=973, ...?rtaid=170, ...?rtaid=840
- Whole-database export: https://rtais.wto.org/UI/PublicMaintainRTAHome.aspx → "Export all RTAs", or https://data.wto.org/en/dataset/ext_rta (xlsx/csv)

## ofc_list.csv — NOT FILLED (header only)
- Target document: IMF, "Offshore Financial Centers – IMF Background Paper", 23 June 2000, https://www.imf.org/external/np/mae/oshore/2000/eng/back.htm (Table 1 by region; Table 2 FSF list).
- Alternative: IMF OFC Assessment Program information note, https://www.imf.org/external/np/mae/oshore/2002/eng/082902.htm
- imf.org, elibrary.imf.org and the translate.goog mirror were all blocked by the egress proxy. Firecrawl was out of credits.
- A WebSearch summary of back.htm listed the members of some regions, but it left out the Middle East region and was clearly incomplete (for example, no Hong Kong). It is not verbatim, so it was not used.

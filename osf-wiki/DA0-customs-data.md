# DA0 · Customs FDI-Sector Trade Data

> *Tóm tắt:* Bộ dữ liệu xuất khẩu và nhập khẩu theo tháng của khu vực doanh nghiệp FDI, theo nhóm hàng, 01/2013–08/2026, đã chuẩn hóa và có xuất xứ rõ ràng. Đây là nền dữ liệu chung cho DA2 và DA3.

**Part of:** [Distance, FDI and the Trade of Foreign-Invested Firms in Vietnam](../) · **Status:** Series processed (323 monthly tables, 01/2013–08/2026); codebook and tests public; licence pending · **Planned output:** data paper (*Data in Brief*)

## Purpose

DA0 builds a harmonised, documented panel of Vietnam's FDI-sector trade for reuse in DA2, DA3 and by other researchers. Each value carries four provenance fields: source, period, method and limitation.

## Source

- Vietnam Customs (Cục Hải quan, Ministry of Finance), Tables 017.T (exports) and 018.T (imports): *goods traded by foreign-invested enterprises*, monthly, by product group (about 36 export and 33 import groups), value in USD and quantity where reported.
- The consolidated 2013–2026 series was purchased from a commercial provider. The monthly tables themselves are published by Customs.

## Processing steps

1. Raw files are archived unchanged, with a checksum (hash) for each file.
2. Product-group names are harmonised across 2013–2026 in a written concordance: added, merged and renamed groups.
3. Consistency checks: the sum of groups is compared with the reported total, and each monthly value with the difference in year-to-date figures.
4. Preliminary (*sơ bộ*) figures are flagged and replaced with official figures where available.
5. Source-table errors are logged (e.g. Table 018.T, August 2026, lists two items numbered 18).
6. Output: a long panel (month × product group × direction) with a codebook and version notes.

## Files in this component

| Folder | Content | Access |
| --- | --- | --- |
| `/raw` | Purchased files, unchanged | **Private** (licence) |
| `/concordance` | Product-group harmonisation; HS–product-group mapping | Public |
| `/codebook` | Variable definitions, units, provenance fields (`CODEBOOK.md`) | Public |
| `/cleaning-log` | Checks run, issues found, decisions made | Public |
| `/code` | Cleaning scripts | Public (MIT) |
| `/derived` | Aggregated series permitted by the licence | Public once licence confirmed |

## Data licence

Redistribution terms of the purchased series are being confirmed with the provider. Until then, raw data stay private. The cleaning code and concordance allow anyone to rebuild the series from the monthly tables Customs publishes.

## Used by

[DA2](../DA2) · [DA3](../DA3) · Teaching tool *FDI Factory* (benchmark figures only)

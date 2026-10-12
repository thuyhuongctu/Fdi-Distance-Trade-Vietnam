# DA0 Codebook – Customs FDI-sector trade panel, 01/2013–08/2026

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương. Licence: CC BY 4.0 (this document).

This codebook describes the two output tables of the DA0 pipeline. The tables themselves are built from purchased data and are **not** distributed until the redistribution licence is confirmed. The code, this codebook, `harmonise_map.csv` and `concordance_draft.csv` are public. Anyone can rebuild the tables from the monthly tables that Customs publishes.

## 1. Source

| Item | Description |
| --- | --- |
| Publisher | Vietnam Customs (Cục Hải quan, Ministry of Finance) |
| Tables | 017.T (exports) and 018.T (imports): goods traded by foreign-invested enterprises, monthly |
| Coverage | 01/2013–08/2026; 323 monthly PDF files (preliminary *SB* and official *CT* versions) |
| Unit of observation | product group × month × direction |
| Not covered | partner country, province, individual firm |

## 2. Pipeline

```
raw/*.txt  →  parse_flat.py  →  panel_flat.csv  →  build_monthly.py  →  monthly_clean.csv
                                                                     →  harmonise.py  →  monthly_harmonised.csv
```

All checks are written to the cleaning logs (`cleaning_log_flat.csv`, `cleaning_log_monthly.csv`). The pipeline does not correct values without a record. `test_da0.py` runs the full pipeline on simulated tables and checks each rule. It does not use purchased data.

## 3. `monthly_clean.csv` – one row per printed line of a table

| Variable | Type | Description |
| --- | --- | --- |
| `period` | YYYY-MM | Reporting month as printed in the table (not the file name). Provenance field 1/4 |
| `year`, `month` | int | Split from `period` |
| `direction` | `export` / `import` | 017.T = export, 018.T = import |
| `status` | `preliminary` / `official` | *Sơ bộ* (SB) or official (CT) release |
| `item_no` | text | Item number printed in the table; `TOTAL` for the total row; empty for sub-items and 2026 memo rows |
| `level` | `total` / `group` / `subitem` | Hierarchy level. Only `group` rows add up to `total` |
| `parent` | text | Group a sub-item belongs to (empty for groups and the total) |
| `product_group` | text | Name as printed (NFC Unicode). Not harmonised |
| `unit` | `USD`, `Tấn`, `Chiếc` | Quantity unit of the row. Values are always USD |
| `qty_month`, `qty_ytd` | number | Quantity in `unit`, month and year-to-date. Empty for USD-only rows |
| `value_usd_month` | integer, USD | Value for the month as printed |
| `value_usd_ytd` | integer, USD | Year-to-date value as printed |
| `value_usd_month_ytddiff` | number, USD | YTD(m) − YTD(m−1); equals `value_usd_ytd` in January. Absorbs Customs' revisions of earlier months. **Recommended monthly value for time-series work** |
| `imputed_from_ytd` | 0/1 | 1 = no table for this month; values derived as YTD(m+1) − month(m+1) − YTD(m−1) |
| `source` | text | Provenance (2/4): publisher and table |
| `method` | text | Provenance (3/4): how the figure was compiled and extracted |
| `limitation` | text | Provenance (4/4): preliminary/official status, sector scope, product list of the period; notes imputation |
| `source_title` | text | Drive file name of the source PDF |
| `drive_file_id`, `drive_modified` | text | Drive identifier and modification time of the source file |
| `text_sha256_16` | text | First 16 hex characters of the SHA-256 of the extracted text |

## 4. `monthly_harmonised.csv` – consistent product basket, 2013–2026

| Variable | Description |
| --- | --- |
| `direction`, `period`, `year`, `month`, `status` | As above |
| `group_h` | Harmonised product group: 30 export and 29 import groups, present in every month |
| `value_usd_month`, `value_usd_ytd`, `value_usd_month_ytddiff` | Sum over the original groups mapped to `group_h` |
| `imputed_from_ytd` | 1 if any component was imputed |

Harmonisation rules (each mapping is listed in `harmonise_map.csv`):

| Rule | Content |
| --- | --- |
| R1 | Pure renaming → one standard name |
| R2 | Groups Customs added from 2024 (6 export, 5 import) → added to *Hàng hóa khác* (other goods). The detailed series in `monthly_clean.csv` keeps them |
| R3 | New table layout from 03/2026: unnumbered memo rows are not added. The memo row *Sản phẩm từ kim loại thường khác* is added to *Kim loại thường khác* (→ *Kim loại thường khác và sản phẩm*) and subtracted from *Hàng hóa khác* |

Invariant, checked at every run: the sum of harmonised groups equals the printed total in every month and direction (325/325 on the full series).

## 5. Known issues in the series

| Issue | Treatment |
| --- | --- |
| Export 03/2023 and 04/2023: files uploaded with February content | Dropped (`mislabelled_upload`); only the two-month total is known |
| Import 12/2023: no file | Missing |
| 02/2013 (X, M), 10/2023 (X, M), 09/2024 (X): no file | Imputed from year-to-date figures |
| YTD(m) − YTD(m−1) ≠ month(m) for 286 of 9,738 pairs (> 0.5%) | Customs revisions; use `value_usd_month_ytddiff` |
| Two items numbered 18 in table 018.T, 08/2026 | Logged (`duplicate_item_number`); both kept |
| Empty row *Ô tô trên 9 chỗ ngồi* | Logged (`empty_row`) |
| Breaks in the product list: 01/2024 (R2), 03/2026 (R3) | Harmonised; check the share of *Hàng hóa khác* around the break |

## 6. Independent check

Annual export totals 2013–2023 match the KT192 tables compiled independently in a student report (Drive folder *Tong hop bao cao qua chuyen de cua SV*): 11/11 annual totals and 231/231 cells (22 groups × 11 years) agree exactly.

## 7. Use in the research programme

- DA2: `../da2/sector_map.csv` assigns each `group_h` a role (output, input, excluded) and a VSIC sector.
- DA3: `../da3/hs_concordance.csv` maps export `group_h` to HS4/HS6 codes.
- Product-group roles and exclusions are fixed in the DA2 and DA3 preregistrations before analysis.

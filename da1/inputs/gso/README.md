# fdi_registered.csv — registered FDI into Viet Nam by partner, 2006–2025

Source: GSO Statistical Yearbooks (Niên giám Thống kê) 2006–2025, table *Foreign direct investment projects licensed in year Y by main counterpart* (one yearbook per year). Files downloaded from nso.gov.vn on 2026-10-05; URLs below. The yearbooks are public; they are not committed here.

| Step | File |
| --- | --- |
| Parse the table from the text of each yearbook (`pdftotext -layout`; 2006: Investment chapter `.doc` read with `antiword`) | `parse_yearbook_fdi.py` → `yearbook_fdi_rows.csv` (every row keeps the printed line in `row_text`) |
| 2016: the investment chapter uses a font without Unicode mapping. Pages 245–246 were OCR-ed (tesseract 5.3.4, 300 dpi) and **every row was checked against the page image**; six OCR errors were corrected | `yearbook_2016_transcribed.csv` |
| Map printed English names to ISO3 | `partner_map.csv` (107 patterns) |
| Aggregate to partner × year, drop the total row, drop source errors | `build_fdi_registered.py` → `../fdi_registered.csv` |

**Checks.** The listed partners cover 98.7–100.0% of the printed total in every year (printed by `build_fdi_registered.py`). Every printed name must match `partner_map.csv` or the build stops.

**Definition break.** Registered capital = newly granted + supplementary capital to 2015; from 2016 it also includes capital contributions and share purchases by foreign investors (footnote to the yearbook FDI tables). The column `capital_definition` records this for each row. The DA1 models include year fixed effects, which absorb a common level shift but not a partner-specific one.

**Source issues logged, not corrected.**
- 2020: the row *United States Virgin Islands* repeats the figures of *British Virgin Islands* (29 projects, 899.1 million USD). Keeping it would make partners exceed the total by 2.6%; it is dropped (`SOURCE_ERRORS`).
- 2017: the partner rows sum to 37,108.5 against a printed total of 37,100.6 (+0.02%).
- 2025: *British Isles* is listed separately from *United Kingdom*; both are coded GBR and summed.
- Codes without ISO equivalents: XBWI (British West Indies), XCHI (Channel Islands). *Congo* is coded COG (Republic of the Congo).

**Zero filling.** The table lists main partners only. `build_panel.py` sets FDI = 0 for an economy in a year it is not listed; the omitted partners hold at most 1.3% of the yearly total.

Yearbook files used:
2006 https://www.nso.gov.vn/wp-content/uploads/2026/01/04.-Dau-tu-mi-D.doc ·
2007 …/2026/01/niengiam2007_watermark.pdf · 2008 …/2026/01/Niengiam2008_watermark.pdf · 2009 …/2026/01/Niengiam2009_watermark.pdf ·
2010 …/2019/10/NGTK-2010-pdf.pdf · 2011 …/2019/10/Niên-giám-2011-pdf-1.pdf · 2012 …/2019/10/Nien-giam-2012-pdf-1.pdf ·
2013 …/2019/10/NGTK-2013.pdf · 2014 …/2019/10/Nien-giam-2014-pdf.pdf · 2015 …/2019/10/Nien-giam-Thong-ke-2015-1.pdf ·
2016 …/2019/10/Nien-giam-Thong-ke-2016.pdf · 2017 …/2019/10/Nien-giam-2017-pdf.pdf · 2018 …/2019/10/Nien-giam-2018.pdf ·
2019 …/2020/09/Nien-giam-thong-ke-day-du-2019.pdf · 2020 …/2021/07/Sach-NGTK-2020Ban-quyen.pdf ·
2021 …/2022/08/Sach-Nien-giam-TK-2021-1.pdf · 2022 …/2023/06/Sach-Nien-giam-TK-2022-final.pdf ·
2023 …/2024/06/NIEN-GIAM-THONG-KE-2023_Ban-quyen-1.pdf · 2024 …/2026/01/NG-TONG-CUC-2024_OKIN_Final.pdf ·
2025 …/2026/07/NG-TOAN-QUOC-2025_WM.pdf (prefix `https://www.nso.gov.vn/wp-content/uploads/`).

# Distance, FDI and the Trade of Foreign-Invested Firms in Vietnam

Research programme DA0–DA4 · **Do Thuy Huong** (ORCID [0000-0002-7711-2487](https://orcid.org/0000-0002-7711-2487)) and **Assoc. Prof. Dr. Phan Anh Tu** (ORCID [0000-0003-0667-3137](https://orcid.org/0000-0003-0667-3137)) · School of Economics, Can Tho University.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

| Folder | Component | Status |
|---|---|---|
| `da0/` | Customs FDI-sector trade panel, 01/2013–08/2026: parsers, cleaning, harmonisation, concordance | Code public; **purchased data excluded** |
| `da1/` | Distance and FDI (structural gravity, PPML) | Code drafted; preregistration drafted |
| `da2/` | Aggregate FDI inflows and FDI-sector trade (local projections) | Code + public inputs; preregistration drafted |
| `da3/` | US–China tariffs and FDI-sector trade (event study, PPML) | Code + exposure measure; preregistration ready |
| `osf-wiki/` | Text of the OSF project and component wikis | — |

## Rules

- **Preregistration first.** `da2_analysis.py` and `da3_analysis.py` refuse to run on real data without the registration DOI. DA3 is registered before DA2; every DA3 run is logged in `disclosure_log.csv` for disclosure in the DA2 registration.
- **Purchased data stay private.** The consolidated Customs series bought from a commercial provider is never committed (see `.gitignore`). Public inputs (GSO releases, IMF BOP, CPB, Bruegel, UN Comtrade, USITC) are included with source columns.
- **Tests.** `python3 da3/test_da3.py`, `python3 da2/test_da2.py`, `python3 da1/test_build_panel.py` run on simulated data only.

## Licences

Code: MIT. Documentation, concordances and preregistration text: CC BY 4.0. Third-party public data remain under their providers' terms. Purchased data: provider's licence; not redistributed.

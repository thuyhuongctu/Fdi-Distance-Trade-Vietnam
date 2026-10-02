# DA2 · Aggregate FDI Inflows and FDI-Sector Trade

> *Tóm tắt:* Ước lượng dòng vốn FDI giải ngân vào Việt Nam mất bao lâu và ở mức nào để chuyển thành xuất khẩu và nhập khẩu đầu vào của khu vực FDI, giai đoạn 2013–2026, ở cấp nhóm hàng × quý.

**Part of:** [Distance, FDI and the Trade of Foreign-Invested Firms in Vietnam](../) · **Status:** Preregistration drafted · **Target journal:** *Journal of International Business Policy*

## Research questions

1. What are the size and timing of the response of FDI-sector exports to aggregate FDI inflows into Vietnam?
2. How much of that response is matched by imported inputs, and has the import-to-export ratio declined over 2013–2026?

## Hypotheses

| Code | Hypothesis |
| --- | --- |
| H1 | Aggregate FDI inflows raise FDI-sector exports of manufactured product groups (positive cumulative response within eight quarters). |
| H2 | The same inflows raise FDI-sector imports of intermediate inputs. |
| H3 | In electronics and in textiles and garments, the ratio of imported inputs to exports declines over 2013–2026. |

## Design

- **Unit:** product group × quarter, 2013Q1–2026Q2 (25 manufactured export groups; 26 intermediate-input import groups).
- **Data:** [DA0](../DA0) Customs series; quarterly disbursed FDI into Vietnam (public releases). Sector-level FDI is not published at sub-annual frequency, so the treatment is the national total.
- **Estimator:** local projections (h = 0–7 quarters) with group and group × quarter-of-year effects, controlling for world import demand and the real exchange rate. FDI is instrumented with a shift-share instrument: the outward FDI of Vietnam's seven main source economies, weighted by their shares in cumulative registered FDI to end-2012.
- **Inference:** Driscoll–Kraay standard errors with fixed-b critical values; Holm correction across three hypotheses; Anderson–Rubin intervals if the first stage is weak.

## Preregistration

OSF secondary data preregistration: **DOI to be added**. Submitted after the series was cleaned and before any outcome analysis.

## Files in this component

| Folder | Content | Access |
| --- | --- | --- |
| `/preregistration` | Registered plan (frozen) | Public |
| `/concordance` | Product-group roles and sector mapping, fixed before analysis | Public |
| `/code` | Analysis scripts | Public (MIT) |
| `/results` | Impulse responses, tables, deviation log | Public |

Raw Customs data are held in [DA0](../DA0) under its access terms.

## Teaching tool

[FDI Factory (Nhà máy FDI)](https://thuyhuongctu.github.io/BizOn/lab/nha-may-fdi.html) lets students experience the trade-off between imported and local inputs. Its parameters are illustrative until DA2 results are available.

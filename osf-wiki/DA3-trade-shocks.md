# DA3 · Trade-Policy Shocks and FDI-Sector Trade

> *Tóm tắt:* Đo phản ứng của xuất khẩu và nhập khẩu đầu vào của khu vực FDI trước thuế quan Mỹ áp lên Trung Quốc năm 2018–2019, theo mức phơi nhiễm của từng nhóm hàng, bằng dữ liệu Hải quan theo tháng.

**Part of:** [Distance, FDI and the Trade of Foreign-Invested Firms in Vietnam](../) · **Status:** Preregistration drafted · **Target journal:** *Journal of World Business*

## Research questions

1. Did FDI-sector exports of product groups more exposed to the 2018–2019 US tariffs on China grow faster afterwards than those of less exposed groups?
2. Did imports of the corresponding inputs rise alongside them?

## Hypotheses

| Code | Hypothesis |
| --- | --- |
| H1 | After July 2018, FDI-sector exports grow more in product groups with higher tariff exposure. |
| H2 | Imports of the inputs matched to more exposed groups also grow more after July 2018. |
| H3 | Identification check: no differential pre-trend before July 2018. |

## Design

- **Unit:** product group × month. Main window: 01/2015–12/2019, ending before COVID-19.
- **Exposure:** share of 2017 US imports from China in each group's HS6 lines that became subject to Section 301 tariffs, weighted by the tariff rate and fixed before outcomes are examined.
- **Estimator:** PPML difference-in-differences with group, month and group × calendar-month fixed effects, plus an event-study version.
- **Inference:** wild cluster bootstrap by product group; Holm correction across H1–H2; sensitivity bounds for parallel-trends violations.
- **Exploratory:** COVID-19 (2020–2021), 2025 US reciprocal tariffs, and a comparison of FDI-sector with domestic-sector trade.

## Preregistration

OSF secondary data preregistration: **DOI to be added**. Submitted separately and before DA2, after the shared Customs series was cleaned and before any outcome analysis. DA3 results seen before DA2 is registered are disclosed in the DA2 registration.

## Files in this component

| Folder | Content | Access |
| --- | --- | --- |
| `/preregistration` | Registered plan (frozen) | Public |
| `/exposure` | Tariff lists, HS concordance, exposure measure | Public |
| `/code` | Analysis scripts | Public (MIT) |
| `/results` | Event-study figures, tables, deviation log | Public |

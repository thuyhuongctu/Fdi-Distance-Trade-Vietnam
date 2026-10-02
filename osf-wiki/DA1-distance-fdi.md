# DA1 · Distance and FDI into Vietnam

> *Tóm tắt:* Kiểm định lại tác động của khoảng cách địa lý, văn hóa, thể chế và kinh tế đến FDI vào Việt Nam, giai đoạn 2006–2024, với toàn bộ nước đầu tư, ước lượng PPML và thước đo khoảng cách Mahalanobis. Nghiên cứu cập nhật Phan và Đỗ (2019).

**Part of:** [Distance, FDI and the Trade of Foreign-Invested Firms in Vietnam](../) · **Status:** Preregistration drafted · **Target journal:** *Asia Pacific Journal of Management*

## Research questions

1. Once FDI is measured more completely and zero flows are retained, do cultural and institutional distance reduce FDI into Vietnam?
2. Do free trade agreements weaken the deterrent effect of institutional distance?

## Hypotheses

| Code | Hypothesis |
| --- | --- |
| H1 | Geographic distance is negatively associated with FDI into Vietnam. |
| H2a | Cultural distance is negatively associated with FDI. |
| H2b | Institutional distance is negatively associated with FDI. |
| H3 | An FTA in force attenuates the negative association between institutional distance and FDI. |

## Design

- **Unit:** source economy × year, 2006–2024, all source economies, zero flows retained.
- **Outcomes:** registered FDI (primary); IMF CDIS direct-investment positions (secondary).
- **Estimator:** PPML with year fixed effects, with standard errors clustered by source economy (`ppmlhdfe`).
- **Distance measures:** CEPII population-weighted distance; Mahalanobis cultural distance (Hofstede) and institutional distance (WGI).
- **Inference:** two-sided tests, α = 0.05, Holm correction across four confirmatory tests.
- **Bridge to the 2019 study:** the original 16-country, 2006–2015 sample is re-estimated with both the original random-effects specification and PPML.

## Preregistration

OSF secondary data preregistration: **DOI to be added**. Submitted before the extended dataset is assembled.

## Files in this component

| Folder | Content | Access |
| --- | --- | --- |
| `/preregistration` | Registered plan (frozen) | Public |
| `/data` | Compiled panel from public sources; codebook | Public |
| `/code` | Stata/R scripts | Public (MIT) |
| `/results` | Tables, figures, deviation log | Public |

## Teaching tool

[Gravity Lab](https://thuyhuongctu.github.io/BizOn/lab/gravity-lab.html) reproduces the published 2019 results and runs OLS/PPML in the browser.

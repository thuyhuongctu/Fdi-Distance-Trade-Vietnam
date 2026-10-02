# DA1 – Bộ mã phân tích (Distance and FDI into Vietnam)

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Bám đúng bản tiền đăng ký OSF của DA1. **Chỉ chạy phần ước lượng (`da1_confirmatory.do`) sau khi đã nộp tiền đăng ký.**

| Tệp | Việc |
| --- | --- |
| `build_panel.py` | Ghép dữ liệu thành bảng nền kinh tế × năm, 2006–2024; lấp 0 cho năm không có FDI; tính khoảng cách Mahalanobis (văn hóa, thể chế) và Kogut–Singh (kiểm định độ vững); khoảng cách kinh tế; FTA; cờ trung tâm tài chính hải ngoại và mẫu 16 nước năm 2019 |
| `test_build_panel.py` | Kiểm thử trên dữ liệu giả lập: chọn mẫu, lấp 0, Mahalanobis khớp `scipy`, FTA, các cờ |
| `da1_confirmatory.do` | Stata: Mô hình 1 và 2 (PPML), hiệu chỉnh Holm cho 4 giả thuyết, độ lớn tác động, 6 kiểm định độ vững đã đăng ký |

## Tệp đầu vào cần chuẩn bị (thư mục `inputs/`, CSV UTF-8)

| Tệp | Cột | Nguồn |
| --- | --- | --- |
| `fdi_registered.csv` | iso3, year, fdi_usd_m | Cục Đầu tư nước ngoài / Niên giám Thống kê – FDI đăng ký theo đối tác |
| `imf_cdis.csv` | iso3, year, position_usd_m | IMF CDIS – vị thế đầu tư trực tiếp vào Việt Nam theo đối tác (dùng số đối ứng nếu Việt Nam không báo cáo) |
| `wdi.csv` | iso3, year, gdp_usd, gdppc_usd | World Bank WDI: NY.GDP.MKTP.CD, NY.GDP.PCAP.CD (gồm cả VNM) |
| `wgi.csv` | iso3, year, va, pv, ge, rq, rl, cc | Worldwide Governance Indicators, điểm ước lượng 6 khía cạnh (gồm cả VNM) |
| `hofstede.csv` | iso3, pdi, idv, mas, uai, lto, ivr | Hofstede (2001) và bộ điểm 6 khía cạnh công bố (gồm cả VNM) |
| `cepii_dist.csv` | iso3, distw_km, contig | CEPII GeoDist – khoảng cách có trọng số dân số tới Việt Nam |
| `fta.csv` | iso3, fta_name, in_force_year | WTO RTA Database – mỗi dòng một hiệp định có Việt Nam là thành viên |
| `ofc_list.csv` | iso3 | Danh sách trung tâm tài chính hải ngoại của IMF |

## Chạy

```
python3 build_panel.py --inputs inputs --out da1_panel.csv
stata -b do da1_confirmatory.do
```

Ghi lại phiên bản và ngày tải của từng tệp đầu vào vào codebook (yêu cầu của tiền đăng ký, Phần 2).

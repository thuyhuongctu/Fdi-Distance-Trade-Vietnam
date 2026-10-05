# DA3 – Cú sốc thuế quan Mỹ–Trung và thương mại khu vực FDI (mã phân tích)

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương. Mã: giấy phép MIT khi công bố trên OSF.

| Tệp | Vai trò |
| --- | --- |
| `hs_concordance.py` → `hs_concordance.csv`, `input_match.csv` | 29 nhóm XK hài hòa → 842 mã HS4/HS6; nhóm NK đầu vào khớp với từng nhóm XK |
| `section301_hts8.csv` | 10.391 dòng HTS8 trong danh sách Section 301 (USITC «China Tariffs», 28/07/2026) |
| `comtrade/part_*.csv` | NK của Mỹ từ TQ năm 2017 theo HS4/HS6 (UN Comtrade). Không kèm trong gói công bố; dựng lại bằng `python3 fetch_comtrade.py` (truy vấn cố định trong `comtrade_urls.json`) |
| `build_exposure.py` → `exposure.csv` | EXP_g (cố định trước khi xem kết quả) |
| `ppml.py` | PPML có FE, sai số cụm, wild score bootstrap (Kline & Santos, 2012), Holm |
| `da3_analysis.py` | Mô hình 1 (DiD), Mô hình 2 (event study), H1–H3, cận Rambachan–Roth xấp xỉ, kiểm định độ vững R1–R6 |
| `test_da3.py` | 9 kiểm thử trên dữ liệu mô phỏng (đối chiếu pyfixest; kích thước & lực kiểm định; ma trận hiệp phương sai xuất cho HonestDiD) |
| `honestdid.R` | Cận Rambachan–Roth bằng gói `HonestDiD`: đọc `event_study_X` và `event_study_X_vcov` trong `da3_results.json`, ghi `honestdid_results.csv` |

**Chạy:** `python3 fetch_comtrade.py && python3 hs_concordance.py && python3 build_exposure.py && python3 test_da3.py`.
`da3_analysis.py` từ chối chạy trên dữ liệu thật nếu không có DOI tiền đăng ký DA3. DA3 đăng ký riêng, trước DA2; mỗi lần chạy ghi vào `../disclosure_log.csv` để DA2 khai báo.

**Thay đổi so với bản tiền đăng ký trước đây (đã sửa trong văn bản, chưa nộp):**
1. Quý tham chiếu của event study là 2017Q3–2018Q2 (k = −4…−1), không phải chỉ 2018Q2: với FE nhóm × tháng-lịch, đặc tả cũ không nhận dạng được (3 hệ số cộng tuyến – mã nay báo lỗi nếu gặp).
2. H3 gồm kiểm định chung các hệ số trước sự kiện **và** kiểm định xu hướng tuyến tính 1 bậc tự do: mô phỏng cho thấy kiểm định chung 10 ràng buộc với ~25 cụm gần như không có lực.
3. Danh sách thuế lấy từ USITC (HTS 2026) thay vì bộ dữ liệu của Fajgelbaum và cộng sự; giới hạn ghi trong Phần 3.

**Giới hạn của `rr_bounds`:** bản xấp xỉ bảo thủ để kiểm tra nhanh trong Python. Bài báo dùng `honestdid.R` (gói `HonestDiD`): `Rscript honestdid.R da3_results.json` sau khi chạy `da3_analysis.py --registered <DOI>`. Tham số đích là hiệu ứng trung bình các kỳ sau; giới hạn độ lớn tương đối Mbar ∈ {0,5; 1; 1,5; 2} và giới hạn độ trơn M ∈ {0; 0,025; …; 0,1}.

**Lựa chọn mã hóa cần ghi trong tiền đăng ký:** khối kỳ gốc REF_K = −4..−1 được HonestDiD coi là một kỳ gốc gộp (gói giả định một kỳ gốc ngay trước can thiệp). Kỳ trước = k ≤ −5, kỳ sau = k ≥ 0.

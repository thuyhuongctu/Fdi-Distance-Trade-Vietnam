# DA0 – Quy trình dữ liệu Hải quan (bản đầu)

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

| Tệp | Nội dung |
| --- | --- |
| `parse_customs.py` | Đọc Biểu 017.T/018.T (PDF hoặc văn bản) → bảng dọc có 4 trường xuất xứ; ghi nhật ký kiểm tra |
| `panel.csv` | Kết quả chạy thử trên biểu tháng 8/2026 (80 dòng) |
| `cleaning_log.csv` | Nhật ký kiểm tra: tổng nhóm so với dòng tổng, STT trùng, dòng trống, tiểu mục vượt nhóm cha |
| `concordance_draft.csv` | Bản nháp đối chiếu nhóm hàng → ngành VSIC, vai trò trong DA2 (đầu ra/đầu vào/loại trừ), chương HS gợi ý, độ tin cậy |

Chạy: `python3 parse_customs.py <các tệp PDF> --out panel.csv --log cleaning_log.csv` (cần `pdftotext`).

Việc tiếp theo khi có chuỗi 2013–2026: chạy hàng loạt, lập bảng hài hòa tên nhóm qua các năm, và đối chiếu chương HS với danh mục chính thức của Hải quan.

## Cập nhật 10/2026 – toàn bộ chuỗi 2013-01 → 2026-08 từ Google Drive

Quy trình: `parse_flat.py raw/` → `build_monthly.py` → `harmonise.py`.

| Bước | Kết quả |
| --- | --- |
| Tệp đọc | 323 PDF (XKHH/NKHH), 11.061 dòng |
| Kiểm tra tổng (Σ nhóm = dòng tổng, tháng & cộng dồn) | 323/323 khớp |
| Đối chiếu độc lập với bảng KT192 (tổng năm XK 2013–2023, 22 nhóm × 11 năm) | 11/11 tổng năm và 231/231 ô khớp tuyệt đối |
| Kiểm tra cộng dồn YTD(m) − YTD(m−1) = tháng m | 286/9.738 cặp lệch > 0,5%, đi theo cặp (+/−) ở tháng có biểu «Điều chỉnh» hoặc số sơ bộ → Hải quan sửa số, không phải lỗi chép. Cột `value_usd_month_ytddiff` cho chuỗi đã hấp thụ điều chỉnh |
| Tệp loại | 2023-T3-XKHH, 2023-T4-XKHH (tải nhầm, nội dung = tháng 2); 1 bản sao 2026-T6-XKHH |
| Tháng suy từ cộng dồn | 2013-02 (XK, NK), 2023-10 (XK, NK), 2024-09 (XK) |
| Tháng còn thiếu | XK 2023-03 và 2023-04 (chỉ biết tổng hai tháng); NK 2023-12 |
| Hài hòa danh mục | 30 nhóm XK, 29 nhóm NK, liên tục mọi tháng; Σ nhóm = tổng ở 325/325 tháng × chiều |

Gãy danh mục: (i) 01/2024 Hải quan tách thêm 6 nhóm XK, 5 nhóm NK → cộng vào «Hàng hóa khác» trong chuỗi hài hòa;
(ii) từ 03/2026 mẫu biểu mới có dòng ghi nhớ không đánh số → xem `harmonise_map.csv`.
Dữ liệu thô và bảng đầu ra là dữ liệu mua – **không** đưa lên repo công khai.

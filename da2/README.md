# DA2 – Từ dòng vốn FDI đến thương mại khu vực FDI (mã phân tích)

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương. Mã: giấy phép MIT khi công bố trên OSF.

| Tệp | Vai trò |
| --- | --- |
| `sector_map.csv` | Vai trò nhóm hàng: 25 nhóm XK (output), 26 nhóm NK (input), nhóm loại trừ có lý do; ngành VSIC (chỉ dùng cho H3) |
| `lp.py` | 2SLS khử FE nhóm × quý-trong-năm, sai số Driscoll–Kraay, giá trị tới hạn fixed-b (Kiefer & Vogelsang, 2005), F hiệu dụng, tập Anderson–Rubin |
| `da2_analysis.py` | Thiết kế sửa 10/2026: cú sốc FDI giải ngân toàn quốc → XK/NK khu vực FDI theo nhóm hàng × quý; LP-IV h = 0…7 và tích lũy (H1, H2); xu hướng tỷ lệ NK/XK ngành điện tử, dệt may (H3); Holm; R2–R6 |
| `test_da2.py` | 9 kiểm thử mô phỏng; độ phủ fixed-b: IV 36/40, OLS (không nhiễu) 29/30 |
| `build_inputs.py` | Dựng `inputs/fdi_quarter.csv`, `instrument.csv`, `controls.csv` từ `inputs/raw/` (STL, tăng trưởng đối xứng) |

**Vì sao đổi thiết kế:** Cục ĐTNN không công bố FDI theo ngành cấp 2 theo quý, cũng không công bố cơ cấu quốc gia × ngành. Thiết kế mới chỉ dùng số liệu công khai; đổi lại, cú sốc chỉ biến thiên theo thời gian (~54 quý) nên nhận dạng dựa hoàn toàn vào công cụ và biến kiểm soát; bước 1 có thể yếu → quyết định dựa trên khoảng Anderson–Rubin.

**Đầu vào cần thu thập (đều công khai):**
- `inputs/fdi_quarter.csv` – FDI giải ngân và đăng ký theo quý 2012–2026 (Tổng cục Thống kê / Cục ĐTNN, từ thông cáo lũy kế tháng), hiệu chỉnh mùa vụ X-13.
- `inputs/instrument.csv` – Z, Z_noKOR, Z_2008: tỷ trọng 7 nguồn (Nhật, Hàn, Singapore, Trung Quốc, Hồng Kông, Đài Loan, Mỹ) trong vốn đăng ký lũy kế đến 2012 (và 2008) × Δln FDI ra nước ngoài (IMF BOP; NHTW Đài Loan), tổng trượt 4 quý.
- `inputs/controls.csv` – d_wtv (CPB World Trade Monitor), d_lnreer (BIS).

Kiểm tra cấu trúc trên dữ liệu thật (chỉ đếm ô): XK 25 nhóm × 54 quý, 50 ô thiếu (2023Q1–Q2); NK 26 nhóm × 54 quý, 26 ô thiếu (2023Q4).

**Quyết định 02/10/2026 (phương án b):** bước 1 của công cụ shift-share có F ≈ 1 (53 quý; không dùng số liệu Hải quan) → phân tích xác nhận là LP OLS có biến kiểm soát, diễn giải là quan hệ động có điều kiện; LP-IV chuyển sang khám phá. Đã khai báo ở Phần 4 tiền đăng ký.

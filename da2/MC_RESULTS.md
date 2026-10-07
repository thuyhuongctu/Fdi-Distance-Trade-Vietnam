# DA2 – Chọn phương pháp suy diễn cho đáp ứng tích lũy OLS (Monte Carlo, 7/10/2026)

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Mã: `mc_inference.py`. Kết quả từng lần lặp: `mc_inference.csv`. Toàn bộ là dữ liệu mô phỏng.

**Thiết kế mô phỏng**
- Bảng gồm 25 nhóm hàng × 56 quý. Sau khi trừ trễ và các bước đi trước, còn T = 46 quý dùng để ước lượng.
- Hồi quy giống hệt `lp_irf`: đáp ứng tích lũy h = 0…7, FE nhóm × quý-trong-năm, cùng các biến kiểm soát.
- Không có nhiễu: OLS không chệch, đúng như vai trò xác nhận của OLS trong DA2.
- Hai kịch bản:
  - *iid*: thiết kế của `test_da2.py`;
  - *persistent*: ΔlnFDI theo AR(1) với ρ = 0,5, và cú sốc chung trong thương mại theo AR(1) với ρ = 0,6.
- Mỗi kịch bản chạy 1.000 lần lặp. Bootstrap khối chạy 200 lần lặp × 199 lần lấy mẫu lại.

**Tỷ lệ khoảng 95% danh nghĩa chứa giá trị thật**

| Phương pháp                           | iid            | persistent     |
|:--------------------------------------|:---------------|:---------------|
| DK–Bartlett, bw_rule, N(0,1)          | 0.769 (n=1000) | 0.748 (n=1000) |
| DK–Bartlett, bw_rule, fixed-b (mã cũ) | 0.860 (n=1000) | 0.850 (n=1000) |
| DK–Bartlett, S=1,3√T, fixed-b         | 0.860 (n=1000) | 0.850 (n=1000) |
| DK–EWC, ν=⌊0,4T^(2/3)⌋, t_ν           | 0.865 (n=1000) | 0.856 (n=1000) |
| Bootstrap khối theo quý, percentile-t | 0.885 (n=200)  | 0.880 (n=200)  |
| Cụm theo quý CR1, t_(T−1)             | 0.860 (n=1000) | 0.840 (n=1000) |
| Cụm theo quý CR2, t_(T−1)             | 0.890 (n=1000) | 0.887 (n=1000) |
| WCR theo quý, Webb, B=399 (chọn)      | 0.925 (n=1000) | 0.918 (n=1000) |

Phương pháp B và C cho kết quả trùng nhau, vì với T = 46 hai quy tắc chọn độ trễ cho cùng độ dài cửa sổ (9).

**Chẩn đoán**
- Chệch gần bằng 0: −0,03 ở kịch bản *iid*, −0,18 ở kịch bản *persistent*, so với độ lệch chuẩn 1,06 và 1,77.
- Sai số DK–Bartlett trung bình chỉ bằng khoảng 2/3 độ lệch chuẩn thật.
- Điểm số hầu như không tự tương quan: tự tương quan ở các độ trễ 1–10 nằm trong khoảng [−0,05; 0]. Biến ΔlnFDI sau khi trừ các biến kiểm soát cũng không tự tương quan. Đây đúng là kết quả của Montiel Olea & Plagborg-Møller (2021) cho LP có kiểm soát trễ, nên không cần ước lượng HAC.
- Phần độ phủ còn thiếu là chệch mẫu nhỏ: chỉ có 46 cụm quý, khoảng 10 biến hồi quy chỉ thay đổi theo thời gian, và điểm số có đuôi dày.

**Quyết định**
- Suy diễn xác nhận cho H1 và H2 dùng wild cluster bootstrap-t theo quý, có áp giả thuyết không (WCR):
  - Cameron, Gelbach & Miller (2008); trọng số Webb 6 điểm (Webb, 2023); B = 9.999;
  - khoảng tin cậy 95% lấy bằng nghịch đảo kiểm định, B = 1.999.
- Đây là phương pháp tốt nhất trong tám phương pháp đã so sánh. Dù vậy, tỷ lệ bác bỏ thực tế ở mức 5% danh nghĩa vẫn khoảng 7,5–8%. Bản tiền đăng ký khai báo rõ điều này.
- DK với giá trị tới hạn fixed-b vẫn được báo cáo kèm.

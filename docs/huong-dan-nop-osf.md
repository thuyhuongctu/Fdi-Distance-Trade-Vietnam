# Hướng dẫn nộp tiền đăng ký lên OSF (DA3 → DA1 → DA2)

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Bấm **Register** là cam kết của tác giả. Bước này làm trên trình duyệt, bằng tài khoản OSF của chị, và không thể hoàn tác.
Việc tải tệp lên Files có thể tự động hóa bằng PowerShell (bước 1b).

## 1. Đưa gói mã lên OSF Storage

Dùng gói mã v1.0: `Fdi-Distance-Trade-Vietnam-v0.1.0-e300047.zip` (64 tệp) kèm tệp `.sha256`.
Tên tệp vẫn giữ "v0.1.0" như lúc đóng gói, nhưng đây đúng là commit e300047 mà bản phát hành v1.0 trên GitHub trỏ tới.
Nếu tải bản *Source code (zip)* của release v1.0 thì nội dung giống hệt: GitHub cũng bỏ thư mục `da3/comtrade/` theo `.gitattributes`.

**1a. Bằng trình duyệt.** Mở https://osf.io/m25qs/files → OSF Storage → Upload, rồi chọn hai tệp.

**1b. Bằng PowerShell.** Chạy được trên Windows PowerShell 5.1 hoặc PowerShell 7.
1. Tạo token tại https://osf.io/settings/tokens. Chọn quyền `osf.full_write` và sao chép token.
2. Mở PowerShell trong thư mục chứa hai tệp và tệp `osf_upload.ps1` (lấy từ thư mục `tools/` của repo). Nếu máy chặn chạy script, chỉ mở khóa cho phiên này:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   ```
3. Chạy thử trước. Lệnh này kiểm tra SHA-256 và đăng nhập, chưa tải gì:
   ```powershell
   .\osf_upload.ps1 -Files Fdi-Distance-Trade-Vietnam-v0.1.0-e300047.zip, Fdi-Distance-Trade-Vietnam-v0.1.0-e300047.zip.sha256 -WhatIf
   ```
4. Tải lên thật, có thể đặt vào thư mục con `code`:
   ```powershell
   .\osf_upload.ps1 -Files Fdi-Distance-Trade-Vietnam-v0.1.0-e300047.zip, Fdi-Distance-Trade-Vietnam-v0.1.0-e300047.zip.sha256 -Folder code
   ```
   Script hỏi token ở dạng ẩn và không lưu token. Nếu tệp đã có trên OSF, script tải lên thành phiên bản mới; OSF vẫn giữ các phiên bản cũ.

## 2. Nộp bản tiền đăng ký (trên trình duyệt)

1. Mở https://osf.io/m25qs → **Registrations** → **New registration**.
2. Chọn mẫu **Secondary Data Preregistration**, giống hai bản luận án Z37KN và HW64C.
3. Dán nội dung từ bản tiền đăng ký tương ứng. Mỗi câu hỏi của mẫu OSF khớp với một mục cùng tên trong bản nháp.
   - DA3: https://claude.ai/code/artifact/635843df-b95b-4748-a4f4-c9ca3639b34b
   - DA1: https://claude.ai/code/artifact/ed16cbaa-9b9c-4123-912b-5a4fd026db6d
   - DA2: https://claude.ai/code/artifact/9f05e36b-e434-46f1-bda2-b6b96192ee03 (nộp sau, khi đã có DOI của DA3)
4. Ở mục tệp đính kèm, chọn gói mã vừa tải lên ở bước 1.
5. Tác giả: Đỗ Thùy Hương (ORCID 0000-0002-7711-2487) và Phan Anh Tú (ORCID 0000-0003-0667-3137).
6. Chọn **công bố ngay**, không giữ kín. OSF chỉ cấp DOI cho bản đăng ký công khai.
7. Bấm **Register**. Nếu thầy Tú là quản trị (admin) của dự án, thầy sẽ nhận email đề nghị duyệt. Theo quy định của OSF, nếu không ai từ chối trong 48 giờ thì bản đăng ký tự được chấp thuận.

## 3. Sau khi có DOI

Gửi DOI cho người phụ trách mã. Các việc tiếp theo:
- ghi DOI vào `README.md`, `CITATION.cff` và `osf-wiki/`;
- chạy phân tích xác nhận với `--registered <DOI>`. Các script từ chối chạy nếu thiếu DOI;
- với DA1: chỉ sau khi đăng ký mới bắt đầu thu thập FDI theo nước đầu tư;
- với DA2: khai báo các lần chạy DA3 ghi trong `disclosure_log.csv` ở Phần 4 của bản DA2.

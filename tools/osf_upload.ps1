<#
.SYNOPSIS
  Tải gói mã và tệp kiểm tra SHA-256 lên OSF Storage của dự án (mặc định osf.io/m25qs).

.DESCRIPTION
  © 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương. Giấy phép MIT.

  Tệp này CHỈ tải tệp lên mục Files của dự án OSF. Nó KHÔNG nộp bản tiền đăng ký:
  bước bấm "Register" là cam kết của tác giả và phải làm trên giao diện osf.io.

  Cần một Personal Access Token của OSF có quyền osf.full_write
  (tạo tại https://osf.io/settings/tokens). Token được hỏi kín khi chạy
  hoặc đọc từ biến môi trường OSF_TOKEN; không ghi ra đĩa, không in ra màn hình.

.EXAMPLE
  # Trong thư mục chứa hai tệp đã tải về:
  .\osf_upload.ps1 -Files Fdi-Distance-Trade-Vietnam-v0.1.0-e300047.zip, Fdi-Distance-Trade-Vietnam-v0.1.0-e300047.zip.sha256

.EXAMPLE
  # Chỉ kiểm tra, không tải lên:
  .\osf_upload.ps1 -Files goi.zip, goi.zip.sha256 -WhatIf
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)] [string[]] $Files,
  [string] $Node = 'm25qs',
  [string] $Folder = ''          # thư mục con trong OSF Storage, ví dụ 'code'; để trống = gốc
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# 1. Kiểm tra tệp và mã SHA-256 (nếu có tệp .sha256 đi kèm)
$paths = foreach ($f in $Files) { (Resolve-Path -LiteralPath $f).Path }
foreach ($p in $paths | Where-Object { $_ -like '*.sha256' }) {
  $line = (Get-Content -LiteralPath $p -TotalCount 1).Trim()
  $expected, $name = $line -split '\s+', 2
  $target = Join-Path (Split-Path $p) $name.TrimStart('*')
  if (Test-Path -LiteralPath $target) {
    $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $expected.ToLower()) { throw "SHA-256 không khớp cho $name`n  mong đợi $expected`n  thực tế  $actual" }
    Write-Host "SHA-256 khớp: $name" -ForegroundColor Green
  }
}

# 2. Token: biến môi trường OSF_TOKEN hoặc hỏi kín
$token = $env:OSF_TOKEN
if (-not $token) {
  $sec = Read-Host 'Dán OSF Personal Access Token (osf.full_write)' -AsSecureString
  $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
}
$headers = @{ Authorization = "Bearer $token" }

# 3. Thư mục đích và danh sách tệp đã có (để cập nhật phiên bản thay vì báo trùng)
$api = "https://api.osf.io/v2/nodes/$Node/files/osfstorage/"
$root = Invoke-RestMethod -Uri $api -Headers $headers
$uploadBase = "https://files.osf.io/v1/resources/$Node/providers/osfstorage/"
$listing = $root
if ($Folder) {
  $dir = $root.data | Where-Object { $_.attributes.kind -eq 'folder' -and $_.attributes.name -eq $Folder }
  if (-not $dir) {
    if ($PSCmdlet.ShouldProcess("osf.io/$Node", "Tạo thư mục $Folder")) {
      $dir = (Invoke-RestMethod -Method Put -Uri "$uploadBase`?kind=folder&name=$([uri]::EscapeDataString($Folder))" -Headers $headers).data
      $uploadBase = $dir.links.upload
      $listing = @{ data = @() }
    }
  } else {
    $uploadBase = $dir.links.upload
    $listing = Invoke-RestMethod -Uri $dir.relationships.files.links.related.href -Headers $headers
  }
}

# 4. Tải lên: tệp mới → PUT ?kind=file&name=…; tệp đã có → PUT lên link upload của tệp (OSF giữ phiên bản cũ)
foreach ($p in $paths) {
  $name = Split-Path $p -Leaf
  $existing = $listing.data | Where-Object { $_.attributes.kind -eq 'file' -and $_.attributes.name -eq $name }
  $uri = if ($existing) { "$($existing.links.upload)?kind=file" } else { "$uploadBase`?kind=file&name=$([uri]::EscapeDataString($name))" }
  $what = if ($existing) { 'Cập nhật phiên bản mới' } else { 'Tải lên' }
  if ($PSCmdlet.ShouldProcess("osf.io/$Node/$Folder$name", $what)) {
    $r = Invoke-RestMethod -Method Put -Uri $uri -Headers $headers -InFile $p -ContentType 'application/octet-stream'
    Write-Host ("{0}: {1} ({2:N0} byte)" -f $what, $name, $r.data.attributes.size) -ForegroundColor Green
  }
}

$token = $null
Write-Host "`nXong. Kiểm tra tại https://osf.io/$Node/files/osfstorage" -ForegroundColor Cyan
Write-Host "Nộp tiền đăng ký: https://osf.io/$Node/registrations → New registration (làm trên trình duyệt)." -ForegroundColor Cyan

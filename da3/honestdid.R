# DA3 – Rambachan & Roth (2023) sensitivity bounds for the export event study (H3), using the HonestDiD package.
#
# © 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương. Licence: CC BY 4.0.
#
# Đầu vào: da3_results.json do da3_analysis.py ghi (khóa event_study_X và event_study_X_vcov: hệ số sự kiện,
# ma trận hiệp phương sai sai số cụm theo nhóm hàng). Chỉ chạy sau khi DA3 đã tiền đăng ký (da3_analysis.py tự chặn).
#
# Chuẩn hóa: các kỳ REF_K = -4..-1 đều bị loại (hệ số = 0). HonestDiD giả định một kỳ gốc duy nhất ngay trước
# can thiệp, nên khối REF_K được coi là một kỳ gốc gộp: kỳ trước gồm k < min(REF_K), kỳ sau gồm k >= 0.
# Mbar khi đó so độ lệch xu hướng sau can thiệp với bước nhảy lớn nhất giữa các kỳ trước liền kề (kể cả bước
# vào khối gốc). Đây là lựa chọn mã hóa cần ghi rõ trong bài báo.
#
# Đã kiểm tra với R 4.3.3, HonestDiD 0.2.6, CVXR 1.0-14 (HonestDiD 0.2.8 cần CVXR mới, đòi Matrix >= 1.7 / R >= 4.4).
# Thời gian chạy khoảng 3–4 phút.
#
# Chạy:  Rscript honestdid.R [da3_results.json] [honestdid_results.csv]

suppressPackageStartupMessages({ library(jsonlite); library(HonestDiD) })

args <- commandArgs(trailingOnly = TRUE)
inp <- if (length(args) >= 1) args[1] else "da3_results.json"
out <- if (length(args) >= 2) args[2] else "honestdid_results.csv"

res <- fromJSON(inp, simplifyVector = TRUE)
vc <- res$event_study_X_vcov
es <- as.data.frame(res$event_study_X)
k <- as.integer(vc$k)
V <- matrix(unlist(vc$V), nrow = length(k), byrow = TRUE)
stopifnot(nrow(V) == length(k), ncol(V) == length(k), identical(as.character(es$term), as.character(vc$terms)))
stopifnot(isTRUE(all.equal(sqrt(diag(V)), es$se, tolerance = 1e-6)))

ord <- order(k)
k <- k[ord]; beta <- es$coef[ord]; V <- V[ord, ord]
pre <- k < min(vc$ref_k); post <- k >= 0
stopifnot(all(pre | post))
nPre <- sum(pre); nPost <- sum(post)
stopifnot(nPre >= 2, nPost >= 1)
l_vec <- rep(1 / nPost, nPost)                       # tham số đích: hiệu ứng trung bình của các kỳ sau

orig <- constructOriginalCS(betahat = beta, sigma = V, numPrePeriods = nPre, numPostPeriods = nPost, l_vec = l_vec)
rm_ <- createSensitivityResults_relativeMagnitudes(betahat = beta, sigma = V, numPrePeriods = nPre,
                                                  numPostPeriods = nPost, l_vec = l_vec,
                                                  Mbarvec = c(0.5, 1, 1.5, 2))
sd_ <- createSensitivityResults(betahat = beta, sigma = V, numPrePeriods = nPre, numPostPeriods = nPost,
                                l_vec = l_vec, Mvec = seq(0, 0.1, by = 0.025))

tab <- rbind(
  data.frame(restriction = "original", parameter = NA, lb = orig$lb, ub = orig$ub, method = orig$method),
  data.frame(restriction = "relative_magnitudes", parameter = rm_$Mbar, lb = rm_$lb, ub = rm_$ub, method = rm_$method),
  data.frame(restriction = "smoothness", parameter = sd_$M, lb = sd_$lb, ub = sd_$ub, method = sd_$method))
tab$excludes_zero <- tab$lb > 0 | tab$ub < 0
# Mbar phá vỡ: Mbar nhỏ nhất trong lưới mà khoảng tin cậy chứa 0
# (chỉ có nghĩa khi khoảng gốc loại trừ 0; nếu ngay Mbar = 0,5 đã chứa 0 thì ghi "<= 0.5")
br <- tab[tab$restriction == "relative_magnitudes" & !tab$excludes_zero, "parameter"]
brk <- if (!tab$excludes_zero[1]) "n/a (original CI includes 0)" else if (!length(br)) "> 2" else
  if (min(br) == 0.5) "<= 0.5" else sprintf("in (%.1f, %.1f]", min(br) - 0.5, min(br))
cat(sprintf("Pre periods: %d, post periods: %d; breakdown Mbar (grid 0.5-2): %s\n", nPre, nPost, brk))
write.csv(tab, out, row.names = FALSE)
print(tab, row.names = FALSE)

"""DA2 – Nghiên cứu Monte Carlo chọn phương pháp suy diễn cho đáp ứng tích lũy OLS (kiểm định xác nhận H1, H2).

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương. Giấy phép MIT.

Chỉ dùng dữ liệu MÔ PHỎNG (simulate() trong test_da2.py; thêm một thiết kế có tự tương quan).
Ước lượng: hồi quy LP tích lũy h = 0…7 như lp_irf (FE nhóm × quý-trong-năm, cùng biến kiểm soát), hệ số OLS của ΔlnFDI.
So sánh độ phủ của khoảng 95% danh nghĩa:
  A  DK–Bartlett, độ trễ theo bw_rule, giá trị tới hạn chuẩn 1,96
  B  DK–Bartlett, độ trễ theo bw_rule, giá trị tới hạn fixed-b (Kiefer & Vogelsang, 2005)   ← mã hiện tại
  C  DK–Bartlett, độ trễ S = 1,3·√T, fixed-b (Lazarus, Lewis, Stock & Watson, 2018)
  D  DK–EWC (cosine trọng số đều), ν = ⌊0,4·T^(2/3)⌋ bậc tự do, giá trị tới hạn t_ν (Lazarus et al., 2018)
  E  Bootstrap khối dịch chuyển theo quý (cả lát cắt), percentile-t với sai số DK–Bartlett
  F  Cụm theo quý, CR1 (hệ số T/(T−1)·(n−1)/(n−k)), giá trị tới hạn t_(T−1) – hợp lệ khi LP đã kiểm soát trễ
     (Montiel Olea & Plagborg-Møller, 2021: phần dư của ΔlnFDI sau khi trừ trễ là nhiễu trắng nên điểm số không tự tương quan)
  G  Cụm theo quý, CR2 (Bell & McCaffrey, 2002; điều chỉnh đòn bẩy từng cụm), giá trị tới hạn t_(T−1)
  W  Wild cluster bootstrap-t theo quý, có áp giả thuyết không (WCR; Cameron, Gelbach & Miller, 2008;
     trọng số Webb 6 điểm), thống kê t dùng sai số CR1; khoảng = các β0 không bị bác bỏ (ở đây: kiểm tra tại β0 = giá trị thật)
Chạy:  python3 mc_inference.py --reps 1000 --boot-reps 200 --B 199 --out mc_inference.csv
       (song song: thêm --shard i --nshards n cho từng tiến trình, rồi ghép các tệp CSV)
"""
import argparse
import numpy as np
import pandas as pd
from scipy import stats

from da2_analysis import group_panel, CTRL, H
from lp import demean1, bw_rule, fixed_b_cv
from test_da2 import PHI

W = ['dY_l1', 'dY_l2', 'dlnFDI_l1', 'dlnFDI_l2'] + CTRL


def simulate(G=25, T=56, seed=0, rho_x=0.0, rho_c=0.0, sd_c=0.3):
    """Thiết kế của test_da2.simulate với conf = 0 (OLS không chệch – đúng vai trò xác nhận),
    mở rộng: ΔlnFDI tự tương quan AR(1) ρ_x, cú sốc chung c_t trong thương mại AR(1) ρ_c."""
    r = np.random.default_rng(seed)
    qs = pd.period_range('2012Q3', periods=T, freq='Q').astype(str)
    wtv = r.normal(size=T); reer = r.normal(size=T); z = r.normal(size=T)
    x = np.zeros(T); c = np.zeros(T)
    for t in range(T):
        x[t] = (rho_x * x[t - 1] if t else 0) + 0.3 * wtv[t] + r.normal()
        c[t] = (rho_c * c[t - 1] if t else 0) + r.normal()
    fdi = pd.DataFrame(dict(quarter=qs, fdi_disb_sa=np.exp(5 + np.cumsum(x))))
    inst = pd.DataFrame(dict(quarter=qs, Z=z))
    ctrl = pd.DataFrame(dict(quarter=qs, d_wtv=wtv, d_lnreer=reer))
    rows = []
    for g in range(G):
        seas = r.normal(0, .1, 4); Y = r.normal(20, 1); slope = r.normal(0.01, 0.005)
        for t in range(T):
            if t:
                Y += slope + sum(PHI[j] * x[t - j] for j in range(len(PHI)) if t - j >= 0) + sd_c * c[t] + 0.2 * wtv[t] + r.normal(0, .05)
            qn = int(qs[t][-1])
            rows.append(dict(direction='export', group_h=f'g{g}', sector='other', role='output', quarter=qs[t],
                             v=np.exp(Y + seas[qn - 1]), nm=3))
    return pd.DataFrame(rows), fdi, inst, ctrl


def true_cum(rho_x):
    """Hệ số tổng thể của x_t (giữ cố định các trễ) trong LP tích lũy: Σ_{h<H} Σ_{k≤h} Σ_{j≤k} φ_j ρ^(k−j)."""
    irf = [sum(PHI[j] * rho_x ** (k - j) for k in range(h + 1) for j in range(min(k, len(PHI) - 1) + 1)) for h in range(H)]
    return float(np.sum(irf))


def design(p):
    d = p.dropna(subset=['Y_cum', 'dlnFDI'] + W)
    D = demean1(d, ['Y_cum', 'dlnFDI'] + W, 'gq')
    tix = pd.Index(sorted(d.quarter.unique())).get_indexer(d.quarter)
    return D['Y_cum'].to_numpy(), D[['dlnFDI'] + W].to_numpy(), tix


def ols_scores(y, X, tix, T):
    A = np.linalg.inv(X.T @ X); b = A @ X.T @ y; e = y - X @ b
    h = np.zeros((T, X.shape[1])); np.add.at(h, tix, X * e[:, None])
    return b, A, h


def meat_bartlett(h, L):
    S = h.T @ h
    for l in range(1, L + 1):
        G = h[l:].T @ h[:-l]; S += (1 - l / (L + 1)) * (G + G.T)
    return S


def meat_ewc(h, nu):
    T = h.shape[0]; t = np.arange(1, T + 1)
    S = np.zeros((h.shape[1],) * 2)
    for j in range(1, nu + 1):
        lam = np.sqrt(2 / T) * (np.cos(np.pi * j * (t - 0.5) / T) @ h)
        S += np.outer(lam, lam)
    return T * S / nu


def se_from(A, S):
    return float(np.sqrt((A @ S @ A)[0, 0]))


WEBB = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])


def wcr_pvalue(y, X, tix, gq_codes, beta0, B, rng):
    """p-value WCR cho H0: β_1 = beta0. y, X đã khử FE; FE được khử lại trên y* ở mỗi lần lặp."""
    T = tix.max() + 1; n, k = X.shape
    A = np.linalg.inv(X.T @ X)
    cnt = np.bincount(gq_codes)
    demean = lambda v: v - (np.bincount(gq_codes, v) / cnt)[gq_codes]

    def tstat(yy):
        b = A @ X.T @ yy; e = yy - X @ b
        h = np.zeros((T, k)); np.add.at(h, tix, X * e[:, None])
        se = np.sqrt((A @ (h.T @ h) @ A)[0, 0] * T / (T - 1) * (n - 1) / (n - k))
        return (b[0] - beta0) / se
    t0 = tstat(y)
    yr = y - beta0 * X[:, 0]
    Xr = X[:, 1:]; g = np.linalg.lstsq(Xr, yr, rcond=None)[0]
    fit = Xr @ g + beta0 * X[:, 0]; er = yr - Xr @ g
    ts = np.array([tstat(demean(fit + er * rng.choice(WEBB, T)[tix])) for _ in range(B)])
    return float((np.abs(ts) >= abs(t0)).mean())


def one_rep(seed, dgp, boot, B, rng_boot, wild_B=0):
    q, fdi, inst, ctrl = simulate(seed=seed, **dgp)
    p = group_panel(q, fdi, inst, ctrl)
    y, X, tix = design(p)
    T = tix.max() + 1
    b, A, h = ols_scores(y, X, tix, T)
    truth = true_cum(dgp.get('rho_x', 0.0))
    L = bw_rule(T, H - 1)
    S_llsw = int(np.ceil(1.3 * np.sqrt(T)))
    nu = int(np.floor(0.4 * T ** (2 / 3)))
    out = dict(seed=seed, T=T, beta=b[0], truth=truth)
    se_b = se_from(A, meat_bartlett(h, L))
    out['A'] = abs(b[0] - truth) / se_b < 1.959964
    out['B'] = abs(b[0] - truth) / se_b < fixed_b_cv((L + 1) / T)
    se_c = se_from(A, meat_bartlett(h, S_llsw - 1))
    out['C'] = abs(b[0] - truth) / se_c < fixed_b_cv(S_llsw / T)
    se_d = se_from(A, meat_ewc(h, nu))
    out['D'] = abs(b[0] - truth) / se_d < stats.t.ppf(0.975, nu)
    out.update(hw_A=1.959964 * se_b, hw_B=fixed_b_cv((L + 1) / T) * se_b, hw_C=fixed_b_cv(S_llsw / T) * se_c,
               hw_D=stats.t.ppf(0.975, nu) * se_d, L=L, S_llsw=S_llsw, nu=nu)
    n, k = X.shape
    se_f = float(np.sqrt((A @ (h.T @ h) @ A)[0, 0] * T / (T - 1) * (n - 1) / (n - k)))
    tcv = stats.t.ppf(0.975, T - 1)
    out['F'] = abs(b[0] - truth) / se_f < tcv
    e = y - X @ b
    h2 = np.zeros_like(h)
    for t in range(T):
        i = np.flatnonzero(tix == t); Xg = X[i]
        Hg = Xg @ A @ Xg.T
        w, V = np.linalg.eigh(np.eye(len(i)) - Hg)
        Mg = V @ np.diag(1 / np.sqrt(np.clip(w, 1e-10, None))) @ V.T
        h2[t] = Xg.T @ (Mg @ e[i])
    se_g = se_from(A, h2.T @ h2)
    out['G'] = abs(b[0] - truth) / se_g < tcv
    out.update(hw_F=tcv * se_f, hw_G=tcv * se_g, se_A=se_b, se_F=se_f, se_G=se_g)
    if wild_B:
        gq_codes = pd.factorize(p.dropna(subset=['Y_cum', 'dlnFDI'] + W)['gq'])[0]
        out['W'] = wcr_pvalue(y, X, tix, gq_codes, truth, wild_B, rng_boot) > 0.05
    if boot:
        # khối dịch chuyển theo quý, dài ℓ = H (phần dư LP tích lũy chồng lấp MA(H−1))
        ell = H; nb = int(np.ceil(T / ell)); starts = np.arange(T - ell + 1)
        rows_by_t = [np.flatnonzero(tix == t) for t in range(T)]
        tstar = []
        for _ in range(B):
            seq = np.concatenate([np.arange(s, s + ell) for s in rng_boot.choice(starts, nb)])[:T]
            idx = np.concatenate([rows_by_t[t] for t in seq])
            newt = np.concatenate([np.full(len(rows_by_t[t]), k) for k, t in enumerate(seq)])
            # FE nhóm × quý-trong-năm tính lại trên mẫu bootstrap
            gq = p.dropna(subset=['Y_cum', 'dlnFDI'] + W)['gq'].to_numpy()[idx]
            Z = np.column_stack([y[idx], X[idx]])
            Z = Z - pd.DataFrame(Z).groupby(gq).transform('mean').to_numpy()
            bs, As, hs = ols_scores(Z[:, 0], Z[:, 1:], newt, T)
            tstar.append((bs[0] - b[0]) / se_from(As, meat_bartlett(hs, L)))
        lo, hi = np.quantile(tstar, [0.025, 0.975])
        out['E'] = (b[0] - hi * se_b) <= truth <= (b[0] - lo * se_b)
        out['hw_E'] = (hi - lo) / 2 * se_b
    return out


DGPS = {
    'iid': dict(rho_x=0.0, rho_c=0.0),                 # thiết kế của test_da2 (conf = 0)
    'persistent': dict(rho_x=0.5, rho_c=0.6),         # FDI và cú sốc chung tự tương quan
}

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--reps', type=int, default=1000)
    ap.add_argument('--boot-reps', type=int, default=300)
    ap.add_argument('--B', type=int, default=199)
    ap.add_argument('--T', type=int, default=56)
    ap.add_argument('--out', default='mc_inference.csv')
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--wild-B', type=int, default=399)
    ap.add_argument('--nshards', type=int, default=1)
    a = ap.parse_args()
    rng = np.random.default_rng(2026 + a.shard)
    res = []
    for name, dgp in DGPS.items():
        for s in range(a.shard, a.reps, a.nshards):
            r = one_rep(10_000 + s, dict(dgp, T=a.T), s < a.boot_reps, a.B, rng, a.wild_B)
            r['dgp'] = name; res.append(r)
    df = pd.DataFrame(res)
    df.to_csv(a.out, index=False)
    ms = [m for m in 'ABCDEFGW' if m in df]
    summ = df.groupby('dgp')[ms + [f'hw_{m}' for m in ms if f'hw_{m}' in df]].mean()
    summ['sd_beta'] = df.groupby('dgp').apply(lambda g: (g.beta - g.truth).std())
    summ['reps'] = df.groupby('dgp').size()
    print(summ.round(3).to_string())

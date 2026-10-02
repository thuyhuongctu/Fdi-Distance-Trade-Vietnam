"""Local projections IV trên bảng ngành × quý: FE hai chiều, sai số Driscoll–Kraay, khoảng tin cậy Anderson–Rubin.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.
"""
import numpy as np
import pandas as pd
from scipy import stats


def demean2(df, cols, i='sector', t='quarter', tol=1e-12, maxit=500):
    """Khử FE hai chiều bằng chiếu luân phiên (đúng cả khi bảng không cân)."""
    out = df[cols].astype(float).copy()
    for _ in range(maxit):
        prev = out.to_numpy().copy()
        out = out - out.groupby(df[i]).transform('mean')
        out = out - out.groupby(df[t]).transform('mean')
        if np.max(np.abs(out.to_numpy() - prev)) < tol:
            break
    return out


def dk_vcov(Xs, e, time, bw):
    """Driscoll–Kraay (1998): cộng điểm số theo kỳ, rồi Newey–West với độ trễ bw (trọng số Bartlett)."""
    h = pd.DataFrame(Xs * e[:, None]).groupby(np.asarray(time)).sum().sort_index().to_numpy()
    T = h.shape[0]
    S = h.T @ h
    for l in range(1, bw + 1):
        w = 1 - l / (bw + 1)
        G = h[l:].T @ h[:-l]
        S += w * (G + G.T)
    return S


def demean1(df, cols, fe):
    return df[cols].astype(float) - df[cols].astype(float).groupby(df[fe]).transform('mean')


def fixed_b_cv(b, level=0.95):
    """Giá trị tới hạn fixed-b cho t-test hai phía, nhân Bartlett (Kiefer & Vogelsang, 2005):
    cv(b) = z + 2.9694 b + 0.4160 b² − 0.5324 b³ ở mức 5%, b = (độ trễ + 1)/T."""
    assert level == 0.95
    return 1.959964 + 2.9694 * b + 0.4160 * b ** 2 - 0.5324 * b ** 3


def iv(df, y, x, z, w, bw, fe='gq', time='quarter'):
    """2SLS một biến nội sinh x, một công cụ z, kiểm soát w; khử FE `fe` (mặc định nhóm × quý-trong-năm)."""
    d = df.dropna(subset=[y, x, z] + w)
    D = demean1(d, [y, x, z] + w, fe) if fe else demean2(d, [y, x, z] + w)
    Y = D[y].to_numpy(); Xe = D[[x] + w].to_numpy(); Zf = D[[z] + w].to_numpy()
    # bước 1
    pi, *_ = np.linalg.lstsq(Zf, Xe[:, 0], rcond=None)
    v1 = Xe[:, 0] - Zf @ pi
    A = np.linalg.inv(Zf.T @ Zf)
    V1 = A @ dk_vcov(Zf, v1, d[time], bw) @ A
    F_eff = pi[0] ** 2 / V1[0, 0]                       # F hiệu dụng (một công cụ: = Wald vững của bước 1)
    Xh = Xe.copy(); Xh[:, 0] = Zf @ pi
    B = np.linalg.inv(Xh.T @ Xh)
    b = B @ Xh.T @ Y
    e = Y - Xe @ b
    V = B @ dk_vcov(Xh, e, d[time], bw) @ B
    # OLS cùng mẫu (báo cáo kèm như tương quan)
    Bo = np.linalg.inv(Xe.T @ Xe); bo = Bo @ Xe.T @ Y; eo = Y - Xe @ bo
    Vo = Bo @ dk_vcov(Xe, eo, d[time], bw) @ Bo
    T = d[time].nunique()
    return dict(beta=b[0], se=np.sqrt(V[0, 0]), F_eff=F_eff, n=len(d), T=T, bw=bw, cv=fixed_b_cv((bw + 1) / T),
                beta_ols=bo[0], se_ols=np.sqrt(Vo[0, 0]),
                ols_all={v: (float(bo[i]), float(np.sqrt(Vo[i, i]))) for i, v in enumerate([x] + w)},
                _D=D, _d=d, _time=time)


def ar_ci(res, y, x, z, w, bw, level=0.95, grid=None):
    """Tập tin cậy Anderson–Rubin: các β0 mà hệ số của z trong hồi quy (y − β0 x) ~ z + w không có ý nghĩa."""
    D, d = res['_D'], res['_d']
    crit = res['cv']                                   # cùng giá trị tới hạn fixed-b
    if grid is None:
        s = max(res['se'], 1e-6)
        grid = np.linspace(res['beta'] - 15 * s, res['beta'] + 15 * s, 601)
    Zf = D[[z] + w].to_numpy(); A = np.linalg.inv(Zf.T @ Zf)
    acc = []
    for b0 in grid:
        u = (D[y] - b0 * D[x]).to_numpy()
        g = A @ Zf.T @ u; e = u - Zf @ g
        V = A @ dk_vcov(Zf, e, d[res['_time']], bw) @ A
        if abs(g[0] / np.sqrt(V[0, 0])) < crit:
            acc.append(b0)
    if not acc:
        return dict(lo=None, hi=None, note='tập rỗng')
    unbounded = acc[0] == grid[0] or acc[-1] == grid[-1]
    return dict(lo=float(min(acc)), hi=float(max(acc)), note='chạm biên lưới – có thể không bị chặn' if unbounded else '')


def bw_rule(T, h=0):
    """Độ trễ Newey–West: max(⌊4(T/100)^(2/9)⌋, h + 1) vì phần dư LP chồng lấp có dạng MA(h)."""
    return max(int(np.floor(4 * (T / 100) ** (2 / 9))), h + 1)

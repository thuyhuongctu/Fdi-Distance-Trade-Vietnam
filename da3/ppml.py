"""PPML với hiệu ứng cố định dạng biến giả, sai số cụm và wild score bootstrap (Kline & Santos, 2012).

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Quy mô DA3 nhỏ (~25 nhóm × 60 tháng, ~400 biến giả) nên ước lượng IRLS trên ma trận đầy đủ là đủ nhanh
và minh bạch; kết quả đã được đối chiếu với pyfixest.fepois trong test_da3.py.
"""
import numpy as np
import pandas as pd


def design(df, xvars, fes):
    """Ma trận thiết kế: các biến giải thích + biến giả cho từng hiệu ứng cố định.
    Cột FE được trực giao hóa trước, biến giải thích sau: biến giải thích nằm trong không gian FE
    (hoặc cộng tuyến với nhau sau khi loại FE) thì báo lỗi thay vì âm thầm loại một cột FE."""
    F, fnames = [], []
    for fe in fes:
        d = pd.get_dummies(df[fe].astype(str), prefix=fe, dtype=float)
        F.append(d.to_numpy()); fnames += list(d.columns)
    cols = np.hstack(F + ([df[xvars].to_numpy(float)] if xvars else []))
    names = fnames + list(xvars)
    nf = len(fnames)
    keep, Q = [], None
    for j in range(cols.shape[1]):
        v = cols[:, [j]]
        if Q is not None:
            v = v - Q @ (Q.T @ v)
            v = v - Q @ (Q.T @ v)          # trực giao hóa lần hai cho ổn định số
        n = np.linalg.norm(v)
        if n > 1e-6 * max(1.0, np.linalg.norm(cols[:, j])):
            keep.append(j); q = v / n
            Q = q if Q is None else np.hstack([Q, q])
        elif j >= nf:
            raise ValueError(f'Biến giải thích «{names[j]}» cộng tuyến với các hiệu ứng cố định – mô hình không nhận dạng được')
    order = [j for j in keep if j >= nf] + [j for j in keep if j < nf]   # biến giải thích lên đầu
    return cols[:, order], [names[j] for j in order]


def fit(y, X, tol=1e-10, maxit=200):
    """PPML bằng IRLS. Trả về hệ số, giá trị kỳ vọng."""
    y = np.asarray(y, float)
    mu = np.where(y > 0, y, y.mean() + 1e-9) * 0.5 + y.mean() * 0.5
    eta = np.log(mu)
    b = None
    for _ in range(maxit):
        z = eta + (y - mu) / mu
        W = mu
        XtW = X.T * W
        b_new = np.linalg.solve(XtW @ X, XtW @ z)
        eta = X @ b_new; mu = np.exp(eta)
        if b is not None and np.max(np.abs(b_new - b)) < tol:
            b = b_new; break
        b = b_new
    return b, mu


def cluster_vcov(y, X, mu, cl):
    H = (X.T * mu) @ X
    Hi = np.linalg.inv(H)
    sc = X * (y - mu)[:, None]
    S = pd.DataFrame(sc).groupby(np.asarray(cl)).sum().to_numpy()
    G = S.shape[0]
    adj = G / (G - 1)
    return adj * Hi @ (S.T @ S) @ Hi


def estimate(df, y, xvars, fes, cluster):
    X, names = design(df, xvars, fes)
    b, mu = fit(df[y].to_numpy(float), X)
    V = cluster_vcov(df[y].to_numpy(float), X, mu, df[cluster].to_numpy())
    k = len(xvars)
    return pd.DataFrame({'coef': b[:k], 'se': np.sqrt(np.diag(V)[:k])}, index=xvars), V[:k, :k], dict(X=X, mu=mu, names=names)


WEBB = np.array([-np.sqrt(1.5), -1, -np.sqrt(0.5), np.sqrt(0.5), 1, np.sqrt(1.5)])


def score_bootstrap(df, y, test_vars, other_vars, fes, cluster, B=9999, seed=20261002, weights='webb'):
    """Wild score bootstrap (Kline & Santos, 2012) cho H0: hệ số của test_vars = 0, áp ràng buộc H0.
    Trả về p-value bootstrap của thống kê LM cụm-vững (kiểm định chung nếu nhiều biến)."""
    yv = df[y].to_numpy(float)
    Xr, _ = design(df, other_vars, fes)
    _, mu = fit(yv, Xr)                                   # mô hình ràng buộc
    D = df[test_vars].to_numpy(float)
    W = mu
    # phần dư có trọng số của biến kiểm định sau khi chiếu lên mô hình ràng buộc (FWL)
    P = np.linalg.solve((Xr.T * W) @ Xr, (Xr.T * W) @ D)
    Dt = D - Xr @ P
    u = yv - mu
    cl = np.asarray(df[cluster])
    Sg = pd.DataFrame(Dt * u[:, None]).groupby(cl).sum().to_numpy()     # G × q
    def lm(Sg):
        # phương sai cụm của điểm số, lấy tâm quanh trung bình cụm: thống kê không bị chặn trên bởi G
        # khi H0 sai (dạng không lấy tâm bị chặn ≤ G nên mất lực kiểm định với nhiều ràng buộc)
        s = Sg.sum(0)
        C = Sg - s / len(Sg)
        return float(s @ np.linalg.pinv(C.T @ C) @ s)
    T = lm(Sg)
    rng = np.random.default_rng(seed)
    G, q = Sg.shape
    v = rng.choice(WEBB, size=(B, G)) if weights == 'webb' else rng.choice([-1.0, 1.0], size=(B, G))
    # cùng một thống kê (điểm số, phương sai cụm lấy tâm, ước lượng lại) cho mẫu gốc và mỗi lần lặp
    Tb = np.array([lm(Sg * vb[:, None]) for vb in v])
    return float((1 + np.sum(Tb >= T)) / (B + 1)), T


def holm(p):
    p = np.asarray(p, float); m = len(p); o = np.argsort(p)
    adj = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, min(1, (m - r) * p[i])); adj[i] = run
    return adj

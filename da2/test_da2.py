"""Kiểm thử mã DA2 (thiết kế cú sốc FDI tổng) trên dữ liệu MÔ PHỎNG. © 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương."""
import numpy as np, pandas as pd
from da2_analysis import group_panel, lp_irf, ratio_trend, fixed_b_pvalue, H
from lp import dk_vcov, fixed_b_cv

PHI = np.array([0.10, 0.10, 0.05, 0.05])
TRUE_IRF = np.array([PHI[:h + 1].sum() for h in range(H)])
TRUE_CUM = TRUE_IRF.sum()


def simulate(G=25, T=56, pi=0.8, conf=0.6, seed=0, ratio_slope=-0.002):
    """Cú sốc chung x_t = π z_t + conf·c_t + v_t; c_t (không quan sát) cũng tác động trực tiếp đến thương mại → OLS chệch.
    w_t (nhu cầu thế giới, quan sát được) tác động cả x và thương mại."""
    r = np.random.default_rng(seed)
    qs = pd.period_range('2012Q3', periods=T, freq='Q').astype(str)
    z = r.normal(size=T); c = r.normal(size=T); wtv = r.normal(0, 1, T); reer = r.normal(0, 1, T)
    x = pi * z + conf * c + 0.3 * wtv + r.normal(size=T)
    fdi = pd.DataFrame(dict(quarter=qs, fdi_disb_sa=np.exp(5 + np.cumsum(x)), fdi_reg_sa=np.exp(5 + np.cumsum(x + r.normal(0, .3, T)))))
    inst = pd.DataFrame(dict(quarter=qs, Z=z, Z_noKOR=z + r.normal(0, .2, T), Z_2008=z + r.normal(0, .2, T)))
    ctrl = pd.DataFrame(dict(quarter=qs, d_wtv=wtv, d_lnreer=reer))
    rows = []
    for g in range(G):
        seas = r.normal(0, .1, 4); Y = r.normal(20, 1); Ym = Y - 0.2; slope = r.normal(0.01, 0.005)
        for t in range(T):
            if t:
                eff = sum(PHI[j] * x[t - j] for j in range(len(PHI)) if t - j >= 0)
                shock = slope + eff + 0.3 * c[t] + 0.2 * wtv[t] + r.normal(0, .05)
                Y += shock; Ym += shock
            qn = pd.Period(qs[t], 'Q').quarter
            sector = '26' if g < 3 else ('13-14' if g < 6 else 'other')
            rows.append(dict(direction='export', group_h=f'g{g}', sector=sector, role='output', quarter=qs[t], v=np.exp(Y + seas[qn - 1]), nm=3))
            rows.append(dict(direction='import', group_h=f'm{g}', sector=sector, role='input', quarter=qs[t],
                             v=np.exp(Y + seas[qn - 1]) * (0.9 + ratio_slope * t + r.normal(0, .01)), nm=3))
    return pd.DataFrame(rows), fdi, inst, ctrl


def panel(seed=0, d='export', **kw):
    q, fdi, inst, ctrl = simulate(seed=seed, **kw)
    return group_panel(q[q.direction == d], fdi, inst, ctrl)


def test_iv_recovers_irf_and_ols_is_biased():
    irf, cum = lp_irf(panel())
    z = np.abs(irf.beta.values - TRUE_IRF) / irf.se.values
    assert z.max() < 3.5, (irf.beta.values.round(3), irf.se.values.round(3))
    assert abs(cum['iv']['beta'] - TRUE_CUM) / cum['iv']['se'] < cum['cv'], cum['iv']
    assert cum['beta_ols'] > TRUE_CUM, cum['beta_ols']            # nhiễu c_t gây chệch OLS lên trên – lý do diễn giải là quan hệ, không phải nhân quả
    assert cum['iv']['F_eff'] > 10 and 0 <= cum['p_ols'] <= 1


def test_weak_instrument_flagged():
    assert lp_irf(panel(seed=3, pi=0.02))[1]['iv']['F_eff'] < 10


def test_fixed_b_coverage():
    """Độ phủ của khoảng β ± cv_fixed-b·se cho đáp ứng tích lũy (danh nghĩa 95%)."""
    cover = 0; N = 40
    for s in range(N):
        _, c = lp_irf(panel(seed=100 + s))
        cover += abs(c['iv']['beta'] - TRUE_CUM) / c['iv']['se'] < c['cv']
    print(f'    độ phủ fixed-b: {cover}/{N}')
    assert cover >= 0.85 * N, cover


def test_ar_contains_truth_usually():
    hit = 0
    for s in range(20):
        _, c = lp_irf(panel(seed=300 + s))
        a = c['iv']['ar95']; hit += a['lo'] is not None and a['lo'] <= TRUE_CUM <= a['hi']
    assert hit >= 17, hit


def test_ratio_trend():
    q, *_ = simulate(ratio_slope=-0.002)
    r = ratio_trend(q, '26'); assert r['b'] < 0 and r['p'] < 0.01, r
    q0, *_ = simulate(ratio_slope=0.0)
    assert abs(ratio_trend(q0, '26')['b']) < 0.001


def test_ols_coverage_without_confounding():
    cover = 0; N = 30
    for s in range(N):
        _, c = lp_irf(panel(seed=500 + s, conf=0.0))
        cover += abs(c['beta_ols'] - TRUE_CUM) / c['se_ols'] < c['cv']
    print(f'    độ phủ OLS fixed-b (không nhiễu): {cover}/{N}')
    assert cover >= 0.85 * N, cover


def test_confirmatory_runs_end_to_end():
    from da2_analysis import confirmatory, robustness
    q, fdi, inst, ctrl = simulate(seed=9)
    fdi['fdi_disb'] = fdi['fdi_disb_sa']
    out, px, pm = confirmatory(q, fdi, inst, ctrl)
    assert {'H1', 'H2', 'H3'} <= set(out) and isinstance(out['H1']['supported'], bool)
    rb = robustness(q, fdi, inst, ctrl, px, pm)
    assert {'R2_excl_covid', 'R5_leads', 'R6_not_seasonally_adjusted'} <= set(rb)


def test_fixed_b_pvalue_matches_cv():
    for b in (0.05, 0.15):
        assert abs(fixed_b_pvalue(fixed_b_cv(b), b) - 0.05) < 0.006


def test_dk_equals_white_with_bw0():
    rr = np.random.default_rng(1); X = rr.normal(size=(50, 2)); e = rr.normal(size=50)
    assert np.allclose(dk_vcov(X, e, np.arange(50), 0), (X * e[:, None]).T @ (X * e[:, None]))


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f(); print('PASS', n)

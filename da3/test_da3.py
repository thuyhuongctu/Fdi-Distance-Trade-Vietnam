"""Kiểm thử mã DA3 trên dữ liệu MÔ PHỎNG (không dùng số liệu Hải quan). © 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương."""
import numpy as np, pandas as pd
import pyfixest as pf
from da3_analysis import add_time, window, did, event_study, rr_bounds, MAIN
from ppml import estimate, holm


def simulate(delta=0.10, pretrend=0.0, G=24, seed=1):
    r = np.random.default_rng(seed)
    months = pd.period_range('2013-01', '2020-12', freq='M').astype(str)
    exp = r.normal(size=G); exp = (exp - exp.mean()) / exp.std(ddof=1)
    rows = []
    for g in range(G):
        a = r.normal(18, 1); seas = r.normal(0, .1, 12)
        for i, m in enumerate(months):
            t = pd.Period(m, 'M')
            post = m >= '2018-07'
            trend = pretrend * exp[g] * (i - 66) / 12   # xu hướng khác biệt kéo dài cả trước và sau
            mu = np.exp(a + 0.01 * i + seas[t.month - 1] + delta * exp[g] * post + trend + r.normal(0, 0.05))
            rows.append(dict(group=f'g{g:02d}', period=m, X=r.gamma(20, mu / 20), M=r.gamma(20, mu / 20) * 0.8,
                             EXP=exp[g], EXP_l13=exp[g] * .7, EXP_4a=exp[g] * .3))
    return add_time(pd.DataFrame(rows))


def test_point_estimate_matches_pyfixest():
    p = window(simulate(), *MAIN); p['D'] = p.EXP * (p.period >= '2018-07')
    res, _, _ = estimate(p, 'X', ['D'], ['group', 'period', 'grp_cal'], 'group')
    f = pf.fepois('X ~ D | group + period + grp_cal', data=p, vcov={'CRV1': 'group'})
    assert abs(res.loc['D', 'coef'] - f.coef()['D']) < 1e-6, (res.loc['D', 'coef'], f.coef()['D'])
    assert abs(res.loc['D', 'se'] / f.se()['D'] - 1) < 0.05, (res.loc['D', 'se'], f.se()['D'])


def test_recovers_effect_and_rejects():
    r = did(window(simulate(delta=0.10), *MAIN), 'X', B=999)
    assert abs(r['coef'] - 0.10) < 0.03 and r['p_boot'] < 0.01, r


def test_null_not_rejected_often():
    rej = sum(did(window(simulate(delta=0.0, seed=s), *MAIN), 'X', B=199)['p_boot'] < 0.05 for s in range(20))
    assert rej <= 4, rej   # kích thước kiểm định ≈ 5%; cho phép dao động khi chỉ có 20 lần lặp


def test_event_study_pretrend():
    _, ok = event_study(window(simulate(delta=0.1), *MAIN), 'X', B=199)
    assert ok['p_boot'] > 0.10, ok
    es, bad = event_study(window(simulate(delta=0.1, pretrend=0.15), *MAIN), 'X', B=199)
    assert bad['lin_p_boot'] < 0.05, bad      # kiểm định tuyến tính phát hiện vi phạm
    assert len(rr_bounds(es)) == 4


def test_pretrend_size():
    r = [event_study(window(simulate(delta=0.1, seed=s), *MAIN), 'X', B=199)[1] for s in range(20)]
    assert sum(x['p_boot'] < 0.10 for x in r) <= 5, [x['p_boot'] for x in r]       # mức 10%: kỳ vọng ~2/20
    assert sum(x['lin_p_boot'] < 0.10 for x in r) <= 5, [x['lin_p_boot'] for x in r]


def test_matches_pyfixest_event_study():
    from da3_analysis import REF_K
    w = window(simulate(), *MAIN); names = []
    for k in sorted(k for k in w.k.unique() if k not in REF_K):
        n = f'k{k + 20}'; w[n] = w.EXP * (w.k == k); names.append(n)
    res, _, _ = estimate(w, 'X', names, ['group', 'period', 'grp_cal'], 'group')
    f = pf.fepois('X ~ ' + '+'.join(names) + ' | group + period + grp_cal', data=w, vcov={'CRV1': 'group'})
    assert np.allclose(res.coef.values, f.coef()[names].values, atol=1e-6)


def test_underidentified_spec_is_caught():
    w = window(simulate(), *MAIN); names = []
    for k in sorted(k for k in w.k.unique() if k != -1):
        n = f'k{k + 20}'; w[n] = w.EXP * (w.k == k); names.append(n)
    try:
        estimate(w, 'X', names, ['group', 'period', 'grp_cal'], 'group'); assert False
    except ValueError:
        pass


def test_holm():
    assert np.allclose(holm([0.01, 0.04]), [0.02, 0.04])
    assert np.allclose(holm([0.03, 0.02]), [0.04, 0.04])


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn(); print('PASS', name)

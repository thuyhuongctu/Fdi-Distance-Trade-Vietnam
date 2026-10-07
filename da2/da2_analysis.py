"""DA2 – Phân tích xác nhận theo Phần 5 bản tiền đăng ký DA2 (thiết kế sửa 10/2026):
FDI giải ngân toàn quốc → thương mại khu vực FDI theo nhóm hàng × quý. Xác nhận: local projections OLS có
biến kiểm soát (quan hệ động có điều kiện, không diễn giải nhân quả); suy diễn bằng wild cluster bootstrap-t theo quý
có áp H0 (WCR, Webb, B = 9.999) – chọn qua mc_inference.py; DK fixed-b báo cáo kèm. Khám phá: LP-IV với công cụ shift-share
(bước 1 yếu, F ≈ 1 – xem Phần 4). H3: xu hướng tỷ lệ NK/XK.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Đầu vào (xem README.md):
  ../da0/monthly_harmonised.csv – chuỗi Hải quan đã hài hòa
  sector_map.csv                – nhóm hàng: vai trò output/input/excluded và ngành (cho H3)
  inputs/fdi_quarter.csv        – quarter, fdi_disb_sa (giải ngân, đã hiệu chỉnh mùa vụ), fdi_reg_sa (đăng ký)
  inputs/instrument.csv         – quarter, Z, Z_noKOR, Z_2008
  inputs/controls.csv           – quarter, d_wtv (tăng trưởng log khối lượng NK thế giới), d_lnreer
DA2 được đăng ký riêng, sau DA3. Chỉ chạy trên dữ liệu thật sau khi tiền đăng ký DA2 đã nộp:
  python3 da2_analysis.py --registered <DOI_DA2>
Trước khi nộp DA2, đối chiếu ../disclosure_log.csv để khai báo trong Phần 4 các kết quả DA3 đã thấy.
"""
import argparse, json, sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import t as tdist, norm
from lp import iv, ar_ci, bw_rule, wcr, wcr_ci

H = 8
H3_SECTORS = ['26', '13-14']
END_Q = '2026Q2'
ELEC = ['Máy vi tính, sản phẩm điện tử và linh kiện', 'Điện thoại các loại và linh kiện', 'Máy ảnh, máy quay phim và linh kiện']
CTRL = ['d_wtv', 'd_wtv_l1', 'd_wtv_l2', 'd_lnreer', 'd_lnreer_l1', 'd_lnreer_l2']


def quarterly(monthly_h, smap):
    m = monthly_h.merge(smap[smap.role != 'excluded'], on=['direction', 'group_h'])
    m['quarter'] = pd.PeriodIndex(m['period'], freq='M').asfreq('Q').astype(str)
    q = m.groupby(['direction', 'group_h', 'sector', 'role', 'quarter'], as_index=False).agg(
        v=('value_usd_month', 'sum'), nm=('period', 'nunique'))
    q.loc[q.nm < 3, 'v'] = np.nan                    # quý thiếu tháng → NA, không lấp
    return q[q.quarter <= END_Q]


def group_panel(q, fdi, inst, ctrl, treat='fdi_disb_sa', z='Z'):
    """Bảng nhóm × quý cho một chiều (export: X, import: M)."""
    a = fdi[['quarter', treat]].merge(inst[['quarter', z]], on='quarter').merge(ctrl, on='quarter').sort_values('quarter')
    a['dlnFDI'] = np.log(a[treat]).diff()
    for c in ('dlnFDI', 'd_wtv', 'd_lnreer'):
        a[f'{c}_l1'] = a[c].shift(1); a[f'{c}_l2'] = a[c].shift(2)
    a = a.rename(columns={z: 'Z'})
    p = q.merge(a, on='quarter').sort_values(['group_h', 'quarter']).reset_index(drop=True)
    p['Y'] = np.log(p['v'])
    g = p.groupby('group_h')
    p['dY'] = g['Y'].diff(); p['dY_l1'] = g['dY'].shift(1); p['dY_l2'] = g['dY'].shift(2)
    lag = g['Y'].shift(1)
    for h in range(H):
        p[f'Y_h{h}'] = g['Y'].shift(-h) - lag
    hs = [f'Y_h{h}' for h in range(H)]
    p['Y_cum'] = p[hs].sum(axis=1, min_count=H)
    p['gq'] = p['group_h'] + '_' + pd.PeriodIndex(p['quarter'], freq='Q').quarter.astype(str)
    return p


def lp_irf(p, wild=True, B=9999, B_ci=1999):
    w = ['dY_l1', 'dY_l2', 'dlnFDI_l1', 'dlnFDI_l2'] + CTRL
    T = p.quarter.nunique()
    rows = []
    for h in range(H):
        r = iv(p, f'Y_h{h}', 'dlnFDI', 'Z', w, bw_rule(T, h))
        rows.append(dict(h=h, beta=r['beta'], se=r['se'], cv=r['cv'], F_eff=r['F_eff'], beta_ols=r['beta_ols'], se_ols=r['se_ols'], n=r['n']))
    c = iv(p, 'Y_cum', 'dlnFDI', 'Z', w, bw_rule(T, H - 1))
    ar = ar_ci(c, 'Y_cum', 'dlnFDI', 'Z', w, c['bw'])
    tstat = c['beta'] / c['se']
    # p-value fixed-b: tìm mức α mà giá trị tới hạn bằng |t| (nghịch đảo số của bảng xấp xỉ, dựa trên t ~ chuẩn ở b → 0)
    p_fb = fixed_b_pvalue(abs(tstat), (c['bw'] + 1) / c['T'])
    t_ols = c['beta_ols'] / c['se_ols']
    p_wcr, t_cr1 = wcr(c, 'Y_cum', 'dlnFDI', w, B=B) if wild else (np.nan, np.nan)
    cum = dict(beta_ols=c['beta_ols'], se_ols=c['se_ols'], t_ols=t_ols, cv=c['cv'],
               p_wcr=p_wcr, t_cr1=t_cr1,                                            # xác nhận (WCR theo quý)
               ci95_wcr=wcr_ci(c, 'Y_cum', 'dlnFDI', w, B=B_ci) if wild else None,
               p_ols=fixed_b_pvalue(abs(t_ols), (c['bw'] + 1) / c['T']),           # DK fixed-b, báo cáo kèm
               iv=dict(beta=c['beta'], se=c['se'], t=tstat, p=p_fb, F_eff=c['F_eff'], ar95=ar),  # khám phá
               n=c['n'], T=c['T'], bw=c['bw'])
    return pd.DataFrame(rows), cum


def fixed_b_pvalue(t, b, sims=20000, T=200, seed=7):
    """p-value fixed-b (Kiefer & Vogelsang, 2005), nhân Bartlett, bằng mô phỏng mô hình vị trí:
    e_t ~ N(0,1) i.i.d., t = √T·ē / √Ω̂, Ω̂ Bartlett với độ trễ M = b·T trên phần dư e − ē."""
    r = np.random.default_rng(seed)
    e = r.normal(size=(sims, T))
    m = e.mean(1); u = e - m[:, None]
    M = max(1, int(round(b * T)))
    v = (u ** 2).mean(1)
    for l in range(1, M):
        v += 2 * (1 - l / M) * (u[:, l:] * u[:, :-l]).sum(1) / T
    tsim = np.sqrt(T) * m / np.sqrt(v)
    return float((np.abs(tsim) >= t).mean())


def ratio_trend(q, sector):
    d = q[q.sector == sector].groupby(['quarter', 'role'])['v'].sum(min_count=1).unstack('role').dropna()
    d['R'] = d['input'] / d['output']
    d = d.reset_index()
    d['t'] = np.arange(len(d))
    qd = pd.get_dummies(pd.PeriodIndex(d.quarter, freq='Q').quarter, prefix='q', drop_first=True, dtype=float)
    X = sm.add_constant(pd.concat([d[['t']], qd], axis=1))
    m = sm.OLS(d['R'].to_numpy(), X).fit(cov_type='HAC', cov_kwds={'maxlags': 4})
    return dict(b=float(m.params['t']), se=float(m.bse['t']), p=float(m.pvalues['t']), n=int(m.nobs))


def holm(pv):
    pv = np.asarray(pv, float); o = np.argsort(pv); m = len(pv); out = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, min(1, (m - r) * pv[i])); out[i] = run
    return out


def confirmatory(q, fdi, inst, ctrl, B=9999, B_ci=1999):
    px = group_panel(q[q.direction == 'export'], fdi, inst, ctrl)
    pm = group_panel(q[q.direction == 'import'], fdi, inst, ctrl)
    irfX, cX = lp_irf(px, B=B, B_ci=B_ci); irfM, cM = lp_irf(pm, B=B, B_ci=B_ci)
    h3 = {s: ratio_trend(q, s) for s in H3_SECTORS}
    p_h3 = max(v['p'] for v in h3.values())
    adj = holm([cX['p_wcr'], cM['p_wcr'], p_h3])
    out = dict(H1=dict(**cX, p_holm=adj[0], supported=bool(cX['beta_ols'] > 0 and adj[0] < 0.05)),
               H2=dict(**cM, p_holm=adj[1], supported=bool(cM['beta_ols'] > 0 and adj[1] < 0.05)),
               H3=dict(by_sector=h3, p_max=p_h3, p_holm=adj[2],
                       supported=bool(all(v['b'] < 0 for v in h3.values()) and adj[2] < 0.05)))
    out['irf_X'] = irfX.to_dict('records'); out['irf_M'] = irfM.to_dict('records')
    return out, px, pm


def with_leads(p):
    p = p.copy()
    lead = p.groupby('group_h')['dlnFDI'].shift
    p['dlnFDI_f1'] = lead(-1); p['dlnFDI_f2'] = lead(-2)
    return p


def robustness(q, fdi, inst, ctrl, px, pm, B=9999, B_ci=1999):
    import lp
    irf = lambda p: lp_irf(p, B=B, B_ci=B_ci)
    rb = {}
    covid = lambda p: p[~((p.quarter >= '2020Q2') & (p.quarter <= '2021Q4'))]
    rb['R2_excl_covid'] = {'X': irf(covid(px))[1], 'M': irf(covid(pm))[1]}
    rb['R3_excl_electronics'] = {'X': irf(px[~px.group_h.isin(ELEC)])[1], 'M': irf(pm[~pm.group_h.isin(ELEC)])[1]}
    rb['R4_registered_fdi'] = {k: irf(group_panel(q[q.direction == d], fdi, inst, ctrl, treat='fdi_reg_sa'))[1]
                               for k, d in (('X', 'export'), ('M', 'import'))}
    # R5: hai giá trị tương lai của ΔlnFDI phải có hệ số 0 (kiểm tra kỳ vọng trước / thứ tự ngược)
    w = ['dY_l1', 'dY_l2', 'dlnFDI_l1', 'dlnFDI_l2', 'dlnFDI_f1', 'dlnFDI_f2'] + CTRL
    rb['R5_leads'] = {}
    for k, p in (('X', px), ('M', pm)):
        r = lp.iv(with_leads(p), 'Y_cum', 'dlnFDI', 'Z', w, bw_rule(p.quarter.nunique(), H - 1))
        rb['R5_leads'][k] = dict(beta_ols=r['beta_ols'], se_ols=r['se_ols'],
                                 lead1=r['ols_all']['dlnFDI_f1'], lead2=r['ols_all']['dlnFDI_f2'], cv=r['cv'])
    # R6: FDI chưa hiệu chỉnh mùa vụ (FE nhóm × quý-trong-năm hấp thụ mùa vụ)
    rb['R6_not_seasonally_adjusted'] = {k: irf(group_panel(q[q.direction == d], fdi, inst, ctrl, treat='fdi_disb'))[1]
                                        for k, d in (('X', 'export'), ('M', 'import'))}
    # R1 (tần suất tháng) chạy bằng da2_monthly.py khi đã có chuỗi FDI tháng
    return rb


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--registered')
    ap.add_argument('--monthly', default='../da0/monthly_harmonised.csv')
    ap.add_argument('--map', default='sector_map.csv')
    ap.add_argument('--inputs', default='inputs')
    ap.add_argument('--out', default='da2_results.json')
    a = ap.parse_args()
    if not a.registered:
        sys.exit('Dừng: cần DOI tiền đăng ký DA2 trước khi chạy phân tích xác nhận (Phần 4).')
    q = quarterly(pd.read_csv(a.monthly), pd.read_csv(a.map, dtype={'sector': str}))
    fdi, inst, ctrl = (pd.read_csv(f'{a.inputs}/{f}.csv') for f in ('fdi_quarter', 'instrument', 'controls'))
    out, px, pm = confirmatory(q, fdi, inst, ctrl)
    out['robustness'] = robustness(q, fdi, inst, ctrl, px, pm)
    out['registration'] = dict(DA2=a.registered)
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: out[k] for k in ('H1', 'H2', 'H3', 'weak_iv')}, ensure_ascii=False, indent=1, default=str))

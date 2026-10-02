"""DA3 – Phân tích xác nhận và kiểm định độ vững, đúng Phần 5 bản tiền đăng ký DA3.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

DA3 được đăng ký RIÊNG và TRƯỚC DA2. Chỉ chạy trên dữ liệu thật sau khi tiền đăng ký DA3 đã nộp:
    python3 da3_analysis.py --registered <DOI_DA3>
Không có DOI, script dừng. Mỗi lần chạy được ghi vào ../disclosure_log.csv để Phần 4 tiền đăng ký DA2
liệt kê đúng những kết quả DA3 đã thấy trước khi DA2 nộp. Phân tích khám phá sau 02/2020 (Phần 5)
chỉ chạy sau khi DA2 đã đăng ký. Kiểm thử trên dữ liệu mô phỏng: python3 test_da3.py
"""
import argparse, json, sys
import numpy as np
import pandas as pd
from ppml import estimate, score_bootstrap, holm

MAIN = ('2015-01', '2019-12')
EVENT_Q = '2018Q3'          # k = 0
# Quý tham chiếu của nghiên cứu sự kiện: bốn quý ngay trước thuế (2017Q3–2018Q2).
# Với FE nhóm × tháng-lịch, mỗi quý-lịch tạo một quan hệ cộng tuyến giữa EXP×1[k] và FE,
# nên phải bỏ một quý cho MỖI quý-lịch (xem ghi chú sửa tiền đăng ký).
REF_K = (-4, -3, -2, -1)
PHONES = 'Điện thoại các loại và linh kiện'


def build_panel(monthly_h, exposure, inputs):
    """Bảng nhóm XK g × tháng m với X_gm, M_gm (tổng các nhóm NK khớp), EXP_g chuẩn hóa."""
    e = exposure[exposure['da3_rule'] == 'include'].copy()
    x = monthly_h[monthly_h.direction == 'export'].rename(columns={'group_h': 'group'})
    x = x[x['group'].isin(e['export_group'])][['group', 'period', 'value_usd_month']].rename(columns={'value_usd_month': 'X'})
    m = monthly_h[monthly_h.direction == 'import'][['group_h', 'period', 'value_usd_month']]
    m = inputs.merge(m, left_on='import_group', right_on='group_h').groupby(['export_group', 'period'], as_index=False)['value_usd_month'].sum()
    m = m.rename(columns={'export_group': 'group', 'value_usd_month': 'M'})
    p = x.merge(m, on=['group', 'period'], how='left')
    p = p.merge(e[['export_group', 'exp_raw', 'exp_l13', 'exp_4a']].rename(columns={'export_group': 'group'}), on='group')
    sd = e['exp_raw'].std(ddof=1)
    p['EXP'] = (p['exp_raw'] - e['exp_raw'].mean()) / sd          # chuẩn hóa: trung bình 0, độ lệch chuẩn 1
    p['EXP_l13'] = p['exp_l13'] / sd                               # tách theo danh sách (kiểm định R3), cùng thang đo
    p['EXP_4a'] = p['exp_4a'] / sd
    return add_time(p)


def add_time(p):
    t = pd.PeriodIndex(p['period'], freq='M')
    p['cal_month'] = t.month
    p['quarter'] = t.asfreq('Q')
    p['k'] = (p['quarter'] - pd.Period(EVENT_Q, 'Q')).map(lambda d: d.n)
    p['grp_cal'] = p['group'] + '_' + p['cal_month'].astype(str)
    return p


def window(p, a, b):
    return p[(p.period >= a) & (p.period <= b)].copy()


def did(p, y, treat='EXP', post_from='2018-07', B=9999, extra=None):
    d = p.dropna(subset=[y]).copy()
    d['POST'] = (d.period >= post_from).astype(float)
    d['D'] = d[treat] * d['POST']
    xv = ['D'] + (extra or [])
    res, _, _ = estimate(d, y, xv, ['group', 'period', 'grp_cal'], 'group')
    pb, _ = score_bootstrap(d, y, ['D'], extra or [], ['group', 'period', 'grp_cal'], 'group', B=B)
    r = res.loc['D']
    return dict(coef=r.coef, se=r.se, p_boot=pb, pct_per_sd=100 * (np.exp(r.coef) - 1), n=len(d), groups=d.group.nunique())


def event_study(p, y, B=9999):
    d = p.dropna(subset=[y]).copy()
    ks = sorted(k for k in d.k.unique() if k not in REF_K)
    names = []
    for k in ks:
        n = f'k{k:+d}'; d[n] = d['EXP'] * (d.k == k); names.append(n)
    res, V, _ = estimate(d, y, names, ['group', 'period', 'grp_cal'], 'group')
    pre = [n for n, k in zip(names, ks) if k < min(REF_K)]
    b = res.loc[pre, 'coef'].to_numpy(); idx = [names.index(n) for n in pre]
    Vp = V[np.ix_(idx, idx)]
    wald = float(b @ np.linalg.pinv(Vp) @ b)
    from scipy.stats import chi2
    p_wald = float(chi2.sf(wald, len(pre)))
    p_boot, _ = score_bootstrap(d, y, pre, [n for n in names if n not in pre], ['group', 'period', 'grp_cal'], 'group', B=B)
    res['k'] = ks
    lin = linear_pretrend(p, y, B=B)
    return res, dict(pre_wald=wald, df=len(pre), p_wald=p_wald, p_boot=p_boot, **lin)


def linear_pretrend(p, y, B=9999):
    """Kiểm định 1 bậc tự do: xu hướng tuyến tính khác biệt theo EXP trong giai đoạn trước thuế
    (01/2015–06/2018). Bổ sung cho kiểm định chung vì kiểm định chung nhiều ràng buộc với ~25 cụm có lực thấp."""
    d = p[(p.period < '2018-07')].dropna(subset=[y]).copy()
    d['TREND'] = d['EXP'] * d['k'] / 4.0          # theo năm
    res, _, _ = estimate(d, y, ['TREND'], ['group', 'period', 'grp_cal'], 'group')
    pb, _ = score_bootstrap(d, y, ['TREND'], [], ['group', 'period', 'grp_cal'], 'group', B=B)
    return dict(lin_trend=float(res.loc['TREND', 'coef']), lin_se=float(res.loc['TREND', 'se']), lin_p_boot=pb)


def rr_bounds(es, Mbar=(0.5, 1.0, 1.5, 2.0), z=1.96):
    """Cận độ nhạy kiểu 'độ lớn tương đối' (Rambachan & Roth, 2023), bản xấp xỉ bảo thủ:
    độ dốc vi phạm xu hướng song song sau sự kiện ≤ M̄ × |thay đổi lớn nhất giữa hai quý liền kề trước sự kiện|.
    Bản chính thức trong bài báo sẽ dùng gói HonestDiD (R); hàm này dùng để kiểm tra nhanh."""
    pre = es[es.k < 0].sort_values('k')
    pre_full = pd.concat([pre, pd.DataFrame({'coef': [0.0] * len(REF_K), 'k': list(REF_K)})]).sort_values('k')
    jump = np.abs(np.diff(pre_full['coef'].to_numpy())).max()
    post = es[es.k >= 0]
    out = []
    for M in Mbar:
        bias = (post['k'] + 1) * M * jump
        lo = (post['coef'] - bias - z * post['se']).mean(); hi = (post['coef'] + bias + z * post['se']).mean()
        out.append(dict(Mbar=M, avg_post=post['coef'].mean(), lo=lo, hi=hi, excludes_zero=bool(lo > 0 or hi < 0)))
    return pd.DataFrame(out)


def run(p, B=9999):
    w = window(p, *MAIN)
    out = {}
    h1 = did(w, 'X', B=B); h2 = did(w, 'M', B=B)
    adj = holm([h1['p_boot'], h2['p_boot']])
    h1['p_holm'], h2['p_holm'] = adj
    h1['supported'] = bool(h1['coef'] > 0 and h1['p_holm'] < 0.05)
    h2['supported'] = bool(h2['coef'] > 0 and h2['p_holm'] < 0.05)
    es, pre = event_study(w, 'X', B=B)
    pre['H3_parallel_not_rejected'] = bool(pre['p_boot'] >= 0.10 and pre['lin_p_boot'] >= 0.10)
    out['H1'], out['H2'], out['H3'] = h1, h2, pre
    out['event_study_X'] = es.reset_index(names='term').to_dict('records')
    out['event_study_M'] = event_study(w, 'M', B=B)[0].reset_index(names='term').to_dict('records')
    out['rr_bounds_X'] = rr_bounds(es).to_dict('records')
    # Kiểm định độ vững (Phần 5)
    rb = {}
    terc = w.groupby('group')['EXP'].first()
    lo, hi = terc.quantile(1 / 3), terc.quantile(2 / 3)
    wb = w[(w.EXP <= lo) | (w.EXP >= hi)].copy(); wb['EXPB'] = (wb.EXP >= hi).astype(float)
    rb['R1_binary_tercile'] = {y: did(wb, y, treat='EXPB', B=B) for y in ('X', 'M')}
    rb['R2_ols_log'] = {y: ols_log(w, y) for y in ('X', 'M')}
    rb['R3_staggered_by_list'] = {y: staggered(w, y) for y in ('X', 'M')}
    rb['R4_excl_phones'] = {y: did(w[w.group != PHONES], y, B=B) for y in ('X', 'M')}
    rb['R5_placebo_2017_07'] = {y: did(window(p, '2015-01', '2018-06'), y, post_from='2017-07', B=B) for y in ('X', 'M')}
    rb['R6_window_to_2020_02'] = {y: did(window(p, '2015-01', '2020-02'), y, B=B) for y in ('X', 'M')}
    out['robustness'] = rb
    return out


def ols_log(w, y):
    import statsmodels.formula.api as smf
    d = w[w[y] > 0].copy(); d['ly'] = np.log(d[y]); d['D'] = d['EXP'] * (d.period >= '2018-07')
    m = smf.ols('ly ~ D + C(period) + C(grp_cal) + C(group)', d).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.group)[0]})
    return dict(coef=m.params['D'], se=m.bse['D'], p=m.pvalues['D'], n=int(m.nobs))


def staggered(w, y):
    d = w.dropna(subset=[y]).copy()
    d['D13'] = d['EXP_l13'] * (d.period >= '2018-07')
    d['D4A'] = d['EXP_4a'] * (d.period >= '2019-09')
    res, _, _ = estimate(d, y, ['D13', 'D4A'], ['group', 'period', 'grp_cal'], 'group')
    return res.to_dict('index')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--registered', help='DOI tiền đăng ký DA3 (bắt buộc với dữ liệu thật)')
    ap.add_argument('--monthly', default='../da0/monthly_harmonised.csv')
    ap.add_argument('--exposure', default='exposure.csv')
    ap.add_argument('--inputs', default='input_match.csv')
    ap.add_argument('--out', default='da3_results.json')
    a = ap.parse_args()
    if not a.registered:
        sys.exit('Dừng: cần DOI tiền đăng ký DA3 trước khi chạy phân tích xác nhận (Phần 4).')
    p = build_panel(pd.read_csv(a.monthly), pd.read_csv(a.exposure), pd.read_csv(a.inputs))
    res = run(p)
    res['registration'] = dict(DA3=a.registered)
    import datetime, os
    log = '../disclosure_log.csv'
    new = not os.path.exists(log)
    with open(log, 'a', encoding='utf-8') as f:
        if new:
            f.write('time,study,doi,window,outputs\n')
        f.write(f'{datetime.datetime.now().isoformat(timespec="seconds")},DA3,{a.registered},{MAIN[0]}..2020-02,'
                f'"H1-H3; event study X,M; R1-R6 (FDI-sector X, M by product group)"\n')
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: res[k] for k in ('H1', 'H2', 'H3')}, ensure_ascii=False, indent=1, default=str))

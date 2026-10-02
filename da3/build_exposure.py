"""DA3 – Chỉ số mức độ chịu thuế Section 301 của từng nhóm hàng (EXP_g), cố định trước khi xem kết quả.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

EXP_g = Σ_{h ∈ g, h bị đánh thuế} V_h × t_h  /  Σ_{h ∈ g} V_h
  V_h : nhập khẩu của Mỹ từ Trung Quốc năm 2017 (UN Comtrade, USD), HS6
  t_h : thuế suất bổ sung cuối 2019 (danh sách 1–3: 25%; 4A: 15%), trung bình các dòng HTS8 trong HS6
Mẫu số lấy từ tổng HS4 (cả dòng không bị đánh thuế) và các HS6 thuộc nhóm.
Nguồn danh sách: USITC, «China Tariffs» (cập nhật 28/07/2026) – xem giới hạn trong README.
"""
import glob
import pandas as pd

conc = pd.read_csv('hs_concordance.csv', dtype=str)
tar = pd.read_csv('section301_hts8.csv', dtype={'hts8': str})
tar['hs6'] = tar['hts8'].str[:6]
ct = pd.concat([pd.read_csv(f, dtype={'cmdCode': str}) for f in sorted(glob.glob('comtrade/part_*.csv'))])
v4 = ct[ct.cmdCode.str.len() == 4].set_index('cmdCode')['primaryValue']
v6 = ct[ct.cmdCode.str.len() == 6].set_index('cmdCode')['primaryValue']

t6 = tar.groupby('hs6').agg(rate=('rate_2019', 'mean'),
                            l13=('list', lambda s: (s.astype(str).isin(['1', '2', '3'])).mean()),
                            l4a=('list', lambda s: (s.astype(str) == '4A').mean()),
                            n8=('hts8', 'size'))
rows = []
for g, d in conc.groupby('export_group', sort=False):
    h4 = d[d.level == 'HS4'].hs.tolist(); h6m = d[d.level == 'HS6'].hs.tolist()
    denom = v4.reindex(h4).fillna(0).sum() + v6.reindex(h6m).fillna(0).sum()
    cov = t6[t6.index.str[:4].isin(h4) | t6.index.isin(h6m)].copy()
    cov['V'] = v6.reindex(cov.index).fillna(0)
    rows.append(dict(export_group=g, da3_rule=d.da3_rule.iloc[0], us_imp_cn_2017=denom,
                     covered_value=cov.V.sum(), coverage_share=cov.V.sum() / denom if denom else None,
                     exp_raw=(cov.V * cov.rate / 100).sum() / denom if denom else None,
                     exp_l13=(cov.V * cov.rate / 100 * cov.l13).sum() / denom if denom else None,
                     exp_4a=(cov.V * cov.rate / 100 * cov.l4a).sum() / denom if denom else None,
                     n_hs6_covered=int((cov.V > 0).sum())))
e = pd.DataFrame(rows)
inc = e.da3_rule == 'include'
e['exp_std'] = None
e.loc[inc, 'exp_std'] = (e.loc[inc, 'exp_raw'] - e.loc[inc, 'exp_raw'].mean()) / e.loc[inc, 'exp_raw'].std(ddof=1)
e.to_csv('exposure.csv', index=False, encoding='utf-8-sig')
# Kiểm tra: tổng mẫu số so với tổng NK Mỹ từ TQ 2017 (USD 525,8 tỷ theo AG2)
print(f"Mẫu số các nhóm: {e.us_imp_cn_2017.sum()/1e9:,.1f} tỷ USD; phần bị đánh thuế: {e.covered_value.sum()/e.us_imp_cn_2017.sum():.1%}")
print(e.sort_values('exp_raw', ascending=False)[['export_group', 'da3_rule', 'us_imp_cn_2017', 'coverage_share', 'exp_raw', 'exp_std']].to_string(
    formatters={'us_imp_cn_2017': lambda x: f'{x/1e9:,.1f}', 'coverage_share': '{:.2f}'.format, 'exp_raw': '{:.3f}'.format}))

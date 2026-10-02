"""DA2 – Dựng ba tệp đầu vào (biến tác động, công cụ, biến kiểm soát) từ dữ liệu thô công khai.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Không dùng số liệu kết quả (Hải quan). Đầu vào trong inputs/raw/ (mỗi giá trị có nguồn và trích dẫn):
  fdi_vn_quarterly.csv     – quarter, variable, value_usd_bn, vintage, …
  fdi_stock_by_source.csv  – as_of, iso3, registered_usd_m, …
  ofdi_quarterly.csv       – iso3, quarter, ofdi_usd_m, …
  controls_monthly.csv     – month, wtv_import_volume, reer_vn, …
Đầu ra: inputs/fdi_quarter.csv, inputs/instrument.csv, inputs/controls.csv, inputs/build_log.txt
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

RAW = 'inputs/raw'
SOURCES = ['JPN', 'KOR', 'SGP', 'CHN', 'HKG', 'TWN', 'USA']
log = []


def ytd_to_flow(s):
    """Lũy kế từ đầu năm (cuối quý) → dòng quý. Thiếu một quý trong năm → các quý phụ thuộc để NA."""
    s = s.sort_index()
    out = {}
    for q, v in s.items():
        p = pd.Period(q, 'Q')
        if p.quarter == 1:
            out[q] = v
        else:
            prev = str(p - 1)
            out[q] = v - s[prev] if prev in s.index and pd.notna(s[prev]) else np.nan
    return pd.Series(out)


def stl_sa(s):
    s = s.dropna()
    res = STL(np.log(s.values), period=4, robust=True).fit()
    return pd.Series(np.exp(res.trend + res.resid), index=s.index)


def build_fdi():
    r = pd.read_csv(f'{RAW}/fdi_vn_quarterly.csv')
    r = r[(r.vintage == 'first') & ~r.source_name.astype(str).str.startswith('ALTERNATIVE SOURCE')]   # số GSO công bố lần đầu
    out = pd.DataFrame(index=sorted(r.quarter.unique()))
    # R4 dùng vốn đăng ký CẤP MỚI: thước đo vốn đăng ký duy nhất được công bố nhất quán 2012–2026
    # (tổng vốn đăng ký gồm góp vốn chỉ có từ 2016–2017 và định nghĩa đổi theo thời gian)
    for var, col in (('disbursed_ytd', 'fdi_disb'), ('registered_new_ytd', 'fdi_reg')):
        s = r[r.variable == var].drop_duplicates('quarter').set_index('quarter')['value_usd_bn']
        f = ytd_to_flow(s)
        out[col] = f
        bad = f[f <= 0]
        if len(bad):
            log.append(f'{col}: dòng quý ≤ 0 tại {list(bad.index)} – kiểm tra số lũy kế')
        out[f'{col}_sa'] = stl_sa(f[f > 0])
        log.append(f'{col}: {f.notna().sum()} quý có số, thiếu {list(f[f.isna()].index)}')
    out.index.name = 'quarter'
    return out.reset_index()


def build_instrument():
    st = pd.read_csv(f'{RAW}/fdi_stock_by_source.csv')
    of = pd.read_csv(f'{RAW}/ofdi_quarterly.csv')
    w = of.pivot_table(index='quarter', columns='iso3', values='ofdi_usd_m').sort_index()
    ms = w.rolling(4, min_periods=4).sum()                      # tổng trượt 4 quý (dòng vốn thất thường)
    if (ms <= 0).any().any():
        log.append('Tổng trượt 4 quý ≤ 0 ở: ' + str(ms[(ms <= 0).any(axis=1)].index.tolist()) + ' → dùng tăng trưởng đối xứng')
    # Tăng trưởng đối xứng (Davis, Haltiwanger & Schuh, 1996): xác định cả khi dòng vốn âm (rút vốn), bị chặn trong [−2, 2]
    g = ms.diff() / (0.5 * (ms.abs() + ms.shift().abs()))
    out = pd.DataFrame(index=g.index)
    for name, as_of, drop in (('Z', '2012-12-31', []), ('Z_noKOR', '2012-12-31', ['KOR']), ('Z_2008', '2008-12-31', [])):
        s = st[(st.as_of == as_of) & st.iso3.isin(SOURCES) & ~st.iso3.isin(drop)].set_index('iso3')['registered_usd_m']
        sh = s / s.sum()
        log.append(f'{name}: tỷ trọng ' + ', '.join(f'{k} {v:.3f}' for k, v in sh.items()))
        out[name] = (g[sh.index] * sh).sum(axis=1, min_count=len(sh))   # thiếu một nguồn → NA, không bù
    out.index.name = 'quarter'
    return out.reset_index()


def build_controls():
    c = pd.read_csv(f'{RAW}/controls_monthly.csv')
    c['quarter'] = pd.PeriodIndex(c['month'], freq='M').asfreq('Q').astype(str)
    q = c.groupby('quarter').agg(wtv=('wtv_import_volume', 'mean'), reer=('reer_vn', 'mean'), n=('month', 'nunique'))
    q = q[q.n == 3]
    return pd.DataFrame({'quarter': q.index, 'd_wtv': np.log(q.wtv).diff().values, 'd_lnreer': np.log(q.reer).diff().values})


if __name__ == '__main__':
    fdi = build_fdi(); fdi.to_csv('inputs/fdi_quarter.csv', index=False)
    z = build_instrument(); z.to_csv('inputs/instrument.csv', index=False)
    ctrl = build_controls(); ctrl.to_csv('inputs/controls.csv', index=False)
    open('inputs/build_log.txt', 'w', encoding='utf-8').write('\n'.join(log) + '\n')
    print('\n'.join(log))
    print(f'fdi {len(fdi)} quý; instrument {z.dropna().shape[0]} quý đủ; controls {ctrl.dropna().shape[0]} quý đủ')

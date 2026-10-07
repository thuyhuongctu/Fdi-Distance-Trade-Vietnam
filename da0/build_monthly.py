"""DA0 – Từ panel_flat.csv dựng bảng tháng sạch 2013–2026 và kiểm tra cộng dồn.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Bước:
  1. Loại tệp trùng (cùng kỳ, cùng chiều, cùng nội dung) và tệp tải nhầm (tiêu đề ghi tháng khác kỳ trong biểu).
  2. Kiểm tra cộng dồn: YTD(m) − YTD(m−1) = giá trị tháng m, cho từng dòng (cả tiểu mục).
  3. Bù tháng thiếu bằng hiệu cộng dồn khi có YTD của tháng sau và tháng trước (đánh dấu imputed_from_ytd).
Chạy: python3 build_monthly.py
"""
import re
import pandas as pd

p = pd.read_csv('panel_flat.csv')
log = []

# 1. Kỳ ghi trên tên tệp vs kỳ in trong biểu
def title_period(t):
    m = re.search(r'(\d{4})-T(\d{1,2})', t)
    return f'{int(m.group(1)):04d}-{int(m.group(2)):02d}' if m else ''
p['title_period'] = p['source_title'].map(title_period)
mis = p[p['title_period'] != p['period']]['source_title'].unique()
for t in mis:
    log.append(dict(check='mislabelled_upload', file=t, detail=f'Tên tệp ghi {title_period(t)} nhưng biểu in kỳ khác → loại; tháng {title_period(t)} coi là thiếu'))
p = p[~p['source_title'].isin(mis)]
# trùng nội dung
keep = p.drop_duplicates(['period', 'direction', 'text_sha256_16'])[['period', 'direction', 'source_title']].drop_duplicates()
dup = keep.groupby(['period', 'direction']).size()
for (per, d), n in dup[dup > 1].items():
    log.append(dict(check='conflicting_versions', file=f'{per} {d}', detail=f'{n} phiên bản khác nội dung'))
first = p.groupby(['period', 'direction'])['source_title'].transform('min')
dropped = p.loc[p['source_title'] != first, 'source_title'].unique()
for t in dropped:
    log.append(dict(check='duplicate_file', file=t, detail='Bản sao cùng kỳ → loại'))
p = p[p['source_title'] == first].copy()

# 2. Kiểm tra cộng dồn
p['year'] = p['period'].str[:4].astype(int)
p['month'] = p['period'].str[5:].astype(int)
key = ['direction', 'year', 'level', 'parent', 'product_group', 'unit']
p['parent'] = p['parent'].fillna('')
p = p.sort_values(key + ['month'])
g = p.groupby(key)
p['prev_month'] = g['month'].shift()
p['prev_ytd'] = g['value_usd_ytd'].shift()
chk = p[(p['month'] > 1) & (p['prev_month'] == p['month'] - 1) & p['value_usd_month'].notna() & p['prev_ytd'].notna()].copy()
chk['gap'] = chk['value_usd_ytd'] - chk['prev_ytd'] - chk['value_usd_month']
chk['rel'] = chk['gap'].abs() / chk['value_usd_ytd'].clip(lower=1)
bad = chk[chk['rel'] > 0.005]
for _, r in bad.iterrows():
    log.append(dict(check='ytd_inconsistent', file=r['source_title'],
                    detail=f"{r['level']} «{r['product_group']}»: YTD−YTDtrước−tháng = {r['gap']:,.0f} ({r['rel']:.2%})"))
print(f'Kiểm tra cộng dồn: {len(chk)} cặp, {len(bad)} lệch >0,5% '
      f'(trong đó tổng: {(bad.level=="total").sum()}, nhóm: {(bad.level=="group").sum()}, tiểu mục: {(bad.level=="subitem").sum()})')

# 3. Bù tháng thiếu từ cộng dồn
out = p.drop(columns=['prev_month', 'prev_ytd', 'title_period'])
out['imputed_from_ytd'] = 0
add = []
for (d, y), grp in out.groupby(['direction', 'year']):
    months = set(grp['month'])
    for m in range(1, 13):
        if m in months or (m + 1) not in months:
            continue
        nxt = grp[grp.month == m + 1]
        prv = grp[grp.month == m - 1] if m > 1 else None
        for _, r in nxt.iterrows():
            ytd_m = None
            # YTD tháng m = YTD(m+1) − tháng(m+1)
            if pd.notna(r['value_usd_ytd']) and pd.notna(r['value_usd_month']):
                ytd_m = r['value_usd_ytd'] - r['value_usd_month']
            prev_ytd = 0 if m == 1 else None
            if prv is not None:
                q = prv[(prv['product_group'] == r['product_group']) & (prv['level'] == r['level']) & (prv['parent'] == r['parent'])]
                if len(q):
                    prev_ytd = q['value_usd_ytd'].iloc[0]
            if ytd_m is None or prev_ytd is None or pd.isna(prev_ytd):
                continue
            n = r.copy()
            n['period'] = f'{y:04d}-{m:02d}'; n['month'] = m
            n['value_usd_ytd'] = ytd_m; n['value_usd_month'] = ytd_m - prev_ytd
            n['qty_month'] = n['qty_ytd'] = None
            n['imputed_from_ytd'] = 1
            n['limitation'] = f'{n["limitation"]}; tháng thiếu biểu, suy từ cộng dồn'
            n['source_title'] = f'(suy từ cộng dồn {r["period"]} − {y:04d}-{m-1:02d})'
            add.append(n)
        if add and add[-1]['period'] == f'{y:04d}-{m:02d}' and add[-1]['direction'] == d:
            log.append(dict(check='imputed_month', file=f'{y}-{m:02d} {d}', detail='Tháng thiếu file; suy từ chênh lệch cộng dồn tháng sau và tháng trước'))
out = pd.concat([out, pd.DataFrame(add)], ignore_index=True).sort_values(['direction', 'period', 'level'])
# Giá trị tháng theo hiệu cộng dồn: hấp thụ các lần Hải quan điều chỉnh số tháng trước
out = out.sort_values(key + ['month'])
gg = out.groupby(key)
prev = gg['value_usd_ytd'].shift()
pm = gg['month'].shift()
out['value_usd_month_ytddiff'] = (out['value_usd_ytd'] - prev).where(pm == out['month'] - 1)
out.loc[out['month'] == 1, 'value_usd_month_ytddiff'] = out['value_usd_ytd']
out = out.sort_values(['direction', 'period', 'level'])
out.to_csv('monthly_clean.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(log).to_csv('cleaning_log_monthly.csv', index=False, encoding='utf-8-sig')
tot = out[out.level == 'total']
cov = tot.groupby('direction')['period'].agg(['nunique', 'min', 'max'])
print(cov)
print('Tháng suy từ cộng dồn:', sorted(set(tot.loc[tot.imputed_from_ytd == 1, 'period'] + ' ' + tot.loc[tot.imputed_from_ytd == 1, 'direction'])))

"""DA0 – Hài hòa danh mục nhóm hàng 2013–2026 thành rổ nhất quán.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Quy tắc (mọi thay đổi đều ghi vào harmonise_map.csv):
  R1  Đổi tên thuần túy (cùng phạm vi) → gộp về tên chuẩn.
  R2  Nhóm mới tách ra từ 2024 (Hải quan mở rộng danh mục) → cộng vào «Hàng hóa khác» trong chuỗi hài hòa;
      chuỗi chi tiết vẫn giữ nguyên.
  R3  Từ 2026-03, biểu dùng mẫu mới: các dòng không đánh số là dòng ghi nhớ (memo), không cộng vào tổng;
      «Kim loại thường khác» (STT 28) được ghép với dòng ghi nhớ «Sản phẩm từ kim loại thường khác»
      để giữ phạm vi «Kim loại thường khác và sản phẩm», và dòng ghi nhớ đó được trừ khỏi «Hàng hóa khác».
Kiểm tra: tổng các nhóm hài hòa = dòng tổng ở mọi tháng.
Chạy: python3 harmonise.py  (sau build_monthly.py)
"""
import pandas as pd

p = pd.read_csv('monthly_clean.csv')
p['parent'] = p['parent'].fillna('')

RENAME = {
    ('export', 'Túi xách, ví,vali, mũ và ô dù'): 'Túi xách, ví,vali, mũ, ô, dù',
}
NEW_2024 = {
    'export': ['Hạt điều', 'Thức ăn gia súc và nguyên liệu', 'Nguyên phụ liệu dệt, may, da, giày',
               'Sản phẩm mây, tre, cói và thảm', 'Sản phẩm nội thất từ chất liệu khác gỗ', 'Vải mành, vải kỹ thuật khác'],
    'import': ['Dầu thô', 'Máy ảnh, máy quay phim và linh kiện', 'Quặng và khoáng sản khác', 'Than các loại',
               'Ô tô nguyên chiếc các loại'],
}
OTHER = 'Hàng hóa khác'
KLTK, KLTK_STD, KLTK_MEMO = 'Kim loại thường khác', 'Kim loại thường khác và sản phẩm', 'Sản phẩm từ kim loại thường khác'

g = p[p.level == 'group'].copy()
mp = []
g['group_h'] = g['product_group']
for (d, old), new in RENAME.items():
    m = (g.direction == d) & (g.product_group == old)
    g.loc[m, 'group_h'] = new
    mp.append(dict(direction=d, product_group=old, group_h=new, rule='R1 đổi tên', periods=f'{g.loc[m,"period"].min()}–{g.loc[m,"period"].max()}'))
for d, names in NEW_2024.items():
    for n in names:
        m = (g.direction == d) & (g.product_group == n)
        g.loc[m, 'group_h'] = OTHER
        mp.append(dict(direction=d, product_group=n, group_h=OTHER, rule='R2 nhóm mới 2024 → Hàng hóa khác', periods=f'{g.loc[m,"period"].min()}–{g.loc[m,"period"].max()}'))

# R3: mẫu biểu 2026-03 trở đi (export)
new_layout = (g.direction == 'export') & (g.period >= '2026-03')
memo = p[(p.direction == 'export') & (p.period >= '2026-03') & (p.item_no.isna()) & (p.level == 'subitem') & (p.product_group == KLTK_MEMO)]
memo = memo.set_index('period')[['value_usd_month', 'value_usd_ytd', 'value_usd_month_ytddiff']]
adj = []
for per, r in memo.iterrows():
    for name, sign in ((KLTK, 1), (OTHER, -1)):
        m = new_layout & (g.period == per) & (g.product_group == name)
        for c in ('value_usd_month', 'value_usd_ytd', 'value_usd_month_ytddiff'):
            g.loc[m, c] = g.loc[m, c] + sign * r[c]
g.loc[new_layout & (g.product_group == KLTK), 'group_h'] = KLTK_STD
mp.append(dict(direction='export', product_group=f'{KLTK} (+ dòng ghi nhớ {KLTK_MEMO})', group_h=KLTK_STD, rule='R3 mẫu biểu 2026-03: cộng dòng ghi nhớ, trừ khỏi Hàng hóa khác', periods='2026-03–'))

cols = ['direction', 'period', 'year', 'month', 'status', 'group_h']
h = g.groupby(cols, as_index=False)[['value_usd_month', 'value_usd_ytd', 'value_usd_month_ytddiff']].sum(min_count=1)
h['imputed_from_ytd'] = g.groupby(cols)['imputed_from_ytd'].max().values

# Kiểm tra cộng
tot = p[p.level == 'total'].set_index(['direction', 'period'])['value_usd_month']
s = h.groupby(['direction', 'period'])['value_usd_month'].sum()
gap = (s - tot).abs()
print('Tháng có tổng nhóm hài hòa ≠ dòng tổng (>2 USD):', int((gap > 2).sum()), '/', len(gap))
for d in ('export', 'import'):
    k = h[h.direction == d]
    full = k.groupby('group_h')['period'].nunique()
    print(d, 'số nhóm hài hòa:', len(full), '; đủ mọi tháng:', int((full == k.period.nunique()).sum()))

# Kiểm tra gãy chuỗi: tỷ trọng «Hàng hóa khác» quanh 2024-01 và 2026-03
for d in ('export', 'import'):
    sh = (h[(h.direction == d) & (h.group_h == OTHER)].set_index('period')['value_usd_month'] / tot.loc[d]).dropna()
    print(d, 'tỷ trọng Hàng hóa khác:', {k: round(v, 3) for k, v in sh.loc['2023-11':'2024-03'].items()}, {k: round(v, 3) for k, v in sh.loc['2026-01':'2026-05'].items()})

h.to_csv('monthly_harmonised.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(mp).to_csv('harmonise_map.csv', index=False, encoding='utf-8-sig')

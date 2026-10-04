"""Kiểm thử build_panel.py trên dữ liệu giả lập (không phải số thật)."""
import os, tempfile
import numpy as np, pandas as pd
from scipy.spatial.distance import mahalanobis
import build_panel as B

rng = np.random.default_rng(0)
iso = ['VNM', 'JPN', 'KOR', 'SGP', 'USA', 'DEU', 'FRA', 'CHN', 'THA', 'HKG', 'XXX']
d = tempfile.mkdtemp()
fdi = pd.DataFrame([(i, y, float(rng.choice([0, rng.gamma(2, 300)]))) for i in iso[1:] for y in B.YEARS if not (i == 'XXX')], columns=['iso3', 'year', 'fdi_usd_m'])
fdi.loc[(fdi.iso3 == 'FRA'), 'fdi_usd_m'] = 0; fdi.loc[(fdi.iso3 == 'FRA') & (fdi.year == 2010), 'fdi_usd_m'] = 50  # có FDI 1 năm
fdi = fdi[~((fdi.iso3 == 'JPN') & (fdi.year == 2012))]   # thiếu dòng → phải lấp 0
fdi.to_csv(f'{d}/fdi_registered.csv', index=False)
pd.DataFrame({'iso3': [], 'year': [], 'position_usd_m': []}).to_csv(f'{d}/imf_cdis.csv', index=False)
pd.DataFrame([(i, y, rng.uniform(1e10, 2e13), rng.uniform(1e3, 7e4)) for i in iso for y in B.YEARS], columns=['iso3', 'year', 'gdp_usd', 'gdppc_usd']).to_csv(f'{d}/wdi.csv', index=False)
pd.DataFrame([(i, y, *rng.normal(0, 1, 6)) for i in iso for y in B.YEARS], columns=['iso3', 'year', *B.WGI_DIMS]).to_csv(f'{d}/wgi.csv', index=False)
hof = pd.DataFrame([(i, *rng.uniform(10, 90, 6)) for i in iso], columns=['iso3', *B.HOF_DIMS]); hof.to_csv(f'{d}/hofstede.csv', index=False)
pd.DataFrame({'iso3': iso[1:], 'distw_km': rng.uniform(800, 14000, len(iso) - 1), 'contig': 0}).to_csv(f'{d}/cepii_dist.csv', index=False)
pd.DataFrame({'iso3': ['JPN', 'KOR', 'JPN'], 'fta_name': ['AJCEP', 'AKFTA', 'VJEPA'], 'in_force_year': [2008, 2007, 2009]}).to_csv(f'{d}/fta.csv', index=False)
pd.DataFrame({'iso3': ['HKG']}).to_csv(f'{d}/ofc_list.csv', index=False)

panel, log = B.build(d)
# 1. Mẫu: 9 nền kinh tế có FDI (không có VNM, không có XXX) × 19 năm; dòng thiếu được lấp 0
assert set(panel.iso3) == set(iso[1:-1]) and len(panel) == 9 * 19
assert panel.loc[(panel.iso3 == 'JPN') & (panel.year == 2012), 'fdi_usd_m'].item() == 0
# 2. Mahalanobis khớp scipy
S_inv = np.linalg.pinv(np.cov(hof[B.HOF_DIMS].to_numpy(float), rowvar=False))
ref = hof.loc[hof.iso3 == 'VNM', B.HOF_DIMS].to_numpy(float)[0]
x = hof.loc[hof.iso3 == 'JPN', B.HOF_DIMS].to_numpy(float)[0]
assert abs(panel.loc[panel.iso3 == 'JPN', 'cult_dist'].iloc[0] - mahalanobis(x, ref, S_inv)) < 1e-9
# 3. FTA: năm hiệu lực sớm nhất
assert panel.loc[(panel.iso3 == 'JPN') & (panel.year == 2007), 'fta'].item() == 0
assert panel.loc[(panel.iso3 == 'JPN') & (panel.year == 2008), 'fta'].item() == 1
assert panel.loc[panel.iso3 == 'USA', 'fta'].sum() == 0
# 4. Cờ OFC, mẫu 2019, hạng tương tác tâm hóa
assert panel.loc[panel.iso3 == 'HKG', 'ofc'].eq(1).all() and panel.loc[panel.iso3 == 'JPN', 'ofc'].eq(0).all()
assert panel.loc[panel.iso3 == 'FRA', 'in_2019_sample'].eq(1).all()
assert abs(panel['inst_dist_c'].mean()) < 1e-12
assert (panel['fta_x_inst'] == panel['fta'] * panel['inst_dist_c']).all()
# 5. Bổ sung GDP cho nền kinh tế WDI không có (wdi_supplement.csv), không ghi đè WDI
w = pd.read_csv(f'{d}/wdi.csv')
w[w.iso3 != 'KOR'].to_csv(f'{d}/wdi.csv', index=False)
sup = pd.DataFrame([('KOR', y, 1e12, 3e4, 'test') for y in B.YEARS] + [('JPN', y, 1.0, 1.0, 'test') for y in B.YEARS],
                   columns=['iso3', 'year', 'gdp_usd', 'gdppc_usd', 'source'])
sup.to_csv(f'{d}/wdi_supplement.csv', index=False)
p2, _ = B.build(d)
assert np.allclose(p2.loc[p2.iso3 == 'KOR', 'ln_gdp'], np.log(1e12))
assert (p2.loc[p2.iso3 == 'JPN', 'ln_gdp'].values == panel.loc[panel.iso3 == 'JPN', 'ln_gdp'].values).all()
# 6. Chưa có tệp FDI: chỉ dựng biến giải thích cho mọi nền kinh tế có số liệu, cột FDI để trống
os.remove(f'{d}/fdi_registered.csv'); os.remove(f'{d}/imf_cdis.csv')
p3, _ = B.build(d)
assert set(p3.iso3) == set(iso[1:]) and p3['fdi_usd_m'].isna().all()
assert (p3.loc[p3.iso3 == 'JPN', 'cult_dist'].values == panel.loc[panel.iso3 == 'JPN', 'cult_dist'].values).all()
print('Tất cả kiểm thử đạt.', len(panel), 'quan sát; thiếu:', log)

"""DA1 – Dựng bảng dữ liệu quốc gia đầu tư × năm cho mô hình lực hấp dẫn FDI (2006–2024).

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Bám đúng Phần 3 (Variables) và quy tắc chọn mẫu của bản tiền đăng ký DA1:
  - Mọi nền kinh tế có FDI đăng ký vào Việt Nam ít nhất một năm; năm không có = 0.
  - Trung tâm tài chính hải ngoại (danh sách IMF) tách khỏi mẫu chính (cờ `ofc`).
  - Khoảng cách văn hóa / thể chế = khoảng cách Mahalanobis tới Việt Nam (Berry et al., 2010).
  - Khoảng cách kinh tế = |ln GDP/người_j − ln GDP/người_VN|.

Tệp đầu vào (CSV, UTF-8) đặt trong thư mục `inputs/` – xem README.md.
Chạy: python build_panel.py --inputs inputs --out da1_panel.csv
"""
import argparse
import numpy as np
import pandas as pd

VN = 'VNM'
WGI_DIMS = ['va', 'pv', 'ge', 'rq', 'rl', 'cc']          # 6 khía cạnh WGI
HOF_DIMS = ['pdi', 'idv', 'mas', 'uai', 'lto', 'ivr']    # 6 khía cạnh Hofstede
YEARS = range(2006, 2025)
# 16 nước trong mẫu của Phan & Đỗ (2019), Bảng 1 – dùng cho kiểm định cầu nối R5
SAMPLE_2019 = {'KOR', 'TWN', 'HKG', 'MYS', 'CHN', 'SGP', 'JPN', 'THA', 'DEU', 'FRA', 'NLD', 'RUS', 'GBR', 'USA', 'CAN', 'AUS'}


def mahalanobis_to(df, dims, ref_iso):
    """Khoảng cách Mahalanobis từ mỗi nước tới nước tham chiếu, ma trận hiệp phương sai
    ước lượng trên toàn bộ các nước có đủ số liệu (Berry, Guillén & Zhou, 2010)."""
    d = df.dropna(subset=dims)
    if ref_iso not in set(d['iso3']):
        raise ValueError(f'Thiếu số liệu của {ref_iso} cho {dims}')
    X = d[dims].to_numpy(float)
    S_inv = np.linalg.pinv(np.cov(X, rowvar=False))
    ref = d.loc[d['iso3'] == ref_iso, dims].to_numpy(float)[0]
    diff = X - ref
    dist = np.sqrt(np.einsum('ij,jk,ik->i', diff, S_inv, diff))
    return pd.Series(dist, index=d['iso3'].values)


def kogut_singh_to(df, dims, ref_iso):
    """Chỉ số Kogut–Singh (1988), dùng cho kiểm định độ vững 3."""
    d = df.dropna(subset=dims)
    var = d[dims].var(ddof=1)
    ref = d.loc[d['iso3'] == ref_iso, dims].iloc[0]
    ks = ((d[dims] - ref) ** 2 / var).sum(axis=1) / len(dims)
    return pd.Series(ks.values, index=d['iso3'].values)


def build(inp):
    fdi = pd.read_csv(f'{inp}/fdi_registered.csv')            # iso3, year, fdi_usd_m
    cdis = pd.read_csv(f'{inp}/imf_cdis.csv')                 # iso3, year, position_usd_m (tùy chọn)
    wdi = pd.read_csv(f'{inp}/wdi.csv')                       # iso3, year, gdp_usd, gdppc_usd
    wgi = pd.read_csv(f'{inp}/wgi.csv')                       # iso3, year, va, pv, ge, rq, rl, cc
    hof = pd.read_csv(f'{inp}/hofstede.csv')                  # iso3, pdi, idv, mas, uai, lto, ivr
    geo = pd.read_csv(f'{inp}/cepii_dist.csv')                # iso3, distw_km, contig  (khoảng cách tới VNM)
    fta = pd.read_csv(f'{inp}/fta.csv')                       # iso3, fta_name, in_force_year
    ofc = set(pd.read_csv(f'{inp}/ofc_list.csv')['iso3'])     # danh sách trung tâm tài chính hải ngoại

    # Mẫu: mọi nền kinh tế có FDI đăng ký > 0 ít nhất một năm; lấp 0 cho năm trống
    ever = sorted(set(fdi.loc[fdi['fdi_usd_m'] > 0, 'iso3']) - {VN})
    panel = pd.MultiIndex.from_product([ever, list(YEARS)], names=['iso3', 'year']).to_frame(index=False)
    panel = panel.merge(fdi, on=['iso3', 'year'], how='left')
    panel['fdi_usd_m'] = panel['fdi_usd_m'].fillna(0.0)
    panel = panel.merge(cdis, on=['iso3', 'year'], how='left')

    # Quy mô và khoảng cách kinh tế
    w = wdi.copy()
    w['ln_gdp'] = np.log(w['gdp_usd'])
    w['ln_gdppc'] = np.log(w['gdppc_usd'])
    vn = w.loc[w['iso3'] == VN, ['year', 'ln_gdppc']].rename(columns={'ln_gdppc': 'ln_gdppc_vn'})
    panel = panel.merge(w[['iso3', 'year', 'ln_gdp', 'ln_gdppc']], on=['iso3', 'year'], how='left')
    panel = panel.merge(vn, on='year', how='left')
    panel['econ_dist'] = (panel['ln_gdppc'] - panel['ln_gdppc_vn']).abs()

    # Khoảng cách thể chế: Mahalanobis theo từng năm (WGI thay đổi theo năm)
    inst = []
    for y, g in wgi.groupby('year'):
        m = mahalanobis_to(g, WGI_DIMS, VN)
        k = kogut_singh_to(g, WGI_DIMS, VN)
        inst.append(pd.DataFrame({'iso3': m.index, 'year': y, 'inst_dist': m.values, 'inst_dist_ks': k.reindex(m.index).values}))
    panel = panel.merge(pd.concat(inst), on=['iso3', 'year'], how='left')

    # Khoảng cách văn hóa: Mahalanobis, cố định theo thời gian
    cd = mahalanobis_to(hof, HOF_DIMS, VN).rename('cult_dist')
    cdk = kogut_singh_to(hof, HOF_DIMS, VN).rename('cult_dist_ks')
    panel = panel.merge(pd.concat([cd, cdk], axis=1).rename_axis('iso3').reset_index(), on='iso3', how='left')

    # Khoảng cách địa lý
    geo = geo.assign(ln_dist=np.log(geo['distw_km']))
    panel = panel.merge(geo[['iso3', 'ln_dist', 'contig']], on='iso3', how='left')

    # FTA có hiệu lực (lấy năm có hiệu lực sớm nhất nếu có nhiều hiệp định)
    first = fta.groupby('iso3')['in_force_year'].min()
    panel['fta'] = (panel['year'] >= panel['iso3'].map(first).fillna(9999)).astype(int)

    # Chuẩn hóa: chuẩn hóa thể chế về trung bình 0 cho hạng tương tác (Model 2)
    panel['inst_dist_c'] = panel['inst_dist'] - panel['inst_dist'].mean()
    panel['fta_x_inst'] = panel['fta'] * panel['inst_dist_c']
    panel['ofc'] = panel['iso3'].isin(ofc).astype(int)
    panel['in_2019_sample'] = panel['iso3'].isin(SAMPLE_2019).astype(int)

    # Nhật ký mẫu: số quan sát bị loại do thiếu số liệu, theo biến (Phần 3, quy tắc 3–4)
    need = ['ln_dist', 'cult_dist', 'inst_dist', 'econ_dist', 'ln_gdp']
    log = {v: int(panel[v].isna().sum()) for v in need}
    return panel, log


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--inputs', default='inputs')
    ap.add_argument('--out', default='da1_panel.csv')
    a = ap.parse_args()
    panel, log = build(a.inputs)
    panel.to_csv(a.out, index=False)
    print(f'{len(panel)} quan sát, {panel.iso3.nunique()} nền kinh tế, {int((panel.fdi_usd_m == 0).sum())} quan sát FDI = 0')
    print('Thiếu số liệu theo biến:', log)

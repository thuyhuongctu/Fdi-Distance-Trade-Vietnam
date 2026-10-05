"""DA1 – Tải và chuẩn hóa bốn nguồn biến giải thích: WGI, CEPII GeoDist, WTO RTA, danh sách OFC của IMF.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương. Giấy phép MIT.

Chạy từ thư mục da1/:  python3 fetch_inputs.py
Tệp tải về lưu ở inputs/raw/ (không đưa lên repo); đầu ra: inputs/wgi.csv, inputs/cepii_dist.csv,
inputs/fta.csv, inputs/ofc_list.csv. Không suy diễn, không nội suy: thiếu thì để trống. Nguồn và quy tắc: inputs/sources_c.md.
"""
import html
import os
import re
import urllib.request
import zipfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'inputs', 'raw')
OUT = os.path.join(HERE, 'inputs')
YEARS = (2005, 2024)

URL = {
    'wgi': 'https://www.worldbank.org/content/dam/sites/govindicators/doc/wgidataset_with_sourcedata-2026.dta',
    'cepii': 'https://www.cepii.fr/distance/dist_cepii.zip',
    'rta': 'https://rtais.wto.org/UI/ExportAllRTAList.aspx',
    'ofc': 'https://www.imf.org/external/np/mae/oshore/2000/eng/back.htm',
    'weo_gdp': 'https://www.imf.org/external/datamapper/api/v1/NGDPD/TWN',
    'weo_gdppc': 'https://www.imf.org/external/datamapper/api/v1/NGDPDPC/TWN',
}
FILE = {'wgi': 'wgi2026.dta', 'cepii': 'dist_cepii.zip', 'rta': 'AllRTAs.xlsx', 'ofc': 'imf_ofc_2000.html',
        'weo_gdp': 'weo_NGDPD_TWN.json', 'weo_gdppc': 'weo_NGDPDPC_TWN.json'}


def get(key):
    path = os.path.join(RAW, FILE[key])
    if not os.path.exists(path):
        os.makedirs(RAW, exist_ok=True)
        req = urllib.request.Request(URL[key], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=600) as r, open(path, 'wb') as f:
            f.write(r.read())
    return path


def wgi():
    d = pd.read_stata(get('wgi'))
    d = d[d['wgi_year'].between(*YEARS)]
    w = d.pivot_table(index=['econ_code', 'wgi_year'], columns='dimension', values='estimate').reset_index()
    w.columns.name = None
    w = w.rename(columns={'econ_code': 'iso3', 'wgi_year': 'year'}).astype({'year': int})
    return w[['iso3', 'year', 'va', 'pv', 'ge', 'rq', 'rl', 'cc']].sort_values(['iso3', 'year'])


def cepii():
    with zipfile.ZipFile(get('cepii')) as z:
        z.extract('dist_cepii.xls', RAW)
    d = pd.read_excel(os.path.join(RAW, 'dist_cepii.xls'), na_values=['.'])
    v = d[(d['iso_d'] == 'VNM') & (d['iso_o'] != 'VNM')].copy()
    # Mã CEPII cũ → ISO3 hiện hành; Nam Tư (YUG) gán cho cả Serbia và Montenegro (cùng một giá trị)
    v['iso3'] = v['iso_o'].replace({'ROM': 'ROU', 'ZAR': 'COD', 'TMP': 'TLS', 'PAL': 'PSE'})
    yug = v[v['iso_o'] == 'YUG']
    v = pd.concat([v[v['iso_o'] != 'YUG'], yug.assign(iso3='SRB'), yug.assign(iso3='MNE')])
    v = v.rename(columns={'iso_o': 'cepii_code', 'distw': 'distw_km', 'dist': 'dist_km'})
    for c in ('distw_km', 'dist_km'):
        v[c] = pd.to_numeric(v[c], errors='coerce')
    return v[['iso3', 'cepii_code', 'distw_km', 'dist_km', 'contig', 'comlang_off', 'colony']].sort_values('iso3')


ASEAN = ['BRN', 'IDN', 'KHM', 'LAO', 'MMR', 'MYS', 'PHL', 'SGP', 'THA']
EU27 = ['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA',
        'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE']
CPTPP_NOTE = 'Pair date = later of Viet Nam (14 Jan 2019) and partner entry into force (WTO Remarks).'
# (RTA ID, đối tác, ngày có hiệu lực giữa cặp – None = ngày hàng hóa (G) của WTO, ghi chú)
RTA_RULES = [
    (126, ASEAN, None, 'AFTA (CEPT) - WTO goods entry-into-force date of the original AFTA; Viet Nam joined ASEAN in 1995. Both precede the 2006-2024 panel.'),
    (1170, ASEAN, None, 'ATIGA, successor to AFTA'),
    (42, ['CHN'], None, ''), (176, ['JPN'], None, ''), (169, ['KOR'], None, ''),
    (437, ['AUS', 'NZL'], None, ''), (438, ['IND'], None, ''), (994, ['HKG'], None, ''),
    ('Japan - Viet Nam', ['JPN'], None, ''), ('Chile - Viet Nam', ['CHL'], None, ''),
    ('Korea, Republic of - Viet Nam', ['KOR'], None, ''),
    ('EAEU - Viet Nam', ['ARM', 'BLR', 'KAZ', 'KGZ', 'RUS'], None, ''),
    ('EU - Viet Nam', EU27, None, ''),
    ('EU - Viet Nam', ['GBR'], None, 'UK covered by EVFTA during the Brexit transition period, until 31 Dec 2020 (WTO Remarks).'),
    ('United Kingdom - Viet Nam', ['GBR'], None, ''), ('Israel - Viet Nam', ['ISR'], None, ''),
    (640, ['AUS', 'CAN', 'JPN', 'MEX', 'NZL', 'SGP'], '2019-01-14', CPTPP_NOTE),
    (640, ['PER'], '2021-09-19', CPTPP_NOTE), (640, ['MYS'], '2022-11-29', CPTPP_NOTE),
    (640, ['CHL'], '2023-02-21', CPTPP_NOTE), (640, ['BRN'], '2023-07-12', CPTPP_NOTE),
    (640, ['GBR'], '2024-12-15', CPTPP_NOTE),
]


def fta():
    x = pd.read_excel(get('rta'))
    x['RTA Name'] = x['RTA Name'].str.strip()
    x = x.set_index('RTA ID')
    rows = []
    for key, isos, date, note in RTA_RULES:
        rid = key if isinstance(key, int) else x.index[x['RTA Name'] == key][0]
        d = pd.Timestamp(date or x.loc[rid, 'Date of Entry into Force (G)'])
        rows += [{'iso3': i, 'fta_name': x.loc[rid, 'RTA Name'], 'rta_id': rid, 'in_force_date': d.date().isoformat(),
                  'in_force_year': d.year, 'note': note} for i in isos]
    return pd.DataFrame(rows).sort_values(['iso3', 'in_force_date'])


# Bảng 2 của IMF (2000): 42 khu vực tài phán FSF; bỏ hai vùng dưới cấp quốc gia (Dublin, Labuan)
FSF = {'I': [('Guernsey', 'GGY'), ('Hong Kong, SAR', 'HKG'), ('Isle of Man', 'IMN'), ('Jersey', 'JEY'),
             ('Luxembourg', 'LUX'), ('Singapore', 'SGP'), ('Switzerland', 'CHE')],
       'II': [('Andorra', 'AND'), ('Bahrain', 'BHR'), ('Barbados', 'BRB'), ('Bermuda', 'BMU'), ('Gibraltar', 'GIB'),
              ('Macao, SAR', 'MAC'), ('Malta', 'MLT'), ('Monaco', 'MCO')],
       'III': [('Anguilla', 'AIA'), ('Antigua & Barbuda', 'ATG'), ('Aruba', 'ABW'), ('Bahamas', 'BHS'), ('Belize', 'BLZ'),
               ('British Virgin Islands', 'VGB'), ('Cayman Islands', 'CYM'), ('Cook Islands', 'COK'), ('Costa Rica', 'CRI'),
               ('Cyprus', 'CYP'), ('Lebanon', 'LBN'), ('Liechtenstein', 'LIE'), ('Marshall Islands', 'MHL'),
               ('Mauritius', 'MUS'), ('Nauru', 'NRU'), ('Netherlands Antilles', 'ANT'), ('Niue', 'NIU'), ('Panama', 'PAN'),
               ('Samoa', 'WSM'), ('Seychelles', 'SYC'), ('St. Kitts and Nevis', 'KNA'), ('St. Lucia', 'LCA'),
               ('St. Vincent and Grenadines', 'VCT'), ('Turks and Caicos', 'TCA'), ('Vanuatu', 'VUT')]}


def ofc():
    page = open(get('ofc'), encoding='latin-1').read()
    text = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', page)))
    table2 = text[text.find('Table 2. Basic'):text.find('Sources: International Financial Statistics')]
    rows = []
    for g, items in FSF.items():
        for name, iso in items:
            assert name in table2, f'{name} không có trong Bảng 2 của IMF'
            rows.append({'iso3': iso, 'name_in_source': name, 'fsf_group': g, 'note': ''})
    for iso in ('CUW', 'SXM'):
        rows.append({'iso3': iso, 'name_in_source': 'Netherlands Antilles', 'fsf_group': 'III',
                     'note': 'Successor of the Netherlands Antilles (dissolved 10 Oct 2010); added by the authors.'})
    return pd.DataFrame(rows)


def gdp_twn():
    """WDI không có Đài Loan; bổ sung GDP và GDP/người (USD hiện hành) từ IMF WEO DataMapper."""
    import json
    g = json.load(open(get('weo_gdp')))['values']['NGDPD']['TWN']
    p = json.load(open(get('weo_gdppc')))['values']['NGDPDPC']['TWN']
    ys = range(YEARS[0], YEARS[1] + 1)
    return pd.DataFrame({'iso3': 'TWN', 'year': list(ys),
                         'gdp_usd': [g[str(y)] * 1e9 for y in ys], 'gdppc_usd': [p[str(y)] for y in ys],
                         'source': 'IMF WEO DataMapper (NGDPD, NGDPDPC)'})


if __name__ == '__main__':
    for name, fn in (('wgi', wgi), ('cepii_dist', cepii), ('fta', fta), ('ofc_list', ofc), ('wdi_supplement', gdp_twn)):
        df = fn()
        df.to_csv(os.path.join(OUT, f'{name}.csv'), index=False)
        print(f'{name}.csv: {len(df)} dòng')

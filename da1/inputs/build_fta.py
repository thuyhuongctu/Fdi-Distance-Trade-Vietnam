"""DA1 – Lập fta.csv từ bản xuất toàn bộ CSDL RTA của WTO (rtais.wto.org/UI/ExportAllRTAList.aspx).

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Mỗi dòng = một đối tác × một hiệp định có Việt Nam là bên tham gia, còn hiệu lực.
Quy tắc (ghi trong inputs/sources_c.md):
  - Chỉ giữ hiệp định thương mại hàng hóa loại FTA, FTA & EIA hoặc CU. Bỏ GSTP (ưu đãi một phần, PSA)
    và ATISA (chỉ dịch vụ).
  - Ngày hiệu lực của cặp Việt Nam – đối tác = ngày muộn hơn trong hai ngày hiệu lực riêng của hai bên
    (cột "Specific Entry/Exit dates"; nếu không có thì lấy ngày hiệu lực phần hàng hóa (G), thiếu G thì lấy S).
  - Hiệp định ASEAN+1: đối tác là bên ngoài ASEAN. AFTA: các thành viên ASEAN khác, theo bản CEPT (RTA 126).
  - EU – Việt Nam: 27 nước thành viên tại 01/08/2020, cộng Vương quốc Anh (có hiệu lực tới 31/12/2020).
  - EAEU: Nga, Belarus, Kazakhstan, Armenia, Kyrgyzstan.
  - CPTPP – gia nhập của Anh (RTA 1218): chỉ thêm cặp Việt Nam – Anh; ngày riêng của các nước khác trong bản
    ghi này là quan hệ của họ với Anh, không liên quan Việt Nam.
  - in_force_year = năm của ngày hiệu lực.
Chạy: python3 build_fta.py
"""
import csv
import re
from datetime import datetime

import pandas as pd

SRC = 'raw/wto_rta_all.xlsx'
ASEAN = {'BRN', 'MMR', 'KHM', 'IDN', 'LAO', 'MYS', 'PHL', 'SGP', 'THA', 'VNM'}
EU27 = ['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA',
        'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE']
EAEU = ['RUS', 'BLR', 'KAZ', 'ARM', 'KGZ']
NAME = {'Brunei Darussalam': 'BRN', 'Myanmar': 'MMR', 'Cambodia': 'KHM', 'Indonesia': 'IDN',
        "Lao People's Democratic Republic": 'LAO', 'Malaysia': 'MYS', 'Philippines': 'PHL', 'Singapore': 'SGP',
        'Thailand': 'THA', 'Viet Nam': 'VNM', 'Australia': 'AUS', 'New Zealand': 'NZL', 'China': 'CHN',
        'Hong Kong, China': 'HKG', 'India': 'IND', 'Japan': 'JPN', 'Korea, Republic of': 'KOR', 'Chile': 'CHL',
        'Canada': 'CAN', 'Mexico': 'MEX', 'Peru': 'PER', 'United Kingdom': 'GBR', 'Israel': 'ISR'}
KEEP_TYPES = {'FTA', 'FTA & EIA', 'CU', 'CU & EIA'}


def specific(cell):
    """'Viet Nam(14-Jan-2019 - ); ...' → {iso3: ngày vào}."""
    out = {}
    for name, start in re.findall(r"([^;()]+)\((\d{2}-\w{3}-\d{4})?\s*-", str(cell)):
        iso = NAME.get(name.strip())
        if iso and start:
            out[iso] = datetime.strptime(start, '%d-%b-%Y')
    return out


def parties(r):
    return [NAME[s.strip()] for s in str(r['Current signatories']).split(';') if s.strip() in NAME]


def main():
    d = pd.read_excel(SRC)
    rows, skipped = [], []
    for _, r in d.iterrows():
        sig = str(r['Current signatories']) + ' ' + str(r['Original signatories'])
        asean_plus = 'ASEAN Free Trade Area (AFTA)' in str(r['Current signatories'])
        if 'Viet Nam' not in sig and not asean_plus:
            continue
        name = r['RTA Name'].strip()
        if r['Status'] != 'In Force' and r['RTA ID'] != 126:
            skipped.append((name, f"status: {r['Status']}"))
            continue
        if r['Type'] not in KEEP_TYPES or 'Goods' not in str(r['Coverage']):
            skipped.append((name, f"type {r['Type']}, coverage {r['Coverage']}"))
            continue
        default = r['Date of Entry into Force (G)']
        if pd.isna(default):
            default = r['Date of Entry into Force (S)']
        spec = specific(r['Specific Entry/Exit dates'])
        vn = spec.get('VNM', default)
        if r['RTA ID'] == 126:                       # AFTA (CEPT) bản cũ: các thành viên ASEAN khác
            partners = sorted(ASEAN - {'VNM'})
        elif r['RTA ID'] == 1170:                    # ATIGA kế thừa CEPT – cùng đối tác, đã có từ RTA 126
            skipped.append((name, 'same partners as AFTA/CEPT (RTA 126)'))
            continue
        elif name == 'EU - Viet Nam':
            partners = EU27 + ['GBR']
        elif name == 'EAEU - Viet Nam':
            partners = EAEU
        else:
            partners = [p for p in parties(r) if p not in ASEAN]
            if 'Accession' in name:                  # chỉ cặp Việt Nam – bên gia nhập là mới
                partners = ['GBR']
            elif 'CPTPP' in name:
                partners = [p for p in parties(r) if p != 'VNM']
        for p in partners:
            start = max(vn, spec.get(p, default))
            rows.append(dict(iso3=p, fta_name=name, rta_id=int(r['RTA ID']), in_force_date=start.date().isoformat(),
                             in_force_year=start.year, type=r['Type']))
    rows.sort(key=lambda x: (x['iso3'], x['in_force_date']))
    with open('fta.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f'{len(rows)} dòng, {len({x["iso3"] for x in rows})} đối tác')
    for s in skipped:
        print('bỏ:', *s)


if __name__ == '__main__':
    main()

"""DA1 – Lập ofc_list.csv từ IMF (2000), Offshore Financial Centers – IMF Background Paper, Bảng 1.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Nguồn: https://www.imf.org/external/np/mae/oshore/2000/eng/back.htm (tải 2026-10-04, lưu ở raw/imf_ofc_back.htm).
Bảng 1 có 64 mục. Quy tắc gắn cờ OFC (ghi lại từng mục trong raw/imf_ofc_table1.csv):
  - Gắn cờ: các vùng lãnh thổ/nền kinh tế được liệt kê trọn vẹn.
  - Không gắn cờ: mục chỉ là một thành phố, vùng hay cơ chế ngân hàng hải ngoại bên trong một nền kinh tế
    trong nước (Dublin, London, Labuan, Madeira, Campione, Tangier; JOM của Nhật, ACU của Singapore,
    BIBF của Thái Lan, IBF của Mỹ – chú thích 1–4 của bảng).
  - Hồng Kông và Singapore giữ trong mẫu chính vì kiểm định R2b đã đăng ký loại riêng hai nền kinh tế này.
  - Antilles thuộc Hà Lan giải thể năm 2010: thêm hai nền kinh tế kế thừa CUW, SXM.
Chạy: python3 build_ofc_list.py
"""
import csv

# (mục in trong Bảng 1, khu vực, iso3, gắn cờ, lý do)
T = [
    ('Djibouti', 'Africa', 'DJI', 1, ''), ('Liberia (J)', 'Africa', 'LBR', 1, ''),
    ('Mauritius (OG) (FSF)', 'Africa', 'MUS', 1, ''), ('Seychelles (FSF)', 'Africa', 'SYC', 1, ''),
    ('Tangier', 'Africa', 'MAR', 0, 'city within an onshore economy'),
    ('Cook Islands (FSF)', 'Asia and Pacific', 'COK', 1, ''), ('Guam', 'Asia and Pacific', 'GUM', 1, ''),
    ('Hong Kong, SAR (J) (OG) (FSF)', 'Asia and Pacific', 'HKG', 0, 'kept in main sample: preregistered R2b tests SGP and HKG separately'),
    ('Japan 1', 'Asia and Pacific', 'JPN', 0, 'facility only (Japanese Offshore Market)'),
    ('Labuan, Malaysia (FSF)', 'Asia and Pacific', 'MYS', 0, 'territory within an onshore economy'),
    ('Macao, SAR (FSF)', 'Asia and Pacific', 'MAC', 1, ''), ('Marianas', 'Asia and Pacific', 'MNP', 1, ''),
    ('Marshall Islands (FSF)', 'Asia and Pacific', 'MHL', 1, ''), ('Micronesia', 'Asia and Pacific', 'FSM', 1, ''),
    ('Nauru (FSF)', 'Asia and Pacific', 'NRU', 1, ''), ('Niue (FSF)', 'Asia and Pacific', 'NIU', 1, ''),
    ('Philippines', 'Asia and Pacific', 'PHL', 1, ''),
    ('Singapore 2 (J) (OG) (FSF)', 'Asia and Pacific', 'SGP', 0, 'facility (Asian Currency Units); kept in main sample per R2b'),
    ('Tahiti', 'Asia and Pacific', 'PYF', 1, 'mapped to French Polynesia'),
    ('Thailand 3', 'Asia and Pacific', 'THA', 0, 'facility only (Bangkok International Banking Facilities)'),
    ('Vanuatu (J) (OG) (FSF)', 'Asia and Pacific', 'VUT', 1, ''), ('Western Samoa (FSF)', 'Asia and Pacific', 'WSM', 1, ''),
    ('Andorra (FSF)', 'Europe', 'AND', 1, ''), ('Campione', 'Europe', 'ITA', 0, 'enclave within an onshore economy'),
    ('Cyprus (OG) (FSF)', 'Europe', 'CYP', 1, ''), ('Dublin, Ireland (FSF)', 'Europe', 'IRL', 0, 'city within an onshore economy'),
    ('Gibraltar (OG) (FSF)', 'Europe', 'GIB', 1, ''), ('Guernsey (OG) (FSF)', 'Europe', 'GGY', 1, ''),
    ('Isle of Man (OG) (FSF)', 'Europe', 'IMN', 1, ''), ('Jersey (OG) (FSF)', 'Europe', 'JEY', 1, ''),
    ('Liechtenstein (FSF)', 'Europe', 'LIE', 1, ''), ('London, U.K.', 'Europe', 'GBR', 0, 'city within an onshore economy'),
    ('Luxembourg (FSF)', 'Europe', 'LUX', 1, ''), ('Madeira', 'Europe', 'PRT', 0, 'region within an onshore economy'),
    ('Malta (OG) (FSF)', 'Europe', 'MLT', 1, ''), ('Monaco (FSF)', 'Europe', 'MCO', 1, ''),
    ('Netherlands', 'Europe', 'NLD', 1, ''), ('Switzerland (FSF)', 'Europe', 'CHE', 1, ''),
    ('Bahrain (J) (OG) (FSF)', 'Middle East', 'BHR', 1, ''), ('Israel', 'Middle East', 'ISR', 1, ''),
    ('Lebanon (J) (OG) (FSF)', 'Middle East', 'LBN', 1, ''),
    ('Anguilla (FSF)', 'Western Hemisphere', 'AIA', 1, ''), ('Antigua (FSF)', 'Western Hemisphere', 'ATG', 1, ''),
    ('Aruba (J) (OG) (FSF)', 'Western Hemisphere', 'ABW', 1, ''), ('Bahamas (J) (OG) (FSF)', 'Western Hemisphere', 'BHS', 1, ''),
    ('Barbados (J) (OG) (FSF)', 'Western Hemisphere', 'BRB', 1, ''), ('Belize (FSF)', 'Western Hemisphere', 'BLZ', 1, ''),
    ('Bermuda (J) (OG) (FSF)', 'Western Hemisphere', 'BMU', 1, ''), ('British Virgin Islands (FSF)', 'Western Hemisphere', 'VGB', 1, ''),
    ('Cayman Islands (J) (OG) (FSF)', 'Western Hemisphere', 'CYM', 1, ''), ('Costa Rica (FSF)', 'Western Hemisphere', 'CRI', 1, ''),
    ('Dominica', 'Western Hemisphere', 'DMA', 1, ''), ('Grenada', 'Western Hemisphere', 'GRD', 1, ''),
    ('Montserrat', 'Western Hemisphere', 'MSR', 1, ''),
    ('Netherlands Antilles (J) (OG) (FSF)', 'Western Hemisphere', 'ANT', 1, 'dissolved 2010; successors CUW and SXM added'),
    ('Panama (J) (OG) (FSF)', 'Western Hemisphere', 'PAN', 1, ''), ('Puerto Rico', 'Western Hemisphere', 'PRI', 1, ''),
    ('St. Kitts and Nevis (FSF)', 'Western Hemisphere', 'KNA', 1, ''), ('St. Lucia (FSF)', 'Western Hemisphere', 'LCA', 1, ''),
    ('St. Vincent and Grenadines (FSF)', 'Western Hemisphere', 'VCT', 1, ''),
    ('Turks and Caicos Islands (FSF)', 'Western Hemisphere', 'TCA', 1, ''),
    ('United States 4', 'Western Hemisphere', 'USA', 0, 'facility only (International Banking Facilities)'),
    ('Uruguay', 'Western Hemisphere', 'URY', 1, ''),
    ('West Indies (UK) (J) 5', 'Western Hemisphere', '', 0, 'aggregate of VGB, AIA, MSR, listed separately'),
]
assert len(T) == 64, len(T)

if __name__ == '__main__':
    with open('raw/imf_ofc_table1.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['entry_as_printed', 'region', 'iso3', 'in_ofc_list', 'reason'])
        w.writerows(T)
    rows = [(iso, e, 'IMF (2000) Table 1') for e, _, iso, inc, _ in T if inc]
    rows += [('CUW', 'Curaçao', 'successor of Netherlands Antilles, IMF (2000) Table 1'),
             ('SXM', 'Sint Maarten', 'successor of Netherlands Antilles, IMF (2000) Table 1')]
    with open('ofc_list.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['iso3', 'entry', 'basis'])
        w.writerows(sorted(rows))
    print(len(rows), 'mã OFC;', sum(1 for t in T if not t[3]), 'mục không gắn cờ')

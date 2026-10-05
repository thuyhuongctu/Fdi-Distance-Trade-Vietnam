"""DA1 – Dựng inputs/fdi_registered.csv (iso3, year, fdi_usd_m) từ biểu FDI cấp phép theo đối tác của Niên giám Thống kê.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Đầu vào: yearbook_fdi_rows.csv (parse_yearbook_fdi.py, 2006–2025 trừ 2016), yearbook_2016_transcribed.csv
(2016: OCR + đối chiếu ảnh trang), partner_map.csv (tên tiếng Anh in trong biểu → ISO3).
Quy tắc: bỏ dòng TỔNG SỐ; gộp các dòng cùng mã trong một năm (2025: "United Kingdom" + "British Isles");
loại dòng lỗi nguồn ghi trong SOURCE_ERRORS. Mọi tên không khớp bảng ánh xạ làm dừng chương trình.
Chạy: python3 build_fdi_registered.py
"""
import csv
import re
from collections import defaultdict

PRIORITY = {'VIR', 'VGB', 'XBWI', 'XCHI', 'HKG', 'MAC', 'TWN'}   # khớp trước "China", "United States", "United Kingdom"
# Lỗi của chính biểu nguồn (giữ nguyên trong yearbook_fdi_rows.csv, loại khi dựng biến)
SOURCE_ERRORS = {(2020, 'VIR'): 'Biểu 2020 in dòng Quần đảo Virgin thuộc Hoa Kỳ trùng số với Quần đảo Virgin thuộc Anh '
                                '(29 dự án; 899,1 triệu USD); tổng các đối tác vượt dòng tổng 2,6% nếu giữ dòng này.'}
DEFINITION = {y: 'vốn cấp mới + vốn tăng thêm' for y in range(2006, 2016)}
DEFINITION.update({y: 'vốn cấp mới + vốn tăng thêm + vốn góp, mua cổ phần' for y in range(2016, 2026)})


def load_map():
    m = list(csv.DictReader(open('partner_map.csv', encoding='utf-8')))
    m.sort(key=lambda r: r['iso3'] not in PRIORITY)
    return [(re.compile(r'(?i)\b(?:' + r['pattern'] + ')'), r['iso3']) for r in m]


def main():
    pats = load_map()
    rows = list(csv.DictReader(open('yearbook_fdi_rows.csv', encoding='utf-8')))
    rows = [r for r in rows if r['year'] != '2016'] + list(csv.DictReader(open('yearbook_2016_transcribed.csv', encoding='utf-8')))
    agg, labels, totals, unmatched, dropped = defaultdict(float), defaultdict(list), {}, [], []
    proj = defaultdict(int)
    for r in rows:
        y, lab, cap = int(r['year']), r['label'], float(r['capital_usd_m'])
        if re.search(r'(?i)\btotal\b', lab):
            totals[y] = cap
            continue
        iso = next((i for p, i in pats if p.search(lab)), None)
        if iso is None:
            unmatched.append((y, lab))
            continue
        if (y, iso) in SOURCE_ERRORS:
            dropped.append((y, iso, lab, cap))
            continue
        agg[(iso, y)] += cap
        proj[(iso, y)] += int(r['projects']) if r['projects'] else 0
        labels[(iso, y)].append(lab)
    if unmatched:
        raise SystemExit(f'Tên chưa có trong partner_map.csv: {unmatched}')
    with open('../fdi_registered.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['iso3', 'year', 'fdi_usd_m', 'projects', 'label_as_printed', 'capital_definition', 'source'])
        for (iso, y) in sorted(agg):
            src = (f'Tổng cục Thống kê, Niên giám Thống kê {y}, biểu "Đầu tư trực tiếp của nước ngoài được cấp giấy phép '
                   f'năm {y} phân theo đối tác đầu tư chủ yếu"')
            w.writerow([iso, y, round(agg[(iso, y)], 1), proj[(iso, y)] or '', ' + '.join(labels[(iso, y)]), DEFINITION[y], src])
    print('năm | tổng in | tổng đối tác | phủ % | số đối tác')
    for y in sorted(totals):
        s = sum(v for (i, yy), v in agg.items() if yy == y)
        n = sum(1 for (i, yy) in agg if yy == y)
        print(y, totals[y], round(s, 1), round(100 * s / totals[y], 1), n)
    for d in dropped:
        print('loại (lỗi nguồn):', *d)


if __name__ == '__main__':
    main()

"""DA1 – Đọc biểu "Đầu tư trực tiếp của nước ngoài được cấp giấy phép năm Y phân theo đối tác đầu tư chủ yếu"
trong Niên giám Thống kê (Tổng cục Thống kê) thành bảng dọc đối tác × năm.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Đầu vào: văn bản của từng niên giám (pdftotext -layout; riêng 2006 là chương Đầu tư dạng .doc, đọc bằng antiword),
đặt tên NG{năm}.txt. Mỗi dòng đầu ra giữ nguyên văn dòng của biểu (cột `row_text`) để đối chiếu.
Chạy: python3 parse_yearbook_fdi.py <thư mục NG*.txt> --out yearbook_fdi_rows.csv
"""
import argparse
import csv
import os
import re

NUMTOK = re.compile(r'^\d{1,3}(?:\.\d{3})+(?:,\d+)?$|^\d+(?:,\d+)?$')
STOP = re.compile(r'(?i)outward|oversea|by province|economic activit|kind of economic|đầu tư trực tiếp ra nước ngoài|'
                  r'investment at current|by industry|1988\s*-\s*\d{4}|1989\s*-\s*\d{4}')
TOTAL = re.compile(r'(?i)^\s*\S+\s+\S+\s*-\s*total\b')            # "TỔNG SỐ - TOTAL" (mọi bảng mã)
NEXT_TABLE = re.compile(r'(?i)(đầu tư trực tiếp|§Çu t\S*\s+trùc tiÕp)')
SKIP = re.compile(r'(?i)\(cont\.?\)|phân theo đối tác|ph©n theo ®èi t¸c|by main counterpart|licensed in \d{4}|tiÕp theo|tiếp theo|^number|of projects|mill\. ?usd|triÖu ®«|triệu đô|registered capital|'
                  r'sè dù ¸n|số dự án|newly granted|supplementary|^capital$|chia ra|of which$|^total$|tæng sè$|tổng số$|'
                  r'^\(\*\)|xem ghi chú|see footnote|see the note|^\d{1,3}\s+(§Çu t|đầu tư|investment)|investment\s*\d{1,3}$|'
                  r'industry, investment|investment and construction|công nghiệp, đầu tư|^đầu tư - investment|^§Çu t− - investment')


def num(t):
    return float(t.replace('.', '').replace(',', '.'))


def body_start(lines, y):
    """Dòng tiêu đề tiếng Anh của biểu trong thân sách (không phải mục lục): sau đó ≤ 25 dòng có dòng TOTAL."""
    pat = re.compile(rf'(?i)licensed in {y}\b')
    for i, l in enumerate(lines):
        if pat.search(l) and (re.search(r'(?i)counterpart', l) or re.search(r'(?i)counterpart', ' '.join(lines[i + 1:i + 3]))):
            for j in range(i, min(i + 25, len(lines))):
                if TOTAL.match(lines[j].replace('|', ' ')) and re.search(r'\d', lines[j]):
                    return j
    return None


def parse(path, y):
    lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
    start = body_start(lines, y)
    if start is None:
        return None
    rows, pending = [], ''
    for raw in lines[start:start + 600]:
        l = raw.replace('|', '  ').rstrip()
        s = l.strip()
        if not s:
            continue
        if rows and (STOP.search(s) or (NEXT_TABLE.search(s) and not re.search(r'(?i)tiếp theo|tiÕp theo', s))):
            break
        if SKIP.search(s) or (len(s) <= 3 and not re.search(r'\d', s)):   # tiêu đề lặp lại, chân trang, chữ watermark
            continue
        toks = s.split()
        k = len(toks)
        while k > 0 and NUMTOK.match(toks[k - 1]):
            k -= 1
        label, nums = ' '.join(toks[:k]), [num(t) for t in toks[k:]]
        label = re.sub(r'(?i)^trong \S+ - of which:?\s*', '', label).strip()     # "Trong đó - Of which:"
        if len(label) <= 2:                                                       # chữ watermark lẫn vào dòng số
            label = ''
        if not label and not nums:
            continue
        if re.fullmatch(r'\d{1,3}', label or ''):       # số biểu ở lề trái
            continue
        if not nums:
            # Tên tiếng Anh nằm SAU dòng số (tên dài bị tách: dòng Việt / dòng số / dòng Anh)
            if rows and rows[-1].get('_open') and re.fullmatch(r"[A-Za-z .,'()&-]+", label):
                rows[-1]['label'] += ' / ' + label
                rows[-1]['_open'] = False
                continue
            pending = (pending + ' ' + label).strip()
            continue
        if rows:
            rows[-1]['_open'] = False
        if label and pending:
            label = pending + ' / ' + label
        elif not label:
            label = pending
        pending = ''
        if not label:
            continue
        projects, capital = (None, nums[0]) if len(nums) == 1 else (int(nums[0]), nums[1])
        rows.append(dict(year=y, label=label, projects=projects, capital_usd_m=capital,
                         extra_cols=';'.join(str(x) for x in nums[2:]), row_text=s,
                         _open=' - ' not in label and ' / ' not in label))   # tên chưa có phần tiếng Anh
    for r in rows:
        r.pop('_open', None)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('textdir')
    ap.add_argument('--out', default='yearbook_fdi_rows.csv')
    a = ap.parse_args()
    allrows = []
    for y in range(2006, 2026):
        p = os.path.join(a.textdir, f'NG{y}.txt')
        if not os.path.exists(p):
            continue
        r = parse(p, y)
        print(y, 'không tìm thấy biểu' if r is None else f'{len(r)} dòng')
        allrows += r or []
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['year', 'label', 'projects', 'capital_usd_m', 'extra_cols', 'row_text'])
        w.writeheader()
        w.writerows(allrows)


if __name__ == '__main__':
    main()

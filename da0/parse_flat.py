"""DA0 – Đọc văn bản biểu Hải quan 017.T/018.T khi đã bị dồn dòng (văn bản trích từ Google Drive).

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Mỗi tệp đầu vào: dòng đầu `#META<TAB>title<TAB>fileId<TAB>modifiedTime`, sau đó là văn bản.
Đọc theo token: mỗi bản ghi = [nhãn] [ĐVT] [các số]. Nhãn bắt đầu bằng số thứ tự hoặc '-'.
Mọi kiểm tra nhất quán ghi vào nhật ký, không sửa âm thầm.

Chạy: python3 parse_flat.py raw/ --out panel_flat.csv --log cleaning_log_flat.csv
"""
import argparse, csv, glob, hashlib, os, re, unicodedata

UNITS = {'USD', 'Tấn', 'Chiếc', 'Tấn/USD'}
NUM = re.compile(r'^\d{1,3}(?:[.,]\d{3})+$|^\d{1,3}$')
ITEM_NO = re.compile(r'^\d{1,2}$')


def to_int(t):
    return int(re.sub(r'[.,]', '', t))


def header_info(text, title):
    form = re.search(r'(01[78])\.T', text)
    direction = {'017': 'export', '018': 'import'}.get(form.group(1)) if form else None
    if direction is None:  # dự phòng theo tên tệp
        direction = 'export' if 'XK' in title.upper() else 'import' if 'NK' in title.upper() else ''
    m = re.search(r'Tháng\s+(\d{1,2})\s+năm\s+(\d{4})', text)
    period = f'{int(m.group(2)):04d}-{int(m.group(1)):02d}' if m else ''
    if not period:
        m = re.search(r'(\d{4})-T(\d{1,2})', title)
        period = f'{int(m.group(1)):04d}-{int(m.group(2)):02d}' if m else ''
    status = 'preliminary' if re.search(r'\bSơ bộ\b', text) or title.upper().endswith('SB.PDF') else 'official'
    if re.search(r'-CT\b', title.upper()):
        status = 'official'
    return direction, period, status


def parse_text(text, title):
    text = unicodedata.normalize('NFC', text)
    direction, period, status = header_info(text, title)
    body = text.split('Ngày in')[0]
    toks = body.split()
    rows, log = [], []
    i, label_start = 0, 0
    # bắt đầu từ "TỔNG TRỊ GIÁ"
    for k in range(len(toks) - 2):
        if toks[k].upper() == 'TỔNG' and toks[k + 1].upper() == 'TRỊ':
            label_start = i = k
            break
    while i < len(toks):
        t = toks[i]
        if t in UNITS and i > label_start:
            j = i + 1
            nums = []
            while j < len(toks) and NUM.match(toks[j]) and not (ITEM_NO.match(toks[j]) and j + 1 < len(toks) and not NUM.match(toks[j + 1]) and toks[j + 1] not in UNITS):
                nums.append(toks[j]); j += 1
            label = toks[label_start:i]
            if '(USD)' in label:  # rác tiêu đề trang 2
                label = label[len(label) - label[::-1].index('(USD)'):]
            # cắt phần tiêu đề cột lặp lại nếu còn sót
            for kw in ('Lượng', 'STT'):
                if kw in label:
                    label = label[len(label) - label[::-1].index(kw):]
            label = [x for x in label if 'www.' not in x and 'http' not in x]  # rác chân/đầu trang
            rows.append((label, t, nums))
            label_start = i = j
            continue
        i += 1

    out, parent, seen = [], None, {}
    for label, unit, nums in rows:
        code, sub = '', False
        if label and ITEM_NO.match(label[0]):
            code, label = label[0], label[1:]
        elif label and label[0] == '-':
            sub, label = True, label[1:]
        elif out:  # mẫu biểu 2026: tiểu mục không có '-' và không có STT
            sub = True
        name = ' '.join(label).rstrip(':').strip()
        level = 'subitem' if sub else 'group'
        if name.upper().startswith('TỔNG TRỊ GIÁ'):
            code, name, level = 'TOTAL', 'Tổng trị giá', 'total'
        vals = [to_int(x) for x in nums]
        qm = vm = qc = vc = None
        if unit == 'USD':
            if len(vals) == 2:
                vm, vc = vals
            elif len(vals) == 1:
                vc = vals[0]
                log.append(dict(file=title, check='one_value_usd', detail=f'{name}: chỉ có 1 số, gán là cộng dồn'))
            elif len(vals):
                log.append(dict(file=title, check='column_count', detail=f'{name}: {len(vals)} số'))
        else:
            if len(vals) == 4:
                qm, vm, qc, vc = vals
            elif len(vals) == 2:
                qc, vc = vals
                log.append(dict(file=title, check='two_values_qty', detail=f'{name}: 2 số, gán là cộng dồn'))
            elif len(vals):
                log.append(dict(file=title, check='column_count', detail=f'{name}: {len(vals)} số'))
        if vm is None and vc is None:
            log.append(dict(file=title, check='empty_row', detail=name))
        if level == 'group':
            parent = name
            if code:
                if code in seen:
                    log.append(dict(file=title, check='duplicate_item_number', detail=f'STT {code}: «{seen[code]}» và «{name}»'))
                seen[code] = name
        out.append(dict(period=period, direction=direction, status=status, item_no=code, level=level,
                        parent=parent if level == 'subitem' else '', product_group=name, unit=unit,
                        qty_month=qm, value_usd_month=vm, qty_ytd=qc, value_usd_ytd=vc))

    total = next((r for r in out if r['level'] == 'total'), None)
    groups = [r for r in out if r['level'] == 'group']
    if not total:
        log.append(dict(file=title, check='no_total', detail='Không tìm thấy dòng tổng'))
    else:
        for col in ('value_usd_month', 'value_usd_ytd'):
            if total[col]:
                s = sum(r[col] or 0 for r in groups)
                ok = abs(s - total[col]) <= max(2, 1e-6 * total[col])
                log.append(dict(file=title, check=f'sum_check_{col}', detail=('OK' if ok else 'LỆCH') + f' tổng nhóm={s} dòng tổng={total[col]} chênh={s - total[col]}'))
    return out, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rawdir')
    ap.add_argument('--out', default='panel_flat.csv')
    ap.add_argument('--log', default='cleaning_log_flat.csv')
    a = ap.parse_args()
    rows, logs = [], []
    for f in sorted(glob.glob(os.path.join(a.rawdir, '**', '*.txt'), recursive=True)):
        raw = open(f, encoding='utf-8').read()
        meta, _, text = raw.partition('\n')
        parts = meta.split('\t')
        title, fid, mod = (parts + ['', '', ''])[1:4] if parts[0] == '#META' else (os.path.basename(f), '', '')
        r, l = parse_text(text, title)
        h = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        for x in r:
            x.update(source_title=title, drive_file_id=fid, drive_modified=mod, text_sha256_16=h,
                     source='Cục Hải quan, Biểu 017.T/018.T – khu vực doanh nghiệp FDI',
                     method='Số liệu tờ khai, tổng hợp theo nhóm hàng; văn bản trích từ PDF qua Google Drive')
        for x in l:
            x['drive_file_id'] = fid
        rows += r; logs += l
    with open(a.out, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(a.log, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=['file', 'drive_file_id', 'check', 'detail']); w.writeheader(); w.writerows(logs)
    bad = [x for x in logs if x['check'].startswith('sum_check') and x['detail'].startswith('LỆCH')]
    print(f'{len(rows)} dòng từ {len(set(r["source_title"] for r in rows))} tệp; {len(bad)} kiểm tra tổng bị lệch')


if __name__ == '__main__':
    main()

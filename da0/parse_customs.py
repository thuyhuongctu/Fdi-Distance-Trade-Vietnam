"""DA0 – Đọc biểu Hải quan 017.T / 018.T (xuất/nhập khẩu của khu vực FDI) thành bảng dọc có xuất xứ.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Cách dùng:
    python parse_customs.py <tệp PDF hoặc TXT> [...] --out panel.csv --log cleaning_log.csv

Mỗi dòng đầu ra = một nhóm hàng × kỳ × chiều (xuất/nhập), kèm 4 trường xuất xứ:
source, period, method, limitation. Mọi kiểm tra nhất quán được ghi vào nhật ký làm sạch
thay vì sửa âm thầm.
"""
import argparse, csv, hashlib, re, subprocess, sys, unicodedata
from pathlib import Path

UNITS = ('USD', 'Tấn', 'Chiếc')
NUM = re.compile(r'^\d{1,3}(?:\.\d{3})*$')


def num(s):
    return int(s.replace('.', ''))


def read_text(path):
    p = Path(path)
    if p.suffix.lower() == '.pdf':
        return subprocess.run(['pdftotext', '-layout', str(p), '-'], capture_output=True, text=True, check=True).stdout
    return p.read_text(encoding='utf-8')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse(text, file_name, file_hash):
    text = unicodedata.normalize('NFC', text)
    form = re.search(r'Biểu số\s+(\S+)', text)
    form = form.group(1) if form else ''
    direction = 'export' if '017.T' in form else 'import' if '018.T' in form else ''
    m = re.search(r'Tháng\s+(\d{1,2})\s+năm\s+(\d{4})', text)
    period = f'{int(m.group(2)):04d}-{int(m.group(1)):02d}' if m else ''
    status = 'preliminary' if re.search(r'^\s*Sơ bộ\s*$', text, re.M) else 'official'
    printed = re.search(r'Ngày in:\s*(\S+)', text)

    rows, log, parent, seen_codes = [], [], None, {}
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or not any(f' {u} ' in f' {line} ' for u in UNITS):
            continue
        toks = line.split()
        # vị trí đơn vị tính: token cuối cùng là một trong UNITS, trước các số
        ui = max((i for i, t in enumerate(toks) if t in UNITS), default=None)
        if ui is None:
            continue
        head, tail = toks[:ui], toks[ui + 1:]
        if tail and not all(NUM.match(t) for t in tail):
            continue  # dòng tiêu đề cột, không phải dữ liệu
        unit = toks[ui]
        nums = [num(t) for t in tail]
        code, sub = '', False
        if head and head[0].isdigit():
            code, head = head[0], head[1:]
        elif head and head[0] == '-':
            sub, head = True, head[1:]
        name = ' '.join(head).rstrip(':').strip()
        if name.upper().startswith('TỔNG TRỊ GIÁ'):
            code, name = 'TOTAL', 'Tổng trị giá'
        if unit == 'USD':
            qty_m = qty_c = None
            val_m, val_c = (nums + [None, None])[:2] if len(nums) <= 2 else (None, None)
        else:
            if len(nums) == 4:
                qty_m, val_m, qty_c, val_c = nums
            elif len(nums) == 0:
                qty_m = val_m = qty_c = val_c = None
            else:
                qty_m = val_m = qty_c = val_c = None
                log.append(dict(file=file_name, line=ln, check='column_count', detail=f'{len(nums)} số cho đơn vị {unit}: {line}'))
        if not sub:
            parent = name
            if code and code != 'TOTAL':
                if code in seen_codes:
                    log.append(dict(file=file_name, line=ln, check='duplicate_item_number',
                                    detail=f'STT {code} lặp lại: «{seen_codes[code]}» và «{name}»'))
                seen_codes[code] = name
        if val_m is None and val_c is None:
            log.append(dict(file=file_name, line=ln, check='empty_row', detail=f'Không có số liệu: {name}'))
        rows.append(dict(
            period=period, direction=direction, sector='FDI', item_no=code,
            level='subitem' if sub else ('total' if code == 'TOTAL' else 'group'),
            parent=parent if sub else '', product_group=name, unit=unit,
            qty_month=qty_m, value_usd_month=val_m, qty_ytd=qty_c, value_usd_ytd=val_c,
            source=f'Cục Hải quan, Biểu {form}', method='Số liệu tờ khai hải quan, tổng hợp theo nhóm hàng',
            limitation=f'Số {"sơ bộ" if status == "preliminary" else "chính thức"}; khu vực FDI; nhóm hàng theo danh mục của kỳ báo cáo',
            status=status, printed=printed.group(1) if printed else '', file=file_name, file_sha256=file_hash))

    # Kiểm tra: tổng các nhóm cấp 1 so với dòng tổng
    total = next((r for r in rows if r['level'] == 'total'), None)
    groups = [r for r in rows if r['level'] == 'group']
    for col in ('value_usd_month', 'value_usd_ytd'):
        if total and total[col]:
            s = sum(r[col] or 0 for r in groups)
            share = s / total[col]
            log.append(dict(file=file_name, line='', check=f'sum_groups_vs_total_{col}',
                            detail=f'Tổng nhóm = {s:,} USD; dòng tổng = {total[col]:,} USD; tỷ lệ = {share:.4f}'))
    # Kiểm tra: tiểu mục không vượt nhóm cha
    for r in rows:
        if r['level'] == 'subitem':
            p = next((g for g in groups if g['product_group'] == r['parent']), None)
            for col in ('value_usd_month', 'value_usd_ytd'):
                if p and r[col] and p[col] and r[col] > p[col]:
                    log.append(dict(file=file_name, line='', check='subitem_exceeds_parent',
                                    detail=f'{r["product_group"]} > {p["product_group"]} ({col})'))
    return rows, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--out', default='panel.csv')
    ap.add_argument('--log', default='cleaning_log.csv')
    a = ap.parse_args()
    all_rows, all_log = [], []
    for f in a.files:
        rows, log = parse(read_text(f), Path(f).name, sha256(f))
        all_rows += rows
        all_log += log
    with open(a.out, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=list(all_rows[0].keys()))
        w.writeheader(); w.writerows(all_rows)
    with open(a.log, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=['file', 'line', 'check', 'detail'])
        w.writeheader(); w.writerows(all_log)
    print(f'{len(all_rows)} dòng → {a.out}; {len(all_log)} mục nhật ký → {a.log}')


if __name__ == '__main__':
    sys.exit(main())

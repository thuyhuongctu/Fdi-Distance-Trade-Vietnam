"""Tải lại nhập khẩu của Mỹ từ Trung Quốc năm 2017 (UN Comtrade) vào comtrade/part_*.csv.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương. Giấy phép MIT.

Số liệu thô của UN Comtrade không được kèm trong gói công bố; chạy tệp này để dựng lại
trước khi chạy build_exposure.py. Danh sách truy vấn cố định trong comtrade_urls.json.
"""
import csv
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'comtrade')
COLS = ['cmdCode', 'aggrLevel', 'primaryValue', 'isAggregate']

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(HERE, 'comtrade_urls.json'), encoding='utf-8') as f:
    urls = json.load(f)
for i, url in enumerate(urls):
    with urllib.request.urlopen(url, timeout=120) as r:
        data = json.load(r)['data']
    with open(os.path.join(OUT, f'part_{i:02d}.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for d in data:
            w.writerow([d['cmdCode'], d['aggrLevel'], float(d['primaryValue']), d['isAggregate']])
    print(f'part_{i:02d}: {len(data)} dòng')
    time.sleep(1)

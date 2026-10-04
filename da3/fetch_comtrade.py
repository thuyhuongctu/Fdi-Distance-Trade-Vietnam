"""Tải lại nhập khẩu của Mỹ từ Trung Quốc năm 2017 (UN Comtrade) vào comtrade/part_*.csv.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương. Giấy phép MIT.

Số liệu thô của UN Comtrade không được kèm trong gói công bố; chạy tệp này để dựng lại
trước khi chạy build_exposure.py. Danh sách truy vấn cố định trong comtrade_urls.json.
"""
import csv
import json
import os
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'comtrade')
COLS = ['cmdCode', 'aggrLevel', 'primaryValue', 'isAggregate']

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(HERE, 'comtrade_urls.json'), encoding='utf-8') as f:
    urls = json.load(f)


def get(url, tries=6):
    """API xem trước công khai giới hạn số lượt gọi (HTTP 403 «Quota Exceeded» hoặc 429): chờ rồi thử lại."""
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)['data']
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429) or k == tries - 1:
                raise
            wait = 15 * 2 ** k
            print(f'  HTTP {e.code} ({e.reason}); chờ {wait} giây rồi thử lại')
            time.sleep(wait)


for i, url in enumerate(urls):
    data = get(url)
    with open(os.path.join(OUT, f'part_{i:02d}.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for d in data:
            # Từ 10/2026 API trả aggrLevel rỗng: suy từ độ dài mã HS (2, 4 hoặc 6 chữ số)
            level = d['aggrLevel'] if d['aggrLevel'] is not None else len(d['cmdCode'])
            w.writerow([d['cmdCode'], level, float(d['primaryValue']), d['isAggregate']])
    print(f'part_{i:02d}: {len(data)} dòng')
    time.sleep(1)

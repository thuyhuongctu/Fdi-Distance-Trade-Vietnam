"""DA0 – Kiểm thử quy trình parse_flat.py → build_monthly.py → harmonise.py trên biểu mô phỏng.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Không dùng dữ liệu Hải quan đã mua: mọi biểu ở đây là văn bản giả lập theo đúng bố cục
Biểu 017.T/018.T (dồn dòng như khi trích từ Google Drive). Mỗi kiểm thử chạy trong thư mục tạm.
Chạy: python3 test_da0.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse_flat  # noqa: E402

HEAD = 'Biểu số {form}/BCB-TC {kind} HÀNG HÓA CỦA DOANH NGHIỆP FDI Tháng {m} năm {y} {status} STT Tên nhóm hàng ĐVT Lượng Trị giá Lượng Trị giá'
TAIL = 'Ngày in: 15/09/2026 www.customs.gov.vn'


def sheet(direction, y, m, body, status='Sơ bộ'):
    form, kind = ('017.T', 'XUẤT KHẨU') if direction == 'export' else ('018.T', 'NHẬP KHẨU')
    return f'{HEAD.format(form=form, kind=kind, m=m, y=y, status=status)} {body} {TAIL}'


# Xuất khẩu 2024: có tháng 1 và 3, thiếu tháng 2 (phải suy từ cộng dồn).
EX_2024_01 = sheet('export', 2024, 1,
                   'TỔNG TRỊ GIÁ USD 1.000 1.000 '
                   '1 Hàng thủy sản USD 400 400 - Tôm Tấn 10 200 10 200 '
                   '2 Hạt điều USD 100 100 '
                   '3 Hàng hóa khác USD 500 500')
EX_2024_03 = sheet('export', 2024, 3,
                   'TỔNG TRỊ GIÁ USD 1.200 3.300 '
                   '1 Hàng thủy sản USD 500 1.400 '
                   '2 Hạt điều USD 100 300 '
                   '3 Hàng hóa khác USD 600 1.600')
# Nhập khẩu 2024-01, có STT trùng (như biểu 018.T tháng 8/2026).
IM_2024_01 = sheet('import', 2024, 1,
                   'TỔNG TRỊ GIÁ USD 800 800 '
                   '18 Than các loại Tấn 5 100 5 100 '
                   '18 Vải các loại USD 300 300 '
                   '19 Hàng hóa khác USD 400 400')
# Mẫu biểu mới từ 2026-03: dòng ghi nhớ không đánh số, không cộng vào tổng.
EX_2026_03 = sheet('export', 2026, 3,
                   'TỔNG TRỊ GIÁ USD 1.000 3.000 '
                   '1 Hàng thủy sản USD 300 900 '
                   '28 Kim loại thường khác USD 100 300 '
                   'Sản phẩm từ kim loại thường khác USD 50 150 '
                   '29 Hàng hóa khác USD 600 1.800')

FILES = {
    '2024-T1-XKHH cua DN FDI-SB.pdf': EX_2024_01,
    '2024-T3-XKHH cua DN FDI-SB.pdf': EX_2024_03,
    '2024-T4-XKHH cua DN FDI-SB.pdf': EX_2024_03,   # tải nhầm: tên ghi tháng 4, biểu in tháng 3
    '2024-T1-NKHH cua DN FDI-SB.pdf': IM_2024_01,
    '2026-T3-XKHH cua DN FDI-SB.pdf': EX_2026_03,
}


class ParseFlat(unittest.TestCase):
    def rows(self, text, title):
        out, log = parse_flat.parse_text(text, title)
        return {r['product_group']: r for r in out}, log

    def test_header_and_values(self):
        r, log = self.rows(EX_2024_01, '2024-T1-XKHH cua DN FDI-SB.pdf')
        tot = r['Tổng trị giá']
        self.assertEqual((tot['period'], tot['direction'], tot['status'], tot['level']),
                         ('2024-01', 'export', 'preliminary', 'total'))
        self.assertEqual((r['Hàng thủy sản']['item_no'], r['Hàng thủy sản']['value_usd_month']), ('1', 400))
        tom = r['Tôm']
        self.assertEqual((tom['level'], tom['parent'], tom['qty_month'], tom['value_usd_ytd']),
                         ('subitem', 'Hàng thủy sản', 10, 200))
        self.assertTrue(all(x['detail'].startswith('OK') for x in log if x['check'].startswith('sum_check')))

    def test_sum_mismatch_is_logged_not_fixed(self):
        bad = EX_2024_01.replace('3 Hàng hóa khác USD 500 500', '3 Hàng hóa khác USD 400 500')
        r, log = self.rows(bad, 't')
        self.assertEqual(r['Hàng hóa khác']['value_usd_month'], 400)
        self.assertTrue(any(x['check'] == 'sum_check_value_usd_month' and x['detail'].startswith('LỆCH') for x in log))

    def test_duplicate_item_number(self):
        _, log = self.rows(IM_2024_01, '2024-T1-NKHH cua DN FDI-SB.pdf')
        self.assertEqual([x['check'] for x in log].count('duplicate_item_number'), 1)

    def test_2026_memo_row(self):
        r, log = self.rows(EX_2026_03, '2026-T3-XKHH cua DN FDI-SB.pdf')
        memo = r['Sản phẩm từ kim loại thường khác']
        self.assertEqual((memo['level'], memo['item_no'], memo['parent']), ('subitem', '', 'Kim loại thường khác'))
        self.assertTrue(all(x['detail'].startswith('OK') for x in log if x['check'].startswith('sum_check')))

    def test_official_flag_from_title(self):
        r, _ = self.rows(EX_2024_01.replace('Sơ bộ', 'Chính thức'), '2013-T1-XKHH cua DN FDI-CT.pdf')
        self.assertEqual(r['Tổng trị giá']['status'], 'official')


class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        raw = os.path.join(cls.tmp, 'raw')
        os.makedirs(raw)
        for i, (title, text) in enumerate(FILES.items()):
            with open(os.path.join(raw, f'{i:02d}.txt'), 'w', encoding='utf-8') as f:
                f.write(f'#META\t{title}\tfid{i}\t2026-09-23T00:00:00Z\n{text}')
        for s in ('parse_flat.py', 'build_monthly.py', 'harmonise.py'):
            shutil.copy(os.path.join(HERE, s), cls.tmp)
        cls.out = {}
        for cmd in (['parse_flat.py', 'raw'], ['build_monthly.py'], ['harmonise.py']):
            res = subprocess.run([sys.executable] + cmd, cwd=cls.tmp, capture_output=True, text=True)
            if res.returncode:
                raise RuntimeError(f'{cmd[0]} lỗi:\n{res.stderr}')
            cls.out[cmd[0]] = res.stdout
        rd = lambda n: pd.read_csv(os.path.join(cls.tmp, n), dtype={'item_no': str})  # noqa: E731
        cls.clean, cls.log, cls.harm = rd('monthly_clean.csv'), rd('cleaning_log_monthly.csv'), rd('monthly_harmonised.csv')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_parse_reports_no_sum_mismatch(self):
        self.assertIn('5 tệp; 0 kiểm tra tổng bị lệch', self.out['parse_flat.py'])

    def test_mislabelled_upload_dropped(self):
        self.assertIn('2024-T4-XKHH cua DN FDI-SB.pdf', set(self.log.loc[self.log.check == 'mislabelled_upload', 'file']))
        self.assertNotIn('2024-T4-XKHH cua DN FDI-SB.pdf', set(self.clean['source_title']))

    def test_missing_month_imputed_from_ytd(self):
        feb = self.clean[(self.clean.period == '2024-02') & (self.clean.direction == 'export')]
        self.assertTrue((feb['imputed_from_ytd'] == 1).all())
        v = feb.set_index('product_group')['value_usd_month']
        self.assertEqual((v['Tổng trị giá'], v['Hàng thủy sản'], v['Hạt điều'], v['Hàng hóa khác']), (1100, 500, 100, 500))
        self.assertIn('imputed_month', set(self.log['check']))
        self.assertTrue(feb['limitation'].str.endswith('suy từ cộng dồn').all())

    def test_four_provenance_fields(self):
        for c in ('source', 'period', 'method', 'limitation'):
            self.assertFalse(self.clean[c].isna().any(), c)

    def test_ytddiff_column(self):
        t = self.clean[(self.clean.level == 'total') & (self.clean.direction == 'export')].set_index('period')
        self.assertEqual(t.loc['2024-01', 'value_usd_month_ytddiff'], 1000)
        self.assertEqual(t.loc['2024-03', 'value_usd_month_ytddiff'], 1200)

    def test_harmonised_sums_equal_totals(self):
        self.assertIn('≠ dòng tổng (>2 USD): 0 /', self.out['harmonise.py'])
        tot = self.clean[self.clean.level == 'total'].set_index(['direction', 'period'])['value_usd_month']
        s = self.harm.groupby(['direction', 'period'])['value_usd_month'].sum()
        self.assertTrue(((s - tot.loc[s.index]).abs() <= 2).all())

    def test_r2_new_2024_groups_go_to_other(self):
        h = self.harm.set_index(['direction', 'period', 'group_h'])['value_usd_month']
        self.assertEqual(h[('export', '2024-01', 'Hàng hóa khác')], 600)   # 500 + Hạt điều 100
        self.assertEqual(h[('import', '2024-01', 'Hàng hóa khác')], 500)   # 400 + Than 100
        self.assertNotIn('Hạt điều', set(self.harm['group_h']))

    def test_r3_2026_memo_moved_from_other(self):
        h = self.harm.set_index(['direction', 'period', 'group_h'])['value_usd_month']
        self.assertEqual(h[('export', '2026-03', 'Kim loại thường khác và sản phẩm')], 150)
        self.assertEqual(h[('export', '2026-03', 'Hàng hóa khác')], 550)


if __name__ == '__main__':
    unittest.main(verbosity=2)

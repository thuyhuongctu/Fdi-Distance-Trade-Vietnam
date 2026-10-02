"""DA3 – Bảng ánh xạ nhóm hàng Hải quan (chuỗi hài hòa) → mã HS4/HS6, và nhóm đầu vào nhập khẩu tương ứng.

© 2026 PGS.TS. Phan Anh Tú & NCS. Đỗ Thùy Hương.

Cố định TRƯỚC khi xem số liệu kết quả (Phần 3 tiền đăng ký DA3). Mã HS theo HS2012 (danh mục Comtrade năm 2017).
Phần tử 4 chữ số = cả nhóm HS4; 6 chữ số = phân nhóm HS6; 'a-b' = dải HS4 liên tục.
Chạy: python3 hs_concordance.py  → hs_concordance.csv, input_match.csv
"""
import csv

def rng(a, b):
    return [f'{i:04d}' for i in range(int(a), int(b) + 1)]

ELEC = ['8471', '8473', '8518', '8519', '8521', '8522', '8523', '8527', '8528', '8529', '8531', '8532', '8533', '8534',
        '8540', '8541', '8542', '8543', '852550', '852560']
CAMERA = ['852580', '9006', '9007']
MACH = [h for h in rng(8401, 8487) if h not in ('8471', '8473')] + \
       [h for h in rng(8501, 8548) if h not in ELEC + ['8517', '8525', '8544']] + \
       [h for h in rng(9001, 9033) if h not in ('9006', '9007')]
WOOD_FURN = ['940161', '940169', '940330', '940340', '940350', '940360', '940391']

# nhóm XK hài hòa → (thành phần HS, nhóm NK đầu vào khớp, quy tắc DA3)
EXPORT = {
    'Hàng thủy sản': (rng(301, 308) + ['1603', '1604', '1605'], [], 'include'),
    'Hàng rau quả': (rng(701, 714) + [h for h in rng(802, 814)] + rng(2001, 2009), [], 'include'),
    'Cà phê': (['0901', '2101'], [], 'exclude: hàng thô theo giá thế giới (quy tắc 3)'),
    'Hạt tiêu': (['0904'], [], 'exclude: hàng thô theo giá thế giới (quy tắc 3)'),
    'Bánh kẹo và các sản phẩm từ ngũ cốc': (['1704', '1806'] + rng(1901, 1905), ['Lúa mì'], 'include'),
    'Hóa chất': (rng(2801, 2853) + rng(2901, 2942), ['Hóa chất'], 'include'),
    'Sản phẩm hóa chất': (rng(3001, 3006) + rng(3101, 3105) + rng(3201, 3215) + rng(3301, 3307) + rng(3401, 3407)
                          + rng(3501, 3507) + rng(3601, 3606) + rng(3701, 3707) + rng(3801, 3826),
                          ['Hóa chất', 'Sản phẩm hóa chất'], 'include'),
    'Chất dẻo nguyên liệu': (rng(3901, 3914), ['Hóa chất'], 'include'),
    'Sản phẩm từ chất dẻo': (rng(3915, 3926), ['Chất dẻo nguyên liệu'], 'include'),
    'Cao su': (rng(4001, 4006), [], 'exclude: hàng thô theo giá thế giới (quy tắc 3)'),
    'Sản phẩm từ cao su': (rng(4007, 4017), ['Cao su'], 'include'),
    'Túi xách, ví,vali, mũ, ô, dù': (['4202'] + rng(6501, 6507) + rng(6601, 6603), ['Nguyên phụ liệu dệt, may, da, giày'], 'include'),
    'Gỗ và sản phẩm gỗ': (rng(4401, 4421) + WOOD_FURN, ['Gỗ và sản phẩm gỗ'], 'include'),
    'Giấy và các sản phẩm từ giấy': (rng(4801, 4823), ['Giấy các loại'], 'include'),
    'Xơ, sợi dệt các loại': (['5004', '5005', '5006'] + rng(5106, 5110) + rng(5204, 5207) + rng(5306, 5308)
                             + rng(5401, 5406) + rng(5501, 5511), ['Bông các loại', 'Xơ, sợi dệt các loại'], 'include'),
    'Hàng dệt, may': (rng(6101, 6117) + rng(6201, 6217) + rng(6301, 6310),
                      ['Vải các loại', 'Xơ, sợi dệt các loại', 'Bông các loại', 'Nguyên phụ liệu dệt, may, da, giày'], 'include'),
    'Giày dép các loại': (rng(6401, 6406), ['Nguyên phụ liệu dệt, may, da, giày'], 'include'),
    'Sản phẩm gốm, sứ': (rng(6901, 6914), [], 'include'),
    'Thủy tinh và các sản phẩm từ thủy tinh': (rng(7001, 7020), [], 'include'),
    'Đá quý, kim loại quý và sản phẩm': (rng(7101, 7118), [], 'exclude: hàng thô theo giá thế giới (quy tắc 3)'),
    'Sắt thép các loại': (rng(7201, 7229), ['Sắt thép các loại'], 'include'),
    'Sản phẩm từ sắt thép': (rng(7301, 7326), ['Sắt thép các loại'], 'include'),
    'Kim loại thường khác và sản phẩm': (rng(7401, 7419) + rng(7501, 7508) + rng(7601, 7616) + rng(7801, 7806)
                                         + rng(7901, 7907) + rng(8001, 8007) + rng(8101, 8113) + rng(8201, 8215) + rng(8301, 8311),
                                         ['Kim loại thường khác', 'Sản phẩm từ kim loại thường khác'], 'include'),
    'Máy vi tính, sản phẩm điện tử và linh kiện': (ELEC, ['Máy vi tính, sản phẩm điện tử và linh kiện'], 'include'),
    'Điện thoại các loại và linh kiện': (['8517'], ['Điện thoại các loại và linh kiện'], 'include'),
    'Máy ảnh, máy quay phim và linh kiện': (CAMERA, ['Máy vi tính, sản phẩm điện tử và linh kiện'], 'include'),
    'Máy móc, thiết bị, dụng cụ phụ tùng khác': (MACH, ['Máy móc, thiết bị, dụng cụ, phụ tùng khác'], 'include'),
    'Dây điện và dây cáp điện': (['8544'], ['Dây điện và dây cáp điện', 'Kim loại thường khác'], 'include'),
    'Phương tiện vận tải và phụ tùng': (rng(8601, 8609) + rng(8701, 8716) + rng(8801, 8805) + rng(8901, 8908),
                                        ['Linh kiện, phụ tùng ô tô', 'Phương tiện vận tải khác và phụ tùng'], 'include'),
    'Hàng hóa khác': ([], [], 'exclude: nhóm còn lại (quy tắc 2)'),
}

if __name__ == '__main__':
    seen = {}
    with open('hs_concordance.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['export_group', 'hs', 'level', 'da3_rule'])
        for g, (codes, _, rule) in EXPORT.items():
            for c in codes:
                assert c not in seen, f'{c} thuộc cả «{seen[c]}» và «{g}»'
                seen[c] = g
                w.writerow([g, c, f'HS{len(c)}', rule])
    with open('input_match.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['export_group', 'import_group'])
        for g, (_, inputs, rule) in EXPORT.items():
            for i in inputs:
                w.writerow([g, i])
    # HS6 nằm trong HS4 đã gán cho nhóm khác → lỗi
    for c, g in seen.items():
        if len(c) == 6 and c[:4] in seen:
            raise SystemExit(f'{c} ({g}) chồng lên HS4 {c[:4]} ({seen[c[:4]]})')
    print(len(seen), 'mã HS gán cho', sum(1 for v in EXPORT.values() if v[0]), 'nhóm')

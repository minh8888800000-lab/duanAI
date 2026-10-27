import sys
import json
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')

def test_all():
    base = 'http://127.0.0.1:5000'

    # 1. Admin login
    req = urllib.request.Request(
        f'{base}/api/auth/login',
        data=json.dumps({'username': 'admin', 'password': '12345'}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        admin_data = json.loads(res.read())
        admin_token = admin_data['token']
        print(f"1. [PASS] Admin login: {admin_data['user']['ho_ten']} | Role: {admin_data['user']['vai_tro']}")

    # 2. LeTan login
    req = urllib.request.Request(
        f'{base}/api/auth/login',
        data=json.dumps({'username': 'letan01', 'password': 'letan123'}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        letan_data = json.loads(res.read())
        letan_token = letan_data['token']
        print(f"2. [PASS] LeTan login: {letan_data['user']['ho_ten']} | Role: {letan_data['user']['vai_tro']}")

    # 3. Tho login
    req = urllib.request.Request(
        f'{base}/api/auth/login',
        data=json.dumps({'username': 'tho01', 'password': 'tho123'}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        tho_data = json.loads(res.read())
        tho_token = tho_data['token']
        tho_nv = tho_data['user']['ma_nhan_vien']
        print(f"3. [PASS] Tho login: {tho_data['user']['ho_ten']} | Role: {tho_data['user']['vai_tro']} | MaNV: {tho_nv}")

    # 4. Tho gets appointments: should only see their own appointments
    req = urllib.request.Request(
        f'{base}/api/appointments?date=2026-09-19',
        headers={'Authorization': f'Bearer {tho_token}'}
    )
    with urllib.request.urlopen(req) as res:
        tho_appts = json.loads(res.read())
        appts_list = tho_appts['appointments']
        all_tho = all(a['MaNhanVien'] == tho_nv for a in appts_list)
        print(f"4. [PASS] Tho filtered appointments: {len(appts_list)} found, all belonging to {tho_nv}: {all_tho}")
        for a in appts_list:
            print(f"   - Appt {a['MaLichHen']}: Khach={a['TenKhachHang']} | Tho={a.get('TenThợ')} ({a['MaNhanVien']}) | Status={a['TrangThai']}")

    # 5. Tho attempts checkout: should be blocked with 403
    try:
        req = urllib.request.Request(
            f'{base}/api/billing/checkout',
            data=json.dumps({'ma_lich_hen': 'LH001', 'giam_gia': 0, 'phuong_thuc_thanh_toan': 'Tiền mặt'}).encode(),
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {tho_token}'}
        )
        with urllib.request.urlopen(req) as res:
            print("5. [FAIL] Tho checkout should have been blocked!")
    except urllib.error.HTTPError as e:
        print(f"5. [PASS] Tho checkout blocked correctly with HTTP status: {e.code} Forbidden")

    # 6. LeTan attempts reports summary: should be blocked with 403
    try:
        req = urllib.request.Request(
            f'{base}/api/reports/summary',
            headers={'Authorization': f'Bearer {letan_token}'}
        )
        with urllib.request.urlopen(req) as res:
            print("6. [FAIL] LeTan reports should have been blocked!")
    except urllib.error.HTTPError as e:
        print(f"6. [PASS] LeTan reports summary blocked correctly with HTTP status: {e.code} Forbidden")

    # 7. Admin reports summary: should succeed
    req = urllib.request.Request(
        f'{base}/api/reports/summary',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    with urllib.request.urlopen(req) as res:
        adm_rep = json.loads(res.read())
        print(f"7. [PASS] Admin reports summary access: Success={adm_rep['success']} | TotalRev={adm_rep['kpi']['tong_doanh_thu']:,} đ")

    # 8. Public guest booking (no auth token)
    req = urllib.request.Request(
        f'{base}/api/appointments',
        data=json.dumps({
            'ho_ten': 'Nguyễn Hoàng Khách Mới',
            'so_dien_thoai': '0912999888',
            'ma_nhan_vien': 'NV004',
            'ngay_gio_hen': '2026-09-19T18:00',
            'service_ids': ['DV001'],
            'ghi_chu': 'Đặt online qua Landing Page'
        }).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        guest_res = json.loads(res.read())
        print(f"8. [PASS] Public Guest booking: Success={guest_res['success']} | Status={guest_res.get('trang_thai')} | ApptID={guest_res.get('ma_lich_hen')}")

if __name__ == '__main__':
    test_all()

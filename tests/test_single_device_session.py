import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def req(url, method='GET', data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req_obj = urllib.request.Request(url, method=method, headers=headers)
    if data:
        req_obj.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req_obj) as res:
            return res.status, json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))

def main():
    print("=== KIỂM THỬ TÍNH NĂNG 1 TÀI KHOẢN CHỈ ĐĂNG NHẬP TRÊN 1 THIẾT BỊ ===\n")

    # 1. Device A đăng nhập
    statusA, dataA = req('http://127.0.0.1:5000/api/auth/login', 'POST', {'username': 'admin', 'password': 'admin123'})
    assert statusA == 200, f"Device A login failed: {dataA}"
    token_A = dataA['token']
    print("[OK] 1. Thiet bi A dang nhap thanh cong voi tai khoan admin.")

    # 2. Device A truy cập bình thường
    statusA_me, dataA_me = req('http://127.0.0.1:5000/api/auth/me', 'GET', token=token_A)
    assert statusA_me == 200 and dataA_me.get('success'), f"Device A me failed: {dataA_me}"
    print("[OK] 2. Thiet bi A goi /api/auth/me hoat dong binh thuong.")

    # 3. Device B đăng nhập CÙNG tài khoản admin
    statusB, dataB = req('http://127.0.0.1:5000/api/auth/login', 'POST', {'username': 'admin', 'password': 'admin123'})
    assert statusB == 200, f"Device B login failed: {dataB}"
    token_B = dataB['token']
    print("[OK] 3. Thiet bi B dang nhap CUNG tai khoan admin tren thiet bi khac.")

    # 4. Device B truy cập bình thường
    statusB_me, dataB_me = req('http://127.0.0.1:5000/api/auth/me', 'GET', token=token_B)
    assert statusB_me == 200 and dataB_me.get('success'), f"Device B me failed: {dataB_me}"
    print("[OK] 4. Thiet bi B goi /api/auth/me hoat dong tot.")

    # 5. Device A gửi request -> PHẢI BỊ VĂNG RA (401, kicked: True, code: CONCURRENT_LOGIN)
    statusA_kicked, dataA_kicked = req('http://127.0.0.1:5000/api/auth/me', 'GET', token=token_A)
    print(f"[KICKED CHECK] Status: {statusA_kicked}, Response: {dataA_kicked}")
    assert statusA_kicked == 401, f"Device A should be kicked with 401, got {statusA_kicked}"
    assert dataA_kicked.get('kicked') is True, f"Expected kicked=True, got {dataA_kicked}"
    assert dataA_kicked.get('code') == 'CONCURRENT_LOGIN', f"Expected CONCURRENT_LOGIN, got {dataA_kicked}"
    print(f"[OK] 5. THANH CONG: Thiet bi A da bi VANG RA ngay lap tuc!")
    print(f"     Thong bao: \"{dataA_kicked.get('error')}\"")

    # 6. Device A gọi các API khác cũng bị văng (ví dụ /api/accounts)
    statusA_acc, dataA_acc = req('http://127.0.0.1:5000/api/accounts', 'GET', token=token_A)
    assert statusA_acc == 401 and dataA_acc.get('kicked') is True
    print("[OK] 6. Thiet bi A goi bat ky API nao cung bi chan va yeu cau dang nhap lai.")

    # 7. Device B đăng xuất
    status_logout, data_logout = req('http://127.0.0.1:5000/api/auth/logout', 'POST', token=token_B)
    assert status_logout == 200
    print("[OK] 7. Thiet bi B dang xuat thanh cong.")

    print("\n>>> TAT CA CAC BUOC KIEM THU CONCURRENT SESSION DAT 100%! <<<")

if __name__ == '__main__':
    main()

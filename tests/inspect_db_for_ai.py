from backend.db import get_db_connection

conn = get_db_connection()
c = conn.cursor()

c.execute('SELECT MaDichVu, TenDichVu, GiaTien, ThoiGianThucHien FROM DichVu ORDER BY GiaTien DESC LIMIT 5')
print('Top Services:')
for r in c.fetchall():
    print(f"  - {r['MaDichVu']}: {r['TenDichVu']} -> {int(r['GiaTien']):,} VND ({r['ThoiGianThucHien']}p)")

c.execute('SELECT MaNhanVien, HoTen, ChucVu, TrangThaiRanh FROM NhanVien')
print('\nStylists:')
for r in c.fetchall():
    print(f"  - {r['MaNhanVien']}: {r['HoTen']} ({r['ChucVu']}) -> Ranh={r['TrangThaiRanh']}")

c.execute('''
    SELECT lh.MaLichHen, lh.NgayGioHen, lh.TrangThai, nv.HoTen as Tho, kh.HoTen as Khach
    FROM LichHen lh
    JOIN NhanVien nv ON lh.MaNhanVien=nv.MaNhanVien
    JOIN KhachHang kh ON lh.MaKhachHang=kh.MaKhachHang
    WHERE lh.TrangThai = 'Đang phục vụ'
''')
print('\nIn-service Appts:')
for r in c.fetchall():
    print(f"  - {r['MaLichHen']}: {r['NgayGioHen']} | Tho: {r['Tho']} | Khach: {r['Khach']}")

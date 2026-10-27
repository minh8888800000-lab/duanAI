import sqlite3

conn = sqlite3.connect('database/salon_hair.db')
cursor = conn.cursor()
cursor.execute("UPDATE TaiKhoan SET MatKhau = 'admin123' WHERE TenDangNhap = 'admin'")
conn.commit()
cursor.execute("SELECT MaTaiKhoan, TenDangNhap, MatKhau FROM TaiKhoan WHERE TenDangNhap = 'admin'")
print("Admin updated:", cursor.fetchone())
conn.close()

"""
Automated Verification & Integrity Test Suite for SQLite Database Schema
Verifies: Entity Integrity, Foreign Keys, ON DELETE behaviors, Filtered Unique Index, CHECK Constraints.
"""

import os
import sqlite3
import sys
import unittest

# Ensure UTF-8 output
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")
SEED_PATH = os.path.join(DB_DIR, "seed.sql")


class TestDatabaseSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Use in-memory database with schema & seed for high-speed, isolated testing."""
        cls.conn = sqlite3.connect(":memory:")
        cls.conn.row_factory = sqlite3.Row
        cls.conn.execute("PRAGMA foreign_keys = ON;")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.conn.executescript(f.read())

        with open(SEED_PATH, "r", encoding="utf-8") as f:
            cls.conn.executescript(f.read())

    def setUp(self):
        # Create a fresh in-memory test database for each test method to isolate modifications
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.conn.executescript(f.read())
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            self.conn.executescript(f.read())

    def tearDown(self):
        self.conn.close()

    def test_all_tables_exist(self):
        """Verify that all 8 core tables are created."""
        expected_tables = {
            "TaiKhoan",
            "NhanVien",
            "KhachHang",
            "DichVu",
            "LichHen",
            "ChiTietLichHen",
            "HoaDon",
            "TroLyAI",
        }
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row["name"] for row in cursor.fetchall()}
        self.assertTrue(expected_tables.issubset(tables))

    def test_filtered_unique_phone_customer(self):
        """Verify SoDienThoai is unique when not null, but multiple NULLs are allowed."""
        cursor = self.conn.cursor()
        # Multiple NULL phones (e.g. walk-ins) must succeed
        cursor.execute(
            "INSERT INTO KhachHang (MaKhachHang, HoTen, SoDienThoai) VALUES ('KH991', 'Khách Vãng Lai 2', NULL);"
        )
        cursor.execute(
            "INSERT INTO KhachHang (MaKhachHang, HoTen, SoDienThoai) VALUES ('KH992', 'Khách Vãng Lai 3', NULL);"
        )
        self.conn.commit()

        # Duplicate non-null phone must fail
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO KhachHang (MaKhachHang, HoTen, SoDienThoai) VALUES ('KH993', 'Trùng SĐT', '0988111222');"
            )

    def test_foreign_key_enforcement(self):
        """Verify foreign key constraint stops invalid customer ID in appointments."""
        cursor = self.conn.cursor()
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO LichHen (MaLichHen, MaKhachHang, MaNhanVien, NgayGioHen) "
                "VALUES ('LH999', 'KH_NONEXISTENT', 'NV003', '2026-09-25 10:00:00');"
            )

    def test_on_delete_cascade_appointment_details(self):
        """Verify deleting a LichHen cascades to its ChiTietLichHen."""
        cursor = self.conn.cursor()
        # Verify LH007 has 2 details and no invoice
        cursor.execute("SELECT COUNT(*) as cnt FROM ChiTietLichHen WHERE MaLichHen = 'LH007'")
        self.assertEqual(cursor.fetchone()["cnt"], 2)

        # Delete appointment LH007
        cursor.execute("DELETE FROM LichHen WHERE MaLichHen = 'LH007'")
        self.conn.commit()

        # Check ChiTietLichHen for LH007 is gone
        cursor.execute("SELECT COUNT(*) as cnt FROM ChiTietLichHen WHERE MaLichHen = 'LH007'")
        self.assertEqual(cursor.fetchone()["cnt"], 0)

    def test_on_delete_restrict_service(self):
        """Verify deleting a DichVu currently in an appointment fails with RESTRICT."""
        cursor = self.conn.cursor()
        # DV001 is used in LH001
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("DELETE FROM DichVu WHERE MaDichVu = 'DV001'")

    def test_on_delete_set_null_tro_ly_ai(self):
        """Verify deleting KhachHang sets MaKhachHang to NULL in TroLyAI."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO KhachHang (MaKhachHang, HoTen, SoDienThoai) VALUES ('KH_TEST', 'Test KH', '0999999999')")
        cursor.execute("INSERT INTO TroLyAI (MaYeuCau, TenModelAI, ThoiGianXuLy, DuLieuPhanHoi, MaKhachHang) VALUES ('YC_TEST', 'gemini-1.5-flash', 120, 'Test phan hoi', 'KH_TEST')")
        self.conn.commit()

        # Delete customer
        cursor.execute("DELETE FROM KhachHang WHERE MaKhachHang = 'KH_TEST'")
        self.conn.commit()

        # Check TroLyAI.MaKhachHang became NULL
        cursor.execute("SELECT MaKhachHang FROM TroLyAI WHERE MaYeuCau = 'YC_TEST'")
        self.assertIsNone(cursor.fetchone()["MaKhachHang"])

        # Clean up
        cursor.execute("DELETE FROM TroLyAI WHERE MaYeuCau = 'YC_TEST'")
        self.conn.commit()

    def test_invoice_calculation_constraint(self):
        """Verify ThanhTien = TongTien - GiamGia check constraint."""
        cursor = self.conn.cursor()
        # Invalid math: Tong 200k, Giam 20k, but ThanhTien = 150k != 180k
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO HoaDon (MaHoaDon, MaLichHen, NgayTao, TongTien, GiamGia, ThanhTien, PhuongThucThanhToan) "
                "VALUES ('HD999', 'LH003', '2026-09-19 15:00:00', 200000, 20000, 150000, 'Tiền mặt');"
            )

    def test_role_enum_constraint(self):
        """Verify TaiKhoan.VaiTro must be Admin, LeTan, or Tho."""
        cursor = self.conn.cursor()
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO TaiKhoan (MaTaiKhoan, TenDangNhap, MatKhau, VaiTro) "
                "VALUES ('TK999', 'hacker', '123', 'SuperUser');"
            )


if __name__ == "__main__":
    unittest.main()

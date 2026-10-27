"""
Database Initialization and Migration Script for AI-Augmented Hair Salon Management System.
Connects to SQLite, sets foreign keys, executes schema and seeds sample data.
"""

import os
import sqlite3
import sys

# Configure UTF-8 output for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "salon_hair.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")
SEED_PATH = os.path.join(DB_DIR, "seed.sql")


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Creates a database connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database(db_path: str = DB_PATH, reset: bool = False):
    """Initializes the database schema and seeds initial data."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if reset and os.path.exists(db_path):
        print(f"[*] Resetting existing database at: {db_path}")
        os.remove(db_path)

    print(f"[*] Initializing SQLite Database at: {db_path}")
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        # 1. Execute Schema
        print(f"[*] Executing schema from: {SCHEMA_PATH}")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
        print("[+] Schema created successfully.")

        # 2. Execute Seed Data
        print(f"[*] Seeding data from: {SEED_PATH}")
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            seed_sql = f.read()
        cursor.executescript(seed_sql)
        conn.commit()
        print("[+] Seed data inserted successfully.")

        # 3. Print Table Summary
        tables = [
            "TaiKhoan",
            "NhanVien",
            "KhachHang",
            "DichVu",
            "LichHen",
            "ChiTietLichHen",
            "HoaDon",
            "TroLyAI",
        ]

        print("\n" + "=" * 55)
        print(f"{'BẢNG (TABLE)':<20} | {'SỐ LƯỢNG BẢN GHI (COUNT)':<30}")
        print("=" * 55)
        for tbl in tables:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {tbl}")
            count = cursor.fetchone()["cnt"]
            print(f"{tbl:<20} | {count:<30}")
        print("=" * 55 + "\n")

    except sqlite3.Error as e:
        print(f"[!] Database Error: {e}", file=sys.stderr)
        conn.rollback()
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    init_database(reset=reset_flag)

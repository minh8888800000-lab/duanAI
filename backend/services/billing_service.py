"""
Billing and Payment Service.
Handles UC006: Invoice generation, discounts, payments, financial integrity, and printable receipt data.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import uuid
from backend.db import get_db_connection


class BillingService:
    @staticmethod
    def get_checkout_preview(ma_lich_hen: str) -> Dict[str, Any]:
        """Loads appointment and service breakdown to prepare invoice."""
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT lh.MaLichHen, lh.NgayGioHen, lh.TrangThai,
                       kh.MaKhachHang, kh.HoTen as TenKhachHang, kh.SoDienThoai,
                       nv.MaNhanVien, nv.HoTen as TenThợ
                FROM LichHen lh
                JOIN KhachHang kh ON lh.MaKhachHang = kh.MaKhachHang
                JOIN NhanVien nv ON lh.MaNhanVien = nv.MaNhanVien
                WHERE lh.MaLichHen = ?
                """,
                (ma_lich_hen,),
            )
            appt = cursor.fetchone()
            if not appt:
                return {"success": False, "message": "Không tìm thấy lịch hẹn."}

            # Check if invoice already exists
            cursor.execute("SELECT * FROM HoaDon WHERE MaLichHen = ?", (ma_lich_hen,))
            existing_inv = cursor.fetchone()
            if existing_inv:
                return {
                    "success": True,
                    "already_paid": True,
                    "invoice": dict(existing_inv),
                    "appointment": dict(appt),
                }

            # Fetch services
            cursor.execute(
                """
                SELECT ctlh.MaDichVu, ctlh.GiaTaiThoiDiemDat, dv.TenDichVu, dv.ThoiGianThucHien
                FROM ChiTietLichHen ctlh
                JOIN DichVu dv ON ctlh.MaDichVu = dv.MaDichVu
                WHERE ctlh.MaLichHen = ?
                """,
                (ma_lich_hen,),
            )
            services = [dict(s) for s in cursor.fetchall()]
            tong_tien = sum(s["GiaTaiThoiDiemDat"] for s in services)

            return {
                "success": True,
                "already_paid": False,
                "appointment": dict(appt),
                "services": services,
                "tong_tien": tong_tien,
            }
        finally:
            conn.close()

    @staticmethod
    def create_invoice(
        ma_lich_hen: str,
        giam_gia: float = 0.0,
        phuong_thuc_thanh_toan: str = "Tiền mặt",
        extra_services: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Creates an invoice, updates appointment to 'Hoàn thành',
        sets stylist to free ('TrangThaiRanh' = 1), and validates math integrity.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 1. Verify appointment exists and is not already paid
            cursor.execute(
                """
                SELECT lh.MaLichHen, lh.MaNhanVien, kh.HoTen as TenKhachHang, nv.HoTen as TenThợ
                FROM LichHen lh
                JOIN KhachHang kh ON lh.MaKhachHang = kh.MaKhachHang
                JOIN NhanVien nv ON lh.MaNhanVien = nv.MaNhanVien
                WHERE lh.MaLichHen = ?
                """,
                (ma_lich_hen,),
            )
            appt = cursor.fetchone()
            if not appt:
                return {"success": False, "message": "Lịch hẹn không tồn tại."}

            cursor.execute("SELECT MaHoaDon FROM HoaDon WHERE MaLichHen = ?", (ma_lich_hen,))
            if cursor.fetchone():
                return {"success": False, "message": "Lịch hẹn này đã được lập hóa đơn trước đó."}

            # 2. Add extra services if customer took more at counter
            if extra_services:
                for svc_id in extra_services:
                    cursor.execute("SELECT GiaTien FROM DichVu WHERE MaDichVu = ?", (svc_id,))
                    svc_row = cursor.fetchone()
                    if svc_row:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO ChiTietLichHen (MaLichHen, MaDichVu, GiaTaiThoiDiemDat)
                            VALUES (?, ?, ?)
                            """,
                            (ma_lich_hen, svc_id, svc_row["GiaTien"]),
                        )

            # 3. Calculate total price
            cursor.execute(
                "SELECT SUM(GiaTaiThoiDiemDat) as TongTien FROM ChiTietLichHen WHERE MaLichHen = ?",
                (ma_lich_hen,),
            )
            total_sum = cursor.fetchone()["TongTien"] or 0.0

            giam_gia = max(0.0, float(giam_gia))
            thanh_tien = max(0.0, total_sum - giam_gia)

            # 4. Generate invoice code: HDxxx
            cursor.execute("SELECT COUNT(*) as cnt FROM HoaDon")
            count = cursor.fetchone()["cnt"] + 1
            ma_hoa_don = f"HD{count:03d}"
            cursor.execute("SELECT 1 FROM HoaDon WHERE MaHoaDon = ?", (ma_hoa_don,))
            if cursor.fetchone():
                ma_hoa_don = f"HD{uuid.uuid4().hex[:6].upper()}"

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 5. Insert invoice
            cursor.execute(
                """
                INSERT INTO HoaDon (MaHoaDon, MaLichHen, NgayTao, TongTien, GiamGia, ThanhTien, PhuongThucThanhToan, TrangThaiThanhToan)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Đã thanh toán')
                """,
                (
                    ma_hoa_don,
                    ma_lich_hen,
                    now_str,
                    total_sum,
                    giam_gia,
                    thanh_tien,
                    phuong_thuc_thanh_toan,
                ),
            )

            # 6. Mark appointment completed
            cursor.execute(
                "UPDATE LichHen SET TrangThai = 'Hoàn thành' WHERE MaLichHen = ?",
                (ma_lich_hen,),
            )

            # 7. Release stylist to free state
            cursor.execute(
                "UPDATE NhanVien SET TrangThaiRanh = 1 WHERE MaNhanVien = ?",
                (appt["MaNhanVien"],),
            )

            conn.commit()

            return {
                "success": True,
                "message": "Tạo hóa đơn và thanh toán thành công!",
                "ma_hoa_don": ma_hoa_don,
                "tong_tien": total_sum,
                "giam_gia": giam_gia,
                "thanh_tien": thanh_tien,
                "phuong_thuc_thanh_toan": phuong_thuc_thanh_toan,
                "ngay_tao": now_str,
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "message": f"Lỗi lập hóa đơn: {str(e)}"}
        finally:
            conn.close()

    @staticmethod
    def get_invoice_receipt(ma_hoa_don: str) -> Dict[str, Any]:
        """Gets full printable invoice details for receipt voucher."""
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT hd.*, lh.NgayGioHen,
                       kh.HoTen as TenKhachHang, kh.SoDienThoai,
                       nv.HoTen as TenThợ
                FROM HoaDon hd
                JOIN LichHen lh ON hd.MaLichHen = lh.MaLichHen
                JOIN KhachHang kh ON lh.MaKhachHang = kh.MaKhachHang
                JOIN NhanVien nv ON lh.MaNhanVien = nv.MaNhanVien
                WHERE hd.MaHoaDon = ?
                """,
                (ma_hoa_don,),
            )
            inv = cursor.fetchone()
            if not inv:
                return {"success": False, "message": "Không tìm thấy hóa đơn."}

            invoice_dict = dict(inv)

            # Fetch services
            cursor.execute(
                """
                SELECT ctlh.GiaTaiThoiDiemDat, dv.TenDichVu
                FROM ChiTietLichHen ctlh
                JOIN DichVu dv ON ctlh.MaDichVu = dv.MaDichVu
                WHERE ctlh.MaLichHen = ?
                """,
                (invoice_dict["MaLichHen"],),
            )
            invoice_dict["danh_sach_dich_vu"] = [dict(s) for s in cursor.fetchall()]

            return {"success": True, "receipt": invoice_dict}
        finally:
            conn.close()

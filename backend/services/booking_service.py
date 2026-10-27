"""
Booking and Appointment Management Service.
Handles UC005: Appointment Scheduling, Time Aggregation, and Strict Stylist Collision/Overlap Prevention.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
from backend.db import get_db_connection


class BookingService:
    @staticmethod
    def calculate_services_duration_and_price(service_ids: List[str]) -> Dict[str, Any]:
        """Calculates total estimated duration and sum of prices for chosen services."""
        if not service_ids:
            return {"total_duration": 0, "total_price": 0, "services": []}

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            placeholders = ",".join(["?"] * len(service_ids))
            cursor.execute(
                f"SELECT MaDichVu, TenDichVu, GiaTien, ThoiGianThucHien FROM DichVu WHERE MaDichVu IN ({placeholders})",
                service_ids,
            )
            rows = cursor.fetchall()
            services = [dict(r) for r in rows]
            total_duration = sum(r["ThoiGianThucHien"] for r in rows)
            total_price = sum(r["GiaTien"] for r in rows)
            return {
                "total_duration": total_duration,
                "total_price": total_price,
                "services": services,
            }
        finally:
            conn.close()

    @classmethod
    def check_stylist_conflict(
        cls,
        ma_nhan_vien: str,
        start_time_str: str,
        total_duration_minutes: int,
        exclude_lich_hen_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Checks if the stylist has an overlapping active appointment.
        Overlap formula between [S1, E1] and [S2, E2]: (S1 < E2) AND (S2 < E1).
        Returns conflicting appointment info or None if available.
        """
        try:
            new_start = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Try ISO format
            new_start = datetime.fromisoformat(start_time_str.replace("T", " "))
        new_end = new_start + timedelta(minutes=total_duration_minutes)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Query active appointments for this stylist
            query = """
                SELECT lh.MaLichHen, lh.NgayGioHen, lh.TrangThai, kh.HoTen as TenKhachHang,
                       COALESCE(SUM(dv.ThoiGianThucHien), 30) as TongThoiGian
                FROM LichHen lh
                JOIN KhachHang kh ON lh.MaKhachHang = kh.MaKhachHang
                LEFT JOIN ChiTietLichHen ctlh ON lh.MaLichHen = ctlh.MaLichHen
                LEFT JOIN DichVu dv ON ctlh.MaDichVu = dv.MaDichVu
                WHERE lh.MaNhanVien = ?
                  AND lh.TrangThai NOT IN ('Đã hủy', 'Hoàn thành')
            """
            params = [ma_nhan_vien]
            if exclude_lich_hen_id:
                query += " AND lh.MaLichHen != ?"
                params.append(exclude_lich_hen_id)

            query += " GROUP BY lh.MaLichHen, lh.NgayGioHen, lh.TrangThai, kh.HoTen"
            cursor.execute(query, params)
            existing_appts = cursor.fetchall()

            for appt in existing_appts:
                ex_start_str = appt["NgayGioHen"]
                try:
                    ex_start = datetime.strptime(ex_start_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    ex_start = datetime.fromisoformat(ex_start_str.replace("T", " "))

                ex_duration = appt["TongThoiGian"] or 30
                ex_end = ex_start + timedelta(minutes=ex_duration)

                # Overlap condition
                if new_start < ex_end and ex_start < new_end:
                    return {
                        "conflicting_id": appt["MaLichHen"],
                        "customer_name": appt["TenKhachHang"],
                        "start_time": ex_start.strftime("%H:%M %d/%m/%Y"),
                        "end_time": ex_end.strftime("%H:%M %d/%m/%Y"),
                        "status": appt["TrangThai"],
                    }

            return None
        finally:
            conn.close()

    @classmethod
    def create_appointment(
        cls,
        ma_khach_hang: str,
        ma_nhan_vien: str,
        ngay_gio_hen: str,
        service_ids: List[str],
        ghi_chu: Optional[str] = None,
        trang_thai: str = "Đã xác nhận",
    ) -> Dict[str, Any]:
        """Creates a new appointment with transaction and conflict validation."""
        if not service_ids:
            return {"success": False, "message": "Vui lòng chọn ít nhất một dịch vụ."}

        # 1. Calculate duration and pricing
        service_calc = cls.calculate_services_duration_and_price(service_ids)
        total_duration = service_calc["total_duration"]
        services = service_calc["services"]

        if not services:
            return {"success": False, "message": "Danh sách dịch vụ không hợp lệ."}

        # 2. Check collision
        conflict = cls.check_stylist_conflict(ma_nhan_vien, ngay_gio_hen, total_duration)
        if conflict:
            return {
                "success": False,
                "message": (
                    f"Thợ đã có lịch bận ({conflict['customer_name']} từ {conflict['start_time']} "
                    f"đến {conflict['end_time']}). Vui lòng chọn khung giờ khác hoặc đổi thợ."
                ),
                "conflict": conflict,
            }

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Generate new appointment ID: LHxxx
            cursor.execute("SELECT COUNT(*) as cnt FROM LichHen")
            count = cursor.fetchone()["cnt"] + 1
            ma_lich_hen = f"LH{count:03d}"

            # Ensure uniqueness
            cursor.execute("SELECT 1 FROM LichHen WHERE MaLichHen = ?", (ma_lich_hen,))
            if cursor.fetchone():
                ma_lich_hen = f"LH{uuid.uuid4().hex[:6].upper()}"

            # Insert LichHen with dynamic status
            cursor.execute(
                """
                INSERT INTO LichHen (MaLichHen, MaKhachHang, MaNhanVien, NgayGioHen, TrangThai, GhiChu)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (ma_lich_hen, ma_khach_hang, ma_nhan_vien, ngay_gio_hen, trang_thai, ghi_chu),
            )

            # Insert ChiTietLichHen
            for svc in services:
                cursor.execute(
                    """
                    INSERT INTO ChiTietLichHen (MaLichHen, MaDichVu, GiaTaiThoiDiemDat, GhiChuDichVu)
                    VALUES (?, ?, ?, ?)
                    """,
                    (ma_lich_hen, svc["MaDichVu"], svc["GiaTien"], None),
                )

            # Update stylist busy state if appointment is starting now
            cursor.execute(
                "UPDATE NhanVien SET TrangThaiRanh = 0 WHERE MaNhanVien = ?",
                (ma_nhan_vien,),
            )

            conn.commit()
            return {
                "success": True,
                "message": "Đặt lịch thành công!",
                "ma_lich_hen": ma_lich_hen,
                "trang_thai": trang_thai,
                "total_duration": total_duration,
                "total_price": service_calc["total_price"],
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "message": f"Lỗi tạo lịch hẹn: {str(e)}"}
        finally:
            conn.close()

    @staticmethod
    def get_appointments(
        date_str: Optional[str] = None,
        ma_nhan_vien: Optional[str] = None,
        trang_thai: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves appointments with customer name, stylist name, and service breakdown."""
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT lh.MaLichHen, lh.NgayGioHen, lh.TrangThai, lh.GhiChu,
                       kh.MaKhachHang, kh.HoTen as TenKhachHang, kh.SoDienThoai, kh.GhiChuToc,
                       nv.MaNhanVien, nv.HoTen as TenThợ, nv.ChucVu,
                       hd.MaHoaDon, hd.ThanhTien
                FROM LichHen lh
                JOIN KhachHang kh ON lh.MaKhachHang = kh.MaKhachHang
                JOIN NhanVien nv ON lh.MaNhanVien = nv.MaNhanVien
                LEFT JOIN HoaDon hd ON lh.MaLichHen = hd.MaLichHen
                WHERE 1=1
            """
            params = []

            if date_str:
                query += " AND date(lh.NgayGioHen) = date(?)"
                params.append(date_str)

            if ma_nhan_vien:
                query += " AND lh.MaNhanVien = ?"
                params.append(ma_nhan_vien)

            if trang_thai:
                query += " AND lh.TrangThai = ?"
                params.append(trang_thai)

            if date_str:
                query += " ORDER BY lh.NgayGioHen ASC"
            else:
                query += " ORDER BY lh.NgayGioHen DESC"
            cursor.execute(query, params)
            appts = [dict(row) for row in cursor.fetchall()]

            # Fetch details for each appointment
            for appt in appts:
                cursor.execute(
                    """
                    SELECT ctlh.MaDichVu, ctlh.GiaTaiThoiDiemDat, dv.TenDichVu, dv.ThoiGianThucHien
                    FROM ChiTietLichHen ctlh
                    JOIN DichVu dv ON ctlh.MaDichVu = dv.MaDichVu
                    WHERE ctlh.MaLichHen = ?
                    """,
                    (appt["MaLichHen"],),
                )
                services = [dict(s) for s in cursor.fetchall()]
                appt["danh_sach_dich_vu"] = services
                appt["tong_thoi_gian"] = sum(s["ThoiGianThucHien"] for s in services)
                appt["tong_chi_phi"] = sum(s["GiaTaiThoiDiemDat"] for s in services)

            return appts
        finally:
            conn.close()

    @staticmethod
    def update_status(ma_lich_hen: str, trang_thai_moi: str) -> Dict[str, Any]:
        """Updates appointment status and auto-syncs stylist availability."""
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT MaNhanVien FROM LichHen WHERE MaLichHen = ?", (ma_lich_hen,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "message": "Không tìm thấy lịch hẹn."}

            ma_nhan_vien = row["MaNhanVien"]
            cursor.execute(
                "UPDATE LichHen SET TrangThai = ? WHERE MaLichHen = ?",
                (trang_thai_moi, ma_lich_hen),
            )

            # Auto-sync stylist status based on Document 2 page 10
            if trang_thai_moi == "Đang phục vụ":
                cursor.execute(
                    "UPDATE NhanVien SET TrangThaiRanh = 0 WHERE MaNhanVien = ?",
                    (ma_nhan_vien,),
                )
            elif trang_thai_moi in ("Hoàn thành", "Đã hủy"):
                cursor.execute(
                    "UPDATE NhanVien SET TrangThaiRanh = 1 WHERE MaNhanVien = ?",
                    (ma_nhan_vien,),
                )

            conn.commit()
            return {"success": True, "message": f"Cập nhật trạng thái '{trang_thai_moi}' thành công."}
        except Exception as e:
            conn.rollback()
            return {"success": False, "message": str(e)}
        finally:
            conn.close()

"""
Financial and Business Intelligence Reporting Service (UC007).
Calculates KPIs, Daily Revenue Trends, Payment Method Distributions, and Stylist Leaderboards.
"""

from typing import Dict, Any, List
from backend.db import get_db_connection


class ReportService:
    @staticmethod
    def get_comprehensive_financial_summary() -> Dict[str, Any]:
        """Calculates multi-dimensional financial and revenue statistics."""
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 1. Core KPIs
            cursor.execute("SELECT COALESCE(SUM(ThanhTien), 0) as TongDoanhThu, COUNT(*) as TongHoaDon FROM HoaDon")
            total_row = cursor.fetchone()
            tong_doanh_thu = total_row["TongDoanhThu"]
            tong_hoa_don = total_row["TongHoaDon"]

            # Today's revenue (with fallback to latest business date if mock dataset or off-hours)
            cursor.execute(
                "SELECT COALESCE(SUM(ThanhTien), 0) as DoanhThuHomNay, COUNT(*) as SoDonHomNay "
                "FROM HoaDon WHERE date(NgayTao) = date('now', 'localtime')"
            )
            today_row = cursor.fetchone()
            doanh_thu_hom_nay = today_row["DoanhThuHomNay"]
            so_don_hom_nay = today_row["SoDonHomNay"]

            if doanh_thu_hom_nay == 0:
                cursor.execute(
                    "SELECT COALESCE(SUM(ThanhTien), 0) as DoanhThuHomNay, COUNT(*) as SoDonHomNay "
                    "FROM HoaDon WHERE date(NgayTao) = (SELECT MAX(date(NgayTao)) FROM HoaDon)"
                )
                latest_day_row = cursor.fetchone()
                if latest_day_row and latest_day_row["DoanhThuHomNay"] > 0:
                    doanh_thu_hom_nay = latest_day_row["DoanhThuHomNay"]
                    so_don_hom_nay = latest_day_row["SoDonHomNay"]

            # This week's revenue (last 7 days, with fallback to latest 7 days of dataset)
            cursor.execute(
                "SELECT COALESCE(SUM(ThanhTien), 0) as DoanhThuTuanNay "
                "FROM HoaDon WHERE date(NgayTao) >= date('now', '-7 days', 'localtime')"
            )
            doanh_thu_tuan_nay = cursor.fetchone()["DoanhThuTuanNay"]
            if doanh_thu_tuan_nay == 0:
                cursor.execute(
                    "SELECT COALESCE(SUM(ThanhTien), 0) as DoanhThuTuanNay "
                    "FROM HoaDon WHERE date(NgayTao) >= (SELECT date(MAX(NgayTao), '-7 days') FROM HoaDon)"
                )
                fallback_week = cursor.fetchone()
                if fallback_week:
                    doanh_thu_tuan_nay = fallback_week["DoanhThuTuanNay"]

            # Average Order Value (AOV)
            aov = round(tong_doanh_thu / tong_hoa_don) if tong_hoa_don > 0 else 0

            # 2. Revenue By Payment Method (Tiền mặt, Chuyển khoản, Thẻ)
            cursor.execute(
                """
                SELECT PhuongThucThanhToan, COUNT(*) as SoDon, SUM(ThanhTien) as DoanhThu
                FROM HoaDon
                GROUP BY PhuongThucThanhToan
                ORDER BY DoanhThu DESC
                """
            )
            methods_raw = [dict(r) for r in cursor.fetchall()]
            revenue_by_method = []
            for m in methods_raw:
                pct = round((m["DoanhThu"] / tong_doanh_thu * 100), 1) if tong_doanh_thu > 0 else 0
                revenue_by_method.append({
                    "phuong_thuc": m["PhuongThucThanhToan"],
                    "so_don": m["SoDon"],
                    "doanh_thu": m["DoanhThu"],
                    "phan_tram": pct,
                })

            # 3. Revenue Trend By Day (Daily Breakdown for the last 7-10 days)
            cursor.execute(
                """
                SELECT date(NgayTao) as Ngay, SUM(ThanhTien) as DoanhThu, COUNT(*) as SoDon
                FROM HoaDon
                GROUP BY date(NgayTao)
                ORDER BY date(NgayTao) ASC
                """
            )
            revenue_by_day = [dict(r) for r in cursor.fetchall()]

            # 4. Stylist Revenue Performance Leaderboard
            cursor.execute(
                """
                SELECT nv.MaNhanVien, nv.HoTen as TenTho, nv.ChucVu,
                       COUNT(DISTINCT hd.MaHoaDon) as SoLuotPhucVu,
                       COALESCE(SUM(hd.ThanhTien), 0) as TongDoanhThuMangVe
                FROM NhanVien nv
                JOIN LichHen lh ON nv.MaNhanVien = lh.MaNhanVien
                JOIN HoaDon hd ON lh.MaLichHen = hd.MaLichHen
                GROUP BY nv.MaNhanVien, nv.HoTen, nv.ChucVu
                ORDER BY TongDoanhThuMangVe DESC
                """
            )
            stylist_leaderboard = [dict(r) for r in cursor.fetchall()]

            # 5. Top popular services
            cursor.execute(
                """
                SELECT dv.TenDichVu, COUNT(ctlh.MaDichVu) as SoLuotDat, SUM(ctlh.GiaTaiThoiDiemDat) as TongDoanhSo
                FROM ChiTietLichHen ctlh
                JOIN DichVu dv ON ctlh.MaDichVu = dv.MaDichVu
                JOIN LichHen lh ON ctlh.MaLichHen = lh.MaLichHen
                WHERE lh.TrangThai = 'Hoàn thành'
                GROUP BY dv.MaDichVu, dv.TenDichVu
                ORDER BY TongDoanhSo DESC LIMIT 6
                """
            )
            top_services = [dict(r) for r in cursor.fetchall()]

            # 6. Recent completed invoices
            cursor.execute(
                """
                SELECT hd.MaHoaDon, hd.ThanhTien, hd.NgayTao, hd.PhuongThucThanhToan,
                       kh.HoTen as TenKhachHang, nv.HoTen as TenTho
                FROM HoaDon hd
                JOIN LichHen lh ON hd.MaLichHen = lh.MaLichHen
                JOIN KhachHang kh ON lh.MaKhachHang = kh.MaKhachHang
                JOIN NhanVien nv ON lh.MaNhanVien = nv.MaNhanVien
                ORDER BY hd.NgayTao DESC LIMIT 8
                """
            )
            recent_invoices = [dict(r) for r in cursor.fetchall()]

            # 7. Total count stats
            cursor.execute("SELECT COUNT(*) as cnt FROM LichHen")
            tong_lich_hen = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) as cnt FROM LichHen WHERE date(NgayGioHen) = date('now', 'localtime')")
            lich_hen_hom_nay = cursor.fetchone()["cnt"]
            if lich_hen_hom_nay == 0:
                cursor.execute("SELECT COUNT(*) as cnt FROM LichHen WHERE date(NgayGioHen) = (SELECT MAX(date(NgayGioHen)) FROM LichHen)")
                lich_hen_hom_nay = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) as cnt FROM KhachHang")
            tong_khach = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) as cnt FROM NhanVien WHERE ChucVu LIKE '%Thợ%'")
            tong_tho = cursor.fetchone()["cnt"]

            return {
                "success": True,
                "kpi": {
                    "tong_doanh_thu": tong_doanh_thu,
                    "doanh_thu_hom_nay": doanh_thu_hom_nay,
                    "doanh_thu_tuan_nay": doanh_thu_tuan_nay,
                    "aov": aov,
                    "tong_hoa_don": tong_hoa_don,
                    "so_don_hom_nay": so_don_hom_nay,
                    "tong_lich_hen": tong_lich_hen,
                    "lich_hen_hom_nay": lich_hen_hom_nay,
                    "tong_khach": tong_khach,
                    "tong_tho": tong_tho,
                },
                "revenue_by_method": revenue_by_method,
                "revenue_by_day": revenue_by_day,
                "stylist_leaderboard": stylist_leaderboard,
                "top_services": top_services,
                "recent_invoices": recent_invoices,
            }
        finally:
            conn.close()

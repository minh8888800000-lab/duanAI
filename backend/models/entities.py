"""
Data Models representing entities and business methods exactly as specified
in Document 2: TÀI LIỆU THIẾT KẾ HƯỚNG ĐỐI TƯỢNG (MÔ HÌNH LỚP).
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.db import get_db_connection


class TaiKhoan:
    """
    2.1 Đặc tả lớp TaiKhoan (Tài khoản)
    Quản lý thông tin tài khoản đăng nhập và phân quyền truy cập.
    """
    def __init__(self, ma_tai_khoan: str, ten_dang_nhap: str, mat_khau: str, vai_tro: str):
        self.MaTaiKhoan = ma_tai_khoan
        self.TenDangNhap = ten_dang_nhap
        self.MatKhau = mat_khau
        self.VaiTro = vai_tro

    @staticmethod
    def DangNhap(ten_dang_nhap: str, mat_khau: str) -> Dict[str, Any]:
        """Phương thức DangNhap() theo đặc tả mục 2.1."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT tk.*, nv.MaNhanVien, nv.HoTen, nv.ChucVu 
                FROM TaiKhoan tk
                LEFT JOIN NhanVien nv ON tk.MaTaiKhoan = nv.MaTaiKhoan
                WHERE tk.TenDangNhap = ?
                """,
                (ten_dang_nhap,),
            )
            row = cursor.fetchone()
            if not row:
                return {"TrangThai": False, "ThongBao": "Tài khoản không tồn tại."}

            if row["MatKhau"] != mat_khau:
                return {"TrangThai": False, "ThongBao": "Mật khẩu không chính xác."}

            return {
                "TrangThai": True,
                "ThongBao": "Đăng nhập thành công!",
                "VaiTro": row["VaiTro"],
                "User": dict(row),
            }
        finally:
            conn.close()

    @staticmethod
    def DangXuat() -> Dict[str, Any]:
        """Phương thức DangXuat() theo đặc tả mục 2.1."""
        return {"TrangThai": True, "ThongBao": "Đã đăng xuất khỏi hệ thống."}

    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        d = {
            "ma_tai_khoan": self.MaTaiKhoan,
            "ten_dang_nhap": self.TenDangNhap,
            "vai_tro": self.VaiTro,
        }
        if include_password:
            d["mat_khau"] = self.MatKhau
        return d


class NhanVien:
    """
    2.2 Đặc tả lớp NhanVien (Nhân viên / Thợ)
    Quản lý thông tin cá nhân, chức vụ và trạng thái làm việc thực tế.
    """
    def __init__(
        self,
        ma_nhan_vien: str,
        ho_ten: str,
        so_dien_thoai: str,
        chuc_vu: str,
        trang_thai_ranh: bool = True,
        ma_tai_khoan: Optional[str] = None,
    ):
        self.MaNhanVien = ma_nhan_vien
        self.HoTen = ho_ten
        self.SoDienThoai = so_dien_thoai
        self.ChucVu = chuc_vu
        self.TrangThaiRanh = bool(trang_thai_ranh)
        self.MaTaiKhoan = ma_tai_khoan

    @staticmethod
    def CapNhatTrangThai(ma_nhan_vien: str, trang_thai_ranh: bool) -> Dict[str, Any]:
        """Phương thức CapNhatTrangThai() theo đặc tả mục 2.2."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE NhanVien SET TrangThaiRanh = ? WHERE MaNhanVien = ?",
                (1 if trang_thai_ranh else 0, ma_nhan_vien),
            )
            conn.commit()
            return {"TrangThaiCapNhat": True, "ThongBao": "Cập nhật trạng thái thành công."}
        except Exception as e:
            conn.rollback()
            return {"TrangThaiCapNhat": False, "ThongBao": str(e)}
        finally:
            conn.close()

    @staticmethod
    def CapNhatThongTinNhanVien(
        ma_nhan_vien: str, ho_ten: str, so_dien_thoai: str, chuc_vu: str
    ) -> Dict[str, Any]:
        """Phương thức CapNhatThongTinNhanVien() dành cho Admin/Quản lý theo đặc tả mục 2.2."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE NhanVien 
                SET HoTen = ?, SoDienThoai = ?, ChucVu = ? 
                WHERE MaNhanVien = ?
                """,
                (ho_ten, so_dien_thoai, chuc_vu, ma_nhan_vien),
            )
            conn.commit()
            return {"TrangThaiCapNhat": True, "ThongBao": "Cập nhật thông tin nhân viên thành công."}
        except Exception as e:
            conn.rollback()
            return {"TrangThaiCapNhat": False, "ThongBao": str(e)}
        finally:
            conn.close()

    @staticmethod
    def CapNhatHoSoCaNhan(ma_nhan_vien: str, so_dien_thoai: str) -> Dict[str, Any]:
        """Phương thức CapNhatHoSoCaNhan() theo đặc tả mục 2.2."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE NhanVien SET SoDienThoai = ? WHERE MaNhanVien = ?",
                (so_dien_thoai, ma_nhan_vien),
            )
            conn.commit()
            return {"TrangThaiCapNhat": True, "ThongBao": "Cập nhật số điện thoại thành công."}
        except Exception as e:
            conn.rollback()
            return {"TrangThaiCapNhat": False, "ThongBao": str(e)}
        finally:
            conn.close()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ma_nhan_vien": self.MaNhanVien,
            "ho_ten": self.HoTen,
            "so_dien_thoai": self.SoDienThoai,
            "chuc_vu": self.ChucVu,
            "trang_thai_ranh": self.TrangThaiRanh,
            "ma_tai_khoan": self.MaTaiKhoan,
        }


class KhachHang:
    """
    2.3 Đặc tả lớp KhachHang (Khách hàng)
    Quản lý hồ sơ khách hàng, số điện thoại, ghi chú chất tóc/công thức.
    """
    def __init__(
        self,
        ma_khach_hang: str,
        ho_ten: str = "Khách vãng lai",
        so_dien_thoai: Optional[str] = None,
        ghi_chu_toc: Optional[str] = None,
    ):
        self.MaKhachHang = ma_khach_hang
        self.HoTen = ho_ten
        self.SoDienThoai = so_dien_thoai
        self.GhiChuToc = ghi_chu_toc

    @staticmethod
    def CapNhatThongTinKhachHang(
        ma_khach_hang: str, ho_ten: str, so_dien_thoai: Optional[str], ghi_chu_toc: Optional[str]
    ) -> Dict[str, Any]:
        """Phương thức CapNhatThongTinKhachHang() theo đặc tả mục 2.3."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Check unique phone if provided
            if so_dien_thoai:
                cursor.execute(
                    "SELECT MaKhachHang FROM KhachHang WHERE SoDienThoai = ? AND MaKhachHang != ?",
                    (so_dien_thoai, ma_khach_hang),
                )
                if cursor.fetchone():
                    return {"TrangThaiCapNhat": False, "ThongBao": "Số điện thoại này đã tồn tại."}

            cursor.execute(
                """
                UPDATE KhachHang 
                SET HoTen = ?, SoDienThoai = ?, GhiChuToc = ? 
                WHERE MaKhachHang = ?
                """,
                (ho_ten, so_dien_thoai or None, ghi_chu_toc, ma_khach_hang),
            )
            conn.commit()
            return {"TrangThaiCapNhat": True, "ThongBao": "Cập nhật hồ sơ khách hàng thành công."}
        except Exception as e:
            conn.rollback()
            return {"TrangThaiCapNhat": False, "ThongBao": str(e)}
        finally:
            conn.close()

    @staticmethod
    def TraCuuLichSu(so_dien_thoai: str) -> Dict[str, Any]:
        """Phương thức TraCuuLichSu() theo đặc tả mục 2.3."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MaKhachHang, HoTen FROM KhachHang WHERE SoDienThoai = ?", (so_dien_thoai,))
            kh = cursor.fetchone()
            if not kh:
                return {"DanhSachLichSu": [], "ThongBao": "Khách hàng mới (chưa có lịch sử)."}

            cursor.execute(
                """
                SELECT lh.MaLichHen, lh.NgayGioHen, lh.TrangThai, nv.HoTen as TenTho,
                       hd.MaHoaDon, hd.ThanhTien
                FROM LichHen lh
                JOIN NhanVien nv ON lh.MaNhanVien = nv.MaNhanVien
                LEFT JOIN HoaDon hd ON lh.MaLichHen = hd.MaLichHen
                WHERE lh.MaKhachHang = ?
                ORDER BY lh.NgayGioHen DESC
                """,
                (kh["MaKhachHang"],),
            )
            history = [dict(r) for r in cursor.fetchall()]
            return {"DanhSachLichSu": history, "ThongBao": f"Tìm thấy {len(history)} lượt phục vụ."}
        finally:
            conn.close()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ma_khach_hang": self.MaKhachHang,
            "ho_ten": self.HoTen,
            "so_dien_thoai": self.SoDienThoai,
            "ghi_chu_toc": self.GhiChuToc,
        }


class DichVu:
    """
    2.4 Đặc tả lớp DichVu (Dịch vụ)
    Quản lý danh mục dịch vụ salon, đơn giá và thời gian thực hiện.
    """
    def __init__(
        self,
        ma_dich_vu: str,
        ten_dich_vu: str,
        gia_tien: float,
        thoi_gian_thuc_hien: int,
        mo_ta: Optional[str] = None,
    ):
        self.MaDichVu = ma_dich_vu
        self.TenDichVu = ten_dich_vu
        self.GiaTien = float(gia_tien)
        self.ThoiGianThucHien = int(thoi_gian_thuc_hien)
        self.MoTa = mo_ta

    @staticmethod
    def CapNhatDichVu(
        ma_dich_vu: str,
        ten_dich_vu: str,
        gia_tien: float,
        thoi_gian_thuc_hien: int,
        mo_ta: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Phương thức CapNhatDichVu() (Thêm/Sửa) theo đặc tả mục 2.4."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM DichVu WHERE MaDichVu = ?", (ma_dich_vu,))
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(
                    """
                    INSERT INTO DichVu (MaDichVu, TenDichVu, GiaTien, ThoiGianThucHien, MoTa)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (ma_dich_vu, ten_dich_vu, gia_tien, thoi_gian_thuc_hien, mo_ta),
                )
            else:
                cursor.execute(
                    """
                    UPDATE DichVu 
                    SET TenDichVu = ?, GiaTien = ?, ThoiGianThucHien = ?, MoTa = ?
                    WHERE MaDichVu = ?
                    """,
                    (ten_dich_vu, gia_tien, thoi_gian_thuc_hien, mo_ta, ma_dich_vu),
                )
            conn.commit()
            return {"TrangThaiCapNhat": True, "ThongBao": "Cập nhật dịch vụ thành công."}
        except Exception as e:
            conn.rollback()
            return {"TrangThaiCapNhat": False, "ThongBao": str(e)}
        finally:
            conn.close()

    @staticmethod
    def LayDanhSachDichVu() -> Dict[str, Any]:
        """Phương thức LayDanhSachDichVu() theo đặc tả mục 2.4."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM DichVu ORDER BY GiaTien ASC")
            services = [dict(r) for r in cursor.fetchall()]
            return {"DanhSachDichVu": services, "ThongBao": "Lấy danh mục thành công."}
        finally:
            conn.close()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ma_dich_vu": self.MaDichVu,
            "ten_dich_vu": self.TenDichVu,
            "gia_tien": self.GiaTien,
            "thoi_gian_thuc_hien": self.ThoiGianThucHien,
            "mo_ta": self.MoTa,
        }


class LichHen:
    """
    2.5 Đặc tả lớp LichHen (Lịch hẹn)
    Quản lý thông tin tổng quan các lượt đặt lịch và trạng thái xử lý.
    """
    def __init__(
        self,
        ma_lich_hen: str,
        ma_khach_hang: str,
        ma_nhan_vien: str,
        ngay_gio_hen: str,
        trang_thai: str = "Chờ xác nhận",
        ghi_chu: Optional[str] = None,
    ):
        self.MaLichHen = ma_lich_hen
        self.MaKhachHang = ma_khach_hang
        self.MaNhanVien = ma_nhan_vien
        self.NgayGioHen = ngay_gio_hen
        self.TrangThai = trang_thai
        self.GhiChu = ghi_chu

    @staticmethod
    def TaoLichHen(
        ma_khach_hang: str, ma_nhan_vien: str, ngay_gio_hen: str, ghi_chu: Optional[str] = None
    ) -> Dict[str, Any]:
        """Phương thức TaoLichHen() theo đặc tả mục 2.5."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM LichHen")
            cnt = cursor.fetchone()["cnt"] + 1
            ma_lich_hen = f"LH{cnt:03d}"

            cursor.execute(
                """
                INSERT INTO LichHen (MaLichHen, MaKhachHang, MaNhanVien, NgayGioHen, TrangThai, GhiChu)
                VALUES (?, ?, ?, ?, 'Chờ xác nhận', ?)
                """,
                (ma_lich_hen, ma_khach_hang, ma_nhan_vien, ngay_gio_hen, ghi_chu),
            )
            conn.commit()
            return {"TrangThaiTao": True, "MaLichHen": ma_lich_hen, "ThongBao": "Tạo lịch hẹn thành công."}
        except Exception as e:
            conn.rollback()
            return {"TrangThaiTao": False, "MaLichHen": None, "ThongBao": str(e)}
        finally:
            conn.close()

    @staticmethod
    def CapNhatTrangThaiLichHen(ma_lich_hen: str, trang_thai_moi: str) -> Dict[str, Any]:
        """Phương thức CapNhatTrangThaiLichHen() theo đặc tả mục 2.5."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MaNhanVien FROM LichHen WHERE MaLichHen = ?", (ma_lich_hen,))
            row = cursor.fetchone()
            if not row:
                return {"TrangThaiCapNhat": False, "ThongBao": "Không tìm thấy lịch hẹn."}

            ma_nhan_vien = row["MaNhanVien"]
            cursor.execute("UPDATE LichHen SET TrangThai = ? WHERE MaLichHen = ?", (trang_thai_moi, ma_lich_hen))

            # Auto sync stylist
            if trang_thai_moi == "Đang phục vụ":
                cursor.execute("UPDATE NhanVien SET TrangThaiRanh = 0 WHERE MaNhanVien = ?", (ma_nhan_vien,))
            elif trang_thai_moi in ("Hoàn thành", "Đã hủy"):
                cursor.execute("UPDATE NhanVien SET TrangThaiRanh = 1 WHERE MaNhanVien = ?", (ma_nhan_vien,))

            conn.commit()
            return {"TrangThaiCapNhat": True, "ThongBao": f"Đã cập nhật trạng thái thành '{trang_thai_moi}'."}
        except Exception as e:
            conn.rollback()
            return {"TrangThaiCapNhat": False, "ThongBao": str(e)}
        finally:
            conn.close()


class ChiTietLichHen:
    """
    2.6 Đặc tả lớp ChiTietLichHen (Chi tiết lịch hẹn)
    Quản lý danh sách dịch vụ cụ thể được đăng ký trong từng lịch hẹn.
    """
    @staticmethod
    def ThemDichVuVaoLichHen(
        ma_lich_hen: str, ma_dich_vu: str, gia_tai_thoi_diem_dat: float, ghi_chu_dich_vu: Optional[str] = None
    ) -> Dict[str, Any]:
        """Phương thức ThemDichVuVaoLichHen() theo đặc tả mục 2.6."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO ChiTietLichHen (MaLichHen, MaDichVu, GiaTaiThoiDiemDat, GhiChuDichVu)
                VALUES (?, ?, ?, ?)
                """,
                (ma_lich_hen, ma_dich_vu, gia_tai_thoi_diem_dat, ghi_chu_dich_vu),
            )
            conn.commit()
            return {"TrangThaiThem": True, "ThongBao": "Thêm dịch vụ vào lịch hẹn thành công."}
        except Exception as e:
            conn.rollback()
            return {"TrangThaiThem": False, "ThongBao": str(e)}
        finally:
            conn.close()

    @staticmethod
    def XoaDichVuKhoiLichHen(ma_lich_hen: str, ma_dich_vu: str) -> Dict[str, Any]:
        """Phương thức XoaDichVuKhoiLichHen() theo đặc tả mục 2.6."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM ChiTietLichHen WHERE MaLichHen = ? AND MaDichVu = ?",
                (ma_lich_hen, ma_dich_vu),
            )
            conn.commit()
            return {"TrangThaiXoa": True, "ThongBao": "Đã bỏ dịch vụ khỏi lịch hẹn."}
        except Exception as e:
            conn.rollback()
            return {"TrangThaiXoa": False, "ThongBao": str(e)}
        finally:
            conn.close()


class HoaDon:
    """
    2.7 Đặc tả lớp HoaDon (Hóa đơn)
    Quản lý thông tin thanh toán, tính toán tổng tiền, chiết khấu và in phiếu.
    """
    @staticmethod
    def TaoHoaDon(
        ma_lich_hen: str, giam_gia: float = 0.0, phuong_thuc_thanh_toan: str = "Tiền mặt"
    ) -> Dict[str, Any]:
        """Phương thức TaoHoaDon() theo đặc tả mục 2.7."""
        from backend.services.billing_service import BillingService
        return BillingService.create_invoice(ma_lich_hen, giam_gia, phuong_thuc_thanh_toan)

    @staticmethod
    def InHoaDon(ma_hoa_don: str) -> Dict[str, Any]:
        """Phương thức InHoaDon() theo đặc tả mục 2.7."""
        from backend.services.billing_service import BillingService
        result = BillingService.get_invoice_receipt(ma_hoa_don)
        if result.get("success"):
            return {"TrangThaiIn": True, "ThongBao": "In hóa đơn thành công.", "Receipt": result["receipt"]}
        return {"TrangThaiIn": False, "ThongBao": result.get("message", "Lỗi in hóa đơn.")}


class TroLyAI:
    """
    2.8 Đặc tả lớp TroLyAI (Trợ lý AI)
    Dịch vụ AI đảm nhận gợi ý dịch vụ, sinh tin nhắn nhắc lịch và tóm tắt lịch sử.
    """
    @staticmethod
    def GoiYDichVu(ma_khach_hang: str, ghi_chu_toc: Optional[str] = None) -> Dict[str, Any]:
        """Phương thức GoiYDichVu() theo đặc tả mục 2.8."""
        from backend.services.tro_ly_ai import TroLyAIService
        res = TroLyAIService.goi_y_dich_vu(ma_khach_hang, ghi_chu_toc)
        return {
            "DuLieuPhanHoi": res.get("suggestion"),
            "ThoiGianXuLy": res.get("elapsed_ms", 0),
            "ThongBao": "Gợi ý dịch vụ thành công." if res.get("success") else res.get("message"),
        }

    @staticmethod
    def SinhTinNhanNhacLich(ma_lich_hen: str) -> Dict[str, Any]:
        """Phương thức SinhTinNhanNhacLich() theo đặc tả mục 2.8."""
        from backend.services.tro_ly_ai import TroLyAIService
        res = TroLyAIService.sinh_tin_nhan_nhac_lich(ma_lich_hen)
        return {
            "DuLieuPhanHoi": res.get("message_content"),
            "ThongBao": "Sinh tin nhắn nhắc lịch thành công." if res.get("success") else res.get("message"),
        }

    @staticmethod
    def TomTatLichSuKhachHang(ma_khach_hang: str) -> Dict[str, Any]:
        """Phương thức TomTatLichSuKhachHang() theo đặc tả mục 2.8."""
        from backend.services.tro_ly_ai import TroLyAIService
        res = TroLyAIService.tom_tat_lich_su_khach_hang(ma_khach_hang)
        return {
            "DuLieuPhanHoi": res.get("summary"),
            "ThongBao": "Tóm tắt lịch sử thành công." if res.get("success") else res.get("message"),
        }

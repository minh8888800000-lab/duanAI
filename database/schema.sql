-- ====================================================================
-- HỆ THỐNG QUẢN LÝ ĐẶT LỊCH SALON TÓC TÍCH HỢP AI
-- Database Schema: SQLite (salon_hair.db)
-- Tuân thủ 100% tài liệu thiết kế CSDL và Đặc tả SRS v1.0
-- ====================================================================

-- Bắt buộc kích hoạt chế độ kiểm tra khóa ngoại trong SQLite
PRAGMA foreign_keys = ON;

-- --------------------------------------------------------------------
-- 1. Bảng TaiKhoan: Quản lý tài khoản đăng nhập và phân quyền hệ thống
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS TaiKhoan (
    MaTaiKhoan VARCHAR(20) PRIMARY KEY NOT NULL,
    TenDangNhap VARCHAR(50) NOT NULL UNIQUE,
    MatKhau VARCHAR(100) NOT NULL,
    VaiTro NVARCHAR(20) NOT NULL CHECK (VaiTro IN ('Admin', 'LeTan', 'Tho')),
    SessionToken VARCHAR(100) NULL
);

-- --------------------------------------------------------------------
-- 2. Bảng NhanVien: Thông tin cá nhân, chức vụ, trạng thái làm việc
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS NhanVien (
    MaNhanVien VARCHAR(20) PRIMARY KEY NOT NULL,
    HoTen NVARCHAR(100) NOT NULL,
    SoDienThoai VARCHAR(15) NOT NULL,
    ChucVu NVARCHAR(30) NOT NULL CHECK (ChucVu IN ('Thợ chính', 'Thợ phụ', 'Lễ tân', 'Quản lý')),
    TrangThaiRanh BOOLEAN NOT NULL DEFAULT 1 CHECK (TrangThaiRanh IN (0, 1)),
    MaTaiKhoan VARCHAR(20) NULL,
    CONSTRAINT fk_nhanvien_taikhoan
        FOREIGN KEY (MaTaiKhoan) 
        REFERENCES TaiKhoan(MaTaiKhoan) 
        ON DELETE SET NULL
);

-- --------------------------------------------------------------------
-- 3. Bảng KhachHang: Hồ sơ khách hàng, chất tóc, công thức thuốc
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS KhachHang (
    MaKhachHang VARCHAR(20) PRIMARY KEY NOT NULL,
    HoTen NVARCHAR(100) NOT NULL DEFAULT 'Khách vãng lai',
    SoDienThoai VARCHAR(15) NULL,
    GhiChuToc NVARCHAR(500) NULL
);

-- Ràng buộc Logic Nghiệp vụ: SoDienThoai cho phép NULL (Khách vãng lai),
-- nhưng nếu có nhập (IS NOT NULL) thì phải là DUY NHẤT (Filtered Index).
CREATE UNIQUE INDEX IF NOT EXISTS uq_khachhang_sodienthoai 
ON KhachHang(SoDienThoai) 
WHERE SoDienThoai IS NOT NULL;

-- --------------------------------------------------------------------
-- 4. Bảng DichVu: Danh mục dịch vụ làm tóc, đơn giá và thời lượng
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DichVu (
    MaDichVu VARCHAR(20) PRIMARY KEY NOT NULL,
    TenDichVu NVARCHAR(100) NOT NULL UNIQUE,
    GiaTien DECIMAL(12,0) NOT NULL CHECK (GiaTien >= 0),
    ThoiGianThucHien INT NOT NULL CHECK (ThoiGianThucHien > 0),
    MoTa NVARCHAR(250) NULL
);

-- --------------------------------------------------------------------
-- 5. Bảng LichHen: Thông tin tổng quan các lượt đặt lịch
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS LichHen (
    MaLichHen VARCHAR(20) PRIMARY KEY NOT NULL,
    MaKhachHang VARCHAR(20) NOT NULL,
    MaNhanVien VARCHAR(20) NOT NULL,
    NgayGioHen DATETIME NOT NULL,
    TrangThai NVARCHAR(30) NOT NULL DEFAULT 'Chờ xác nhận' 
        CHECK (TrangThai IN ('Chờ xác nhận', 'Đã xác nhận', 'Đang phục vụ', 'Hoàn thành', 'Đã hủy')),
    GhiChu NVARCHAR(250) NULL,
    CONSTRAINT fk_lichhen_khachhang
        FOREIGN KEY (MaKhachHang) 
        REFERENCES KhachHang(MaKhachHang) 
        ON DELETE RESTRICT,
    CONSTRAINT fk_lichhen_nhanvien
        FOREIGN KEY (MaNhanVien) 
        REFERENCES NhanVien(MaNhanVien) 
        ON DELETE RESTRICT
);

-- --------------------------------------------------------------------
-- 6. Bảng ChiTietLichHen: Chi tiết danh sách dịch vụ trong một lịch hẹn
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ChiTietLichHen (
    MaLichHen VARCHAR(20) NOT NULL,
    MaDichVu VARCHAR(20) NOT NULL,
    GiaTaiThoiDiemDat DECIMAL(12,0) NOT NULL CHECK (GiaTaiThoiDiemDat >= 0),
    GhiChuDichVu NVARCHAR(250) NULL,
    PRIMARY KEY (MaLichHen, MaDichVu),
    CONSTRAINT fk_chitiet_lichhen
        FOREIGN KEY (MaLichHen) 
        REFERENCES LichHen(MaLichHen) 
        ON DELETE CASCADE,
    CONSTRAINT fk_chitiet_dichvu
        FOREIGN KEY (MaDichVu) 
        REFERENCES DichVu(MaDichVu) 
        ON DELETE RESTRICT
);

-- --------------------------------------------------------------------
-- 7. Bảng HoaDon: Quản lý thanh toán, giảm giá và doanh thu
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS HoaDon (
    MaHoaDon VARCHAR(20) PRIMARY KEY NOT NULL,
    MaLichHen VARCHAR(20) NOT NULL UNIQUE,
    NgayTao DATETIME NOT NULL,
    TongTien DECIMAL(12,0) NOT NULL CHECK (TongTien >= 0),
    GiamGia DECIMAL(12,0) NOT NULL DEFAULT 0 CHECK (GiamGia >= 0),
    ThanhTien DECIMAL(12,0) NOT NULL CHECK (ThanhTien >= 0),
    PhuongThucThanhToan NVARCHAR(30) NOT NULL 
        CHECK (PhuongThucThanhToan IN ('Tiền mặt', 'Chuyển khoản', 'Thẻ')),
    TrangThaiThanhToan NVARCHAR(30) NOT NULL DEFAULT 'Đã thanh toán' 
        CHECK (TrangThaiThanhToan IN ('Chưa thanh toán', 'Đã thanh toán')),
    CONSTRAINT fk_hoadon_lichhen
        FOREIGN KEY (MaLichHen) 
        REFERENCES LichHen(MaLichHen) 
        ON DELETE RESTRICT,
    CONSTRAINT chk_hoadon_thanhtien
        CHECK (ThanhTien = TongTien - GiamGia)
);

-- --------------------------------------------------------------------
-- 8. Bảng TroLyAI: Lịch sử xử lý, prompt & phản hồi tư vấn từ AI
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS TroLyAI (
    MaYeuCau VARCHAR(20) PRIMARY KEY NOT NULL,
    TenModelAI VARCHAR(50) NOT NULL,
    ThoiGianXuLy INT NOT NULL CHECK (ThoiGianXuLy >= 0),
    DuLieuPhanHoi NVARCHAR(1000) NOT NULL,
    MaKhachHang VARCHAR(20) NULL,
    CONSTRAINT fk_trolyai_khachhang
        FOREIGN KEY (MaKhachHang) 
        REFERENCES KhachHang(MaKhachHang) 
        ON DELETE SET NULL
);

-- Các Index bổ trợ tối ưu truy vấn nghiệp vụ
CREATE INDEX IF NOT EXISTS idx_lichhen_nhanvien_ngay ON LichHen(MaNhanVien, NgayGioHen);
CREATE INDEX IF NOT EXISTS idx_lichhen_khachhang ON LichHen(MaKhachHang);
CREATE INDEX IF NOT EXISTS idx_hoadon_ngaytao ON HoaDon(NgayTao);
CREATE INDEX IF NOT EXISTS idx_trolyai_khachhang ON TroLyAI(MaKhachHang);

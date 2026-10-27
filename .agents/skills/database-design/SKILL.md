---
name: database-design
description: Quy trình thiết kế CSDL quan hệ chuẩn hóa 3NF, 4 cấp độ ràng buộc toàn vẹn, tối ưu chỉ mục Filtered Index và migrations an toàn trong SQLite.
version: 2.0.0
---

# Database Design Skill (Kỹ Năng Thiết Kế & Quản Trị CSDL Quan Hệ)

## 1. Mục Tiêu & Tiêu Chuẩn Chuẩn Hóa 3NF
Đảm bảo cơ sở dữ liệu SQLite của Salon Tóc đạt chuẩn hóa cấp 3 (**Third Normal Form - 3NF**):
- **1NF**: Mọi thuộc tính đều là nguyên tố (atomic), không chứa mảng lồng nhau (tách quan hệ nhiều-nhiều giữa Lịch hẹn và Dịch vụ thành bảng trung gian `ChiTietLichHen`).
- **2NF**: Toàn bộ các thuộc tính không khóa đều phụ thuộc hoàn toàn vào khóa chính (không có phụ thuộc một phần vào một phần khóa phức hợp).
- **3NF**: Không có phụ thuộc bắc cầu (transitive dependency); các thuộc tính nhân viên, khách hàng, dịch vụ không được lưu trùng lặp vào hóa đơn hoặc lịch hẹn mà thông qua khóa ngoại.

---

## 2. Đặc Tả Chi Tiết 8 Bảng CSDL SQLite

### 2.1. Bảng `TaiKhoan` (Tài Khoản Đăng Nhập & Đơn Phiên Session)
| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc | Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `MaTaiKhoan` | VARCHAR(20) | PRIMARY KEY | Mã tài khoản định danh (TK001, TK002, ...) |
| `TenDangNhap` | VARCHAR(50) | UNIQUE, NOT NULL | Tên đăng nhập (chữ thường, không dấu) |
| `MatKhau` | VARCHAR(100) | NOT NULL | Mật khẩu bảo mật |
| `VaiTro` | NVARCHAR(20) | NOT NULL, CHECK (VaiTro IN ('Admin', 'LeTan', 'Tho')) | Phân quyền truy cập hệ thống |
| `SessionToken` | VARCHAR(100) | NULLABLE | Token phiên hiện tại, hỗ trợ Single Device Session |

### 2.2. Bảng `NhanVien` (Hồ Sơ Thợ & Nhân Sự Salon)
| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc | Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `MaNhanVien` | VARCHAR(20) | PRIMARY KEY | Mã nhân viên (NV001, NV002, ...) |
| `HoTen` | NVARCHAR(100) | NOT NULL | Họ và tên thợ / nhân viên |
| `SoDienThoai` | VARCHAR(15) | NULLABLE | Số điện thoại liên hệ |
| `ChucVu` | NVARCHAR(50) | NOT NULL | Quản lý, Thợ chính, Thợ phụ, Lễ tân |
| `ChuyenMon` | NVARCHAR(255) | NULLABLE | Chuyên môn tạo kiểu (Uốn tóc, Nhuộm Balayage, Phục hồi) |
| `MaTaiKhoan` | VARCHAR(20) | FOREIGN KEY -> TaiKhoan(MaTaiKhoan) ON DELETE SET NULL | Tài khoản đăng nhập liên kết |

### 2.3. Bảng `KhachHang` (Hồ Sơ Khách & Lịch Sử Tóc)
| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc | Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `MaKhachHang` | VARCHAR(20) | PRIMARY KEY | Mã khách hàng (KH001, KH002, ...) |
| `HoTen` | NVARCHAR(100) | NOT NULL | Họ và tên khách hàng |
| `SoDienThoai` | VARCHAR(15) | Filtered UNIQUE Index | Số điện thoại khách (hỗ trợ NULL cho khách vãng lai) |
| `GhiChuToc` | TEXT | NULLABLE | Lịch sử chất tóc, da đầu, dị ứng thuốc nhuộm |

### 2.4. Bảng `DichVu` (Menu Dịch Vụ Salon)
| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc | Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `MaDichVu` | VARCHAR(20) | PRIMARY KEY | Mã dịch vụ (DV001, DV002, ...) |
| `TenDichVu` | NVARCHAR(100) | NOT NULL | Tên dịch vụ (Uốn sóng hippie, Cắt layer, ...) |
| `ThoiLuongPhut` | INTEGER | NOT NULL, CHECK (ThoiLuongPhut > 0) | Thời gian thực hiện tính bằng phút |
| `GiaTien` | DECIMAL(12,2) | NOT NULL, CHECK (GiaTien >= 0) | Đơn giá niêm yết (VNĐ) |
| `MoTa` | TEXT | NULLABLE | Chi tiết công nghệ, dòng sản phẩm sử dụng |

### 2.5. Bảng `LichHen` (Lịch Hẹn Đặt Chỗ)
| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc | Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `MaLichHen` | VARCHAR(20) | PRIMARY KEY | Mã lịch hẹn (LH001, LH002, ...) |
| `NgayHen` | DATE | NOT NULL | Ngày hẹn (YYYY-MM-DD) |
| `GioBatDau` | TIME | NOT NULL | Giờ bắt đầu (HH:MM) |
| `GioKetThuc` | TIME | NOT NULL, CHECK (GioKetThuc > GioBatDau) | Giờ kết thúc ước tính |
| `TrangThai` | NVARCHAR(30) | NOT NULL, CHECK (TrangThai IN ('Chờ phục vụ', 'Đang làm', 'Hoàn thành', 'Đã thanh toán', 'Hủy')) | Trạng thái vòng đời lịch hẹn |
| `MaKhachHang` | VARCHAR(20) | NOT NULL, FK -> KhachHang(MaKhachHang) ON DELETE RESTRICT | Khách hàng đặt lịch |
| `MaNhanVien` | VARCHAR(20) | NOT NULL, FK -> NhanVien(MaNhanVien) ON DELETE RESTRICT | Thợ phụ trách chính |

### 2.6. Bảng `ChiTietLichHen` (Chi Tiết Dịch Vụ Chọn Trong Lịch Hẹn)
| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc | Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `MaLichHen` | VARCHAR(20) | PK, FK -> LichHen(MaLichHen) ON DELETE CASCADE | Khóa chính phức hợp |
| `MaDichVu` | VARCHAR(20) | PK, FK -> DichVu(MaDichVu) ON DELETE RESTRICT | Khóa chính phức hợp |
| `DonGiaTaiThoiDiem` | DECIMAL(12,2) | NOT NULL, CHECK (DonGiaTaiThoiDiem >= 0) | Giá lưu vết tại thời điểm chốt lịch |

### 2.7. Bảng `HoaDon` (Hóa Đơn Thu Ngân POS)
| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc | Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `MaHoaDon` | VARCHAR(20) | PRIMARY KEY | Mã hóa đơn (HD001, HD002, ...) |
| `NgayLap` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm xuất hóa đơn |
| `TongTien` | DECIMAL(12,2) | NOT NULL, CHECK (TongTien >= 0) | Tổng tiền dịch vụ nguyên giá |
| `GiamGia` | DECIMAL(12,2) | NOT NULL, DEFAULT 0, CHECK (GiamGia >= 0 AND GiamGia <= TongTien) | Tiền chiết khấu / voucher |
| `ThanhTien` | DECIMAL(12,2) | NOT NULL, CHECK (ThanhTien = TongTien - GiamGia) | Số tiền thực thu của khách |
| `PhuongThucThanhToan` | NVARCHAR(30) | NOT NULL, CHECK (PhuongThucThanhToan IN ('Tiền mặt', 'Chuyển khoản', 'Thẻ')) | Hình thức thanh toán |
| `MaLichHen` | VARCHAR(20) | UNIQUE, NOT NULL, FK -> LichHen(MaLichHen) ON DELETE RESTRICT | Lịch hẹn tương ứng |

### 2.8. Bảng `TroLyAI` (Lưu Vết Tư Vấn AI)
| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc | Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `MaYeuCau` | VARCHAR(20) | PRIMARY KEY | Mã giao dịch AI (YC001, YC002, ...) |
| `ThoiGianTao` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Thời điểm hỏi AI |
| `TenModelAI` | VARCHAR(50) | NOT NULL | Tên mô hình (gemini-3.8-flash, Grounded-SQLite, ...) |
| `ThoiGianXuLy` | INTEGER | NOT NULL | Thời gian phản hồi tính bằng millisecond |
| `DuLieuPhanHoi` | TEXT | NOT NULL | Nội dung tư vấn / phân tích chuyên môn |
| `MaKhachHang` | VARCHAR(20) | NULLABLE, FK -> KhachHang(MaKhachHang) ON DELETE SET NULL | Khách hàng được phân tích |

---

## 3. Bốn Cấp Độ Ràng Buộc Toàn Vẹn (Integrity Constraints)

1. **Entity Integrity (Toàn Vẹn Thực Thể)**:
   - 100% bảng đều sở hữu Khóa chính (Primary Key).
   - Quan hệ nhiều-nhiều `ChiTietLichHen` bắt buộc sử dụng Composite Primary Key `(MaLichHen, MaDichVu)`.
2. **Referential Integrity (Toàn Vẹn Tham Chiếu)**:
   - `ON DELETE CASCADE`: Khi xóa `LichHen`, toàn bộ bản ghi con trong `ChiTietLichHen` tự động dọn dẹp để không có mồ côi.
   - `ON DELETE RESTRICT`: Chặn xóa `DichVu` hoặc `NhanVien` nếu đang có lịch hẹn hoặc hóa đơn tham chiếu tới.
   - `ON DELETE SET NULL`: Khi xóa `KhachHang`, log tư vấn trong `TroLyAI` giữ nguyên lịch sử kiểm toán với `MaKhachHang = NULL`.
3. **Domain Integrity (Toàn Vẹn Miền Giá Trị)**:
   - `CHECK (ThoiLuongPhut > 0)` và `CHECK (GiaTien >= 0)`.
   - `CHECK (GioKetThuc > GioBatDau)`.
   - Giới hạn enum chặt chẽ: `VaiTro IN ('Admin', 'LeTan', 'Tho')`.
4. **Business Logic Integrity (Toàn Vẹn Nghiệp Vụ)**:
   - Bắt buộc kiểm tra `CHECK (ThanhTien = TongTien - GiamGia)` để chống rò rỉ gian lận thu ngân tại quầy.
   - Quản lý phiên đồng thời: `TaiKhoan(SessionToken)` được cập nhật nguyên tử (atomic) mỗi khi người dùng đăng nhập.

---

## 4. Tối Ưu Hóa Chỉ Mục (Indexing Strategy)

```sql
-- 1. Filtered Unique Index cho SĐT khách hàng (Hỗ trợ NULL cho khách vãng lai, nhưng nếu có số thì không được trùng)
CREATE UNIQUE INDEX IF NOT EXISTS uq_khachhang_sdt 
ON KhachHang(SoDienThoai) 
WHERE SoDienThoai IS NOT NULL;

-- 2. Index tăng tốc tìm kiếm lịch hẹn theo ngày và thợ (Chống trùng giờ)
CREATE INDEX IF NOT EXISTS idx_lichhen_ngay_tho 
ON LichHen(NgayHen, MaNhanVien, GioBatDau, GioKetThuc);

-- 3. Index báo cáo doanh thu theo ngày lập hóa đơn
CREATE INDEX IF NOT EXISTS idx_hoadon_ngaylap 
ON HoaDon(NgayLap);

-- 4. Index tìm kiếm nhanh tài khoản theo Session Token
CREATE INDEX IF NOT EXISTS idx_taikhoan_session 
ON TaiKhoan(SessionToken);
```

---

## 5. Quy Trình Migrations An Toàn (Safe Schema Evolution)

1. **Nguyên tắc an toàn**: Không bao giờ xóa file `.db` trên môi trường đang vận hành.
2. **Script Migration mẫu (Bổ sung cột `SessionToken`)**:
```python
def migrate_session_token(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(TaiKhoan)")
    columns = [col[1] for col in cursor.fetchall()]
    if "SessionToken" not in columns:
        cursor.execute("ALTER TABLE TaiKhoan ADD COLUMN SessionToken VARCHAR(100)")
        conn.commit()
    conn.close()
```
3. **Lệnh kiểm tra toàn vẹn**:
   - `PRAGMA foreign_key_check;` (Trả về 0 dòng nếu CSDL hoàn hảo).
   - `PRAGMA integrity_check;` (Trả về `ok`).
   - Chạy test suite tự động: `python -m unittest tests/test_db_schema.py`.

# KẾT QUẢ AI AGENT: 03_database_design.txt

*Thời gian chạy: 1.12s*

# BÁO CÁO THIẾT KẾ CSDL QUAN HỆ SQLITE CHUẨN 3NF (8 BẢNG)
## Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI - HÀ MINH HAIR SALON

### 1. Mô Hình Thực Thể & Danh Mục 8 Bảng
1. `TaiKhoan`: Quản lý định danh nhân viên, mật khẩu hash SHA-256, SessionToken đơn phiên.
2. `NhanVien`: Quản lý hồ sơ stylist, thợ chính, thợ phụ, số điện thoại và chuyên môn.
3. `KhachHang`: Quản lý khách hàng, SĐT (Unique Filtered Index), hạng VIP, GhiChuToc, tổng chi tiêu.
4. `DichVu`: Danh mục 21 dịch vụ niêm yết (DV001-DV021) kèm đơn giá và thời lượng phục vụ.
5. `LichHen`: Quản lý lịch hẹn phục vụ, ngày giờ, thợ chính phụ trách, trạng thái (Chờ, Đang làm, Hoàn thành).
6. `ChiTietLichHen`: Bảng nối nhiều-nhiều lưu vết từng dịch vụ được làm trong lịch hẹn và đơn giá thời điểm đặt.
7. `HoaDon`: Lưu vết thanh toán tài chính, giảm giá, thành tiền thực thu, phương thức thanh toán (Tiền mặt, VietQR, Thẻ).
8. `TroLyAI`: Nhật ký kiểm toán toàn bộ câu hỏi/trả lời AI, thời gian xử lý ms, người dùng truy vấn.

### 2. Ràng Buộc Toàn Vẹn CSDL
- **Khóa chính**: Định dạng chuẩn (NV001, KH001, DV001, LH001, HD001).
- **Khóa ngoại**: 
  - `ChiTietLichHen -> LichHen` (ON DELETE CASCADE)
  - `ChiTietLichHen -> DichVu` (ON DELETE RESTRICT)
  - `HoaDon -> LichHen` (ON DELETE RESTRICT)
- **Ràng buộc CHECK**: `ThanhTien = TongTien - GiamGia`, `Gia >= 0`, `ThoiLuongPhut > 0`.
- **Chỉ mục thông minh**: `CREATE UNIQUE INDEX idx_khach_hang_sdt ON KhachHang(SoDienThoai) WHERE SoDienThoai IS NOT NULL;`

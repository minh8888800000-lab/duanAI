# KẾT QUẢ AI AGENT: 02_use_cases.txt

*Thời gian chạy: 5.55s*

# BÁO CÁO ĐẶC TẢ CHI TIẾT 10 USE CASES (UC001 - UC010)
## Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI - HÀ MINH HAIR SALON

### UC001: Đăng Nhập & Kiểm Soát Đơn Phiên (Single-Device Session)
- **Tác nhân**: Tất cả nhân viên (Admin, LeTan, Tho).
- **Tiền điều kiện**: Đã có tài khoản trong bảng `TaiKhoan`.
- **Luồng chính**: Đăng nhập tên/mật khẩu -> Sinh SessionToken mới -> Cấp JWT -> Điều hướng phân quyền.
- **Luồng ngoại lệ (A1)**: Tài khoản đang mở ở máy khác, máy cũ nhận mã lỗi 401 khi heartbeat sau 3.5s và tự đăng xuất.

### UC002: Quản Lý Hồ Sơ Khách Hàng & Chất Tóc
- **Tác nhân**: LeTan, Admin.
- **Luồng chính**: Tìm kiếm theo tên hoặc SĐT; cập nhật trường `GhiChuToc` (chất tóc tẩy, tóc xơ, dị ứng).

### UC003: Quản Lý Danh Mục Dịch Vụ & Bảng Giá
- **Tác nhân**: Admin (Master Stylist Hà Minh).
- **Ràng buộc**: Đơn giá >= 0, Thời lượng > 0, Không xóa dịch vụ đang có lịch hẹn tham chiếu.

### UC004: Quản Lý Đội Ngũ Stylist & Lịch Làm Việc
- **Tác nhân**: Admin.
- **Nghiệp vụ**: Phân công chuyên môn (Uốn sóng, Nhuộm Balayage, Phục hồi Nano).

### UC005: Tạo Lịch Hẹn & Chống Trùng Giờ (De Morgan)
- **Tác nhân**: LeTan, Khách hàng.
- **Công thức chống trùng**: `(S1 < E2) AND (S2 < E1)`. Chặn tuyệt đối 2 lịch hẹn đè giờ nhau trên cùng một thợ.

### UC006: Thu Ngân POS, Giảm Giá & In Hóa Đơn Nhiệt
- **Tác nhân**: LeTan.
- **Công thức**: `ThanhTien = TongTien - GiamGia` (Kiểm tra ràng buộc CHECK CSDL). Xuất phiếu in nhiệt 80mm/58mm.

### UC007: Báo Cáo Doanh Thu & Hiệu Suất Vận Hành
- **Tác nhân**: Admin.
- **Nghiệp vụ**: Thống kê doanh thu theo ngày/tháng, phương thức thanh toán, xuất file CSV.

### UC008: AI Gợi Ý Liệu Trình Dịch Vụ Thông Minh
- **Tác nhân**: LeTan, Stylist.
- **Nghiệp vụ**: AI đối chiếu chất tóc và tiền sử làm hóa chất để đề xuất gói uốn/nhuộm/phục hồi tối ưu.

### UC009: AI Tự Động Sinh Tin Nhắn Nhắc Lịch (Zalo/SMS)
- **Tác nhân**: LeTan, Hệ thống.
- **Nội dung**: Tin nhắn văn minh, chuẩn mực, nêu rõ thợ làm, khung giờ, địa chỉ 188 Thái Hà.

### UC010: AI Tóm Tắt Hồ Sơ Khách 5 Giây Cho Stylist
- **Tác nhân**: Stylist (Thợ).
- **Nghiệp vụ**: Hiển thị nhanh 3 gạch đầu dòng: Tên khách, chất tóc, dịch vụ đã chọn để stylist sẵn sàng đón tiếp.

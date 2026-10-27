# KẾT QUẢ AI AGENT: 01_requirements_analysis.txt

*Thời gian chạy: 1.40s*

# BÁO CÁO ĐẶC TẢ YÊU CẦU PHẦN MỀM (SOFTWARE REQUIREMENTS SPECIFICATION)
## Dự Án: Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI - HÀ MINH HAIR SALON

### 1. Bối Cảnh & Mục Tiêu Hệ Thống
- **Thương hiệu**: HÀ MINH HAIR SALON - 188 Thái Hà, Đống Đa, Hà Nội.
- **Mục tiêu**: Tự động hóa 100% quy trình đặt lịch, thu ngân POS, quản lý khách hàng thân thiết và tích hợp Trợ lý AI Stylist 24/7.
- **Pain Points giải quyết**: Chặn triệt để trùng lịch thợ, loại bỏ sai sót tính tiền, lưu vết lịch sử chất tóc khách hàng để chống cháy/hỏng tóc khi làm hóa chất.

### 2. Bốn Nhóm Tác Nhân & Phân Quyền Hệ Thống (Actors & RBAC)
1. **Quản Lý / Chủ Salon (`Admin` - Master Stylist Hà Minh, NV001)**:
   - Toàn quyền cấu hình bảng giá dịch vụ, quản lý tài khoản nhân viên, xem báo cáo doanh thu tài chính thời gian thực.
2. **Lễ Tân & Thu Ngân (`LeTan`)**:
   - Tiếp đón khách hàng, tạo lịch hẹn mới, xem bàn cờ thợ rảnh, thanh toán POS và in phiếu thanh toán nhiệt.
3. **Thợ Làm Tóc / Stylist (`Tho`)**:
   - Xem lịch phân công cá nhân, xem tóm tắt hồ sơ chất tóc của khách trong 5 giây trước khi vào dịch vụ.
4. **Khách Hàng Trải Nghiệm (`Guest`)**:
   - Tra cứu menu dịch vụ niêm yết, tương tác với AI Stylist tư vấn kiểu tóc và liệu trình phục hồi hư tổn.

### 3. Danh Mục Yêu Cầu Chức Năng Cốt Lõi (Functional Requirements - FR)
- **FR01 (Quản lý Hồ sơ & Lịch sử Tóc)**: Lưu thông tin họ tên, SĐT, hạng thành viên và trường `GhiChuToc` (chất tóc tẩy, tóc dầu, dị ứng hóa chất).
- **FR02 (Quản lý Danh mục Dịch vụ)**: Quản lý mã DV (DV001-DV021), tên dịch vụ, đơn giá niêm yết, thời lượng (phút).
- **FR03 (Đặt Lịch Hẹn & Chống Trùng Giờ)**: Bố trí lịch hẹn không giao thoa theo công thức De Morgan `(S1 < E2) AND (S2 < E1)`.
- **FR04 (Thu Ngân POS & In Hóa Đơn)**: Tự động tính tổng tiền dịch vụ, chiết khấu giảm giá VIP, thanh toán VietQR/POS/Tiền mặt và in phiếu thanh toán.
- **FR05 (Trợ Lý AI Đa Tầng)**: Gợi ý dịch vụ theo chất tóc, sinh tin nhắn nhắc lịch Zalo/SMS, tóm tắt 5s cho thợ, chat trực tuyến giải đáp tóc học (Trichology).

### 4. Yêu Cầu Phi Chức Năng (Non-Functional Requirements - NFR)
- **NFR01 (Bảo mật Đơn phiên - Single-Device Session)**: Mỗi tài khoản chỉ đăng nhập trên 1 thiết bị; cơ chế Session Heartbeat 3.5s đá phiên cũ khi phát hiện đăng nhập nơi khác.
- **NFR02 (Hiệu năng CSDL)**: SQLite WAL Mode, cache_size = 64MB, thời gian phản hồi API < 100ms.
- **NFR03 (Zero-Hallucination Guardrail)**: AI không bao giờ tự bịa đặt giá tiền ngoài CSDL; từ chối trả lời câu hỏi ngoài phạm vi salon (giá vàng, chứng khoán).

### 5. Quy Tắc Nghiệp Vụ & Khoa Học Tóc Học (Trichology & Business Rules)
- **Quy tắc đặt cọc**: Gói dịch vụ có tổng giá trị > 2.000.000đ bắt buộc đặt cọc 20%.
- **Quy tắc phân công VIP**: Khách làm hóa chất nặng luôn được phân công 1 Thợ chính kèm 1 Thợ phụ thao tác 2 bên đầu đồng thời trong 15 phút.
- **Khoa học tóc học**: Tóc tẩy cấp 8-9 cấm uốn nhiệt; phục hồi protein tơ tằm / nano keratin ở pH 4.5 khóa biểu bì; dầu gội Sulfate-free.

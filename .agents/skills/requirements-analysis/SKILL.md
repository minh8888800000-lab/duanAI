---
name: requirements-analysis
description: Quy trình phân tích yêu cầu phần mềm, lập đặc tả 10 Use Cases chuẩn (UC001 - UC010), yêu cầu phi chức năng NFR và kiểm soát phê duyệt Human Gate 1 trong AI-Augmented SDLC.
version: 2.0.0
---

# Requirements Analysis Skill (Kỹ Năng Phân Tích & Quản Lý Yêu Cầu Phần Mềm)

## 1. Mục Tiêu & Phương Pháp Phân Tích
Thiết lập quy trình chuẩn hóa từ việc khảo sát thực địa tại Salon Tóc, mô hình hóa các điểm nghẽn (Pain Points) thành danh mục yêu cầu chức năng (FR) và phi chức năng (NFR), triệt tiêu hiện tượng AI Hallucination (AI tự sáng tác tính năng không có thật hoặc vượt quá phạm vi khảo sát).

---

## 2. Bốn Nhóm Tác Nhân Hệ Thống (Actors)

1. **Quản Lý / Chủ Salon (`Admin`)**:
   - Theo dõi doanh thu thời gian thực, quản lý danh mục giá dịch vụ, giám sát hiệu suất thợ, quản lý tài khoản nhân viên.
2. **Lễ Tân & Thu Ngân (`LeTan`)**:
   - Tiếp đón khách, kiểm tra thợ rảnh, tạo lịch hẹn, sử dụng AI gợi ý dịch vụ, thanh toán POS và in hóa đơn.
3. **Thợ Làm Tóc / Stylist (`Tho`)**:
   - Xem lịch hẹn cá nhân được phân công, xem tóm tắt hồ sơ chất tóc của khách trong 5 giây, cập nhật trạng thái làm tóc.
4. **Khách Hàng Trải Nghiệm (`Guest`)**:
   - Xem menu bảng giá niêm yết, tương tác 24/7 với Trợ lý AI Stylist để được tư vấn chất tóc và phác đồ điều trị tóc hư tổn.

---

## 3. Đặc Tả Chi Tiết 10 Use Cases Cốt Lõi (UC001 - UC010)

### UC001: Đăng Nhập & Phân Quyền Đơn Phiên (Single-Device Session)
- **Mục tiêu**: Xác thực người dùng và bảo đảm mỗi tài khoản chỉ hoạt động trên một thiết bị duy nhất.
- **Tiền điều kiện**: Tài khoản đã được cấp trong hệ thống.
- **Luồng chính**:
  1. Người dùng nhập tên đăng nhập và mật khẩu.
  2. Hệ thống kiểm tra thông tin, sinh mã `SessionToken` mới và lưu vào bảng `TaiKhoan`.
  3. Cấp phát JWT token mang claim `session_id`.
  4. Điều hướng người dùng về màn hình tương ứng với vai trò (`Admin`, `LeTan`, `Tho`).
- **Luồng phụ (A1 - Đăng nhập đồng thời nơi khác)**: Khi có thiết bị B đăng nhập cùng tài khoản, thiết bị A nhận mã lỗi `401 CONCURRENT_LOGIN` qua session heartbeat (chu kỳ 3.5s), tự động đăng xuất và hiển thị popup cảnh báo.
- **Tiêu chí nghiệm thu (AC)**: Đăng nhập sai quá 5 lần phải thông báo rõ ràng; đăng nhập thành công phải có token hợp lệ.

### UC002: Quản Lý Hồ Sơ Khách Hàng & Lịch Sử Tóc
- **Mục tiêu**: Lưu vết thông tin khách, số điện thoại và đặc điểm chất tóc (tóc tẩy, tóc dầu, dị ứng hóa chất).
- **Luồng chính**: Thêm mới hoặc chỉnh sửa hồ sơ khách hàng. Tìm kiếm nhanh theo tên hoặc SĐT.
- **Luồng phụ (A1 - Khách vãng lai)**: Nếu khách không để lại SĐT, hệ thống cho phép lưu với SĐT `NULL` (không vi phạm unique index).
- **Tiêu chí nghiệm thu (AC)**: Không cho phép 2 khách hàng khác nhau dùng chung một số điện thoại thực.

### UC003: Quản Lý Danh Mục Dịch Vụ & Bảng Giá (Admin)
- **Mục tiêu**: Cập nhật giá tiền, thời lượng (phút), mô tả công nghệ cho từng dịch vụ.
- **Tiêu chí nghiệm thu (AC)**: Giá tiền `>= 0`, thời lượng `> 0`. Không cho phép xóa dịch vụ đang có lịch hẹn tham chiếu (`RESTRICT`).

### UC004: Quản Lý Đội Ngũ Nhân Sự & Thợ Làm Tóc
- **Mục tiêu**: Thêm stylist, cập nhật chuyên môn (Uốn sóng, Nhuộm Balayage, Phục hồi Nano) và gán tài khoản đăng nhập.
- **Tiêu chí nghiệm thu (AC)**: Mỗi nhân viên chỉ liên kết tối đa 1 tài khoản đăng nhập.

### UC005: Quản Lý Lịch Hẹn, Chống Trùng Lịch & Giao Diện Thẻ Lịch Hẹn
- **Mục tiêu**: Đặt chỗ phục vụ với thợ chính xác theo khung giờ không bị giao thoa; hiển thị trực quan lịch trình qua 2 chế độ: **Sơ Đồ Ghế (Timeline Scheduler)** và **Lưới Thẻ Lịch Hẹn (Appointment Cards Grid)**.
- **Tiền điều kiện**: Đã có khách hàng và dịch vụ được chọn.
- **Luồng chính (Đặt lịch)**:
  1. Lễ tân chọn khách hàng, danh sách dịch vụ và ngày hẹn.
  2. Hệ thống tính tổng thời lượng = `Sum(ThoiLuongPhut)`.
  3. Chọn giờ bắt đầu `GioBatDau`, hệ thống tự tính `GioKetThuc = GioBatDau + TongThoiLuong`.
  4. Hệ thống kiểm tra xung đột với mọi lịch hẹn hiện có của thợ: Điều kiện xung đột là `(S1 < E2) AND (S2 < E1)`.
  5. Nếu không trùng, tạo bản ghi `LichHen` và các `ChiTietLichHen`.
- **Đặc tả Chi Tiết Thẻ Lịch Hẹn (Appointment Card UI Specification)**:
  1. **Header Thẻ**:
     - Mã định danh lịch hẹn dạng badge nổi bật: `#LHxxx`.
     - Khung giờ phục vụ trực quan: `Giờ Bắt Đầu - Giờ Kết Thúc` kèm ngày tháng (ví dụ: `14:30 - 15:45 (19/09)`).
     - Huy hiệu trạng thái (Status Badge) có màu sắc quy chuẩn: `⏳ Chờ xác nhận`, `✓ Đã xác nhận`, `✂️ Đang phục vụ`, `★ Hoàn thành`, `✕ Đã hủy`.
  2. **Viền Trạng Thái (Status Border Styling)**:
     - Thẻ tự động đổi màu viền trái theo trạng thái: Xanh ngọc (`Đang phục vụ`), Vàng cam (`Chờ xác nhận`), Xanh dương (`Đã xác nhận`), Xám (`Hoàn thành`), Đỏ mờ (`Đã hủy`).
  3. **Khối Thông Tin Khách Hàng & Stylist**:
     - Tên khách hàng in đậm kèm số điện thoại liên hệ (hoặc nhãn `Khách vãng lai`).
     - Tên thợ phụ trách chính kèm chức vụ (Stylist / Thợ chính / Thợ phụ).
     - Nút tắt `📜 Lịch Sử` tra cứu tức thì toàn bộ dịch vụ khách từng làm.
  4. **Cảnh Báo Chất Tóc & Kỹ Thuật (Hair Profile Alert)**:
     - Tự động trích xuất `GhiChuToc` từ hồ sơ khách (Ví dụ: `🧬 Chất tóc: Tóc tẩy level 8, dị ứng amoniac`) để thợ và lễ tân nhìn thấy ngay trên thẻ, tránh sai sót hóa chất nguy hiểm.
  5. **Chi Tiết Dịch Vụ & Tài Chính**:
     - Danh sách chip dịch vụ đã chọn kèm thời lượng và đơn giá từng món.
     - Tổng chi phí tạm tính và tổng thời lượng dự kiến.
     - Tag hóa đơn kèm mã `#HDxxx` khi lịch hẹn đã thanh toán.
  6. **Bộ Nút Hành Động Nhanh Theo Phân Quyền (RBAC Actions)**:
     - **Thợ (`Tho`)**: `▶ Bắt đầu làm`, `★ Hoàn thành`, `⚡ AI Tóm Tắt 5s`, `📜 Lịch Sử`.
     - **Lễ tân / Admin (`LeTan`, `Admin`)**: `✓ Xác Nhận`, `⏱️ Đổi Giờ`, `▶ Bắt đầu làm`, `💳 Thu Tiền (POS)`, `📲 Nhắc Lịch SMS/Zalo`, `⚡ AI Tóm Tắt`, `✕ Hủy Lịch`.
- **Luồng phụ (A1 - Thợ bị trùng giờ)**: Trả về HTTP 400 kèm thông báo thợ đã bận và đề xuất các thợ khác đang rảnh.
- **Tiêu chí nghiệm thu (AC)**: 
  - 100% không cho phép tạo lịch hẹn giao thoa thời gian của cùng một thợ.
  - Chuyển đổi mượt mà giữa chế độ Sơ đồ ghế và Thẻ lịch hẹn không bị vỡ layout.
  - Thẻ lịch hẹn phản ánh thời gian thực trạng thái phục vụ và hiển thị đầy đủ cảnh báo chất tóc.

### UC006: Thu Ngân POS, Giảm Giá & Xuất Hóa Đơn
- **Mục tiêu**: Hoàn tất thanh toán, áp dụng chiết khấu và in phiếu thanh toán sang trọng.
- **Luồng chính**:
  1. Chọn lịch hẹn đã hoàn thành.
  2. Nhập số tiền giảm giá (mặc định 0 đ).
  3. Kiểm tra tính hợp lệ: `0 <= GiamGia <= TongTien` và `ThanhTien = TongTien - GiamGia`.
  4. Chọn hình thức: Tiền mặt, Chuyển khoản, Thẻ.
  5. Lưu vào bảng `HoaDon`, đổi trạng thái lịch hẹn sang `Đã thanh toán`.
- **Tiêu chí nghiệm thu (AC)**: Sai lệch công thức tiền tệ bị chặn ngay từ tầng CSDL qua ràng buộc `CHECK`.

### UC007: Báo Cáo Doanh Thu & Hiệu Suất Vận Hành (Admin)
- **Mục tiêu**: Tổng hợp doanh thu thực tế, số lượng hóa đơn, giá trị trung bình/hóa đơn và xuất file CSV.
- **Tiêu chí nghiệm thu (AC)**: Dữ liệu tính toán từ hóa đơn thực tế, hỗ trợ lọc theo ngày/tháng/năm.

### UC008: AI Gợi Ý Dịch Vụ Thông Minh (AI Smart Recommender)
- **Mục tiêu**: Phân tích chất tóc của khách để gợi ý liệu trình phù hợp nhất từ menu salon.
- **Quy tắc**: Chỉ gợi ý các dịch vụ có thực trong CSDL, giải thích lý do khoa học rõ ràng (Ví dụ: tóc tẩy yếu cần Nano Keratin thay vì uốn nóng).

### UC009: AI Sinh Tin Nhắn Nhắc Lịch Tự Động (AI Reminder)
- **Mục tiêu**: Tự động sinh nội dung SMS / Zalo nhắc hẹn khách chu đáo, bao gồm tên khách, giờ hẹn, tên stylist và dịch vụ.

### UC010: AI Tóm Tắt Hồ Sơ 5 Giây Cho Thợ (AI Stylist 5s Summary)
- **Mục tiêu**: Giúp thợ làm tóc nắm bắt tình trạng tóc và các cảnh báo nguy hiểm (dị ứng hóa chất, tẩy cấp độ cao) chỉ trong 5 giây trước khi thực hiện.

---

## 4. Đặc Tả Yêu Cầu Phi Chức Năng (NFRs)

1. **Hiệu năng (Performance)**:
   - Các API truy vấn CSDL nội bộ phản hồi dưới **150ms**.
   - API Trợ lý AI qua Cloud phản hồi dưới **3.5 giây**, có cơ chế fallback không làm đơ giao diện.
2. **Bảo mật (Security)**:
   - Toàn bộ dữ liệu mật khẩu được bảo vệ; API Key lưu trong `.env` không rò rỉ cho client.
   - Phiên làm việc kiểm soát nghiêm ngặt Single Device Session.
3. **Độ tin cậy (Reliability)**:
   - Hoạt động ổn định trên môi trường máy chủ nội bộ không đòi hỏi kết nối Internet liên tục cho các nghiệp vụ đặt lịch và thu ngân.
4. **Trải nghiệm người dùng (Usability)**:
   - Giao diện Neo-Glassmorphism hiện đại, hỗ trợ nút mắt 👁️ xem mật khẩu, tương thích mọi độ phân giải màn hình.

---

## 5. Điểm Kiểm Soát Con Người: Human Gate 1
- **Mục đích**: Chặn đứng việc chuyển tiếp các yêu cầu mơ hồ hoặc sai lệch nghiệp vụ salon sang bước thiết kế và code.
- **Quy tắc Gate 1**:
  1. [x] Đầy đủ 10 Use Cases đã được phê duyệt.
  2. [x] Ma trận truy vết yêu cầu (Traceability Matrix) từ Nhu cầu -> Use Case -> CSDL -> API đã được xác nhận.
  3. [x] Không tồn tại xung đột giữa các luồng Alternative.

<!--
  BÁO CÁO SINH TỰ ĐỘNG BỞI AI AGENT RUNNER
  Kỹ năng: Thiết Kế Giao Diện & Trải Nghiệm POS (UI/UX Design) (ui-ux-design)
  Thời gian tạo: 2026-10-03 13:42:09
  Thời gian thực thi: 1.03s
  Model: Google Gemini (gemini-3.8-flash)
-->

# BÁO CÁO ĐẶC TẢ KỸ NĂNG: Thiết Kế Giao Diện & Trải Nghiệm POS (UI/UX Design)

> **Trạng thái**: Tự động sinh bởi Grounded Local Engine
> **Thời gian**: 03/10/2026 13:42:09

## 1. Tổng Quan Kỹ Năng
Neo-Glassmorphism, bàn cờ lịch hẹn trực quan, POS thu ngân, in hóa đơn nhiệt 80mm/58mm.

## 2. Nội Dung Chỉ Dẫn Kỹ Năng Chi Tiết

---
name: ui-ux-design
description: Quy chuẩn thiết kế giao diện Neo-Glassmorphism, trải nghiệm quầy thu ngân POS, in ấn hóa đơn nhiệt, quản lý trạng thái client và kiểm soát tương tác người dùng đa nền tảng.
version: 2.0.0
---

# UI/UX Design & Frontend Engineering Skill (Kỹ Năng Thiết Kế Giao Diện & Trải Nghiệm Người Dùng)

## 1. Mục Tiêu & Triết Lý Thiết Kế Cốt Lõi
Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI phục vụ nhiều đối tượng với nhu cầu tương tác khác biệt: Chủ salon (Admin) cần bảng số liệu trực quan; Lễ tân/Thu ngân (LeTan) cần thao tác POS siêu tốc trên màn hình cảm ứng; Thợ tóc (Tho) thao tác nhanh trên điện thoại di động; và Khách hàng cần trải nghiệm tư vấn phong cách tóc sang trọng.

### Triết lý "Neo-Glassmorphism Salon Luxury"
- **Không gian màu**: Tông nền tối bí ẩn và hiện đại kết hợp hiệu ứng kính mờ chiều sâu (`backdrop-filter: blur(16px)`), viền phát sáng siêu mảnh (`border: 1px solid rgba(255, 255, 255, 0.08)`), điểm xuyết sắc vàng ánh kim (Gold/Amber `#f59e0b`) biểu trưng cho sự quý phái của ngành thời trang tóc cao cấp.
- **Tốc độ & Sự mượt mà**: Không sử dụng framework frontend cồng kềnh, ưu tiên Vanilla CSS và JavaScript thuần để thời gian khởi tạo (First Contentful Paint) luôn dưới 300ms trên mọi máy tính quầy POS salon.

---

## 2. Hệ Thống Design Tokens & Bảng Màu Chuẩn

### 2.1. Biến CSS Toàn Cục (`static/css/style.css`)
```css
:root {
  /* Tông màu nền chính */
  --bg-primary: #0f172a;       /* Slate 900 */
  --bg-surface: #1e293b;       /* Slate 800 */
  --bg-card: rgba(30, 41, 59, 0.7);
  --bg-glass: rgba(15, 23, 42, 0.65);

  /* Màu điểm nhấn thương hiệu */
  --primary: #f59e0b;          /* Amber Gold */
  --primary-hover: #d97706;
  --primary-light: rgba(245, 158, 11, 0.15);

  /* Màu trạng thái nghiệp vụ */
  --success: #10b981;          /* Emerald - Hoàn thành, Đã thanh toán */
  --warning: #f59e0b;          /* Amber - Đang phục vụ, Chờ xác nhận */
  --danger: #ef4444;           /* Rose - Hủy lịch, Cảnh báo nguy hiểm */
  --info: #06b6d4;             /* Cyan - AI Suggestions, Khách mới */

  /* Kiểu chữ & Độ mờ */
  --font-sans: 'Outfit', 'Inter', system-ui, -apple-system, sans-serif;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 18px;
  --shadow-glass: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  --border-glass: 1px solid rgba(255, 255, 255, 0.08);
}
```

---

## 3. Đặc Tả Hiện Thực Hóa 4 Screen Flows Nghiệp Vụ

### 3.1. Screen Flow 1: Đăng Nhập & Chuyển Đổi Phân Hệ Theo Vai Trò
- **Role Switcher Tức Thì**: Bộ chuyển vai trò Demo tiện ích (`#role-selector`) cho phép thử nghiệm nhanh quyền `Admin`, `LeTan`, `Tho`, `Guest` mà không cần logout thủ công.
- **Bảo Vệ Đơn Phiên (Single-Device Kickout Dialog)**:
  - Khi thiết bị khác đăng nhập, hộp thoại cảnh báo `#modal-session-kicked` lập tức hiển thị với hiệu ứng khóa nền `backdrop-filter: blur(20px)`.
  - Nút bấm duy nhất: "Đăng Nhập Lại Tại Đây", đồng thời xóa token trong `localStorage` để dọn sạch phiên làm việc cũ.

### 3.2. Screen Flow 2: Modal Tạo Lịch Hẹn & Tích Hợp AI Gợi Ý
- **Luồng 3 Bước Tối Giản**:
  - **Bước 2.1**: Chọn hoặc tìm kiếm nhanh khách hàng qua số điện thoại/tên. Tự động hiển thị thẻ tóm tắt chất tóc gần nhất.
  - **Bước 2.2**: Nút bấm `✨ AI Gợi Ý Dịch Vụ` mở popup tư vấn thông minh, phân tích chất tóc và đề xuất combo dịch vụ thích hợp, bấm "Áp Dụng" để tự động tick chọn dịch vụ vào form.
  - **Bước 2.3**: Checkbox "Chỉ hiện Thợ đang rảnh" tự động kiểm tra khoảng thời gian `[ThoiGianBatDau, ThoiGianBatDau + TongThoiLuong]` để loại trừ thợ đã vướng lịch, ngăn chặn 100% lỗi xung đột lịch thợ.

### 3.3. Screen Flow 3: Trạm Thu Ngân POS & In Hóa Đơn Nhiệt
- **POS Checkout Modal**:
  - Tự động cộng tổng tiền gốc các dịch vụ đã làm.
  - Trường nhập liệu giảm giá (`GiamGia`) với cơ chế tính tự động: `ThanhTien = TongTien - GiamGia`.
  - Lựa chọn phương thức thanh toán nhanh: Tiền mặt, Chuyển khoản QR, Thẻ ngân hàng.
- **Mẫu In Phiếu Hóa Đơn Chuẩn Khổ 80mm/58mm**:
  - CSS chuyên trách `@media print` ẩn toàn bộ header, thanh điều hướng và nút thao tác, chỉ tập trung vào khổ hóa đơn nhiệt salon sắc nét.
  - Bao gồm: Logo Salon, Mã hóa đơn (`HD001`), Tên thợ phụ trách, Bảng dịch vụ chi tiết, Mã QR chuyển khoản và Lời cảm ơn.

### 3.4. Screen Flow 4: Phân Hệ Quản Trị Hệ Thống (Admin Dashboard)
- **4 Thẻ Chỉ Số KPI Thời Gian Thực**: Doanh thu hôm nay, Số lịch hẹn mới, Tỷ lệ lấp đầy ghế làm tóc, Đánh giá chất lượng trung bình.
- **Quản lý Nhân sự & Phân ca**: Bật tắt trạng thái làm việc trực quan (`Rảnh`, `Bận`, `Nghỉ ca`).
- **Xuất Dữ Liệu Báo Cáo**: Nút xuất file CSV báo cáo doanh thu theo mốc ngày chỉ với 1 cú nhấp chuột.

---

## 4. Quản Lý Trạng Thái Phía Client (State Management)

Hệ thống quản lý trạng thái tập trung trong biến toàn cục `state`:
```javascript
const state = {
  authToken: localStorage.getItem('token') || null,
  currentRole: 'Admin',
  currentUser: null,
  services: [],
  stylists: [],
  appointments: [],
  activeFilterDate: new Date().toISOString().split('T')[0],
  heartbeatTimer: null
};
```

### Quy tắc cập nhật giao diện (UI State Rules):
1. **Không Reload Trang**: Toàn bộ thao tác thêm/sửa/xóa/đổi ngày đều sử dụng fetch API bất đồng bộ và cập nhật cục bộ vùng DOM tương ứng (DOM Patching).
2. **Debounce Tìm Kiếm**: Các ô tìm kiếm khách hàng, tìm kiếm dịch vụ phải gắn debounce tối thiểu `250ms` để giảm áp lực gọi API liên tục.
3. **Toast Notifications Thống Nhất**: Mọi thông báo thành công hoặc lỗi đều hiển thị qua hàm `showToast(message, type)` ở góc trên bên phải màn hình, tự động biến mất sau 3.5 giây.

---

## 5. Checklist Kiểm Thử Trải Nghiệm Giao Diện (UX Quality Checklist)

- [ ] **Kích thước nút bấm cảm ứng (Touch Target)**: Mọi nút bấm trên giao diện POS và điện thoại phải đạt kích thước tối thiểu `44x44px` để nhân viên dễ thao tác bằng ngón tay.
- [ ] **Trạng thái Trống (Empty State)**: Khi ngày chọn không có lịch hẹn hoặc bảng dịch vụ rỗng, luôn hiển thị hình minh họa và thông báo hướng dẫn thay vì để trống màn hình.
- [ ] **Khả năng tương thích in ấn**: Nhấn phím `Ctrl + P` trên hóa đơn thanh toán hiển thị đúng kích cỡ giấy in nhiệt, không bị tràn lề hoặc mất chi tiết.
- [ ] **Hiển thị mật khẩu**: Mọi trường mật khẩu đều có nút icon con mắt 👁️ cho phép nhân viên kiểm tra trước khi bấm lưu.
- [ ] **Phím tắt tiện dụng**: Hỗ trợ phím `Escape` để đóng modal nhanh và phím `Enter` trong form tìm kiếm để tra cứu tức thì.


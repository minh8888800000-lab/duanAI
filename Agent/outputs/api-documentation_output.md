<!--
  BÁO CÁO SINH TỰ ĐỘNG BỞI AI AGENT RUNNER
  Kỹ năng: Đặc Tả Hợp Đồng RESTful API (API Documentation) (api-documentation)
  Thời gian tạo: 2026-10-03 13:42:07
  Thời gian thực thi: 15.87s
  Model: Google Gemini (gemini-3.8-flash)
-->

# BÁO CÁO ĐẶC TẢ KỸ NĂNG: Đặc Tả Hợp Đồng RESTful API (API Documentation)

> **Trạng thái**: Tự động sinh bởi Grounded Local Engine
> **Thời gian**: 03/10/2026 13:42:07

## 1. Tổng Quan Kỹ Năng
Quy chuẩn 25+ endpoints, chuẩn Envelope, RFC 7807 Problem Details và tài liệu SOP.

## 2. Nội Dung Chỉ Dẫn Kỹ Năng Chi Tiết

---
name: api-documentation
description: Quy chuẩn thiết kế RESTful API, hợp đồng dữ liệu chuẩn hóa, đặc tả 25+ endpoints cho salon tóc, xử lý lỗi RFC 7807 và tài liệu SOP vận hành.
version: 2.0.0
---

# API Design & Technical Documentation Skill (Kỹ Năng Thiết Kế API & Tài Liệu Kỹ Thuật)

## 1. Mục Tiêu & Nguyên Tắc Thiết Kế RESTful Chuẩn Quốc Tế
Cung cấp bộ quy chuẩn thống nhất về thiết kế, tài liệu hóa và bảo trì các giao diện lập trình ứng dụng (RESTful API) trong Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI. Đảm bảo tính nhất quán giữa Backend (Python/Flask) và Frontend (Vanilla JS POS), hỗ trợ kiểm thử tự động và tích hợp bên thứ ba (máy in nhiệt, cổng thanh toán QR, Zalo OA).

### Chuẩn Hóa Cấu Trúc Envelope Phản Hồi (Standard Response Envelope)
Mọi endpoint đều phải trả về định dạng JSON có cấu trúc bao đóng đồng nhất:
```json
{
  "success": true,
  "data": { ... },
  "message": "Mô tả trạng thái thực thi thành công",
  "errors": null,
  "meta": {
    "timestamp": "2026-09-26T16:30:00",
    "version": "v1"
  }
}
```

Khi có lỗi phát sinh, cấu trúc tuân theo chuẩn **RFC 7807 Problem Details**:
```json
{
  "success": false,
  "data": null,
  "code": "CONCURRENT_LOGIN",
  "message": "Tài khoản của bạn đã được đăng nhập từ một thiết bị khác.",
  "errors": [
    { "field": "SessionToken", "reason": "Token session mismatch" }
  ]
}
```

---

## 2. Danh Mục 25+ API Endpoints Hệ Thống Salon Tóc

### 2.1. Phân Hệ Xác Thực & Quản Lý Đơn Phiên (Authentication & Session)
| Method | Endpoint | Yêu cầu quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Public | Đăng nhập tài khoản, thu hồi phiên cũ, cấp phát SessionToken & JWT mới |
| `POST` | `/api/auth/logout` | Đã đăng nhập | Đăng xuất, hủy bỏ SessionToken trong CSDL |
| `GET` | `/api/auth/me` | Đã đăng nhập | Heartbeat kiểm tra tính hợp lệ của đơn phiên (Single-Device Session) |

### 2.2. Phân Hệ Quản Lý Khách Hàng (Customer Management)
| Method | Endpoint | Yêu cầu quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/customers` | LeTan, Admin | Lấy danh sách khách hàng (hỗ trợ lọc theo SĐT hoặc tên) |
| `POST` | `/api/customers` | LeTan, Admin | Thêm mới hồ sơ khách hàng và đặc điểm chất tóc |
| `GET` | `/api/customers/<id>` | LeTan, Admin | Lấy chi tiết hồ sơ và lịch sử làm tóc của một khách hàng |
| `PUT` | `/api/customers/<id>` | LeTan, Admin | Cập nhật hồ sơ chất tóc, số điện thoại, ghi chú |
| `DELETE` | `/api/customers/<id>` | Admin | Xóa hồ sơ khách hàng (Bảo toàn log AI với `SET NULL`) |

### 2.3. Phân Hệ Quản Lý Dịch Vụ Salon (Service Catalog)
| Method | Endpoint | Yêu cầu quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/services` | Public | Xem menu bảng giá niêm yết và thời lượng dịch vụ |
| `POST` | `/api/services` | Admin | Tạo mới dịch vụ |
| `PUT` | `/api/services/<id>` | Admin | Cập nhật tên dịch vụ, giá tiền hoặc thời lượng phút |
| `DELETE` | `/api/services/<id>` | Admin | Xóa dịch vụ (Chặn xóa nếu dịch vụ đang có lịch hẹn: `RESTRICT`) |

### 2.4. Phân Hệ Quản Lý Nhân Sự & Stylist (Staff & Stylists)
| Method | Endpoint | Yêu cầu quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/stylists` | Public | Lấy danh sách Thợ làm tóc kèm trạng thái làm việc |
| `GET` | `/api/employees` | Admin | Lấy danh sách toàn bộ nhân viên (Lễ tân, Thợ, Quản lý) |
| `POST` | `/api/employees` | Admin | Thêm nhân viên mới |
| `PUT` | `/api/employees/<id>` | Admin | Cập nhật thông tin nhân viên, đổi vai trò |
| `PUT` | `/api/stylists/<id>/status` | Tho, Admin | Bật/tắt trạng thái thợ (`Rảnh`, `Bận`, `Nghỉ ca`) |

### 2.5. Phân Hệ Lịch Hẹn & Chống Trùng Lịch (Appointments & Conflict Prevention)
| Method | Endpoint | Yêu cầu quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/appointments` | Đã đăng nhập | Xem danh sách lịch hẹn theo ngày (Thợ chỉ thấy lịch của mình) |
| `POST` | `/api/appointments` | LeTan, Admin | Tạo lịch hẹn mới (Kiểm tra chặn giao thoa giờ thợ `[S1, E1] ∩ [S2, E2]`) |
| `PUT` | `/api/appointments/<id>/status`| LeTan, Tho, Admin| Cập nhật trạng thái (`Đã đặt`, `Đang phục vụ`, `Hoàn thành`, `Hủy`) |
| `DELETE` | `/api/appointments/<id>` | Admin | Hủy lịch hẹn (Tự động xóa cascade các dòng trong `ChiTietLichHen`) |

### 2.6. Phân Hệ Hóa Đơn & Thu Ngân POS (POS Billing & Invoices)
| Method | Endpoint | Yêu cầu quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/invoices` | LeTan, Admin | Tạo hóa đơn thanh toán từ lịch hẹn, tính tiền tự động |
| `GET` | `/api/invoices/<id>` | LeTan, Admin | Xem chi tiết hóa đơn phục vụ in ấn phiếu nhiệt khổ 80mm/58mm |
| `GET` | `/api/invoices/daily` | Admin | Thống kê danh sách hóa đơn theo ngày |

### 2.7. Phân Hệ Báo Cáo & Thống Kê Doanh Thu (Reports & Analytics)
| Method | Endpoint | Yêu cầu quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/reports/dashboard` | Admin | 4 chỉ số KPI tổng quan (Doanh thu hôm nay, Số lịch, Tỷ lệ lấp đầy) |
| `GET` | `/api/reports/export-csv` | Admin | Xuất tệp tin dữ liệu báo cáo tài chính định dạng CSV |

### 2.8. Phân Hệ Trợ Lý AI (AI Stylist Assistant)
| Method | Endpoint | Yêu cầu quyền | Mô tả chức năng |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/ai/suggest` | Public | Gợi ý dịch vụ theo tình trạng chất tóc và lịch sử khách (UC008) |
| `POST` | `/api/ai/reminder` | LeTan, Admin | Soạn tin nhắn nhắc hẹn ấm áp gửi Zalo/SMS cho khách (UC009) |
| `POST` | `/api/ai/summary` | Tho, Admin | Tóm tắt hồ sơ chất tóc 5 giây hiển thị cho Thợ (UC010) |
| `POST` | `/api/ai/chat` | Đã đăng nhập | Trò chuyện với Trợ lý AI và cập nhật giá dịch vụ (RBAC Enforced) |
| `GET` | `/api/ai/config` | Admin | Kiểm tra trạng thái kết nối Cloud Gemini và Local Fallback |

---

## 3. Quy Trình Vận Hành Chuẩn SOP (Standard Operating Procedures)

### 3.1. SOP-01 Dành Cho Quản Trị Viên (Admin)
1. **Đăng nhập hệ thống**: Truy cập `http://localhost:5000`, đăng nhập bằng tài khoản Quản trị.
2. **Kiểm tra KPI Salon**: Xem doanh thu hôm nay và tỷ lệ lấp đầy ghế tại thẻ Dashboard.
3. **Quản lý danh mục dịch vụ**: Cập nhật giá niêm yết qua giao diện hoặc ra lệnh tự nhiên cho Trợ lý AI (ví dụ: *"Cập nhật giá cắt tóc nam lên 150k"*).
4. **Xuất báo cáo định kỳ**: Nhấp nút "Xuất CSV Báo Cáo" cuối mỗi ngày làm việc để lưu trữ sổ sách kế toán.

### 3.2. SOP-02 Dành Cho Lễ Tân & Thu Ngân (LeTan)
1. **Tiếp nhận khách đặt lịch**:
   - Mở màn hình Lịch Hẹn -> Bấm "Tạo Lịch Mới".
   - Nhập SĐT khách hàng; nếu khách có hồ sơ cũ, bấm "✨ AI Gợi Ý" để nhận tư vấn combo phù hợp.
   - Bật checkbox "Chỉ thợ đang rảnh" để chọn Stylist phù hợp, không bị trùng giờ.
2. **Gửi tin nhắn xác nhận**: Bấm nút "Nhắc lịch AI" để hệ thống tự soạn tin nhắn gửi qua Zalo/SMS.
3. **Thanh toán tại quầy POS**:
   - Khi khách làm xong, bấm nút "Thanh toán POS" trên lịch hẹn.
   - Nhập giảm giá nếu có (hệ thống tự tính Thành tiền), chọn phương thức (Tiền mặt/Chuyển khoản).
   - Bấm "Xác nhận & In Phiếu", bấm `Ctrl + P` in bill nhiệt gửi khách.

### 3.3. SOP-03 Dành Cho Thợ Stylist (Tho)
1. **Kiểm tra ca làm việc**: Đăng nhập tài khoản Stylist, xem danh sách khách hàng được phân công trong ngày.
2. **Đọc hồ sơ nhanh 5 giây**: Trước khi mời khách vào ghế, mở thẻ lịch hẹn để đọc bản tóm tắt cảnh báo chất tóc (tránh dùng hóa chất tẩy mạnh nếu tóc yếu).
3. **Cập nhật tiến độ**: Bấm chuyển trạng thái từ "Đang phục vụ" sang "Hoàn thành" để quầy thu ngân tiếp nhận thanh toán.


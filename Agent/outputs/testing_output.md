<!--
  BÁO CÁO SINH TỰ ĐỘNG BỞI AI AGENT RUNNER
  Kỹ năng: Kịch Bản Kiểm Thử Toàn Diện (Testing & QA) (testing)
  Thời gian tạo: 2026-10-03 13:42:12
  Thời gian thực thi: 1.37s
  Model: Google Gemini (gemini-3.8-flash)
-->

# BÁO CÁO ĐẶC TẢ KỸ NĂNG: Kịch Bản Kiểm Thử Toàn Diện (Testing & QA)

> **Trạng thái**: Tự động sinh bởi Grounded Local Engine
> **Thời gian**: 03/10/2026 13:42:12

## 1. Tổng Quan Kỹ Năng
Bộ kiểm thử Unit Tests, Integration Tests, kịch bản tranh chấp Single-Device Session và E2E.

## 2. Nội Dung Chỉ Dẫn Kỹ Năng Chi Tiết

---
name: testing
description: Quy trình kiểm thử tự động toàn diện (Unit Tests, Integration Tests, E2E Browser Concurrency Tests) và tiêu chí nghiệm thu trước khi release.
version: 2.0.0
---

# Testing Skill (Kỹ Năng Kiểm Thử Tự Động & Đảm Bảo Chất Lượng)

## 1. Mục Tiêu & Chiến Lược Kiểm Thử (Testing Strategy)
Đảm bảo 100% các tính năng nghiệp vụ, ràng buộc CSDL SQLite, cơ chế kiểm soát đơn phiên (Single-Device Session) và động cơ Trợ lý AI đều được kiểm thử tự động, không để sót lỗi hồi quy (regression bugs) khi cập nhật mã nguồn.

Kiến trúc kiểm thử 3 tầng:
1. **Tầng 1 - Unit Test CSDL & Mô Hình**: Kiểm chứng tính toàn vẹn của schema, quan hệ khóa ngoại, filtered unique index và CHECK constraints.
2. **Tầng 2 - Integration Test Web API**: Kiểm chứng các luồng gọi REST API, tính toán thời gian đặt lịch, phân quyền JWT và xử lý ngoại lệ nghiệp vụ.
3. **Tầng 3 - E2E & Concurrency Test**: Kiểm thử trực tiếp tương tác trình duyệt (Chrome headless) mô phỏng thiết bị A và thiết bị B đăng nhập đồng thời để kiểm tra cơ chế đá văng (kick out).

---

## 2. Danh Mục Các Bộ Kiểm Thử Bắt Buộc Trong Kho Mã Nguồn

### 2.1. Kiểm Thử CSDL SQLite (`tests/test_db_schema.py`)
Bao gồm 8 unit tests kiểm tra toàn vẹn dữ liệu:
1. `test_all_tables_exist`: Kiểm tra sự tồn tại đầy đủ của 8 bảng (`TaiKhoan`, `NhanVien`, `KhachHang`, `DichVu`, `LichHen`, `ChiTietLichHen`, `HoaDon`, `TroLyAI`).
2. `test_filtered_unique_phone_customer`: Kiểm tra Filtered Unique Index cho phép lưu nhiều khách `SoDienThoai = NULL` nhưng chặn đứng việc lưu trùng số điện thoại thực.
3. `test_foreign_key_enforcement`: Kiểm tra máy chủ SQLite bật cờ `PRAGMA foreign_keys = ON;`, chặn thêm khóa ngoại không tồn tại.
4. `test_invoice_calculation_constraint`: Kiểm tra ràng buộc `CHECK (ThanhTien = TongTien - GiamGia)` văng lỗi `sqlite3.IntegrityError` nếu cố tình sửa lệch tiền.
5. `test_on_delete_cascade_appointment_details`: Kiểm tra khi xóa `LichHen`, toàn bộ `ChiTietLichHen` liên quan tự động bị xóa theo cascade.
6. `test_on_delete_restrict_service`: Kiểm tra xóa `DichVu` đang có lịch hẹn bị chặn bởi `sqlite3.IntegrityError`.
7. `test_on_delete_set_null_tro_ly_ai`: Kiểm tra khi xóa `KhachHang`, log trong `TroLyAI` được cập nhật `MaKhachHang = NULL` để bảo toàn dữ liệu kiểm toán.
8. `test_role_enum_constraint`: Kiểm tra chỉ chấp nhận 3 vai trò `Admin`, `LeTan`, `Tho`.

### 2.2. Kiểm Thử Tích Hợp Web API (`tests/test_web_integration.py`)
1. `test_health_and_index`: Kiểm tra endpoint `/health` và trang chủ `/` trả về mã 200 kèm giao diện tiếng Việt UTF-8.
2. `test_services_and_customers_api`: Kiểm tra danh sách dịch vụ và khách hàng trả về đúng cấu trúc JSON.
3. `test_booking_conflict_prevention`: Kiểm tra thuật toán phát hiện giao thoa giờ hẹn của thợ:
   - Thử tạo lịch hẹn 1: 09:00 - 10:30 với Stylist NV004.
   - Thử tạo lịch hẹn 2: 10:00 - 11:00 với cùng Stylist NV004 -> Bắt buộc trả về HTTP 400 và thông báo xung đột lịch.
4. `test_ai_endpoints`: Kiểm tra các endpoint `/api/ai/suggest`, `/api/ai/reminder`, `/api/ai/summary`.

### 2.3. Kiểm Thử Đơn Phiên Đăng Nhập (`tests/test_single_device_session.py`)
Quy trình kiểm thử 6 bước mô phỏng 2 thiết bị:
1. Thiết bị A đăng nhập tài khoản `admin` -> Nhận `Token_A` (thành công).
2. Thiết bị A gọi API `/api/auth/me` với `Token_A` -> Trả về HTTP 200 (hợp lệ).
3. Thiết bị B đăng nhập cùng tài khoản `admin` -> Cấp `SessionToken` mới, nhận `Token_B` (thành công).
4. Thiết bị B gọi API `/api/auth/me` với `Token_B` -> Trả về HTTP 200 (hợp lệ).
5. Thiết bị A gọi lại API `/api/auth/me` với `Token_A` -> Bắt buộc trả về **HTTP 401** kèm `{ "kicked": True, "code": "CONCURRENT_LOGIN" }`.
6. Thiết bị A gọi bất kỳ API nghiệp vụ nào khác (như `/api/accounts`) -> Bắt buộc bị chặn HTTP 401.

### 2.4. Kiểm Thử Trình Duyệt Chrome Headless (`tests/verify_browser_kicked.py`)
- Mở phiên trình duyệt Chrome thực tế, đăng nhập tài khoản.
- Kích hoạt đăng nhập từ phiên thứ hai.
- Kiểm tra DOM trình duyệt thứ nhất: Sau chu kỳ heartbeat (3.5 giây), modal cảnh báo `#modal-session-kicked` phải tự động bật lên và `localStorage` bị xóa sạch.

---

## 3. Quy Trình Chạy Kiểm Thử Tự Động (Run Commands)

```bash
# 1. Chạy toàn bộ test suites CSDL & Nghiệp vụ
python -m unittest discover tests -v

# 2. Chạy riêng test kiểm tra schema CSDL
python tests/test_db_schema.py

# 3. Chạy riêng test kiểm tra đơn phiên Single Device Session
python tests/test_single_device_session.py

# 4. Kiểm tra tương tác Trợ lý AI thực tế
python tests/test_demo_ai.py
```

---

## 4. Tiêu Chí Nghiệm Thu Chất Lượng (Quality Gate Criteria)

- **100% Pass Rate**: Tuyệt đối không release khi có bất kỳ bài test nào bị FAIL hoặc ERROR.
- **Tính Bất Biến Của Ràng Buộc**: Mọi sự thay đổi về schema hoặc logic thanh toán bắt buộc phải cập nhật test case tương ứng trước khi commit.
- **Kiểm Thử Môi Trường Thực**: Test phải chạy thành công trực tiếp trên máy chủ Flask đang vận hành tại `http://127.0.0.1:5000`.


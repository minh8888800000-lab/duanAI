<!--
  BÁO CÁO SINH TỰ ĐỘNG BỞI AI AGENT RUNNER
  Kỹ năng: Kiểm Toán An Ninh & Bảo Mật (Security Review) (security-review)
  Thời gian tạo: 2026-10-03 13:42:15
  Thời gian thực thi: 1.04s
  Model: Google Gemini (gemini-3.8-flash)
-->

# BÁO CÁO ĐẶC TẢ KỸ NĂNG: Kiểm Toán An Ninh & Bảo Mật (Security Review)

> **Trạng thái**: Tự động sinh bởi Grounded Local Engine
> **Thời gian**: 03/10/2026 13:42:15

## 1. Tổng Quan Kỹ Năng
Phòng chống SQL Injection, RBAC rào chắn phân quyền, bảo vệ Session Token và API Key.

## 2. Nội Dung Chỉ Dẫn Kỹ Năng Chi Tiết

---
name: security-review
description: Quy trình kiểm toán an ninh bảo mật, ngăn chặn SQL Injection, bảo vệ phiên đơn Single-Device Session, kiểm soát RBAC, an toàn API Key và phòng chống rò rỉ dữ liệu.
version: 2.0.0
---

# Security Review Skill (Kỹ Năng Kiểm Toán & Bảo Mật Hệ Thống)

## 1. Mục Tiêu & Nguyên Lý An Toàn Thông Tin
Bảo vệ toàn diện dữ liệu nhạy cảm của Salon Tóc: thông tin khách hàng, số điện thoại, doanh thu tài chính, tài khoản đăng nhập của nhân viên và các khóa xác thực bí mật (JWT Secret, Google Gemini API Key). Đảm bảo hệ thống đạt chuẩn an toàn trước các lỗ hổng phổ biến trong OWASP Top 10.

---

## 2. Các Trụ Cột An Ninh Bắt Buộc

### 2.1. Phòng Chống SQL Injection (SQLi Prevention)
- **Quy tắc tuyệt đối**: 100% các câu truy vấn cơ sở dữ liệu SQLite trong backend bắt buộc phải sử dụng cơ chế tham số hóa (**Parameterized Queries**) với ký tự `?`.
- **Cấm kỵ**: Tuyệt đối không dùng kỹ thuật nối chuỗi (string concatenation), f-string, hoặc `%` format để đưa biến do người dùng nhập vào câu SQL.

```python
# CHUẨN AN TOÀN:
cursor.execute("SELECT * FROM TaiKhoan WHERE TenDangNhap = ?", (username,))

# NGUY CƠ LỖ HỔNG (CẤM):
cursor.execute(f"SELECT * FROM TaiKhoan WHERE TenDangNhap = '{username}'") # LỖI BẢO MẬT NGHIÊM TRỌNG
```

### 2.2. Kiểm Soát Đơn Phiên Đăng Nhập (Single-Device Session Security)
- **Rủi ro**: Nhân viên chia sẻ tài khoản dùng chung, đăng nhập cùng lúc ở nhiều quầy hoặc trên điện thoại cá nhân gây thất thoát doanh thu hoặc sai lệch thao tác POS.
- **Cơ chế phòng thủ**:
  1. Mỗi lần đăng nhập thành công (`AuthService.login`), hệ thống sinh một mã phiên ngẫu nhiên `sess_<uuid>` và cập nhật vào cột `SessionToken` của tài khoản trong CSDL.
  2. Mã này được đưa vào claim `session_id` của JWT token.
  3. Mọi request và heartbeat định kỳ (3.5 giây) đều kiểm tra: Nếu `session_id` trong token khác với `SessionToken` hiện tại trong CSDL, hệ thống lập tức thu hồi phiên (revoke) và trả về mã lỗi `401 CONCURRENT_LOGIN`.
  4. Trình duyệt cũ tự động xóa sạch `localStorage`, hủy phiên và bật popup cảnh báo.

### 2.3. Phân Quyền Dữ Liệu Dựa Trên Vai Trò (RBAC Enforcement)
Hệ thống thiết lập 4 cấp độ phân quyền chặt chẽ thông qua decorator `@require_auth(roles=[...])`:
- **`Admin` (Quản trị viên)**: Toàn quyền truy cập mọi API, quản lý tài khoản nhân viên, xem báo cáo doanh thu, cấu hình hệ thống.
- **`LeTan` (Lễ tân / Thu ngân)**: Được phép tạo lịch hẹn, xem thông tin khách, thực hiện thanh toán POS và in hóa đơn. Bị chặn truy cập các tab cấu hình hệ thống, xóa dịch vụ, hoặc xem báo cáo tài chính nâng cao.
- **`Tho` (Thợ làm tóc)**: Chỉ được xem lịch hẹn được phân công cho chính mã nhân viên của mình (`MaNhanVien`). Bị chặn toàn bộ các thao tác chỉnh sửa giá tiền, tạo khách, hoặc thu ngân.
- **`Guest` (Khách hàng vãng lai)**: Chỉ được xem menu dịch vụ công khai và trò chuyện tư vấn kiểu tóc với Trợ lý AI Stylist.

### 2.4. Quản Lý Khóa Bí Mật & API Keys
- Khóa bí mật máy chủ `SECRET_KEY` và `GEMINI_API_KEY` được tách biệt hoàn toàn trong file môi trường `.env`, có trong danh sách `.gitignore` để không bao giờ bị lộ lên kho mã nguồn công khai.
- Cung cấp file [`.env.example`](file:///d:/hay/.env.example) an toàn làm mẫu cấu hình.
- Khi API trả về thông tin cấu hình (`/api/ai/config`), chuỗi API Key bắt buộc phải được che giấu định danh (masking), ví dụ: `...8SPQ`, không bao giờ trả về nguyên vẹn chuỗi key gốc ra phía client.

### 2.5. Phòng Chống Cross-Site Scripting (XSS) & Dữ Liệu Độc Hại
- Toàn bộ dữ liệu hiển thị từ người dùng (tên khách hàng, ghi chú chất tóc) và phản hồi từ Trợ lý AI đều được gán thông qua các phương thức text node an toàn của DOM (`innerText` / `textContent`) hoặc qua hàm render có escape ký tự đặc biệt (`<`, `>`, `&`, `"`).
- Tuyệt đối không nhúng trực tiếp dữ liệu thô chưa kiểm duyệt vào `innerHTML`.

### 2.6. An Toàn Động Cơ Trợ Lý AI (AI Safety & Prompt Injection Prevention)
- Prompt gửi lên LLM (Google Gemini) luôn kèm **System Instruction** chặt chẽ, ràng buộc AI chỉ được đóng vai Trợ lý Salon Tóc Chuyên Nghiệp Hà Minh.
- Kỹ thuật Grounding: Khi hỏi về bảng giá hoặc doanh thu, dữ liệu được trích xuất trực tiếp từ CSDL SQLite trước khi gửi vào prompt, nghiêm cấm LLM tự suy diễn hoặc bịa đặt giá tiền ngoài danh mục đã được kiểm duyệt.

---

## 3. Quy Trình Kiểm Toán Bảo Mật Định Kỳ (Audit Checklist)

- [ ] Chạy kiểm thử tự động toàn vẹn khóa ngoại: `python tests/test_db_schema.py`.
- [ ] Chạy kiểm thử kịch bản đá văng phiên đồng thời: `python tests/test_single_device_session.py`.
- [ ] Quét toàn bộ repository tìm kiếm chuỗi bí mật bị hardcode (Regex search cho `AIzaSy...`, `secret_key...`).
- [ ] Kiểm tra phân quyền: Thử gọi các endpoint Admin bằng token của Thợ hoặc Lễ tân để xác nhận trả về `403 Forbidden`.


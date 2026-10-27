<!--
  BÁO CÁO SINH TỰ ĐỘNG BỞI AI AGENT RUNNER
  Kỹ năng: Quy Chuẩn Viết Mã Sạch (Implementation Standards) (implementation)
  Thời gian tạo: 2026-10-03 13:42:08
  Thời gian thực thi: 1.03s
  Model: Google Gemini (gemini-3.8-flash)
-->

# BÁO CÁO ĐẶC TẢ KỸ NĂNG: Quy Chuẩn Viết Mã Sạch (Implementation Standards)

> **Trạng thái**: Tự động sinh bởi Grounded Local Engine
> **Thời gian**: 03/10/2026 13:42:08

## 1. Tổng Quan Kỹ Năng
Clean Code, Service Layer độc lập, thuật toán De Morgan chống trùng lịch, xử lý Windows.

## 2. Nội Dung Chỉ Dẫn Kỹ Năng Chi Tiết

---
name: implementation
description: Tiêu chuẩn viết mã sạch Clean Code, phân tách lớp dịch vụ, xử lý triệt để logic biên (chống trùng lịch, quản lý phiên đơn, AI 2 tầng) và tương thích môi trường Windows.
version: 2.0.0
---

# Implementation Skill (Kỹ Năng Hiện Thực Hóa Mã Nguồn & Clean Code)

## 1. Mục Tiêu & Chuẩn Mực Lập Trình
Hiện thực hóa các tính năng phần mềm theo đúng tài liệu kiến trúc và đặc tả yêu cầu, tuân thủ nguyên tắc **Clean Code (Mã Sạch)**, **SOLID** (đặc biệt là Single Responsibility Principle), xử lý an toàn các trường hợp biên (Edge Cases) và bảo đảm tính tương thích cao trên môi trường Windows.

---

## 2. Tiêu Chuẩn Phân Tách Trách Nhiệm (SRP)

### 2.1. Quy Tắc Tuyệt Đối Cho Route Handlers (`backend/routes/api.py`)
- Route handler **chỉ** thực hiện 3 nhiệm vụ:
  1. Trích xuất thông tin người dùng xác thực từ token (`get_auth_user()`).
  2. Parse và validate sơ bộ input dữ liệu từ `request.get_json()`.
  3. Gọi hàm tương ứng từ Service Layer và trả về `jsonify(...)` kèm HTTP Status Code chuẩn (200, 201, 400, 401, 403, 404, 500).
- **Cấm kỵ**: Không viết câu lệnh SQL trực tiếp hay thuật toán tính toán phức tạp bên trong route handlers.

### 2.2. Quy Tắc Cho Service Layer (`backend/services/`)
- Toàn bộ logic nghiệp vụ, công thức toán học, quản lý transaction SQL `conn.commit() / conn.rollback()` phải nằm trọn vẹn trong Service class.
- Mọi hàm trong service đều có type hints rõ ràng (`from typing import Optional, Dict, Any, List`).

---

## 3. Xử Lý Các Trường Hợp Biên Cốt Lõi (Edge Cases)

### 3.1. Thuật Toán Chống Trùng Lịch Thợ (Overlapping Prevention)
Khoảng thời gian lịch hẹn mới `[S_new, E_new]` bị coi là **giao thoa / xung đột** với lịch hẹn đã có `[S_old, E_old]` của cùng một nhân viên khi và chỉ khi thỏa mãn biểu thức toán học:
$$\text{Conflict} \iff (S_{new} < E_{old}) \land (S_{old} < E_{new})$$

```python
# Code chuẩn hóa trong BookingService:
cursor.execute(
    """
    SELECT MaLichHen, GioBatDau, GioKetThuc
    FROM LichHen
    WHERE MaNhanVien = ?
      AND NgayHen = ?
      AND TrangThai != 'Hủy'
      AND (? < GioKetThuc AND ? > GioBatDau)
    """,
    (ma_nhan_vien, ngay_hen, gio_bat_dau, gio_ket_thuc),
)
conflict = cursor.fetchone()
if conflict:
    raise ValueError(f"Thợ đã có lịch phục vụ trong khung giờ {conflict['GioBatDau']} - {conflict['GioKetThuc']}.")
```

### 3.2. Xử Lý Khách Vãng Lai & SĐT Trống
- Khi khách hàng vãng lai không cung cấp số điện thoại:
  - Trường `SoDienThoai` được gán giá trị `None` (SQL `NULL`).
  - Filtered Unique Index `uq_khachhang_sdt` chỉ bắt buộc tính duy nhất đối với các bản ghi có `SoDienThoai IS NOT NULL`, cho phép lưu nhiều khách vãng lai `NULL` mà không bao giờ bị nghẽn CSDL.

### 3.3. Ràng Buộc Tiền Giảm Giá Hóa Đơn (Discount Edge Case)
- Nghiệp vụ thu ngân cấm tuyệt đối giảm giá âm hoặc giảm giá vượt quá tổng tiền dịch vụ:
```python
if giam_gia < 0:
    return {"success": False, "message": "Số tiền giảm giá không được âm."}
if giam_gia > tong_tien:
    return {"success": False, "message": "Giảm giá không được vượt quá tổng tiền hóa đơn."}
thanh_tien = tong_tien - giam_gia
```

### 3.4. Quản Lý Đơn Phiên Đăng Nhập (Single Device Session)
- Trong `AuthService.verify_token(token)`:
  - Giải mã JWT, lấy `session_id` từ claim token.
  - So sánh trực tiếp với `SessionToken` đang lưu trong CSDL của tài khoản đó.
  - Nếu khác nhau: Trả về lỗi `{ "kicked": True, "code": "CONCURRENT_LOGIN" }` để client tự động đăng xuất và báo động người dùng.

### 3.5. Động Cơ AI 2 Tầng Với Fallback Toàn Diện
- **Tầng 1 (Local Grounded Engine)**: Chạy tức thì, truy vấn CSDL SQLite và áp dụng 43+ quy tắc khoa học tóc Trichology (pH, liên kết Disunfua S-S, bọc Protein tơ tằm).
- **Tầng 2 (Cloud LLM)**: Kết nối Google Gemini qua direct REST API (`gemini-3.8-flash` hoặc `gemini-flash-latest`).
- **Nguyên tắc an toàn**: Nếu mất kết nối Internet, máy chủ Google quá tải (503) hoặc chưa có API Key, hệ thống **tự động fallback về Tầng 1**, tuyệt đối không trả về lỗi 500 hay làm treo ứng dụng.

---

## 4. Tương Thích Môi Trường Windows & Đa Nền Tảng

1. **Khắc phục lỗi mã hóa Windows Console (CP1252 / UnicodeEncodeError)**:
   - Mọi script entrypoint (`app.py`, test runners) phải cấu hình định dạng UTF-8 cho luồng stdout/stderr:
   ```python
   import sys
   if hasattr(sys.stdout, "reconfigure"):
       sys.stdout.reconfigure(encoding="utf-8")
   ```
2. **Khởi chạy Flask Server dưới dạng Daemon Process**:
   - Tắt tính năng tự tải lại gây nhân bản tiến trình trên Windows: `debug=False`, `use_reloader=False`.
   - Quản lý tiến trình bền vững bằng background task manager.

---

## 5. Chuẩn Hóa Phản Hồi API (Standardized JSON Responses)

Mọi API trả về đều tuân thủ cấu trúc đồng nhất:
```json
// Thành công:
{
  "success": true,
  "data": { ... },
  "message": "Thông báo thân thiện với người dùng"
}

// Thất bại:
{
  "success": false,
  "message": "Mô tả nguyên nhân lỗi cụ thể",
  "code": "ERROR_CODE_NẾU_CÓ"
}
```


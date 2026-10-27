---
name: code-review
description: Quy trình rà soát chất lượng mã nguồn, tuân thủ Clean Architecture, quản lý transaction an toàn, kiểm soát RBAC và mẫu so sánh Good vs Bad code.
version: 2.0.0
---

# Code Review Skill (Kỹ Năng Rà Soát Chất Lượng Mã Nguồn)

## 1. Mục Tiêu & Phạm Vi Rà Soát
Thiết lập quy chuẩn kiểm duyệt mã nguồn có hệ thống (Code Review Runbook) cho các thay đổi trong Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI. Đảm bảo mọi commit đều tuân thủ kiến trúc phân tầng, quản lý transaction an toàn và không gây suy giảm bảo mật hoặc hiệu năng.

---

## 2. Checklist Rà Soát 5 Trọng Điểm Cốt Lõi

### 2.1. Phân Tầng Kiến Trúc & Trách Nhiệm Đơn Lẻ (Architecture & SRP)
- [ ] **Tách biệt Routes và Services**: Các file `routes/api.py` có giữ đúng vai trò tiếp nhận request và phản hồi JSON? Có hàm nào bị "béo phì" do chứa logic tính toán nghiệp vụ hay không?
- [ ] **Không bypass tầng nghiệp vụ**: Mọi thao tác ghi dữ liệu phức tạp (như tạo lịch hẹn kèm nhiều dịch vụ, xuất hóa đơn) bắt buộc phải đi qua Service class chuyên trách (`booking_service.py`, `billing_service.py`).
- [ ] **Không lẫn lộn View và Logic**: Giao diện client (`templates/index.html`) không chứa các đoạn mã tính toán tiền tệ nhạy cảm; toàn bộ số tiền thanh toán cuối cùng phải do máy chủ xác nhận.

### 2.2. Toàn Vẹn Dữ Liệu & Quản Lý Giao Dịch (Transactions & Atomicity)
- [ ] **Bọc khối Transaction**: Mọi thao tác ghi ảnh hưởng từ 2 bảng trở lên (ví dụ: tạo `LichHen` và ghi nhiều dòng `ChiTietLichHen`, hoặc xóa tài khoản và gỡ liên kết nhân viên) bắt buộc phải sử dụng `try ... conn.commit()` và `except ... conn.rollback()`.
- [ ] **Đóng kết nối**: Mọi khối kết nối CSDL phải có `finally: conn.close()` để tránh cạn kiệt tài nguyên (Connection Leak).
- [ ] **Sử dụng Parameterized Query**: 100% câu truy vấn phải dùng dấu `?` của SQLite, nghiêm cấm dùng f-string nối chuỗi biến người dùng vào SQL.

### 2.3. Bảo Mật & Kiểm Soát Phiên Làm Việc (Security & Sessions)
- [ ] **Bảo vệ Endpoint với RBAC**: Các route thao tác nhạy cảm bắt buộc có decorator `@require_auth(roles=['Admin'])` hoặc tương ứng.
- [ ] **Kiểm tra Session Token**: Mọi lời gọi API từ client đã đăng nhập đều phải được kiểm tra qua `AuthService.verify_token()`, bảo đảm `session_id` trong JWT khớp với `SessionToken` hiện hành trong CSDL.
- [ ] **Bảo mật mật khẩu**: Mật khẩu không bao giờ được trả về trong các payload phản hồi danh sách nhân viên hoặc danh sách tài khoản (phải loại bỏ trường `MatKhau` trước khi trả về client).

### 2.4. Xử Lý Ngoại Lệ & Mã Lỗi HTTP (Error Handling & Status Codes)
- [ ] Trả về mã lỗi HTTP có ý nghĩa:
  - `400 Bad Request`: Thiếu trường bắt buộc, sai định dạng ngày giờ, hoặc trùng lịch hẹn.
  - `401 Unauthorized`: Chưa đăng nhập, token hết hạn, hoặc bị đá văng do đăng nhập đồng thời (`CONCURRENT_LOGIN`).
  - `403 Forbidden`: Người dùng không có vai trò phù hợp (Ví dụ: Thợ cố tình xóa dịch vụ).
  - `404 Not Found`: Không tìm thấy bản ghi theo mã định danh.
  - `500 Internal Server Error`: Lỗi máy chủ không mong muốn (kèm log chi tiết ở backend, không lộ stack trace cho client).

### 2.5. Trải Nghiệm Giao Diện Người Dùng (UI / UX Polish)
- [ ] **Form nhập liệu**: Có nút toggle con mắt 👁️ xem mật khẩu trong các form đăng nhập, đổi mật khẩu và tạo tài khoản.
- [ ] **Trạng thái tải (Loading state)**: Các nút bấm gọi AI hoặc thanh toán có vô hiệu hóa (disabled) trong lúc chờ máy chủ phản hồi để tránh bấm đúp (double-click).
- [ ] **Thông báo trực quan**: Sử dụng toast notification hoặc modal rõ ràng, không dùng các hàm `alert()` mặc định thô sơ của trình duyệt.

---

## 3. Mẫu So Sánh Thực Tế: Code Tốt vs Code Xấu

### Ví dụ 1: Quản lý Transaction khi tạo Lịch Hẹn
❌ **CODE XẤU (Vi phạm: Không có rollback, route làm việc của Service)**:
```python
@api_bp.route("/booking", methods=["POST"])
def bad_booking():
    data = request.json
    conn = get_db_connection()
    # Viết SQL trực tiếp trong route, không có rollback khi lỗi ghi ChiTietLichHen
    conn.execute("INSERT INTO LichHen VALUES (?, ...)", (data['id'], ...))
    for dv in data['services']:
        conn.execute("INSERT INTO ChiTietLichHen VALUES (?, ...)", (data['id'], dv))
    conn.commit()
    return jsonify({"success": True})
```

✅ **CODE TỐT (Chuẩn Clean Architecture, có transaction an toàn)**:
```python
# Tại backend/routes/api.py:
@api_bp.route("/booking", methods=["POST"])
@require_auth(roles=["Admin", "LeTan"])
def good_booking():
    data = request.get_json() or {}
    result = BookingService.tao_lich_hen(data, user=get_auth_user())
    return jsonify(result), (200 if result.get("success") else 400)

# Tại backend/services/booking_service.py:
@classmethod
def tao_lich_hen(cls, data: dict, user: dict) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Kiểm tra chống trùng lịch thợ...
        # 2. Ghi LichHen...
        # 3. Ghi ChiTietLichHen...
        conn.commit()
        return {"success": True, "message": "Tạo lịch hẹn thành công!"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        conn.close()
```

---

## 4. Tiêu Chí Từ Chối Duyệt (Rejection Criteria)

Một bản cập nhật mã nguồn bắt buộc phải bị **TỪ CHỐI (REJECT)** nếu vi phạm bất kỳ điều nào sau đây:
1. Có câu lệnh SQL nối chuỗi biến ngoài dạng f-string (Nguy cơ SQL Injection).
2. Xóa hoặc sửa schema mà không kèm script migration hoặc làm gãy bộ unit test `tests/test_db_schema.py`.
3. Bỏ qua cơ chế kiểm tra `SessionToken`, cho phép 1 tài khoản đăng nhập tự do trên nhiều máy.
4. Hardcode API Key hoặc Secret Key trực tiếp vào mã nguồn thay vì đọc từ `.env`.

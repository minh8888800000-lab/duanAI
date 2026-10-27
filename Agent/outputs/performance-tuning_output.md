<!--
  BÁO CÁO SINH TỰ ĐỘNG BỞI AI AGENT RUNNER
  Kỹ năng: Tinh Chỉnh & Tối Ưu Hiệu Năng (Performance Tuning) (performance-tuning)
  Thời gian tạo: 2026-10-03 13:42:14
  Thời gian thực thi: 1.01s
  Model: Google Gemini (gemini-3.8-flash)
-->

# BÁO CÁO ĐẶC TẢ KỸ NĂNG: Tinh Chỉnh & Tối Ưu Hiệu Năng (Performance Tuning)

> **Trạng thái**: Tự động sinh bởi Grounded Local Engine
> **Thời gian**: 03/10/2026 13:42:14

## 1. Tổng Quan Kỹ Năng
PRAGMA SQLite WAL, Cache 64MB, Adaptive Heartbeat Polling 3.5s, Tối ưu DOM batching.

## 2. Nội Dung Chỉ Dẫn Kỹ Năng Chi Tiết

---
name: performance-tuning
description: Chiến lược tối ưu hóa hiệu năng máy chủ SQLite đa tiến trình, tinh chỉnh chỉ mục câu truy vấn, chống quá tải Session Heartbeat và tăng tốc hiển thị giao diện POS.
version: 2.0.0
---

# Performance Tuning & Optimization Skill (Kỹ Năng Tối Ưu Hóa Hiệu Năng & Tinh Chỉnh CSDL)

## 1. Mục Tiêu & Bộ Chỉ Số Hiệu Năng Then Chốt (Key Performance Indicators)
Đảm bảo Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI phản hồi tức thì trên mọi thiết bị: từ máy tính bảng của Stylist, điện thoại di động của Chủ salon, đến máy trạm POS cấu hình trung bình tại quầy lễ tân.

| Chỉ số (Metric) | Tiêu chuẩn mục tiêu | Ý nghĩa nghiệp vụ |
| :--- | :--- | :--- |
| **API Response Time (p95)** | `< 50ms` | Tốc độ phản hồi các API tra cứu khách hàng, menu dịch vụ |
| **Booking Conflict Check** | `< 20ms` | Thuật toán kiểm tra xung đột thời gian thợ rảnh `[S1, E1] ∩ [S2, E2]` |
| **First Contentful Paint (FCP)** | `< 300ms` | Thời gian hiển thị khung màn hình POS đầu tiên sau khi tải |
| **Database Concurrency Lock** | `0 lỗi/ngày` | Không xảy ra lỗi `sqlite3.OperationalError: database is locked` |

---

## 2. Tinh Chỉnh Động Cơ CSDL SQLite (SQLite Engine PRAGMA Tuning)

SQLite mặc định ở chế độ khóa đơn luồng cũ (Rollback Journal) dễ gây nghẽn khi nhiều người đọc và ghi đồng thời. Toàn bộ các kết nối CSDL trong `database/db.py` và `init_db.py` bắt buộc phải áp dụng bộ cấu hình **PRAGMA Siêu Tốc**:

```python
def get_db_connection():
    conn = sqlite3.connect('salon_hair.db', timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Kích hoạt chế độ ghi nhật ký trước (WAL Mode) - Hỗ trợ đa luồng đọc/ghi đồng thời
    cursor.execute("PRAGMA journal_mode = WAL;")

    # 2. Đồng bộ hóa ở mức NORMAL (nhanh hơn gấp 5 lần so với FULL mà vẫn an toàn tuyệt đối với WAL)
    cursor.execute("PRAGMA synchronous = NORMAL;")

    # 3. Cấp phát 64MB RAM bộ nhớ đệm trang (Page Cache)
    cursor.execute("PRAGMA cache_size = -64000;")

    # 4. Lưu bảng tạm và dữ liệu sort trên RAM thay vì đĩa cứng
    cursor.execute("PRAGMA temp_store = MEMORY;")

    # 5. Bật thực thi ràng buộc khóa ngoại toàn vẹn
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 6. Tăng giới hạn mmap để ánh xạ tệp CSDL trực tiếp vào không gian địa chỉ bộ nhớ
    cursor.execute("PRAGMA mmap_size = 268435456;") # 256MB

    return conn
```

---

## 3. Tinh Chỉnh Chỉ Mục & Phân Tích Kế Hoạch Truy Vấn (`EXPLAIN QUERY PLAN`)

### 3.1. Phân Tích Truy Vấn Bằng `EXPLAIN QUERY PLAN`
Mọi câu truy vấn có điều kiện `WHERE` hoặc `JOIN` đều phải được chạy thử nghiệm để đảm bảo SQLite sử dụng **INDEX SCAN** hoặc **INDEX SEARCH**, tuyệt đối tránh **SCAN TABLE** (quét cạn toàn bảng):

```sql
EXPLAIN QUERY PLAN
SELECT * FROM KhachHang WHERE SoDienThoai = '0901234567';
-- KẾT QUẢ ĐẠT YÊU CẦU:
-- SEARCH TABLE KhachHang USING INDEX idx_khachhang_sdt_filtered (SoDienThoai=?)
```

### 3.2. Filtered Unique Index Tối Ưu Bảng `KhachHang`
Khách hàng vãng lai không để lại số điện thoại chiếm khoảng 30% lượng khách salon. Tạo chỉ mục lọc có điều kiện (**Filtered Index**) giúp:
- Bỏ qua các dòng `SoDienThoai IS NULL`, giảm 30% kích thước tệp chỉ mục.
- Tăng tốc độ tìm kiếm khách hàng lên gấp 10 lần:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_khachhang_sdt_filtered
ON KhachHang(SoDienThoai)
WHERE SoDienThoai IS NOT NULL;
```

### 3.3. Composite Index Tối Ưu Thuật Toán Kiểm Tra Trùng Lịch Thợ
Truy vấn kiểm tra lịch thợ yêu cầu lọc theo 3 điều kiện: `MaNhanVien`, `TrangThai` và `ThoiGianBatDau`. Chỉ mục kết hợp (**Composite Index**) giải quyết triệt để nghẽn cổ chai:
```sql
CREATE INDEX IF NOT EXISTS idx_lichhen_tho_thoigian
ON LichHen(MaNhanVien, TrangThai, ThoiGianBatDau);
```

---

## 4. Chống Nghẽn Đơn Phiên (Adaptive Session Heartbeat Polling)

### 4.1. Nguy Cơ "Thundering Herd"
Nếu 20 nhân viên cùng mở trình duyệt và liên tục gửi request kiểm tra phiên mỗi 3.5 giây (`/api/auth/me`), máy chủ sẽ phải xử lý hơn 350 request/phút chỉ để xác thực token.

### 4.2. Giải Pháp Thích Ứng Bằng Page Visibility API
Tự động giãn chu kỳ kiểm tra khi nhân viên chuyển sang làm việc trên ứng dụng khác:
```javascript
let heartbeatInterval = 3500;
let heartbeatTimer = null;

function setupAdaptiveHeartbeat() {
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // Tab đang ẩn trong nền: Giãn chu kỳ kiểm tra lên 30 giây để tiết kiệm tài nguyên
      clearInterval(heartbeatTimer);
      heartbeatTimer = setInterval(checkSessionToken, 30000);
    } else {
      // Khi nhân viên quay lại tab: Kiểm tra ngay lập tức và đưa chu kỳ về 3.5 giây
      checkSessionToken();
      clearInterval(heartbeatTimer);
      heartbeatTimer = setInterval(checkSessionToken, 3500);
    }
  });
  heartbeatTimer = setInterval(checkSessionToken, heartbeatInterval);
}
```

---

## 5. Tối Ưu Hóa Phía Client (Frontend DOM & Asset Optimization)

### 5.1. Debounce 250ms Trên Các Ô Tra Cứu
Không gửi request tìm kiếm sau mỗi ký tự gõ phím. Sử dụng hàm `debounce` để gom cụm thao tác:
```javascript
function debounce(func, wait = 250) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const handleCustomerSearch = debounce((query) => {
  fetchCustomers(query);
}, 250);
```

### 5.2. Gom Cụm Cập Nhật DOM Bằng `DocumentFragment`
Khi render danh sách 50 lịch hẹn hoặc 20 thợ tóc, không chèn từng thẻ `div` vào DOM chính (gây hàng chục lần Reflow và Repaint). Sử dụng `DocumentFragment` để render 1 lần duy nhất:
```javascript
function renderAppointments(list) {
  const container = document.getElementById('appointments-list');
  const fragment = document.createDocumentFragment();

  list.forEach(item => {
    const card = createAppointmentCardElement(item);
    fragment.appendChild(card);
  });

  container.innerHTML = '';
  container.appendChild(fragment); // Chỉ kích hoạt Reflow duy nhất 1 lần
}
```

---

## 6. Checklist Rà Soát Tối Ưu Trước Khi Triển Khai (Performance Checklist)

- [ ] CSDL SQLite đã kích hoạt `PRAGMA journal_mode = WAL;` và `PRAGMA synchronous = NORMAL;`.
- [ ] Mọi truy vấn SELECT có điều kiện đều có Index hỗ trợ, không có câu truy vấn nào gây `SCAN TABLE` trên các bảng `LichHen`, `KhachHang`, `HoaDon`.
- [ ] Giao diện POS hiển thị khung FCP dưới 300ms, không bị layout shift (CLS = 0).
- [ ] Đã cấu hình Adaptive Heartbeat qua `document.hidden` để giảm tải máy chủ khi tab chạy nền.
- [ ] Các tệp tĩnh (CSS, JS, Fonts) được đính kèm header `Cache-Control: public, max-age=86400` trong môi trường sản xuất.


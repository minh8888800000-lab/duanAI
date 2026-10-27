# ✂️ Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI
> **Nền tảng Full-Stack hiện đại: Python (Flask / ASGI với Uvicorn), CSDL SQLite chuẩn 3NF, Giao diện Neo-Glassmorphism, kết nối Trí tuệ nhân tạo Google Gemini Cloud & Local Grounded Engine.**

---

## 📋 Mục Lục
1. [Giới Thiệu Dự Án](#-giới-thiệu-dự-án)
2. [Tính Năng Chính & Vị Trí AI](#-tính-năng-chính--vị-trí-tích-hợp-ai)
3. [Tài Khoản Đăng Nhập Mẫu](#-tài-khoản-đăng-nhập-mẫu)
4. [Chạy Bằng Docker (Khuyến Nghị)](#-chạy-bằng-docker-khuyến-nghị)
5. [Chạy Trực Tiếp Bằng Python](#-chạy-trực-tiếp-bằng-python-không-dùng-docker)
6. [Kiểm Thử Hệ Thống](#-kiểm-thử-hệ-thống)
7. [Cấu Trúc Thư Mục](#-cấu-trúc-thư-mục-dự-án)

---

## 🌟 Giới Thiệu Dự Án

Hệ thống quản lý đặt lịch và vận hành Salon tóc chuyên nghiệp được xây dựng theo mô hình **AI-Augmented SDLC**, tối ưu hóa toàn diện trải nghiệm tại quầy thu ngân và hỗ trợ quyết định nhanh cho thợ làm tóc:
- **Kiến trúc phân tầng sạch (Clean Layered Architecture)**: Routes (API Blueprint), Services (Nghiệp vụ), Models (Thực thể), Database (SQLite 3NF).
- **Trải nghiệm quầy thu ngân POS**: Tính tiền tự động, áp dụng giảm giá, in hóa đơn nhiệt chuẩn khổ 80mm/58mm.
- **Bảo mật phiên đăng nhập đơn (Single-Device Session)**: Tự động đăng xuất và thông báo tức thời khi tài khoản đăng nhập trên thiết bị thứ hai.
- **Động cơ AI 2 Tầng (Dual-Engine AI)**: Kết nối Google Gemini Cloud API và tự động dự phòng 100% sang Grounded Expert Engine nội bộ khi mất kết nối mạng (Zero-Downtime Fallback).

---

## 🤖 Tính Năng Chính & Vị Trí Tích Hợp AI

1. **Gợi ý combo dịch vụ cá nhân hóa (UC008)**: Phân tích chất tóc, da đầu và lịch sử làm đẹp của khách hàng để đưa ra gói liệu trình phục hồi tối ưu nhất.
2. **Soạn tin nhắn nhắc lịch hẹn tự động (UC009)**: Tự động tạo tin nhắn ngắn gọn, ấm áp qua Zalo/SMS gồm thời gian, tên Stylist và dịch vụ đã chọn.
3. **Tóm tắt hồ sơ khách hàng 5 giây cho Thợ (UC010)**: Trích xuất nhanh các lưu ý quan trọng (chất tóc tẩy, dị ứng hóa chất, công thức nhuộm cũ) trước khi thợ tiến hành làm tóc.
4. **Trợ lý AI Copilot & Tư vấn Trichology**: Giải đáp câu hỏi khoa học sợi tóc và hỗ trợ cập nhật danh mục giá dịch vụ bằng ngôn ngữ tự nhiên tiếng Việt (có rào chắn kiểm soát phân quyền RBAC chỉ dành cho Admin).

---

## 🔐 Tài Khoản Đăng Nhập Mẫu

Hệ thống đã chuẩn bị sẵn cơ sở dữ liệu với các tài khoản phân quyền theo vai trò (RBAC):

| Vai Trò (Role) | Tên Đăng Nhập | Mật Khẩu Mẫu | Quyền Hạn Trong Hệ Thống |
| :--- | :--- | :--- | :--- |
| **Quản trị viên (Admin)** | `admin` | `admin123` *(hoặc `12345`)* | Toàn quyền quản trị tài khoản, nhân viên, dịch vụ, báo cáo tài chính và cấu hình AI |
| **Lễ tân (LeTan)** | `letan01` | `letan123` | Quản lý khách hàng, đặt lịch hẹn, đổi thợ, thu ngân POS và xuất hóa đơn |
| **Lễ tân phụ** | `letan02` | `letan123` | Tiếp đón khách, tạo lịch hẹn, theo dõi trạng thái bàn ghế |
| **Thợ chính (Stylist)** | `tho01` | `tho123` | Xem lịch phục vụ cá nhân trong ngày, tóm tắt hồ sơ khách hàng 5s, bật/tắt trạng thái rảnh |
| **Thợ tóc 2** | `tho02` | `tho123` | Xem lịch làm việc được phân công |

---

## 🐳 Chạy Bằng Docker (Khuyến Nghị)

Ứng dụng được đóng gói hoàn chỉnh bằng **Docker** (ảnh Python 3.10-slim siêu nhẹ, chạy bằng máy chủ **Uvicorn ASGI**, chạy dưới quyền người dùng **non-root user** đảm bảo an toàn tuyệt đối) và điều phối qua **Docker Compose** với cơ chế lưu trữ dữ liệu bền vững (Persistent Volume).

### Bước 1: Sao chép tệp cấu hình môi trường
Mở Terminal/PowerShell tại thư mục gốc của dự án:
```bash
# Trên Windows PowerShell:
Copy-Item .env.example .env

# Trên Linux / macOS:
cp .env.example .env
```

### Bước 2: Điền khóa cấu hình vào tệp `.env`
Mở tệp `.env` vừa tạo và điền khóa Google Gemini API của bạn:
```env
PORT=5000
SECRET_KEY=salon_hair_ai_secret_key_2026_super_secure
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-flash-lite-latest
```
*(Nếu chưa có API Key, hệ thống sẽ tự động kích hoạt Động cơ AI nội bộ Grounded SQLite đảm bảo 100% tính năng vẫn chạy bình thường).*

### Bước 3: Khởi chạy ứng dụng với Docker Compose
```bash
docker compose up --build -d
```
Quá trình build sẽ tự động:
- Cài đặt các thư viện trong `requirements.txt` (Flask, Uvicorn, a2wsgi, PyJWT, Requests, Google Generative AI).
- Tạo người dùng an toàn `appuser` (non-root).
- Tự động khởi tạo cấu trúc CSDL 8 bảng và nạp dữ liệu mẫu vào volume bền vững `salon_hair_db_volume`.

### Bước 4: Kiểm tra trạng thái và truy cập ứng dụng
- **Giao diện Web chính**: Mở trình duyệt truy cập: [http://localhost:5000](http://localhost:5000)
- **Đường dẫn kiểm tra sức khỏe (Healthcheck)**: [http://localhost:5000/health](http://localhost:5000/health)
- **Xem nhật ký hoạt động (Logs)**:
  ```bash
  docker compose logs -f
  ```

### Bước 5: Cách dừng và xóa container
- **Dừng dịch vụ (Giữ lại dữ liệu CSDL)**:
  ```bash
  docker compose down
  ```
- **Dừng dịch vụ và xóa sạch volume dữ liệu (Reset hoàn toàn)**:
  ```bash
  docker compose down -v
  ```

---

## 💻 Chạy Trực Tiếp Bằng Python (Không Dùng Docker)

### 1. Yêu cầu môi trường
- Python 3.8+ (khuyến nghị Python 3.10 hoặc 3.11).
- Trình duyệt Chrome / Edge / Firefox.

### 2. Cài đặt các thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### 3. Thiết lập biến môi trường
```bash
Copy-Item .env.example .env
```

### 4. Khởi chạy máy chủ
Có thể khởi chạy bằng 1 trong 2 cách:

- **Cách 1: Khởi chạy bằng Uvicorn ASGI Server (Chuẩn Production)**:
  ```bash
  uvicorn app:asgi_app --host 127.0.0.1 --port 5000 --reload
  ```

- **Cách 2: Khởi chạy trực tiếp bằng Python Script**:
  ```bash
  python app.py
  ```

Truy cập hệ thống tại: `http://127.0.0.1:5000`

---

## 🧪 Kiểm Thử Hệ Thống (Testing)

Chạy bộ kiểm thử tự động toàn diện:
```bash
# 1. Kiểm thử cấu trúc và 4 cấp độ ràng buộc toàn vẹn CSDL SQLite
python -m unittest tests/test_db_schema.py

# 2. Kiểm thử tích hợp các luồng Endpoints Web & API
python -m unittest tests/test_web_integration.py
```

---

## 📂 Cấu Trúc Thư Mục Dự Án

```
├── Dockerfile                  # Cấu hình đóng gói ảnh Docker (Python 3.10-slim, non-root, Uvicorn)
├── docker-compose.yml          # Cấu hình Docker Compose (Dịch vụ Web + SQLite Persistent Volume)
├── .dockerignore               # Danh sách loại trừ khi đóng gói container
├── .gitignore                  # Danh sách loại trừ khi commit lên Git
├── .env.example                # Bản mẫu biến môi trường bảo mật
├── requirements.txt            # Danh sách thư viện Python cần thiết
├── app.py                      # Điểm vào chính của ứng dụng (Flask + ASGI bridge)
├── README.md                   # Tài liệu hướng dẫn sử dụng và triển khai
├── SDLC_ARTIFACTS.md           # Báo cáo tổng hợp bằng chứng vòng đời phát triển AI-Augmented SDLC
├── backend/
│   ├── config.py               # Quản lý cấu hình biến môi trường
│   ├── db.py                   # Quản lý kết nối SQLite và Context Manager
│   ├── models/
│   │   └── entities.py         # 8 Class thực thể nghiệp vụ chuẩn Class Diagram
│   ├── routes/
│   │   └── api.py              # 25+ Endpoints RESTful API & phân quyền JWT
│   └── services/
│       ├── auth_service.py     # Đăng nhập, JWT, Single-Device Session
│       ├── booking_service.py  # Đặt lịch hẹn, phát hiện xung đột lịch thợ
│       ├── billing_service.py  # Thu ngân POS, tính tiền, hóa đơn
│       ├── report_service.py   # Báo cáo doanh thu và chỉ số KPI
│       └── tro_ly_ai.py        # Động cơ Trợ lý AI 2 tầng & Grounding CSDL
├── database/
│   ├── schema.sql              # Cấu trúc 8 bảng chuẩn 3NF và khóa ngoại
│   ├── seed.sql                # Dữ liệu mẫu chuẩn nghiệp vụ ban đầu
│   └── init_db.py              # Script tự động khởi tạo CSDL SQLite
├── static/
│   ├── css/styles.css          # Giao diện Neo-Glassmorphism hiện đại
│   └── js/app.js               # Logic tương tác SPA, POS, Socket và AI
├── templates/
│   └── index.html              # Màn hình điều khiển chính (Dashboard, POS, Booking, AI)
└── tests/                      # Bộ kiểm thử tự động (Unit test, Integration test, E2E)
```

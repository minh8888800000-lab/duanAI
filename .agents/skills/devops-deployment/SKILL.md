---
name: devops-deployment
description: Quy trình đóng gói phần mềm, triển khai máy chủ sản xuất WSGI trên Windows/Linux, container hóa Docker, sao lưu phục hồi SQLite tự động và CI/CD.
version: 2.0.0
---

# DevOps & Deployment Skill (Kỹ Năng Triển Khai Vận Hành, Đóng Gói & CI/CD)

## 1. Mục Tiêu & Tiêu Chuẩn Sẵn Sàng Vận Hành (Production Readiness)
Đảm bảo Hệ Thống Quản Lý Đặt Lịch Salon Tóc Tích Hợp AI hoạt động ổn định 24/7 tại các chi nhánh salon, tự động khởi động cùng hệ điều hành, bảo vệ toàn vẹn tệp CSDL SQLite trước các sự cố mất điện đột ngột hoặc xung đột ghi dữ liệu, và tự động hóa quy trình kiểm thử trước khi release phiên bản mới.

---

## 2. Triển Khai Máy Chủ Sản Xuất (Production WSGI Server)

### 2.1. Cấu Hình Waitress WSGI Trên Máy Trạm Windows POS
Tuyệt đối không dùng máy chủ tích hợp của Flask (`app.run(debug=True)`) trong môi trường vận hành thực tế vì rủi ro rò rỉ socket và tiến trình con kép.

Cài đặt và khởi chạy với **Waitress** (Production-grade WSGI Server tối ưu cho Windows):
```bash
pip install waitress
```

Tạo tệp khởi chạy sản xuất `wsgi.py`:
```python
import os
import sys
from waitress import serve
from app import app

# Đảm bảo mã hóa UTF-8 trên Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    threads = int(os.environ.get('WEB_CONCURRENCY', 4))
    print(f"🚀 Hair Salon Management System đang chạy trên Waitress WSGI: http://0.0.0.0:{port}")
    serve(app, host='0.0.0.0', port=port, threads=threads)
```

### 2.2. Chạy Ẩn Như Một Windows Service Với NSSM (Non-Sucking Service Manager)
Để máy chủ tự động khởi động khi bật máy tính salon và tự phục hồi nếu có lỗi:
```powershell
# 1. Cài đặt NSSM hoặc tải binary nssm.exe
nssm install HairSalonPOS "d:\hay\venv\Scripts\python.exe" "d:\hay\wsgi.py"
nssm set HairSalonPOS AppDirectory "d:\hay"
nssm set HairSalonPOS AppStdout "d:\hay\logs\service_out.log"
nssm set HairSalonPOS AppStderr "d:\hay\logs\service_err.log"
nssm set HairSalonPOS Start SERVICE_AUTO_START

# 2. Khởi động dịch vụ
nssm start HairSalonPOS
```

---

## 3. Đóng Gói Container Hóa Với Docker & Docker Compose

### 3.1. Tệp `Dockerfile` Tối Ưu Hóa & Bảo Mật
```dockerfile
# Sử dụng Python Slim để giảm dung lượng image
FROM python:3.11-slim

# Thiết lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PORT=5000

WORKDIR /app

# Cài đặt thư viện hệ thống cần thiết cho SQLite và build
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt waitress

# Copy toàn bộ mã nguồn
COPY . .

# Tạo thư mục cho cơ sở dữ liệu và phân quyền an toàn
RUN mkdir -p /app/data /app/logs && \
    useradd -u 8888 salonapp && \
    chown -R salonapp:salonapp /app

USER salonapp

EXPOSE 5000

# Health check định kỳ
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "wsgi.py"]
```

### 3.2. Tệp `docker-compose.yml`
```yaml
version: '3.8'

services:
  salon-web:
    build: .
    container_name: hair_salon_app
    restart: always
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DATABASE_PATH=/app/data/salon_hair.db
    volumes:
      - salon_data:/app/data
      - ./logs:/app/logs

volumes:
  salon_data:
    driver: local
```

---

## 4. Chiến Lược Sao Lưu & Phục Hồi CSDL SQLite (Disaster Recovery)

### 4.1. Kịch Bản Sao Lưu Trực Tuyến Tự Động (`backup_db.py`)
Sử dụng SQLite Online Backup API (`conn.backup()`) để tạo bản snapshot an toàn mà không cần ngắt kết nối máy chủ hoặc khóa bảng ghi:

```python
import sqlite3
import os
import shutil
from datetime import datetime

DB_SOURCE = os.path.join(os.path.dirname(__file__), 'salon_hair.db')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')

def run_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'salon_hair_backup_{timestamp}.db')

    print(f"🔄 Đang tạo bản sao lưu trực tuyến: {backup_file}...")
    src_conn = sqlite3.connect(DB_SOURCE)
    dst_conn = sqlite3.connect(backup_file)

    with dst_conn:
        src_conn.backup(dst_conn, pages=100, sleep=0.01)

    dst_conn.close()
    src_conn.close()

    # Kiểm tra toàn vẹn bản sao lưu
    verify_conn = sqlite3.connect(backup_file)
    integrity = verify_conn.execute("PRAGMA integrity_check;").fetchone()[0]
    verify_conn.close()

    if integrity == "ok":
        print(f"✅ Sao lưu thành công! Tính toàn vẹn: {integrity}")
        # Giữ lại tối đa 30 bản sao lưu gần nhất
        _cleanup_old_backups(limit=30)
    else:
        raise RuntimeError(f"❌ Bản sao lưu bị lỗi cấu trúc: {integrity}")

def _cleanup_old_backups(limit=30):
    files = [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
    files.sort(key=os.path.getmtime)
    while len(files) > limit:
        oldest = files.pop(0)
        os.remove(oldest)
        print(f"🧹 Đã xóa bản sao lưu cũ: {oldest}")

if __name__ == '__main__':
    run_backup()
```

### 4.2. Kích Hoạt Chế Độ Ghi WAL (Write-Ahead Logging)
Trong mọi script kết nối CSDL, luôn kích hoạt WAL để hỗ trợ đọc đồng thời mà không bị nghẽn:
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
```

---

## 5. Đường Ống CI/CD Tự Động (GitHub Actions Workflow)

Tệp `.github/workflows/ci-cd.yml` đảm bảo mọi PR và commit lên nhánh `main` đều vượt qua toàn bộ 46 tests trước khi cho phép triển khai:

```yaml
name: CI/CD Hair Salon Pipeline

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main ]

jobs:
  test-and-quality:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout mã nguồn
        uses: actions/checkout@v4

      - name: Thiết lập môi trường Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Cài đặt dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt flake8 bandit

      - name: Kiểm tra cú pháp & Linting
        run: |
          # Dừng nếu có lỗi cú pháp Python
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Khởi tạo CSDL SQLite mẫu
        run: |
          python database/init_db.py

      - name: Chạy toàn bộ 46 Unit & Integration Tests
        run: |
          python -m unittest discover tests -v

      - name: Quét lỗ hổng an ninh mã nguồn với Bandit
        run: |
          bandit -r backend/ -ll -ii
```

---

## 6. Nhật Ký Hệ Thống & Giám Sát (Logging Runbook)
- Cấu hình tệp nhật ký tự động xoay vòng với `RotatingFileHandler` (kích thước tối đa 5MB/file, giữ lại 5 files xoay vòng):
```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    handler = RotatingFileHandler('logs/salon_app.log', maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s (%(funcName)s:%(lineno)d): %(message)s'
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
```

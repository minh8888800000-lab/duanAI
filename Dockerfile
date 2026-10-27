# ====================================================================
# DOCKERFILE - HỆ THỐNG QUẢN LÝ SALON TÓC TÍCH HỢP AI
# Base image: Python 3.10 Slim (Bản nhẹ, tối ưu bảo mật và kích thước)
# Server: Uvicorn ASGI Server (Chạy ứng dụng bằng non-root user)
# ====================================================================

FROM python:3.10-slim

# Thiết lập biến môi trường chuẩn của Python và hệ thống
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=5000

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các gói hệ thống cần thiết (curl dùng cho container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tạo nhóm và người dùng không có quyền quản trị (Non-root user)
# Tuân thủ nguyên tắc Least Privilege trong an toàn thông tin
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 --no-create-home appuser

# Sao chép và cài đặt các gói phụ thuộc Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn ứng dụng vào container
COPY . .

# Tạo thư mục lưu trữ cơ sở dữ liệu SQLite và phân quyền cho người dùng non-root
RUN mkdir -p /app/database && \
    chown -R appuser:appgroup /app && \
    chmod -R 775 /app/database

# Chuyển quyền thực thi sang người dùng không phải quản trị
USER appuser

# Mở cổng dịch vụ 5000
EXPOSE 5000

# Khởi chạy ứng dụng bằng máy chủ Uvicorn (kết nối ASGI qua app:asgi_app)
CMD ["uvicorn", "app:asgi_app", "--host", "0.0.0.0", "--port", "5000"]

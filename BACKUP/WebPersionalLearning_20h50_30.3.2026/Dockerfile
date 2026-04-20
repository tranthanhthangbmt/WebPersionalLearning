# Sử dụng Python 3.10 Slim cho nhẹ
FROM python:3.10-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (để cài PyTorch, Numpy)
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt PyTorch bản CPU siêu nhẹ để tiết kiệm >5GB ổ đĩa và RAM.
# Phù hợp chạy 1 worker đơn giản trên VPS
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn (.dockerignore sẽ chặn file nặng)
COPY . .

# Mở port 8081 (vì code main.py của bạn đang chạy ở 8081)
EXPOSE 8081

# Biến môi trường
ENV PYTHONUNBUFFERED=1

# Lệnh chạy ứng dụng đơn tiến trình (cách này nhẹ giống hệt cách bạn chạy trên VS Code)
CMD ["python", "main.py"]

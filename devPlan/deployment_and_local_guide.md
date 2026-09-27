# Hướng Dẫn Chạy Trang Web Ở Local Và Đưa Lên Google Cloud

## 1. Hướng Dẫn Chạy Trang Web Ở Local
Để chạy trang web ở local (trên máy tính cá nhân), bạn có hai cách dựa trên cấu hình dự án:

### Cách 1: Sử dụng file chạy tự động (Nhanh nhất)
Bạn đã có sẵn file `run_server.bat` được cấu hình để tự động kích hoạt môi trường ảo và chạy server.
1. Mở thư mục dự án trong File Explorer.
2. Click đúp chuột vào file `run_server.bat`.
3. Một cửa sổ Command Prompt sẽ hiện lên và tự động khởi động server.
Hoặc mở Terminal tại thư mục dự án và chạy:
```powershell
.\run_server.bat
```

### Cách 2: Chạy thủ công từng bước qua Terminal
1. Mở Terminal tại thư mục dự án.
2. Kích hoạt môi trường ảo:
```powershell
.\.venv\Scripts\activate
```
3. Chạy server:
```powershell
.\.venv\Scripts\python.exe main.py
```
Sau đó truy cập đường link (ví dụ: `http://localhost:8080`) trên trình duyệt web.

> **Lưu ý quan trọng**: Việc đổi tên hoặc di chuyển thư mục chứa dự án (ví dụ từ ổ D sang ổ I) có thể làm hỏng biến môi trường trong file kích hoạt của `.venv`. File `run_server.bat` đã được cấu hình lại sử dụng đường dẫn tương đối để giải quyết vấn đề này.

---

## 2. Hướng Dẫn Đưa Trang Web Lên Google Cloud (Bản Miễn Phí)
Cách tốt nhất, miễn phí và hiện đại nhất để đưa trang web có sẵn `Dockerfile` này lên Google Cloud là sử dụng **Google Cloud Run**.
Cloud Run cung cấp gói miễn phí hàng tháng (Free Tier) rất rộng rãi và tự động cấp sẵn chứng chỉ bảo mật `https://`.

### Bước 1: Chuẩn bị tài khoản và dự án
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/) và đăng nhập bằng tài khoản Google.
2. Tạo một **Project mới** (ví dụ: `web-personal-learning`) và lưu lại ID của Project.

### Bước 2: Cài đặt công cụ Google Cloud CLI
1. Tải và cài đặt Google Cloud CLI tại đây: [Tải GCloud CLI cho Windows](https://cloud.google.com/sdk/docs/install#windows)
2. Mở Terminal trên máy tính và chạy lệnh đăng nhập:
```powershell
gcloud auth login
```
3. Kết nối Terminal với Project vừa tạo:
```powershell
gcloud config set project PROJECT_ID
```

### Bước 3: Đưa trang web lên Cloud (Deploy)
Do dự án dùng PyTorch và AI, cần cấp tối thiểu 2GB RAM. Web đang chạy ở port 8081 trong Dockerfile.
Mở Terminal tại thư mục code và chạy lệnh:
```powershell
gcloud run deploy web-app --source . --port 8081 --memory 2Gi --region us-central1 --allow-unauthenticated
```
- `--source .`: Đóng gói code tại thư mục hiện tại dựa trên `Dockerfile`.
- `--memory 2Gi`: Cấp 2GB RAM.
- `--region us-central1`: Chọn máy chủ vùng US (thuộc gói miễn phí).

### Bước 4: Chờ đợi và nhận kết quả
- Chấp nhận bật các API cần thiết nếu được hỏi (nhập `y`).
- Quá trình sẽ mất khoảng 10-20 phút để cài đặt thư viện và đóng gói.
- Sau khi hoàn tất, Terminal sẽ trả về một đường link HTTPS màu xanh lá. Mọi người có thể truy cập vào đường link này.

> 💡 **Lưu ý về Biến môi trường**: Nếu web cần API keys hoặc file `.env`, Cloud Run sẽ không tải file `.env` lên. Bạn cần cấu hình trên giao diện web Console của Cloud Run bằng cách chọn `Edit & Deploy New Revision` -> Tab `Variables & Secrets`.

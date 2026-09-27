# Hướng dẫn kết nối lại AWS và sửa lỗi 521 Web server is down

Lỗi "521 Web server is down" thường xảy ra khi WebApp bên trong máy chủ AWS bị crash (dừng hoạt động), hoặc do máy chủ bị khởi động lại mà Docker chưa chạy lên, hoặc do thiếu file cấu hình (như API Key).

## 1. Lệnh SSH để đăng nhập vào AWS
Hãy mở một cửa sổ Terminal/PowerShell mới trong VS Code và dán lệnh sau vào (nhấn Enter):

```powershell
ssh -i "i:\MY_CODE\WebPersionalLearning\BACKUP\AWS\aws-tree-key.pem" ubuntu@56.10.131.44
```
*(Ghi chú: Nếu IP `56.10.131.44` bị đổi do AWS reset, hãy vào giao diện AWS EC2 copy lại **IPv4 Public address** và thay vào dòng trên).*

Trường hợp file `.pem` trên không đúng, hãy thử file dự phòng này:
```powershell
ssh -i "i:\MY_CODE\WebPersionalLearning\AWS key\my-key1.pem" ubuntu@56.10.131.44
```

## 2. Cách cập nhật API Key mới (Khắc phục lỗi Crash do thiếu Key)
Vừa nãy bạn đã đẩy code lên Github nhưng bỏ qua thư mục `GeminiKey` (để bảo mật). Do đó trên AWS bị mất file này, dẫn tới WebApp crash ngay khi vừa khởi động.

Sau khi đã SSH thành công vào máy chủ AWS, hãy chạy các lệnh sau để nạp Key thủ công:

```bash
# Vào thư mục chứa dự án
cd WebPersionalLearning

# Tạo thư mục GeminiKey (nếu chưa có)
mkdir -p GeminiKey

# Chèn Key mới nhất (AQ.Ab8...) vào file geminiKey.txt
echo "YOUR_GEMINI_API_KEY_HERE" > GeminiKey/geminiKey.txt
```

## 3. Khởi động lại Docker
Sau khi đã nạp đủ file Key, bạn khởi động lại hệ thống bằng 2 lệnh sau:

```bash
# Xóa toàn bộ container cũ đang bị lỗi
sudo docker rm -f $(sudo docker ps -aq)

# Chạy lại container mới ở cổng 80 (chuyển tiếp vào 8081 bên trong)
sudo docker run -d --restart unless-stopped -p 80:8081 my-web-app
```

**Cách kiểm tra:**
Chạy lệnh `sudo docker ps`. Nếu thấy trạng thái `Up X seconds`, nghĩa là app đã sống. Quay lại web F5 là xong!

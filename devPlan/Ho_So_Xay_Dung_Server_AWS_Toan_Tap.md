# HỒ SƠ XÂY DỰNG SERVER AWS VÀ DEPLOY WEB APP (Toàn tập)

Tài liệu này tổng hợp toàn bộ các bước, vấn đề đã gặp phải và cách giải quyết trong quá trình đưa WebApp lên AWS EC2, thiết lập HTTPS và xử lý lỗi liên quan đến API Key mà chúng ta đã làm việc cùng nhau.

## 1. Kết nối vào Server AWS EC2
Để quản trị server AWS, bạn cần kết nối SSH từ máy tính cá nhân.
- **IP Public của Server**: `56.10.131.44` (hoặc IP hiện tại trên giao diện AWS EC2 Console).
- **File Khóa bảo mật (Key PEM)**: 
  - `i:\MY_CODE\WebPersionalLearning\AWS key\my-key1.pem`
  - *(hoặc)* `i:\MY_CODE\WebPersionalLearning\BACKUP\AWS\aws-tree-key.pem`
- **Câu lệnh kết nối (Chạy trên Terminal/PowerShell của máy cá nhân)**:
  ```powershell
  ssh -i "AWS key/my-key1.pem" ubuntu@56.10.131.44
  ```

## 2. Quy trình Cập nhật Code và Deploy bằng Docker
Mỗi khi bạn code xong một tính năng mới trên máy cá nhân, đây là quy trình chuẩn để cập nhật lên web:
1. Đẩy code lên Github từ máy tính: `git add .`, `git commit -m "update..."`, `git push`.
2. Vào server AWS kéo code mới: `git pull`.
3. Xóa Docker cũ và Build lại Docker mới (Chạy trên AWS):
   ```bash
   sudo docker rm -f $(sudo docker ps -aq)
   sudo docker build -t my-web-app .
   sudo docker run -d --restart unless-stopped -p 80:8081 my-web-app
   ```
*(Lưu ý: App chạy ở port 8081 bên trong Docker, và map ra port 80 bên ngoài máy chủ AWS để trình duyệt web có thể đọc được).*

## 3. Các Vấn đề Đã Xử Lý & Bài Học Kinh Nghiệm

### Lỗi 1: Đồng bộ thiếu dữ liệu khóa học (`DB/public_trees/`)
- **Trạng thái**: Website online hiển thị trống trơn, không có khóa học nào dù ở Local vẫn có.
- **Nguyên nhân**: File `.gitignore` mặc định đang bỏ qua (ignore) toàn bộ thư mục `DB/` khiến các biểu đồ khóa học không được đưa lên Github. 
- **Cách khắc phục**: Mình đã thêm ngoại lệ vào file `.gitignore` (cụm từ `!DB/public_trees/`) để ép Github phải lưu thư mục chứa cấu trúc khóa học. 

### Lỗi 2: Cài đặt HTTPS miễn phí (Khóa bảo mật SSL)
- **Trạng thái**: Người dùng phàn nàn muốn trang web chạy 100% trên giao thức an toàn `https://`.
- **Vấn đề**: AWS EC2 mặc định chỉ chạy HTTP (Port 80) không bảo mật, và cài SSL trên máy chủ rất phức tạp.
- **Cách giải quyết**: Đã thiết lập qua **Cloudflare**.
  - Đổi Nameserver của GoDaddy sang Nameserver của Cloudflare.
  - Trên Cloudflare: Bật tính năng **Flexible SSL** (cho phép Cloudflare mã hóa HTTPS cho khách hàng và kết nối ngầm HTTP về AWS) và bật **Always Use HTTPS** (Tự động chuyển hướng khách hàng sang link bảo mật).

### Lỗi 3: Lỗi Google Gemini API Key và Định dạng mới
- **Trạng thái**: Chức năng chat AI bị liệt.
- **Nguyên nhân**: 
  - Toàn bộ 31 API Keys cũ bị dính lỗi cạn kiệt dung lượng (Lỗi 429 - Quota Exceeded) hoặc báo lỗi 403, 404.
  - Google đã **khai tử** model `gemini-1.5-flash` và **thay đổi định dạng** của API Key. Mã key không còn bắt đầu bằng `AIzaSy...` mà chuyển sang định dạng mới bắt đầu bằng `AQ.Ab8...`.
- **Cách giải quyết**: 
  - Bạn đã tạo thành công 1 API Key mới toanh định dạng `AQ.Ab8...`
  - Đã chuyển model trong code `gemini_helper.py` sang dùng `gemini-3.5-flash-lite`.
  - Đã đưa thư mục `/GeminiKey/` vào file `.gitignore` để Github Security không chặn (Push Protection) khi đẩy code lên mạng.

### Lỗi 4: Web Server is Down (Lỗi sập mạng 521 Cloudflare)
- **Trạng thái**: Vào trang web hiển thị lỗi 521 từ Cloudflare.
- **Nguyên nhân**: Do mình đã chặn Github đẩy thư mục `GeminiKey` lên mạng (vì bảo mật), nên khi AWS `git pull` code về, nó KHÔNG có file key này. App Python vừa khởi động lên bị thiếu "chìa khóa" nên Crash (đóng băng) ngay lập tức. Cổng mạng sập dẫn tới lỗi 521.
- **Cách khắc phục**: Phải vào AWS tự tạo lại file Key bằng tay (Chỉ cần làm 1 lần), sau đó chạy lại Docker:
  ```bash
  # 1. Tạo thư mục và chép Key vào
  mkdir -p GeminiKey
  echo "YOUR_GEMINI_API_KEY_HERE" > GeminiKey/geminiKey.txt
  
  # 2. Xóa các container lỗi và chạy lại web
  sudo docker rm -f $(sudo docker ps -aq)
  sudo docker run -d --restart unless-stopped -p 80:8081 my-web-app
  ```

---
*Hồ sơ này được lập vào ngày 27/09/2026 bởi Antigravity AI. Hãy mở lại tài liệu này bất cứ khi nào bạn cần nâng cấp hay cài đặt lại một máy chủ AWS mới.*

# Hướng Dẫn Tạo Tài Khoản và Đưa Trang Web Lên AWS (Amazon Web Services)

> ⚠️ **Lưu ý cực kỳ quan trọng trước khi bắt đầu:** 
> Giống y hệt như Google Cloud, **Amazon Web Services (AWS) cũng BẮT BUỘC bạn phải nhập thẻ Visa/Mastercard** để xác minh danh tính khi tạo tài khoản. Họ cũng sẽ trừ thử 1$ (và hoàn lại sau đó). 

Dưới đây là hướng dẫn từ A-Z cách tạo tài khoản AWS và đưa trang web (bằng Docker) lên máy chủ ảo (EC2) hoàn toàn miễn phí trong 1 năm đầu.

---

## Phần 1: Tạo tài khoản AWS
1. Truy cập trang chủ AWS: [https://aws.amazon.com/vi/free/](https://aws.amazon.com/vi/free/) và nhấn **"Tạo tài khoản miễn phí"**.
2. Điền email và mật khẩu.
3. Điền thông tin cá nhân (Tên, địa chỉ, số điện thoại...). Điền tiếng Việt không dấu.
4. **Nhập thông tin thẻ Visa/Mastercard** của bạn. 
5. Xác minh số điện thoại bằng tin nhắn SMS.
6. Chọn gói **Basic Support (Miễn phí)**.
7. Đăng nhập vào giao diện chính AWS Management Console.

---

## Phần 2: Khởi tạo máy chủ ảo (EC2) miễn phí
Vì code dùng AI (PyTorch), máy chủ AWS miễn phí (gói t2.micro chỉ có 1GB RAM) có thể sẽ hơi yếu và dễ bị quá tải RAM, nhưng vẫn có thể chạy thử.

1. Tại thanh tìm kiếm trên cùng của giao diện AWS, gõ **EC2** và click vào đó.
2. Ở góc trên cùng bên phải, đổi khu vực (Region) sang **Singapore (ap-southeast-1)** để tốc độ mạng về Việt Nam nhanh nhất.
3. Nhấn nút màu cam **Launch Instance** (Tạo máy chủ).
4. **Thiết lập máy chủ:**
   - **Name:** Đặt tên tuỳ ý (ví dụ: `my-web-server`).
   - **OS Images (Hệ điều hành):** Chọn **Ubuntu** (lưu ý phải có chữ *Free tier eligible* bên dưới).
   - **Instance Type:** Chọn **t2.micro** (*Free tier eligible*).
   - **Key pair (Đăng nhập):** Nhấn *Create new key pair* -> Đặt tên là `my-key` -> Định dạng `.pem` -> Nhấn *Create*. **(Quan trọng: Trình duyệt sẽ tải về 1 file `.pem`, hãy cất kỹ file này).**
5. **Network settings (Mạng):** 
   - Đánh dấu tick vào cả 3 ô: **Allow SSH**, **Allow HTTPS**, **Allow HTTP** để mọi người có thể vào được web.
6. **Storage (Ổ cứng):** Sửa số `8` thành `30` (AWS cho phép tối đa 30GB ổ cứng miễn phí).
7. Nhấn **Launch instance** ở góc dưới bên phải để bắt đầu tạo.

---

## Phần 3: Kết nối vào máy chủ và chạy Web
Khi máy chủ hiện trạng thái *Running*, click vào mã ID của máy chủ để xem thông tin. Copy địa chỉ **Public IPv4 address** (đây là IP trang web của bạn).

### Bước 3.1: Đưa code lên máy chủ (thông qua Github)
1. Ở máy tính của bạn, đẩy toàn bộ thư mục dự án lên một kho chứa (Repository) trên Github.

### Bước 3.2: Truy cập vào Server và chạy Docker
1. Mở Terminal (PowerShell) trên máy tính, trỏ tới thư mục chứa file `.pem` vừa tải về. Gõ lệnh:
   ```powershell
   ssh -i "my-key.pem" ubuntu@<ĐỊA_CHỈ_IP_CỦA_BẠN>
   ```
   *(Gõ `yes` nếu được hỏi).*
2. Khi đã vào được server, tiến hành cài đặt Docker:
   ```bash
   sudo apt update
   sudo apt install docker.io -y
   ```
3. Kéo code của bạn từ Github về máy chủ:
   ```bash
   git clone <LINK_GITHUB_CỦA_BẠN>
   cd <TÊN_THƯ_MỤC_VỪA_KÉO_VỀ>
   ```
4. Dùng Docker để đóng gói và chạy server:
   ```bash
   sudo docker build -t my-web-app .
   sudo docker run -d -p 80:8081 my-web-app
   ```
   *(Lệnh này giúp chuyển port 8081 từ code của bạn ra port 80 mặc định của website).*

Mở trình duyệt lên, dán địa chỉ IP máy chủ vào là trang web sẽ chạy.

> **Lưu ý**: Vì máy chủ t2.micro chỉ có 1GB RAM, lúc chạy lệnh build Docker cài PyTorch máy chủ có thể bị đơ. Nếu bị lỗi Out of Memory, bạn sẽ cần cấu hình tạo thêm RAM ảo (Swap) trên Server.

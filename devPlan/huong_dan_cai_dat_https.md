# Hướng dẫn thiết lập HTTPS (Ổ khoá xanh) miễn phí với Cloudflare

Vì máy chủ AWS EC2 hiện tại chỉ phục vụ web ở cổng 80 (HTTP), cách tối ưu và nhanh nhất để có HTTPS mà không phải đụng chạm mã code hay cấu hình máy chủ là sử dụng **Cloudflare**. 
Cloudflare sẽ làm trung gian: Nó cung cấp chứng chỉ bảo mật HTTPS cho người dùng truy cập, sau đó ngầm lấy dữ liệu từ máy chủ AWS của bạn qua HTTP.

Dưới đây là các bước chi tiết:

## Bước 1: Tạo tài khoản và Thêm tên miền vào Cloudflare
1. Truy cập vào trang chủ [Cloudflare](https://dash.cloudflare.com/sign-up) và tạo một tài khoản miễn phí (chỉ cần nhập Email và Mật khẩu).
2. Sau khi đăng nhập, nhấn nút **Add a Site** (Thêm trang web) ở góc phải.
3. Nhập tên miền của bạn: `treeknowledge.online` rồi nhấn **Continue**.
4. Cloudflare sẽ hỏi bạn chọn gói cước (Plan). Kéo xuống dưới cùng, chọn gói **Free (Miễn phí)** có giá $0, rồi nhấn **Continue**.

## Bước 2: Kiểm tra bản ghi DNS
1. Cloudflare sẽ tự động quét các cấu hình DNS cũ của bạn ở GoDaddy (ví dụ bản ghi IP trỏ về AWS `56.10.131.44` mà bạn vừa làm).
2. Bạn chỉ cần lướt qua xem đã có dòng `A` trỏ về IP của máy chủ chưa. Nếu có rồi, cứ cuộn xuống cuối cùng và nhấn **Continue**.

## Bước 3: Đổi Nameserver ở GoDaddy (Quan trọng nhất)
Cloudflare sẽ hiện ra một bảng yêu cầu bạn xoá Nameserver cũ và thay bằng **2 Nameserver của Cloudflare** (trông giống như thế này: `luke.ns.cloudflare.com` và `zara.ns.cloudflare.com`).

**Cách làm trên GoDaddy:**
1. Quay lại trang quản lý tên miền ở GoDaddy (chỗ lúc nãy bạn đổi IP).
2. Nhìn sang tab/cột menu bên cạnh (hoặc kéo lên phía trên), tìm phần **Nameservers** (Máy chủ tên).
3. Nhấn vào nút **Change Nameservers** (Đổi máy chủ tên) -> Chọn **I'll use my own nameservers** (Tôi sẽ dùng nameserver của riêng mình).
4. Copy 2 dòng Nameserver mà Cloudflare cấp dán vào 2 ô tương ứng ở GoDaddy.
5. Nhấn **Save** (Lưu lại).

## Bước 4: Chờ đợi và Bật cấu hình SSL
1. Quay lại tab Cloudflare, nhấn nút **Done, check nameservers**. Cloudflare sẽ bắt đầu kiểm tra (quá trình này có thể mất từ 5 phút đến 1 tiếng để cập nhật trên toàn thế giới).
2. Khi trang web được Cloudflare xác nhận thành công (Active), bạn nhìn sang menu bên trái của Cloudflare, chọn mục **SSL/TLS**.
3. Chọn chế độ **Flexible** (Linh hoạt). 
   *Giải thích: Chế độ Flexible cho phép trình duyệt của khách hàng kết nối bằng HTTPS an toàn, còn Cloudflare sẽ lấy dữ liệu từ máy chủ AWS của bạn qua HTTP thông thường.*
4. Vẫn ở menu bên trái, mục **SSL/TLS**, nhấn xuống menu con **Edge Certificates**. Cuộn xuống dòng **Always Use HTTPS** và gạt công tắc sang trạng thái **ON** (Bật). Mọi khách hàng gõ http sẽ tự động được chuyển sang https an toàn.

---
🎉 **Thành quả:** Bây giờ bạn chờ vài phút rồi mở trình duyệt, gõ `https://treeknowledge.online` là trang web đã có ổ khóa an toàn tuyệt đối!

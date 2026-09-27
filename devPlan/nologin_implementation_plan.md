# Trải nghiệm Khách (Frictionless Guest Mode) - Phân tích UI/UX

Mục tiêu: Cho phép người dùng trải nghiệm gần như toàn bộ hệ thống (Graph Studio, Gia sư AI, Bài giảng, Trắc nghiệm) mà không cần đăng ký. Dữ liệu sẽ được lưu tạm thời và xóa đi khi họ thoát. Tính năng duy nhất bị khóa là **Creator Hub (AI)**.

## Phân Tích Chuỗi Tư Duy (Chain of Thought) & UX Design

1. **Khởi tạo Phiên Khách (Guest Session):**
   - **Vấn đề:** Nếu dùng chung một ID `guest`, những người dùng khách khác nhau sẽ ghi đè dữ liệu của nhau trong Graph Studio.
   - **Giải pháp:** Khi khách nhấn vào môn học ở Landing Page, hệ thống tạo một `session_id` ngẫu nhiên (VD: `guest_a1b2`). 
   - **Không gian lưu trữ:** Tạo thư mục riêng `user_data/guest_a1b2/`. Khi khách thêm môn học vào Cây, file sẽ được copy vào thư mục tạm này.

2. **Trải nghiệm Học tập & Gamification:**
   - **Vấn đề:** Các tính năng Streak, XP, Leaderboard liên kết chặt chẽ với Database. Nếu gọi DB cho khách sẽ gây lỗi.
   - **Giải pháp:** Bỏ qua các lệnh gọi Database (Gamification, Prediction) nếu `role == 'guest'`. Khách vẫn sẽ thấy giao diện 3D và tương tác mượt mà, nhưng không bị làm phiền bởi các thông báo thăng cấp (vì dữ liệu không được lưu vĩnh viễn).

3. **Chặn tính năng Creator Hub (Regwall/Paywall):**
   - **Vấn đề:** Nếu chỉ ẩn Tab đi, khách sẽ không biết hệ thống có tính năng xịn xò này. Nếu hiện thông báo lỗi thông thường thì trải nghiệm rất tệ.
   - **Giải pháp:** Vẫn hiển thị Tab "Creator Hub (AI)". Khi khách nhấn vào, hiển thị một **Màn hình Khóa (Lock Screen)** thiết kế theo chuẩn Apple/MIT Glassmorphism:
     - Icon AI lấp lánh hoặc Ổ khóa.
     - Tiêu đề: "Trở Thành Nhà Sáng Tạo Tri Thức".
     - Nội dung: "Tính năng tạo Cây Tri Thức tự động bằng AI siêu cấp dành riêng cho thành viên. Đăng ký hoàn toàn miễn phí để mở khóa sức mạnh này và lưu trữ vĩnh viễn dữ liệu của bạn."
     - Nút Call-to-Action rực rỡ để Đăng ký/Đăng nhập.

4. **Dọn dẹp Dữ liệu (Garbage Collection):**
   - Hệ thống sẽ có một hàm chạy ngầm (hoặc khi khởi động server) để tự động xóa các thư mục `guest_*` đã tạo quá 24 giờ, tránh đầy ổ cứng.

## User Review Required

> [!IMPORTANT]
> Dưới đây là các phần cần chỉnh sửa. Xin vui lòng xác nhận trước khi tôi thực thi:

### [MODIFY] pages/landing_page.py
- Đổi hàm `redirect_to_login_with_message` thành `enter_guest_mode(subject)`.
- Hàm này sẽ gán `app.storage.user` thành một guest với `uuid` riêng biệt, sau đó chuyển hướng thẳng vào `/app`.

### [MODIFY] main.py
- **Auth check**: Cho phép `app.storage.user.get('role') == 'guest'` vượt qua kiểm tra đăng nhập.
- **Mock User**: Tạo `class MockGuestUser` để đóng giả làm object user cho các hàm phía sau.
- **Bypass DB**: Chặn các lệnh gọi Gamification, Knowledge Tracing nếu là guest.
- **Tab Creator Hub**: Thêm điều kiện `if user.role == 'guest':` để hiển thị màn hình Khóa Glassmorphism tuyệt đẹp thay vì giao diện công cụ bình thường.
- **Header**: Nút góc trên bên phải thay vì chữ "Đăng xuất" sẽ là màu xanh/tím nổi bật "Đăng nhập để lưu tiến trình".

## Open Questions

> [!NOTE]
> Bạn có muốn tôi thiết kế màn hình khóa của Creator Hub theo tông màu Tối (Dark mode) sang trọng, hay tông màu Sáng (Light mode) tinh tế? (Mặc định tôi sẽ làm tông màu tối, đồng bộ với phong cách AI hiện tại).

## Verification Plan
1. Truy cập Landing Page ẩn danh.
2. Nhấn khám phá môn học -> Vào được thẳng `/app` với danh nghĩa "Khách".
3. Thêm thử một cây tri thức vào Graph Studio -> Thành công (lưu tạm).
4. Qua tab Creator Hub -> Thấy màn hình khóa rực rỡ mời đăng ký.
5. Kiểm tra code dọn dẹp thư mục khách.

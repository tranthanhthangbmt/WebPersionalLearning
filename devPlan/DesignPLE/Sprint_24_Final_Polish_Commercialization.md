# Sprint 24: Đóng Gói Toàn Diện, Mã Nguồn Mở & Thương Mại Hóa (Final Polish & Go-to-Market)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Đánh dấu sự kết thúc của Lộ trình Phát triển 2 năm (24 Sprints). Mục tiêu của Sprint này là hoàn thiện mọi ngóc ngách về hiệu năng, bảo mật dữ liệu cấp độ doanh nghiệp (End-to-End Encryption). Đồng thời, chuẩn bị cho việc phát hành sản phẩm dưới hai hình thức: Mã nguồn mở (Self-hosted/Open-Source) cho cộng đồng, và Phiên bản Doanh nghiệp (Enterprise/Commercialization) dành cho các trường học tích hợp.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một nhà phát triển hoặc một trường học nhỏ, tôi muốn có thể tải toàn bộ mã nguồn của hệ thống này và chạy nó trên server riêng của tôi bằng một lệnh cài đặt duy nhất (Ví dụ: Docker Compose) để tôi tự quản lý chi phí API.
- **US2:** Là một Giám đốc Đào tạo (CLO) của một trường Đại học, tôi muốn mua phiên bản Enterprise của nền tảng này để tích hợp trực tiếp với hệ thống quản lý sinh viên (LMS) hiện tại của trường thông qua các API chuẩn.
- **US3:** Là một người dùng cá nhân (Freemium), tôi muốn toàn bộ file JSON lưu trên Google Drive của tôi phải được mã hóa đầu cuối (End-to-End Encryption) để ngay cả nhà cung cấp dịch vụ (Google hay Admin) cũng không thể đọc được nhật ký học tập riêng tư của tôi.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 24.1: Mã hóa Đầu cuối (End-to-End Encryption - E2EE)
- Tích hợp thư viện mã hóa chuẩn AES-256 (ví dụ: `crypto-js`) ở phía Client-side.
- Trước khi luồng Auto-Sync đẩy file `profile.json` và `[Mã_Môn_Học].json` lên Google Drive (Sprint 2), hệ thống sẽ sử dụng một Mật khẩu Master (Master Password) hoặc Khóa công khai của người dùng để mã hóa toàn bộ chuỗi JSON.
- Đảm bảo dữ liệu nằm trên Google Drive chỉ là một cục mã hóa (Ciphertext), hoàn toàn bất khả xâm phạm nếu không có Khóa giải mã lưu tại Local Storage của thiết bị.

### Task 24.2: Đóng gói Ứng dụng & Triển khai (Dockerization)
- Tích hợp và tối ưu `sync_scripts_from_online.py` để tự động cập nhật code mới nhất.
- Viết `Dockerfile` và `docker-compose.yml`. Đóng gói toàn bộ các file Python (cho Backend API phụ nếu có), các Engine 3D, và Node.js server thành một khối thống nhất (All-in-One).
- Cung cấp file cấu hình `.env.example` để người dùng Open-Source dễ dàng điền `GEMINI_API_KEY` và `GOOGLE_DRIVE_CLIENT_ID` của riêng họ.

### Task 24.3: Chuẩn hóa Cổng Giao Tiếp (API Gateway & Webhooks)
- Xây dựng tài liệu API chuẩn **OpenAPI/Swagger**.
- Mở các điểm kết nối (Webhooks) để hệ thống có thể giao tiếp với các LMS phổ biến như Moodle, Canvas, hoặc Blackboard.
- Ví dụ: Khi một sinh viên đạt 100% Mastery một Cây tri thức, hệ thống sẽ tự động bắn Webhook về hệ thống Moodle của nhà trường để cộng điểm tích lũy môn học.

### Task 24.4: Mô hình Kinh doanh (Freemium & Payment Gateway)
- Thiết lập giới hạn (Rate Limits) cho người dùng miễn phí (Ví dụ: Tối đa tạo 3 Cây tri thức/tháng, chỉ RAG được file PDF < 50 trang).
- Tích hợp cổng thanh toán (Stripe/PayPal) cho tài khoản Pro (Không giới hạn tính năng, dùng chung API Key tốc độ cao của nền tảng, có hỗ trợ Voice AI).

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Mở file JSON trên Google Drive bằng Text Editor thông thường, người dùng chỉ thấy một đoạn mã hóa vô nghĩa (AES-256). Nhưng khi mở bằng App, dữ liệu được giải mã và hiển thị 3D bình thường.
- [ ] Một Developer mới chỉ cần chạy lệnh `docker-compose up -d`, sau 5 phút hệ thống chạy hoàn hảo trên `localhost:3000`.
- [ ] Tài liệu hướng dẫn sử dụng API (Swagger UI) hiển thị chuyên nghiệp và đầy đủ các Endpoints.
- [ ] Người dùng Free bị chặn khi cố upload file PDF quá 50 trang, và được chuyển hướng mượt mà đến trang Nâng cấp (Upgrade to Pro).

## 4. Risk & Dependencies
- **Rủi ro 1 - Mất Khóa mã hóa (Lost E2EE Key):** Nếu người dùng quên Master Password hoặc xóa Local Storage mà chưa sao lưu Khóa giải mã, họ sẽ vĩnh viễn mất trắng toàn bộ dữ liệu trên Google Drive (vì không ai có thể giải mã được, kể cả Admin).
- **Giải pháp:** Trong luồng Onboarding (Sprint 19), bắt buộc người dùng tải xuống một file "Recovery Key" (Mã khôi phục) hoặc in ra giấy cất giữ cẩn thận trước khi bật tính năng E2EE.
- **Phụ thuộc:** Yêu cầu toàn bộ 23 Sprints trước đó phải ở trạng thái "Stable" (Ổn định, không có Bug P0).

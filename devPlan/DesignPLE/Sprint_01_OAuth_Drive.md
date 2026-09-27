# Sprint 1: Khởi tạo Google OAuth & Cấu trúc Google Drive API

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Thiết lập thành công luồng xác thực Google Login. Ứng dụng xin được quyền truy cập Drive của người dùng (scope `drive.file`) và tự động tạo được thư mục gốc `KnowledgeGalaxy_Data` trên Drive sau khi đăng nhập thành công.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, tôi muốn đăng nhập bằng tài khoản Google của mình để không phải tạo tài khoản mới hay nhớ mật khẩu.
- **US2:** Là một người học, tôi muốn ứng dụng tự động thiết lập một không gian riêng tư trên Google Drive của tôi để lưu trữ dữ liệu học tập an toàn.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 1.1: Thiết lập Google Cloud Console
- Tạo Project mới trên Google Cloud Console (VD: "Knowledge Galaxy PLE").
- Cấu hình **OAuth Consent Screen**:
  - Chọn User Type: External.
  - Thêm Scope: `https://www.googleapis.com/auth/drive.file`.
  - Thêm Test Users (Email của nhà phát triển và email thử nghiệm).
- Tạo **OAuth 2.0 Client ID** (Loại ứng dụng: Web Application). Lấy `Client ID` và `Client Secret`.
- Cấu hình Authorized JavaScript origins và Authorized redirect URIs (VD: `http://localhost:5000/callback`).

### Task 1.2: Tích hợp Google Sign-In vào Frontend (UI/UX)
- Tạo nút "Đăng nhập với Google" chuẩn thiết kế (có logo G).
- Thư viện đề xuất: Sử dụng Google Identity Services (GIS) script gốc `https://accounts.google.com/gsi/client`.
- Viết Javascript để gọi luồng đăng nhập dạng Popup hoặc Redirect. Trả về `access_token`.

### Task 1.3: Cấu hình Backend nhận Token (hoặc xử lý 100% Frontend)
- Vì hệ thống hướng tới Backendless, chúng ta sẽ lưu trữ `access_token` tại `sessionStorage` của trình duyệt.
- Xây dựng file `drive_service.js` (hoặc `.py` nếu dùng backend Flask/FastAPI làm proxy). 
- Viết hàm `verify_token()` để kiểm tra token hợp lệ.

### Task 1.4: Viết API Giao tiếp Google Drive
- Viết hàm `initDriveEnvironment()`:
  - Gọi API `GET https://www.googleapis.com/drive/v3/files` để kiểm tra xem thư mục `KnowledgeGalaxy_Data` đã tồn tại chưa.
  - Nếu chưa, gọi `POST https://www.googleapis.com/drive/v3/files` với mimeType là `application/vnd.google-apps.folder` để tạo thư mục.
  - Lưu `folder_id` của thư mục này vào LocalStorage để sử dụng cho các lần sau.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Code có nút Đăng nhập Google hoạt động, lấy được Access Token.
- [ ] Không có lỗi CORS khi gọi API.
- [ ] Kiểm tra thực tế trên Google Drive của người dùng thử nghiệm: Thư mục `KnowledgeGalaxy_Data` được tạo thành công ngay sau khi đăng nhập lần đầu.
- [ ] Đóng app mở lại, hệ thống nhận diện được trạng thái đã đăng nhập (Persist login session).

## 4. Risk & Dependencies
- **Rủi ro:** Google yêu cầu duyệt (App Verification) nếu app chuyển sang chế độ Production. Hiện tại chỉ chạy ở chế độ Testing để tránh rườm rà.
- **Phụ thuộc:** Yêu cầu phải có kết nối Internet ổn định để xác thực.

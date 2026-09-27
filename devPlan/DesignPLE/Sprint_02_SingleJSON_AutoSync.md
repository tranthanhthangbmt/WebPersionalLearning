# Sprint 2: Kiến trúc Single JSON & Cơ chế Auto-Sync (Đồng bộ Google Drive)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Chuyển đổi hoàn toàn hệ thống lưu trữ sang cấu trúc "Single JSON" (File JSON độc lập). Triển khai thành công luồng đọc/ghi file trực tiếp lên Google Drive của người dùng (Backendless/Stateless) và xây dựng cơ chế tự động đồng bộ (Auto-sync) chống nghẽn mạng (debounce).

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, tôi muốn tất cả điểm số Gamification và cấu trúc môn học của tôi được lưu tự động lên Drive dưới dạng file để tôi hoàn toàn làm chủ dữ liệu.
- **US2:** Là một người học, tôi muốn quá trình lưu dữ liệu diễn ra ngầm (background) và không làm gián đoạn hay làm chậm quá trình học tập của tôi.
- **US3:** Là một người học, tôi muốn khi mở ứng dụng ở một máy tính khác và đăng nhập Google, toàn bộ Cây tri thức và tiến độ học tập của tôi lập tức hiển thị lại y hệt.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 2.1: Định nghĩa chuẩn Schema JSON (Data Modeling)
- Tạo file thiết kế `schema.md` định nghĩa 2 cấu trúc cốt lõi:
  - `profile.json`: Chứa User Info, Global XP, Level, Danh sách các Môn học (Kèm `folder_id` của thư mục môn học trên Drive).
  - `[subject_id].json`: Chứa mảng `nodes` (id, label, bloom_score, mastery_score, documents_list) và `edges` (from, to, type).
  
### Task 2.2: Viết các hàm API Giao tiếp File trên Drive (CRUD)
- Cập nhật `drive_service.js` (hoặc Python tương đương) với các hàm:
  - `uploadFileToDrive(fileName, jsonContent, parentFolderId)`: Upload file mới.
  - `updateFileOnDrive(fileId, jsonContent)`: Ghi đè (Overwrite) file cũ để tránh sinh ra nhiều file trùng tên. Cần sử dụng phương thức `PATCH` hoặc `PUT` của Google Drive API v3.
  - `downloadFileFromDrive(fileId)`: Lấy nội dung JSON về RAM.

### Task 2.3: Quản lý Trạng thái Cục bộ (Local State & Caching)
- Xây dựng một Module State Management (VD: Redux, Context API, hoặc Python Global State tùy kiến trúc UI).
- Khi ứng dụng khởi động: 
  - Kéo `profile.json` từ Drive xuống.
  - Lưu vào Local Storage / Session của trình duyệt. 
- Mọi thao tác click, làm bài tập, tăng XP của UI sẽ chỉ thao tác Đọc/Ghi trên **bộ nhớ tạm** này để đảm bảo độ trễ là 0ms.

### Task 2.4: Xây dựng Cơ chế Auto-Sync (Debounce)
- Viết một vòng lặp hoặc hàm Observer lắng nghe sự thay đổi của State cục bộ.
- Áp dụng thuật toán **Debounce** (Đợi 3-5 giây sau thao tác cuối cùng mới gọi API) hoặc **Throttling** (Cứ mỗi 10 giây sẽ tự động push lên Drive một lần nếu có thay đổi).
- Xử lý lỗi: Nếu mất mạng khi đang Sync, lưu cờ (flag) `is_dirty = true` ở Local Storage để lần có mạng tiếp theo sẽ tự động đẩy lên.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [x] Schema JSON được phê duyệt và đáp ứng đủ lưu trữ cả hệ thống.
- [x] Thực hiện một hành động (VD: Cộng 10 XP), file `profile.json` trên Google Drive tự động cập nhật sau 5 giây mà không cần người dùng bấm nút "Lưu".
- [x] Đóng trình duyệt, mở tab Ẩn danh, đăng nhập lại Google, số điểm XP hiện ra chính xác như lần cuối cùng học.
- [x] Xử lý thành công việc ghi đè file trên Drive thay vì tạo ra hàng loạt file JSON trùng tên.

## 4. Risk & Dependencies
- **Rủi ro:** Google Drive API có giới hạn số lượt request mỗi phút (Rate Limiting). Nếu thuật toán Auto-sync gọi API quá liên tục khi user thao tác nhanh, app sẽ bị khóa API tạm thời (Error 429). Bắt buộc phải có cơ chế Debounce.
- **Phụ thuộc:** Yêu cầu hoàn thành 100% Sprint 1 (Đã có Access Token và hàm tạo thư mục gốc).

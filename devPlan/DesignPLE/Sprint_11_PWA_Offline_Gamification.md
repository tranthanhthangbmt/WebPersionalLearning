# Sprint 11: Ứng dụng Di động, Học Offline & Gamification Nâng cao

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Xóa nhòa ranh giới giữa Web và Ứng dụng Native bằng công nghệ PWA (Progressive Web App), cho phép người dùng cài đặt lên điện thoại và **học Offline không cần mạng**. Đồng thời, nâng cấp hệ thống Động lực học (Gamification) với Chuỗi ngày học (Streaks) và Huy hiệu (Badges) để giữ chân người dùng.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, tôi muốn cài đặt ứng dụng này lên màn hình chính của điện thoại (iOS/Android) để mở ra học nhanh chóng mà không cần gõ URL trình duyệt.
- **US2:** Là một người học, tôi muốn tranh thủ ôn bài (làm Quiz SRS) khi đang ngồi trên xe buýt không có Wi-Fi. Khi về nhà có mạng, dữ liệu tự động đồng bộ lên Drive.
- **US3:** Là một người học, tôi muốn thấy biểu tượng "Ngọn lửa" 🔥 (Streak) tăng lên mỗi ngày tôi vào học, và nhận được Huy hiệu khi tôi đạt cột mốc mới để có động lực khoe với bạn bè.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 11.1: Thiết lập PWA (Progressive Web App)
- Tạo file `manifest.json`: Định nghĩa tên app, icon các kích cỡ, màu chủ đạo (theme_color) và thiết lập `display: "standalone"` để ẩn thanh địa chỉ trình duyệt.
- Viết `Service Worker (sw.js)`:
  - Cache toàn bộ các file tĩnh (HTML, CSS, JS, các thư viện 3D).
  - Áp dụng chiến lược `Cache-First` cho tài nguyên tĩnh để app mở lên tức thì dù không có mạng.

### Task 11.2: Cơ chế Offline & Hàng đợi Đồng bộ (Sync Buffer)
- Kế thừa cấu trúc Single JSON từ Sprint 2.
- Sử dụng API `navigator.onLine` để theo dõi trạng thái mạng.
- **Khi Offline:**
  - Mọi thay đổi (điểm số, bài tập, thêm node) đều được ghi vào `LocalStorage` hoặc `IndexedDB`.
  - Cờ `is_sync_pending = true` được bật.
- **Khi Online trở lại:**
  - Bắt sự kiện `window.addEventListener('online', ...)`.
  - Khởi chạy tiến trình ngầm: Đọc dữ liệu JSON mới nhất từ LocalStorage và gọi `updateFileOnDrive` (API Google Drive) để ghi đè.

### Task 11.3: Nâng cấp Gamification (Streaks & Badges)
- Cập nhật schema `profile.json`:
  - Thêm `current_streak` (int), `longest_streak` (int), `last_study_date` (YYYY-MM-DD).
  - Thêm `unlocked_badges` (mảng ID huy hiệu).
- **Thuật toán Streak:** Khi user hoàn thành 1 bài tập, kiểm tra `last_study_date`. Nếu là "Hôm qua", `current_streak += 1`. Nếu cách xa hơn 1 ngày, `current_streak = 1` (Mất chuỗi).
- **Hệ thống Huy hiệu (Achievements):** Tích hợp logic từ `achievement_service.py`. Ghi nhận các sự kiện: VD: User tải lên 5 file PDF -> Mở khóa huy hiệu "Nhà Nghiên Cứu". User có 10 Node đạt mức Bloom 6 -> Mở khóa huy hiệu "Học Giả".

### Task 11.4: UI Hồ sơ Người dùng (Profile Dashboard)
- Tạo một màn hình/Drawer riêng biệt cho Profile.
- Hiển thị Avartar Google, Tổng XP, Cấp độ (Level progress bar).
- Hiển thị hiệu ứng Ngọn lửa cháy (CSS Animation) biểu thị Streak.
- Hiển thị bộ sưu tập Huy hiệu (Các huy hiệu chưa mở khóa sẽ có màu xám/bóng mờ).

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Truy cập ứng dụng trên điện thoại, trình duyệt gợi ý "Add to Home Screen". Sau khi add, app mở lên full màn hình như app Native.
- [ ] Tắt Wi-Fi máy tính/điện thoại: App vẫn load được, Cây tri thức vẫn hiện. Làm thử 1 Quiz, điểm số thay đổi trên Local.
- [ ] Bật lại Wi-Fi: Bật F12 Network xem, thấy app tự động bắn API `PATCH` lên Google Drive để cập nhật file JSON.
- [ ] Điểm Streak tăng khi đổi ngày giờ hệ thống sang ngày hôm sau và làm bài.

## 4. Risk & Dependencies
- **Rủi ro 1 - Xung đột Dữ liệu (Data Conflict):** Người dùng học offline trên Điện thoại (tạo ra File A), nhưng đồng thời mở Laptop có mạng (tạo ra File B). Khi Điện thoại có mạng trở lại, nó sẽ ghi đè lên Laptop gây mất dữ liệu của Laptop.
- **Giải pháp:** Sử dụng cơ chế Check Timestamp (Ngày giờ chỉnh sửa cuối cùng). Khi Điện thoại online, trước khi ghi đè, nó tải Timestamp của file trên Drive về. Nếu file trên Drive MỚI HƠN file local của điện thoại -> Hiển thị cảnh báo: *"Dữ liệu của bạn có sự xung đột giữa 2 thiết bị. Bạn muốn giữ bản nào?"*
- **Phụ thuộc:** Yêu cầu đã hoàn thành API Google Drive từ Sprint 1 & 2.

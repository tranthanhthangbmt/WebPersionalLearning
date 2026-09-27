# Sprint 16: Mạng Xã Hội Học Tập & Thư Viện Cộng Đồng (Social & Public Library)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Hoàn thiện mảnh ghép cuối cùng của khung PLiF: **Learner-to-Social Network**. Xây dựng một "Mạng xã hội tri thức" thu nhỏ (Social Page), nơi sinh viên có thể xuất bản Cây tri thức của mình lên Thư viện Cộng đồng (Public Library) cho toàn thế giới tải về. Đồng thời, kết nối bảng vàng (Leaderboard) để vinh danh những người đóng góp và tạo động lực học tập nhóm.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một sinh viên học giỏi, sau khi xây dựng xong Cây tri thức môn Giải tích siêu chi tiết, tôi muốn "Xuất bản" (Publish) nó lên Thư viện chung để cộng đồng tải về, qua đó tôi nhận được điểm Danh vọng (Reputation).
- **US2:** Là một sinh viên mới, tôi muốn dạo quanh trang Mạng Xã Hội (Explore/Social Page) để tìm kiếm và tải về các Cây tri thức được đánh giá 5 sao thay vì tự tạo từ đầu.
- **US3:** Là một người dùng, tôi muốn thấy một Bảng tin (News Feed) và Bảng xếp hạng (Leaderboard) báo cáo việc bạn bè tôi vừa đạt chuỗi học 30 ngày (Streak) hoặc vừa mở khóa huy hiệu, để tôi có động lực phấn đấu.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 16.1: Cấu trúc Dữ liệu Thư viện Cộng đồng (Public Library)
- Khởi tạo file `DB/public_library.json` (Lưu trữ tập trung trên Server/Firebase thay vì Google Drive cá nhân).
- Khi user bấm nút "Xuất bản":
  - Hệ thống tự động chuyển thư mục môn học trên Drive của họ sang `Public`.
  - Đẩy một bản ghi (Record) lên `public_library.json` gồm: `author_name`, `subject_name`, `tags`, `node_count`, `drive_link`, `downloads: 0`, `rating: 5.0`.

### Task 16.2: Xây dựng Giao diện Social / Explore (Marketplace)
- Tích hợp và hoàn thiện `social_page.py`.
- Tạo giao diện giống như một "Chợ ứng dụng" (Marketplace) hoặc kho Plugin.
- Có thanh Tìm kiếm (Search bar), Bộ lọc (Tags) và cơ chế Sắp xếp (Sort by Downloads, Sort by Rating).
- Khi người dùng bấm vào một mục, hiển thị bản xem trước (Preview) một phần của Đồ thị 3D trước khi họ quyết định bấm "Tải về".
- Kết nối nút "Tải về" với tính năng Import (Đã làm ở Sprint 6) để clone dữ liệu vào Drive cá nhân.

### Task 16.3: Thuật toán Xếp hạng & Đánh giá (Ranking & Rating)
- Viết tính năng Đánh giá 5 sao. Khi người dùng tải về và học xong 10% môn đó, hiện popup xin đánh giá chất lượng Cây tri thức của tác giả.
- **Thuật toán Danh vọng (Reputation System):** Tác giả sẽ được cộng +10 XP Danh vọng cho mỗi lượt tải về, và +50 XP nếu nhận được đánh giá 5 sao. Danh vọng cao sẽ giúp Avatar của tác giả có viền Vàng/Kim cương trên hệ thống.

### Task 16.4: Bảng tin Xã hội & Leaderboard
- Tích hợp `leaderboard_page.py`.
- Tạo một WebSocket hoặc Polling API để phát (Broadcast) các sự kiện hệ thống lên Bảng tin (News Feed):
  - *"Học sinh A vừa xuất bản Cây tri thức Sinh học."*
  - *"Học sinh B vừa đạt chuỗi học tập 30 ngày (Streak Flame)!"*
  - *"Học sinh C vừa lọt vào Top 10 Bảng xếp hạng Tuần."*
- Xây dựng Leaderboard tuần/tháng dựa trên tổng số XP học tập và XP Danh vọng cộng lại.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] User A bấm Publish, ngay lập tức Cây tri thức xuất hiện trên trang `Social Page` của toàn bộ user khác.
- [ ] User B vào tìm kiếm từ khóa "Giải tích", thấy bài của User A, bấm Tải về thành công. Bộ đếm `downloads` của User A tăng lên 1.
- [ ] Điểm số của User A tăng lên trên Leaderboard.
- [ ] Bảng tin hiển thị mượt mà các hoạt động vinh danh.

## 4. Risk & Dependencies
- **Rủi ro 1 - Rác dữ liệu (Spam Content):** Người dùng có thể xuất bản những cây tri thức rỗng, nội dung phản cảm hoặc đặt tên sai lệch để câu lượt tải.
- **Giải pháp:** Áp dụng hệ thống Kiểm duyệt AI (AI Moderation). Trước khi file được đẩy lên `public_library.json`, hệ thống dùng Gemini chạy qua các Label của Node. Nếu có từ ngữ vi phạm hoặc số lượng Node < 5, hệ thống từ chối cho xuất bản. Bổ sung nút "Report" cho cộng đồng tự kiểm duyệt.
- **Phụ thuộc:** Yêu cầu thuật toán Import/Clone Google Drive (Sprint 6) hoạt động hoàn hảo 100%.

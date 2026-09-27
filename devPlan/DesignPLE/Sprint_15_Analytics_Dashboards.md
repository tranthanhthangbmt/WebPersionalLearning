# Sprint 15: Cổng Phân tích & Giám sát (Teacher & Parent Dashboard)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Hoàn thiện hệ sinh thái giáo dục bằng việc bổ sung vai trò "Người quan sát" (Observer). Dựa trên dữ liệu cá nhân hóa khổng lồ của học sinh, xây dựng các bảng điều khiển (Dashboards) chuyên biệt cho Giáo viên (để phân tích năng lực cả lớp) và Phụ huynh (để theo dõi tiến độ của con cái), kết nối trực tiếp với tính năng Omni-Drawer để tạo ra cơ chế can thiệp sư phạm kịp thời.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một giáo viên đứng lớp, tôi muốn nhìn thấy một "Bản đồ nhiệt" (Heatmap) gộp chung Cây tri thức của cả 40 sinh viên, để tôi biết ngay Khái niệm nào cả lớp đang yếu (Đỏ) và giảng lại vào ngày mai.
- **US2:** Là một phụ huynh, tôi muốn có một giao diện đơn giản trên điện thoại để xem hôm nay con tôi có học bài không (Streak), kiếm được bao nhiêu XP, và đang kẹt ở môn nào.
- **US3:** Là một học sinh, tôi muốn có quyền chủ động cấp phép (Cấp quyền Reader trên Google Drive) cho giáo viên hoặc phụ huynh xem dữ liệu của mình để đảm bảo quyền riêng tư.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 15.1: Cấu trúc Phân quyền & Chia sẻ Dữ liệu (Access Control)
- Tạo giao diện "Quản lý Quyền Truy cập" ở mục Cài đặt của Học sinh.
- Khi Học sinh nhập Email của Giáo viên/Phụ huynh, ứng dụng gọi Google Drive API cấp quyền `Reader` cho file `profile.json` và các file `[Mã_Môn_Học].json`.
- **Bảo mật:** Dữ liệu cá nhân nhạy cảm như (Nhật ký chat với AI, Mức độ mệt mỏi theo giờ) sẽ được mã hóa hoặc ẩn đi, chỉ cho phép Người quan sát xem điểm số (Mastery, Bloom, XP).

### Task 15.2: Phát triển Teacher Dashboard (Phân tích Lớp học)
- Tích hợp và xây dựng logic cho file `teacher_dashboard.py`.
- **Thuật toán Aggregation (Gộp dữ liệu):**
  - Hệ thống tải file JSON của 40 học sinh (đã cấp quyền) xuống bộ nhớ.
  - Tính điểm trung bình (Average Mastery) của từng Node.
  - Vẽ ra một Cây tri thức 3D của Lớp học (Class-level Knowledge Graph). Khái niệm nào < 50% trung bình sẽ hiện màu Đỏ nhấp nháy, báo hiệu "Điểm mù kiến thức của lớp".

### Task 15.3: Phát triển Parent Dashboard (Báo cáo Tiến độ)
- Tích hợp và xây dựng logic cho file `parent_dashboard.py`.
- Thiết kế UI dạng Báo cáo tổng quan (Analytics Report):
  - Biểu đồ đường (Line chart) hiển thị sự tăng trưởng XP trong 7 ngày qua.
  - Trạng thái Ngọn lửa (Streak) hiện tại.
  - Danh sách các "Lỗ hổng kiến thức" (Các Node màu Đỏ tồn tại quá 3 ngày chưa được giải quyết).

### Task 15.4: Cơ chế Can thiệp Sư phạm (Teacher Intervention System)
- Trên Teacher Dashboard, khi giáo viên click chuột phải vào một Học sinh đang yếu ở một Node cụ thể, sẽ có nút: **"Gửi khuyến nghị ôn tập"**.
- Một bản ghi nhỏ được đẩy vào cấu trúc JSON của học sinh đó.
- Lần tới khi học sinh mở app, Trợ lý AI (Omni-Drawer - Sprint 10) sẽ nhận diện bản ghi này và chủ động popup: *"Chào em, Cô giáo bộ môn vừa lưu ý em cần làm lại bài tập phần [Đạo hàm]. Bấm vào đây để làm ngay 3 câu hỏi nhé!"*.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Giao diện Teacher Dashboard load thành công Cây tri thức gộp của 3 tài khoản Học sinh giả lập. Hiển thị đúng màu trung bình.
- [ ] Parent Dashboard vẽ được biểu đồ tăng trưởng XP chính xác dựa trên `profile.json` của Học sinh.
- [ ] Giáo viên gửi lệnh "Khuyến nghị", Học sinh nhận được tin nhắn trực tiếp qua Omni-Drawer ngay trong phiên học.

## 4. Risk & Dependencies
- **Rủi ro 1 - Tải dữ liệu chậm:** Nếu giáo viên quản lý 100 học sinh, việc gọi API Google Drive tải 100 file JSON cùng lúc sẽ mất nhiều thời gian và dễ bị Google chặn (Rate Limit).
- **Giải pháp:** Xây dựng cơ chế **Caching & Batching**. Dashboard của giáo viên không tải Real-time (Thời gian thực) mà chỉ cập nhật dữ liệu (Sync) 1 lần vào mỗi cuối ngày. Tải theo từng lô (Batch) 10 học sinh/lần.
- **Rủi ro 2 - Xâm phạm quyền riêng tư:** Cần có thỏa thuận rõ ràng (Consent Form) trên giao diện Học sinh khi cấp quyền cho phụ huynh/giáo viên.

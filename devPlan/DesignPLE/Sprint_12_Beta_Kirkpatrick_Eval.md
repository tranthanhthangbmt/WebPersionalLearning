# Sprint 12: Đánh Giá Hiệu Quả (Kirkpatrick L5) & Đóng Gói (Beta Testing)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Hoàn tất vòng đời phát triển 12 tháng bằng việc mở cửa cho một nhóm sinh viên dùng thử (Beta Testing). Tối ưu hóa chi phí API gọi Gemini, sửa các lỗi (Bugs) phát sinh. Đặc biệt, triển khai bộ công cụ đo lường hiệu quả của hệ thống học tập dựa trên mô hình Kirkpatrick 5 cấp độ (như đã phân tích trong cuốn sách Designing PLE).

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người dùng thử (Beta Tester), tôi muốn hệ thống hoạt động ổn định, không bị văng (crash) hoặc đứng máy khi tôi tải lên một giáo trình nặng 500 trang.
- **US2:** Là một quản trị viên / nhà nghiên cứu, tôi muốn thu thập dữ liệu (ẩn danh) để chứng minh rằng hệ thống PLE này thực sự giúp sinh viên học tốt hơn so với phương pháp truyền thống.
- **US3:** Là một nhà phát triển, tôi muốn kiểm soát được chi phí token (API Cost) của mô hình LLM, đảm bảo hệ thống có thể mở rộng (scale) mà không bị "cháy túi".

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 12.1: Xử lý Lỗi & Giám sát Hệ thống (Bug Triaging)
- Tích hợp công cụ giám sát lỗi Frontend (Ví dụ: Sentry hoặc LogRocket) để tự động ghi nhận các lỗi hiển thị 3D hoặc lỗi xung đột File JSON.
- Thiết lập kênh thu thập phản hồi: Gắn một nút "Góp ý/Báo lỗi" ở góc dưới màn hình để sinh viên gõ text chụp màn hình gửi thẳng về hệ thống.

### Task 12.2: Tối ưu Chi phí API (API Cost Optimization)
- **Vấn đề:** RAG và Trích xuất Graph tốn rất nhiều token. Nếu sinh viên upload sách liên tục, chi phí sẽ rất cao.
- **Giải pháp:** 
  - Cài đặt giới hạn (Hard Cap): Tối đa 500 trang/ngày cho mỗi sinh viên.
  - Implement Caching Layer: Nếu sinh viên A hỏi câu X, sinh viên B cũng hỏi câu X (với cùng 1 cuốn sách đã Share ở Sprint 6), hệ thống sẽ trả về đáp án đã lưu ở Cache thay vì gọi lại Gemini.

### Task 12.3: Triển khai Khung Đánh giá Kirkpatrick (Kirkpatrick Evaluation Framework)
Căn cứ theo sách "Designing Personalized Learning Experiences", ta số hóa 5 cấp độ đánh giá:
- **Level 1 (Phản ứng - Reaction):** Thêm popup đánh giá 5 sao (NPS) sau khi sinh viên hoàn thành 100% Mastery một môn học.
- **Level 2 (Học tập - Learning):** Trích xuất tự động sự chênh lệch (Delta) của `mastery_score` và `bloom_level` từ file JSON vào Ngày 1 so với Ngày 14.
- **Level 3 (Hành vi - Behavior):** Sử dụng dữ liệu Gamification (Sprint 11). Nếu `current_streak` trung bình của sinh viên tăng lên -> Chứng minh ứng dụng đã thay đổi được thói quen học tập.
- **Level 4 & 5 (Kết quả & ROI):** Viết script Python tính toán: `Tổng chi phí API bỏ ra / Số giờ học thực tế của sinh viên`. So sánh với chi phí thuê gia sư thật để ra được ROI (Lợi tức đầu tư) của dự án.

### Task 12.4: Đóng gói & Phát hành bản v1.0 (Final Polish)
- Kiểm tra toàn diện UI/UX: Độ mượt của hiệu ứng (Animations), độ tương phản màu sắc trong Chế độ Tối (Dark Mode).
- Đóng gói code, dọn dẹp các thư viện không dùng đến (Tree shaking).
- Viết tài liệu Hướng dẫn sử dụng (User Manual) ngay trên trang chủ của ứng dụng.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Hoàn thành chạy thử nghiệm với 10-20 sinh viên thực tế. Không có lỗi nghiêm trọng (Severity P0/P1) nào xuất hiện gây mất dữ liệu file JSON trên Google Drive.
- [ ] Bảng dashboard đánh giá Kirkpatrick xuất ra được các biểu đồ trực quan chứng minh sinh viên có sự tiến bộ về Mastery.
- [ ] Ứng dụng chạy mượt mà trên cả PC và Mobile (PWA). Chi phí API được giữ ở mức dưới $1/người/tháng.

## 4. Risk & Dependencies
- **Rủi ro:** Sinh viên Beta Tester lười dùng app, dẫn đến không có đủ dữ liệu để tính toán Kirkpatrick ROI.
- **Giải pháp:** Đưa ra các phần thưởng ngoài đời thực (Ví dụ: Thẻ cào, Voucher) cho những Beta Tester đạt được huy hiệu "Mastery" đầu tiên trên ứng dụng để kích thích họ dùng thử.

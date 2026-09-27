# Sprint 19: Onboarding Thông minh & Hệ thống Luyện tập Nâng cao

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Hoàn thiện "Điểm chạm đầu tiên" (First touch-point) cho người dùng mới qua một luồng Onboarding tương tác. Đồng thời, nâng cấp hệ thống đánh giá lên mức độ chuyên sâu (Bloom 5 & 6) bằng tính năng "Advanced Practice" (Làm tự luận do AI chấm điểm), và âm thầm theo dõi hành vi học tập (Behavior Tracking) để tối ưu hóa thuật toán.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một sinh viên mới biết đến ứng dụng, tôi muốn có một bài hướng dẫn ngắn gọn (Interactive Tour) chỉ cho tôi cách thao tác với Không gian 3D và cách gọi Trợ lý AI, để tôi không bị ngợp.
- **US2:** Là một người học đang ở mức độ Sáng tạo/Đánh giá (Bloom 5, 6), việc chọn trắc nghiệm A B C D là quá dễ. Tôi muốn hệ thống đưa ra một câu hỏi mở (Tự luận) và AI sẽ đóng vai Giáo sư để chấm điểm bài viết của tôi.
- **US3:** Là một hệ thống thông minh, tôi muốn theo dõi ngầm xem sinh viên dừng lại đọc lý thuyết ở một Node bao lâu (Dwell time) để đoán xem họ có đang gặp khó khăn hay không.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 19.1: Xây dựng Luồng Onboarding Tương tác (onboarding.py)
- Sử dụng thư viện hướng dẫn UI (ví dụ: `driver.js` hoặc `intro.js`).
- Thiết kế kịch bản Onboarding 3 bước:
  - **Bước 1:** Khóa màn hình, làm nổi bật Cây tri thức 3D. (Text: "Đây là vũ trụ kiến thức của bạn").
  - **Bước 2:** Mô phỏng click vào một Node mẫu, làm nổi bật Omni-Drawer. (Text: "Nơi AI giải thích chi tiết mọi khái niệm").
  - **Bước 3:** Làm nổi bật nút Quiz.
- Thêm trường `has_completed_onboarding: true` vào file `profile.json` trên Google Drive để không bao giờ hiện lại luồng này ở lần đăng nhập sau.

### Task 19.2: Chế độ Luyện tập Nâng cao (Advanced Practice - Tự luận)
- Tích hợp logic xử lý vào `advanced_practice.py`.
- **Cơ chế kích hoạt:** Khi người dùng mở Quiz cho một Node có `bloom_level >= 4`.
- **Giao diện:** Thay vì 4 nút A, B, C, D, hiển thị một ô Text Area yêu cầu người dùng tự gõ câu trả lời (Viết tiểu luận / Giải thích ngắn).
- **Thuật toán Chấm điểm (AI Grader):**
  - Prompt: *"Ngữ cảnh: [Lấy từ FAISS]. Câu hỏi: X. Câu trả lời của sinh viên: Y. Hãy đóng vai một giáo sư khắt khe, chấm điểm câu trả lời này trên thang 0-100 dựa chặt chẽ vào Ngữ cảnh. Chỉ ra những ý sinh viên còn thiếu."*
  - Parse JSON kết quả từ LLM để lấy `score` và cập nhật trực tiếp vào thuật toán `calculate_new_mastery` (Sprint 8).

### Task 19.3: Thuật toán Theo dõi Hành vi ngầm (Behavior Tracker)
- Xây dựng module `behavior_tracker.py` chạy ngầm ở phía Client.
- Gắn các Event Listener: `scroll`, `mousemove`, `click`, và tính toán thời gian `dwell_time` (thời gian dừng lại nhìn chằm chằm vào màn hình Omni-Drawer của một Node).
- Nếu `dwell_time > 3 phút` mà không chuyển trang, AI ngầm hiểu khái niệm này khó hiểu.
- Chuyển dữ liệu này gộp vào thuật toán tính mệt mỏi (`Fatigue` - Sprint 10) và tự động giảm `ease_factor` (Độ dễ) trong công thức lặp lại ngắt quãng SRS (Sprint 9).

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Xóa cache trình duyệt, đăng nhập bằng tài khoản mới tinh: Hệ thống lập tức chạy luồng Onboarding chỉ dẫn từng nút bấm.
- [ ] Click vào Node đang có Bloom Level 4. Hệ thống yêu cầu gõ tự luận.
- [ ] Gõ một đoạn văn sai kiến thức hoàn toàn. Đợi 5 giây, AI trả về kết quả 20/100 điểm, đánh dấu Đỏ và giải thích chi tiết lý do sai dựa trên trang sách PDF.
- [ ] Dừng chuột đọc bài quá 3 phút, mở DevTools xem thấy biến `behavior_tracker.dwell_time` tăng lên chính xác.

## 4. Risk & Dependencies
- **Rủi ro 1 - AI chấm điểm cảm tính (Subjective Grading):** Mô hình LLM đôi khi chấm điểm quá nương tay hoặc quá khắt khe, không ổn định qua các lần gọi khác nhau.
- **Giải pháp:** Cung cấp Rubric (Barem chấm điểm) cực kỳ cứng nhắc trong Prompt. Yêu cầu AI tư duy theo từng bước (Chain of Thought): B1 - Phân tích ý chính trong sách, B2 - Tìm ý chính trong bài làm của SV, B3 - Trừ 10 điểm cho mỗi ý thiếu.
- **Rủi ro 2 - Quá tải Tracker:** Bắt sự kiện chuột (mousemove) liên tục sẽ làm giật lag trình duyệt.
- **Giải pháp:** Phải sử dụng hàm `Lodash.throttle()` để giới hạn chỉ lấy mẫu hành vi mỗi 2-3 giây một lần.

# Sprint 10: Trợ lý AI Đồng hành Chủ động & Tìm đường (Proactive Companion)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Khởi động Quý 4 bằng việc nâng cấp Trợ lý AI (Omni-Drawer). Thay vì chỉ nằm im chờ người dùng hỏi, AI sẽ trở thành một gia sư thực thụ: biết quan sát thời gian học để tính toán sự mệt mỏi (Fatigue), tự động phân tích đồ thị để gợi ý lộ trình học tối ưu (Pathfinder) và tự động xuất hiện nhắc nhở khi cần thiết.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, nếu tôi đã ngồi giải bài tập liên tục 45 phút và bắt đầu làm sai nhiều, tôi muốn AI tự nhận ra tôi đang mệt và khuyên tôi nghỉ ngơi 5 phút.
- **US2:** Là một người học đứng trước một cây tri thức có hàng trăm Node, tôi không muốn phải tự mò mẫm xem nên học cái gì trước. Tôi muốn AI tự động chỉ ra Node "điểm nghẽn" (Prerequisite) cần giải quyết ngay bây giờ.
- **US3:** Là một người học, tôi không muốn bị AI làm phiền liên tục bằng các popup quảng cáo kiểu cũ. Sự xuất hiện của AI phải thật tinh tế và đúng lúc.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 10.1: Engine Theo dõi Trạng thái (Fatigue & Session Tracker)
- Xây dựng một Background Script chạy ngầm trên trình duyệt.
- Tính toán biến `current_fatigue` (0-100%):
  - Tăng 2% cho mỗi phút active (chuột/bàn phím hoạt động).
  - Tăng đột biến (+10%) nếu làm sai Quiz (Dấu hiệu stress).
  - Giảm (-50%) nếu không có tương tác trong 10 phút (Nghỉ ngơi).
- Lưu biến này vào Local Storage tạm thời (Không cần đồng bộ Google Drive vì đây là session-based data).

### Task 10.2: Thuật toán Tìm đường (Topological Pathfinder)
- Viết thuật toán Duyệt đồ thị có hướng (Directed Acyclic Graph - DAG) dựa trên file `[Mã_Môn_Học].json`.
- Nhiệm vụ: Tìm tất cả các đường đi dẫn đến một Khái niệm mục tiêu.
- Lọc ra các Node trên đường đi có `mastery_score < 50`.
- Sắp xếp (Topological Sort) để trả về đúng 1 Node gốc rễ (Root cause) mà sinh viên đang bị hổng kiến thức nhất, đánh dấu nó là "Next Optimal Step".

### Task 10.3: Logic Trigger Chủ động (Proactive Omni-Drawer)
- Viết hệ thống Rule-based (Dựa trên luật) để tự động kích hoạt Omni-Drawer trượt ra từ cạnh màn hình:
  - **Rule 1 (Fatigue):** Nếu `current_fatigue > 85%` VÀ vừa làm sai Quiz -> Popup: *"Có vẻ bạn đang khá mệt, hệ số hấp thụ kiến thức đang giảm. Đi uống ly nước 5 phút nhé?"*
  - **Rule 2 (Pathfinder):** Khi user login vào môn học -> Popup: *"Chào mừng quay lại! Để làm chủ khái niệm Y, bạn cần hoàn thành khái niệm X trước. Bắt đầu ngay nhé?"*
  - **Rule 3 (SRS Due):** Lấy từ Task 9.4 (Sprint 09) để nhắc nhở ôn bài.

### Task 10.4: Contextual Prompting (Cá nhân hóa Giọng điệu AI)
- Cập nhật hàm gọi Gemini API. Bơm toàn bộ các biến số vào Prompt hệ thống:
  ```json
  {
    "user_state": {
       "fatigue": 85,
       "mastery_focus": "Machine Learning",
       "bloom_level": 2
    }
  }
  ```
- Prompt: *"Bạn là một gia sư thấu cảm. Sinh viên đang rất mệt (Fatigue 85%) và chỉ hiểu bài ở mức cơ bản (Bloom 2). Hãy giải thích khái niệm này một cách cực kỳ ngắn gọn, dùng phép ẩn dụ hài hước để giải tỏa căng thẳng."*

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Tính năng Timer hoạt động ngầm. Mở app để đó tương tác 45 phút, `current_fatigue` tăng dần và Omni-drawer tự động trượt ra nhắc nghỉ ngơi.
- [ ] Bấm nút "Học gì tiếp theo", Camera 3D tự động bay thẳng tới Node tiên quyết đang bị yếu nhất và Drawer hiện ra bài giảng của Node đó.
- [ ] Câu văn do AI sinh ra thay đổi giọng điệu rõ rệt (dài/ngắn/nghiêm túc/hài hước) dựa vào thanh Fatigue.

## 4. Risk & Dependencies
- **Rủi ro 1 - Hiệu ứng Clippy (Phiền nhiễu):** Nếu AI tự động bung ra quá nhiều lần sẽ gây ức chế, làm gián đoạn luồng suy nghĩ của người học.
- **Giải pháp:** Cài đặt biến `cooldown_timer`. AI chủ động chỉ được phép xuất hiện **tối đa 1 lần mỗi 30 phút**. Bổ sung thêm nút Toggle (Bật/Tắt chế độ Gia sư chủ động) trong phần Cài đặt.
- **Phụ thuộc:** Yêu cầu Cây tri thức 3D (Sprint 5) và SRS (Sprint 9) hoạt động ổn định.

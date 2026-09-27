# Lý thuyết Chuyên sâu - Phần 3: Hệ thống Tương tác AI Tutor theo Thang Bloom

AI Tutor trong hệ thống Cây Tri Thức không phải là một mô hình ngôn ngữ tĩnh hay một Chatbot hỏi-đáp thông thường. Nó được thiết kế như một **Hệ thống Tác tử Nhận thức Ngữ cảnh (Context-Aware Agent System)**. Tại mỗi Node, AI sẽ đọc Vector Trạng thái của người học và tự động chuyển đổi "Vai diễn sư phạm" (Pedagogical Persona) để phù hợp với bậc Bloom mục tiêu.

---

## 3.1. Mô hình AI Nhận thức Ngữ cảnh (Context-Aware AI Model)

Mỗi khi người học mở một node, AI Tutor sẽ được khởi tạo với một System Prompt được lắp ghép động (Dynamically Assembled) từ 3 tham số:
1. **Nội dung Node ($C_v$):** Dữ liệu kiến thức thô.
2. **Lịch sử Người học ($H_u$):** Điểm số hiện tại, lịch sử sai lầm.
3. **Bậc Bloom Mục tiêu ($B_{target}$):** Tham số cốt lõi quyết định hành vi.

Việc tiêm $B_{target}$ vào prompt ép AI từ bỏ thói quen "giải đáp hộ" (vốn là bản năng của LLM) để trở thành một người thầy thực thụ.

---

## 3.2. Ánh xạ Vai diễn Sư phạm (Pedagogical Persona Mapping)

### Bậc 1 & 2: Ghi nhớ và Thấu hiểu (Remember & Understand)
- **Vai diễn của AI:** `Người Kiểm Tra Trực Tiếp (The Examiner)`
- **Chiến lược:** Ở tầng này, mục tiêu là chuyển đổi dữ liệu từ Trí nhớ làm việc (Working Memory) sang Trí nhớ ngắn hạn (Short-term Memory). Sự mơ hồ (Ambiguity) là kẻ thù.
- **Cách AI hoạt động:**
  - Sinh ra các dạng bài tập xác định (Deterministic) như MCQ, Flashcard, Matching.
  - Xây dựng các "Distractors" (Đáp án nhiễu) dựa trên những lỗi sai phổ biến nhất (Common Misconceptions) sinh ra từ lịch sử học tập.
- **Cơ chế Feedback:** Trực diện và ngay lập tức. Nếu sai, AI cung cấp câu trả lời đúng và giải thích ngắn gọn bằng 1-2 câu. Đánh giá tính đúng/sai dựa trên thuật toán Semantic Similarity với ngưỡng tin cậy cao.

### Bậc 3 & 4: Áp dụng và Phân tích (Apply & Analyze)
- **Vai diễn của AI:** `Người Hướng Dẫn Socratic (The Socratic Guide)`
- **Chiến lược:** Chuyển từ "Biết gì" (What) sang "Dùng thế nào" (How) và "Tại sao" (Why).
- **Cách AI hoạt động:**
  - AI khởi tạo một bối cảnh (Scenario/Case Study) chứa các biến số thực tế và yêu cầu người học vận dụng kiến thức để giải quyết.
  - **Vòng lặp Socratic (Socratic Loop):** Đây là thuật toán cốt lõi. Nếu người học trả lời sai, AI bị chặn (hard-coded) không được phép cung cấp đáp án. Thay vào đó, AI phải phân tích câu trả lời của người học, tìm ra lỗ hổng logic, và phản hồi bằng một *Câu hỏi gợi mở*.
  - *Ví dụ:* Nếu học viên áp dụng sai công thức, AI sẽ hỏi: *"Nếu biến X tăng gấp đôi thì theo công thức của bạn, Y sẽ thế nào? Liệu điều đó có hợp lý trong thực tế không?"* Vòng lặp này ép não bộ học viên phải tự tái cấu trúc mạng nơ-ron (Neuroplasticity).

### Bậc 5 & Bậc 6: Đánh giá và Sáng tạo (Evaluate & Create)
- **Vai diễn của AI:** `Luật Sư Của Quỷ (Devil's Advocate) & Đồng Ban Giám Khảo (Co-Evaluator)`
- **Chiến lược:** Đẩy người học ra khỏi vùng an toàn, ép họ phải bảo vệ quan điểm và tổng hợp tri thức để tạo ra cái mới.
- **Cách AI hoạt động:**
  - **Tranh biện (Debate Mode - Bậc 5):** AI cố tình đưa ra một luận điểm sai lầm nhưng được ngụy trang bằng các lập luận rất logic. Nhiệm vụ của người học là "bắt bẻ" AI. Nếu người học đuối lý, AI sẽ hạ cấp độ phức tạp của lập luận để mớm lời.
  - **Thiết kế (Design Mode - Bậc 6):** Người học phải nộp một dự án/kế hoạch mini. AI sẽ rà soát bản thiết kế này, chạy các bài test tưởng tượng (Edge-case testing) và phản hồi lại những lỗ hổng tiềm ẩn. Quá trình này mô phỏng môi trường làm việc thực tế, nơi kiến thức được nhào nặn thành sản phẩm.

---

## 3.3. Tích hợp Vòng lặp Micro-Feedback (Integration Loop)

Sự tương tác của AI Tutor không diễn ra trong không gian biệt lập mà được nối thẳng vào các thuật toán Toán học ở Phần 2. Mọi đoạn Text mà AI phản hồi đều đi kèm với một JSON payload ngầm:

1. **Gọi API Ebbinghaus:** Tính toán độ phức tạp của câu trả lời người học để cập nhật biến Performance ($P$), từ đó thay đổi Cường độ trí nhớ ($S_{new}$) ngay lập tức.
2. **Gọi API XP Engine:** Kích hoạt trigger cộng/trừ XP, hiển thị các hiệu ứng Gamification hạt (particle effects) như lửa (combo) hay rung lắc màn hình (khi sai) để neo giữ cảm xúc của học viên vào nền tảng.

Tóm lại, thông qua kiến trúc AI Context-Aware phân tầng theo Bloom, Knowledge Tree không chỉ dừng lại ở một công cụ quản lý nội dung học (LMS) mà đã tiến hóa thành một **Hệ sinh thái Gia sư Tư nhân Kỹ thuật số (Digital Private Tutoring Ecosystem)** có khả năng thấu hiểu và thích ứng vô hạn.

# Sprint 7: Đánh giá Động - Máy Sinh Câu Hỏi AI (Auto-Quiz Generator)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Chuyển đổi từ việc "Hấp thụ kiến thức" sang "Kiểm tra kiến thức". Dựa trên các Khái niệm (Nodes) trong Cây tri thức và tệp Vector DB (FAISS), hệ thống sử dụng LLM để tự động sinh ra các bài kiểm tra (Trắc nghiệm, Điền khuyết) chuẩn xác theo đúng tài liệu người dùng đã upload, giúp họ tự đánh giá năng lực mà không cần giáo viên.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, khi tôi thấy một Node kiến thức đang ở trạng thái "Màu Đỏ" (Chưa nắm vững), tôi muốn bấm nút "Luyện tập" để làm 3-5 câu trắc nghiệm nhanh về khái niệm đó.
- **US2:** Là một người học, tôi muốn các câu hỏi trắc nghiệm phải bám sát chính xác cuốn sách tôi đã tải lên, chứ không phải do AI lấy từ kiến thức chung trên mạng (tránh tình trạng sai lệch định nghĩa).
- **US3:** Là một người học, sau khi tôi chọn đáp án, tôi muốn hệ thống giải thích rõ tại sao đúng/sai và chỉ ra đoạn văn bản (trang số mấy) trong sách chứng minh điều đó.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 7.1: Luồng truy vấn RAG cho Câu hỏi (Targeted RAG Retrieval)
- Khi user bấm nút `Tạo Quiz` tại một Node (VD: Khái niệm "Machine Learning").
- Backend gọi Local FAISS (đã làm ở Sprint 3) để thực hiện `Similarity Search` với từ khóa là Tên Khái niệm + Mô tả của khái niệm đó.
- Lấy ra Top 5 chunks ngữ cảnh tốt nhất (Kèm số trang).

### Task 7.2: LLM Prompt Engineering cho Trắc nghiệm (Structured JSON)
- Cấu hình `Gemini 1.5 Pro` với `response_mime_type="application/json"`.
- Viết System Prompt chuyên biệt:
  *Ngữ cảnh: [5 Chunks từ sách]*
  *Nhiệm vụ: Bạn là chuyên gia khảo thí. Hãy tạo 3 câu trắc nghiệm dựa TỐI ĐA vào ngữ cảnh trên để kiểm tra người học về khái niệm X.*
- Ép LLM trả về cấu trúc:
  ```json
  {
    "questions": [
      {
        "id": "q1",
        "type": "multiple_choice",
        "question_text": "Học máy (Machine Learning) là gì theo tài liệu trên?",
        "options": ["A", "B", "C", "D"],
        "correct_answer_index": 1,
        "explanation": "Theo trang 45, tác giả định nghĩa Học máy là...",
        "source_page": 45
      }
    ]
  }
  ```

### Task 7.3: Giao diện Làm bài & Đánh giá (Quiz UI)
- Tạo Modal/Card hiển thị câu hỏi từng câu một (Flashcard style).
- Không cho phép xem trước kết quả.
- Khi user chọn đáp án và bấm "Nộp":
  - Hiển thị hiệu ứng Xanh (Đúng) / Đỏ (Sai).
  - Bung ô `explanation` (Giải thích chi tiết) và `source_page` để người học lật sách ra xem lại nếu cần.
- **Quan trọng:** Tính toán tỷ lệ đúng (VD: Đúng 2/3 câu) và lưu tạm vào biến `temp_score` chờ xử lý ở Sprint sau (Sprint 8: Cập nhật Mastery/Bloom).

### Task 7.4: Xử lý Lỗi & Nút "Tái sinh" (Regenerate)
- **Vấn đề AI Ảo giác (Hallucination):** Dù dùng RAG, đôi khi AI vẫn sinh câu hỏi quá dễ, bị trùng lặp, hoặc cả 4 đáp án đều sai.
- Thêm nút "Sinh lại câu hỏi" (Regenerate) gọi lại API với tham số `temperature` cao hơn một chút (0.4 -> 0.7) để tạo bộ câu hỏi mới.
- Thêm nút "Báo lỗi" (Report) để người dùng tự đánh dấu câu hỏi bị lỗi (nếu cần thu thập dữ liệu cải thiện Prompt).

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Tính năng RAG hoạt động mượt: Trích xuất đúng đoạn văn bản trong PDF liên quan đến Node được click.
- [ ] Gemini sinh ra JSON hợp lệ chứa 3-5 câu trắc nghiệm có đủ 4 lựa chọn, đáp án đúng và giải thích.
- [ ] Giao diện làm bài trực quan, phản hồi màu sắc đúng/sai ngay lập tức sau khi bấm chọn.
- [ ] Giải thích của AI có đính kèm số trang trích dẫn chính xác từ tài liệu gốc.

## 4. Risk & Dependencies
- **Rủi ro 1 - Chất lượng tài liệu kém:** Nếu người dùng tải lên slide bài giảng chỉ gạch đầu dòng ngắn gọn (thiếu ngữ cảnh ngữ nghĩa), LLM sẽ không đủ thông tin để sinh câu hỏi trắc nghiệm chất lượng.
- **Giải pháp:** Trong Prompt, cần xử lý trường hợp không đủ thông tin: Nếu không đủ dữ kiện, AI sẽ trả về JSON chứa mảng `questions` rỗng, kèm thông báo `error: "Tài liệu quá ngắn, không thể sinh câu hỏi"`. Giao diện sẽ hiển thị thân thiện yêu cầu người dùng tự đọc thay vì ép AI "bịa" ra.
- **Phụ thuộc:** Bắt buộc hệ thống Local RAG (Sprint 3) và Cây Tri thức (Sprint 4,5) đã chạy trơn tru.

# Sprint 23: Dò tìm Kiến thức Cá nhân hóa bằng Toán học (PKT Engine & Bayesian)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Nâng cấp toàn diện Thuật toán Chấm điểm (Sprint 8) từ dạng "Trung bình cộng" đơn giản lên một Động cơ Dò tìm Kiến thức Cá nhân hóa (Personalized Knowledge Tracing - `pkt_engine.py`). Áp dụng mô hình toán học chuẩn mực của ngành EdTech là **Bayesian Knowledge Tracing (BKT)** để xác định chính xác xác suất thực sự một sinh viên đã nắm vững khái niệm, loại bỏ yếu tố "Đoán mò" (Guess) hoặc "Sẩy chân" (Slip).

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, đôi khi tôi đánh lụi (đoán mò) trúng đáp án trắc nghiệm. Tôi không muốn hệ thống dễ dãi lập tức chuyển Node đó thành Màu Xanh (Mastery 100%), vì thực chất tôi chưa hiểu bài.
- **US2:** Là một người học giỏi, đôi khi tôi làm sai một câu chỉ vì sơ ý đọc nhầm đề (Sẩy chân/Slip). Tôi không muốn điểm Mastery của tôi bị tụt thê thảm chỉ vì một lỗi nhỏ này.
- **US3:** Là một hệ thống, khi người dùng ghép nối môn Toán và môn Lý (Graph Bridge), tôi muốn "chuyển giao năng lực". Nếu sinh viên đã giỏi "Vector" bên Toán, thì hệ thống mặc định cho "Vector" bên Lý khởi điểm cao hơn bình thường.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 23.1: Tích hợp Mô hình Toán học BKT (pkt_engine.py)
- Khởi tạo và thiết kế thuật toán trong `pkt_engine.py`.
- Định nghĩa 4 tham số cốt lõi cho mỗi Node trong file JSON:
  - $P(L_0)$: Xác suất ban đầu biết kiến thức (Mặc định 10-20%).
  - $P(T)$: Xác suất chuyển đổi (Học được sau khi làm bài).
  - $P(G)$: Xác suất đoán mò (Guess). Thường để ở mức 25% nếu quiz có 4 đáp án.
  - $P(S)$: Xác suất sẩy chân (Slip). Thường để ở mức 10%.
- Ẩn điểm `mastery_score` tuyến tính cũ, thay bằng biến `p_learned` (Xác suất thực sự nắm vững bài).

### Task 23.2: Thuật toán Cập nhật Trạng thái Ẩn (Hidden State Updater)
- Mỗi khi người dùng làm xong 1 bài Quiz (Sprint 7), truyền kết quả (Right/Wrong) vào `pkt_engine.py`.
- Viết công thức Định lý Bayes để cập nhật:
  - Nếu làm đúng: Tính xác suất người học thực sự biết bài hay chỉ đang đoán mò.
  - Nếu làm sai: Tính xác suất người học chưa biết bài hay chỉ đang sẩy chân.
- **Tác động UI:** Màu sắc của Đồ thị 3D giờ đây phản ánh **Xác suất BKT**. Một Node chỉ thực sự chuyển sang màu Xanh khi $P(L_n) > 0.95$. Nó đòi hỏi người dùng phải trả lời đúng liên tiếp nhiều lần để chứng minh sự ổn định.

### Task 23.3: Nâng cấp Công cụ Nối Đồ thị (patch_bridge_v3.py)
- Triển khai logic Transfer Learning (Học chuyển giao) trong `patch_bridge_v3.py`.
- Khi dùng AI tìm ra 2 Node giao thoa giữa Môn A và Môn B.
- Hệ thống sẽ lấy biến $P(L_n)$ của Node gốc bên Môn A để gán vào làm $P(L_0)$ khởi điểm cho Node bên Môn B. Nhờ đó, sinh viên học môn mới sẽ không bị bắt ép làm lại từ đầu những bài kiểm tra trắc nghiệm quá cơ bản của các kiến thức họ đã Master ở môn cũ.

### Task 23.4: Tracker Chống Đoán Mò (Anti-Guessing Timer)
- Tích hợp với `behavior_tracker.py` (Sprint 19).
- Nếu sinh viên nộp đáp án trắc nghiệm trong thời gian `< 2 giây` sau khi câu hỏi hiện ra. Hệ thống ngầm định hành vi này là "Đánh lụi".
- Đẩy tham số $P(G)$ (Xác suất đoán mò) lên 90% cho câu hỏi đó. Lúc này, dù sinh viên có chọn đúng, Điểm Mastery $P(L_n)$ trên biểu đồ cũng gần như không nhúc nhích.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Mở App, làm đúng 1 câu trắc nghiệm cực nhanh (< 2 giây). Điểm Mastery chỉ tăng 1% do hệ thống đoán là đánh lụi.
- [ ] Làm sai 1 câu sau khi đã Master 100%. Điểm Mastery chỉ tụt về 92% (Hệ thống tính là Sẩy chân - Slip) thay vì tụt về 50% như thuật toán cũ.
- [ ] Chạy lệnh `patch_bridge_v3` nối môn Toán và Lý. Khái niệm "Đạo hàm" bên Lý tự động nhận màu Vàng (đã có xác suất hiểu bài) ngay khi mới Import, nhờ thừa hưởng từ môn Toán.

## 4. Risk & Dependencies
- **Rủi ro 1 - Thông số (Parameters) BKT không chính xác:** Nếu cài đặt $P(S)$ và $P(G)$ tĩnh (Static) cho tất cả các bài tập, thuật toán sẽ bị cứng nhắc. Một câu hỏi siêu khó có xác suất đoán mò khác với câu hỏi dễ.
- **Giải pháp:** Sử dụng chính LLM (Gemini) để ước lượng $P(G)$ và $P(S)$ trong lúc sinh ra câu hỏi trắc nghiệm (Sprint 7). Prompt: *"Bạn hãy đánh giá độ khó của câu hỏi này, và cho tôi biết xác suất 1 sinh viên giỏi có thể làm sai vì bất cẩn là bao nhiêu %?"*.

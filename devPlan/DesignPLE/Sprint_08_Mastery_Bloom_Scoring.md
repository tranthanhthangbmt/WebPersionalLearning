# Sprint 8: Thuật toán Chấm Điểm Năng Lực (Mastery & Bloom Scoring)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Xây dựng não bộ đánh giá năng lực cốt lõi của hệ thống PLE. Khi người học hoàn thành bài Quiz (từ Sprint 7), hệ thống sẽ tính toán lại mức độ Thành thạo (Mastery) và Bậc nhận thức (Bloom Level) cho khái niệm đó bằng các công thức toán học, đồng thời cộng điểm kinh nghiệm (XP) thông qua Gamification Engine, cập nhật tất cả vào Single JSON và đẩy lên Drive.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, sau khi tôi làm đúng toàn bộ bài trắc nghiệm, tôi muốn Khái niệm đó trên Cây tri thức 3D lập tức chuyển từ Màu Đỏ sang Màu Xanh để tôi thấy được sự tiến bộ.
- **US2:** Là một người học, tôi muốn hệ thống đánh giá xem tôi chỉ mới "Thuộc lòng" (Remember) hay đã có khả năng "Áp dụng/Phân tích" (Apply/Analyze) kiến thức đó, thay vì chỉ chấm điểm 10/10 chung chung.
- **US3:** Là một người học, tôi muốn được thưởng Điểm kinh nghiệm (XP) và thăng cấp (Level up) khi tôi nắm vững một kiến thức khó, tạo động lực học tập.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 8.1: Nâng cấp AI sinh Quiz (Bloom-Targeted Generation)
- Nâng cấp Prompt ở Sprint 07. Thay vì sinh câu hỏi ngẫu nhiên, hệ thống sẽ truyền `current_bloom_level` của Node vào Prompt.
- Yêu cầu Gemini sinh câu hỏi ở **mức độ Bloom + 1**.
  - *Ví dụ:* Nếu Node đang ở Bloom 1 (Ghi nhớ), AI phải sinh câu hỏi Bloom 2 (Thông hiểu).
- JSON output của AI phải trả về thêm trường `"bloom_tag": 2` cho mỗi câu hỏi.

### Task 8.2: Xây dựng Thuật toán Mastery (Độ thành thạo)
- Viết hàm `calculate_new_mastery(old_mastery, correct_count, total_questions)` trong Local State.
- **Công thức đề xuất:**
  - `Base_Reward` = `(correct_count / total_questions) * 20` (Tối đa +20% mỗi lần test).
  - `Penalty` = Nếu sai > 50%, trừ 5-10% Mastery.
  - `New_Mastery = clamp(old_mastery + Base_Reward - Penalty, 0, 100)` (Giới hạn trong khoảng 0-100).
- Nếu `New_Mastery >= 100`, khóa tính năng cày điểm liên tục (cooldown) để chống spam.

### Task 8.3: Thuật toán Xét duyệt Bloom Taxonomy
- Viết logic thăng cấp Bloom:
  - Nếu người dùng vượt qua (đúng >80%) bài test được tag ở Bloom N, thì cập nhật `bloom_level = N` cho Node đó.
  - Giới hạn Bloom Level từ 1 đến 6. Mức càng cao, câu hỏi AI sinh ra càng là dạng tình huống phức tạp (Analyze/Evaluate).

### Task 8.4: Tích hợp Gamification (XP Engine)
- Tích hợp module `xp_engine.py` (hiện có trong hệ thống).
- Khi hàm `calculate_new_mastery` chạy xong:
  - Nếu Node lần đầu vượt mốc 50% Mastery: Gọi API/Hàm `add_xp(50)`.
  - Nếu Node đạt 100% Mastery: Gọi API/Hàm `add_xp(150)` kèm thông báo "Mastery Achieved!".
- Cập nhật số điểm này vào file `profile.json` của người dùng.

### Task 8.5: Cập nhật UI 3D và Đồng bộ Drive
- Ghi đè `mastery_score` và `bloom_level` mới vào `[Mã_Môn_Học].json`.
- Engine 3D (Sprint 5) sẽ tự động lắng nghe sự thay đổi của State và **chuyển màu Node lập tức (Ví dụ: Đỏ -> Vàng)**.
- Thuật toán Auto-Sync (Sprint 2) gom chung cả `profile.json` (XP mới) và `[Mã_Môn_Học].json` đẩy lên Google Drive cùng một lúc.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Hoàn thành 1 bài Quiz đạt 3/3 câu đúng: Node trên đồ thị 3D đổi màu ngay lập tức mà không cần F5 trình duyệt.
- [ ] Thông báo cộng XP hiện lên ở góc màn hình.
- [ ] Mở file `[Mã_Môn_Học].json` trên Google Drive kiểm tra, thấy `mastery_score` đã tăng (VD: từ 0 lên 20).
- [ ] Cố tình làm sai liên tục: `mastery_score` bị trừ dần nhưng không bao giờ rớt xuống dưới 0.

## 4. Risk & Dependencies
- **Rủi ro 1 - Lạm phát điểm (Score Inflation):** Người dùng có thể spam bấm "Tạo Quiz" làm đi làm lại một khái niệm cực dễ để cày XP.
- **Giải pháp:** Áp dụng hệ số giảm dần (Diminishing returns). Nếu làm quiz trong cùng 1 ngày trên cùng 1 Node, lượng XP và Mastery nhận được sẽ chia đôi ở lần 2, bằng 0 ở lần 3. Phải đợi sang ngày hôm sau (Kết nối chặt chẽ với thuật toán Spaced Repetition ở Sprint 09).
- **Phụ thuộc:** Yêu cầu hoàn thiện toàn bộ luồng sinh JSON của Sprint 07.

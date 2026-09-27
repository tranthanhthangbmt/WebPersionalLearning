# Lý thuyết Cây Tri Thức (Knowledge Tree Theory)

Tài liệu này mô tả chi tiết về lý thuyết nền tảng, cấu trúc toán học, và phương pháp tương tác sư phạm của hệ thống **Cây Tri Thức (Knowledge Tree)**. Hệ thống được thiết kế để cá nhân hóa lộ trình học tập, tối ưu hóa việc duy trì trí nhớ và kích thích động lực học tập thông qua AI Tutor và Gamification.

---

## 1. Cấu trúc Cây Tri Thức (Knowledge Tree Structure)

Cây Tri Thức là một đồ thị có hướng (Directed Graph) biểu diễn sự phụ thuộc lẫn nhau của các đơn vị kiến thức. Cấu trúc này không chỉ cho phép tổ chức nội dung học tập một cách logic mà còn giúp hệ thống AI định vị chính xác vị trí và trạng thái của người học.

### Kiến trúc phân tầng
- **Macro Nodes (Chương/Chủ đề lớn):** Đại diện cho các cột mốc lớn trong khóa học. Chúng mang tính tổng quan và chứa các khái niệm (Concepts) bao trùm.
- **Micro Nodes (Đơn vị kiến thức/Bài học):** Là các hạt nhân nhỏ nhất của cây. Mỗi Micro Node đại diện cho một mảng kiến thức cụ thể cần nắm vững.
- **Assess Nodes (Nút đánh giá):** Là các điểm chốt (checkpoint) định kỳ để đánh giá tổng hợp khả năng vận dụng nhiều Micro Nodes trước khi chuyển sang Macro Node mới.

### Thuộc tính của Node
Mỗi node trong cây sở hữu các thuộc tính cơ bản định hình cách AI Tutor vận hành:
- **`alpha_base` (Độ khó sinh học/nhận thức):** Một chỉ số từ 10 (rất dễ) đến 30+ (rất khó) đại diện cho độ phức tạp nội tại của kiến thức.
- **`position_ratio` (Vị trí tương đối):** Tỉ lệ từ 0.0 (mở đầu) đến 1.0 (kết thúc) cho biết vị trí của node trong toàn bộ lộ trình khóa học.
- **Bloom Profile:** Một hồ sơ nhận thức mục tiêu (Target Bloom Levels) dựa trên Thang đo Bloom (Anderson & Krathwohl, 2001), trải dài từ Bậc 1 (Ghi nhớ) đến Bậc 6 (Sáng tạo).

---

## 2. Lý thuyết Toán học và Thuật toán (Mathematical Theory)

Hệ thống sử dụng các thuật toán định lượng để số hóa quá trình nhận thức của con người, biến việc học thành các con số có thể tính toán, theo dõi và tối ưu.

### 2.1. Hiệu chuẩn Thang Bloom (Bloom Calibration)
Thuật toán tự động ánh xạ mức độ khó của kiến thức vào các bậc Bloom tương ứng:
- Nếu `alpha_base` $\le 12$: Chỉ yêu cầu Bậc 1 (Ghi nhớ), Bậc 2 (Thấu hiểu).
- Nếu $12 <$ `alpha_base` $\le 18$: Yêu cầu Bậc 1, 2, 3 (Áp dụng).
- Nếu $18 <$ `alpha_base` $\le 24$: Yêu cầu Bậc 2, 3, 4 (Phân tích).
- Nếu `alpha_base` $> 24$: Yêu cầu mức độ cao Bậc 3, 4, 5 (Đánh giá).
- **Thưởng tiến trình:** Nếu `position_ratio` $\ge 0.85$ (cuối khóa học), hệ thống tự động đẩy thêm một bậc Bloom cao hơn (có thể lên tới Bậc 6 - Sáng tạo) nhằm thử thách năng lực tổng hợp của người học.

### 2.2. Thuật toán Chấm điểm Bloom (Bloom Scoring & Progressive Unlock)
Điểm số tổng quát (Overall Bloom Score) dao động từ $0.0$ đến $6.0$ được tính bằng trung bình có trọng số:

$$ Overall = \frac{\sum (Level \times Score_{level} \times W_{level})}{\sum W_{level}} $$

Trong đó:
- $Score_{level}$: Độ chính xác (Tỷ lệ phần trăm) của người học ở bậc đó.
- $W_{level}$: Trọng số của bậc Bloom (L1 = 1.0, L2 = 1.2, ..., L6 = 2.0).

**Logic Mở khóa Tiến trình (Progressive Unlock):**
Người học không được phép nhảy cóc. Để mở khóa bài tập ở bậc $n$, người học phải:
1. Đạt độ chính xác ở bậc $n-1$ vượt qua ngưỡng (Threshold) (Ví dụ: 70% cho L1).
2. Hoàn thành ít nhất $2$ loại hình đánh giá khác nhau (ví dụ: MCQ và Flashcard) ở bậc $n-1$ để chống học vẹt.

### 2.3. Đường cong lãng quên Ebbinghaus (Ebbinghaus Forgetting Curve)
Hệ thống tính toán sự suy giảm trí nhớ theo thời gian để nhắc nhở ôn tập kịp thời. Độ duy trì trí nhớ $R$ được tính bằng:

$$ R = e^{-t/S} $$

- **$t$**: Thời gian trôi qua (tính bằng giờ) kể từ lần ôn tập cuối cùng.
- **$S$**: Cường độ trí nhớ (Memory Strength). Bắt đầu với $S = 2.0$ (giờ).

**Cập nhật Cường độ $S$ sau ôn tập:**
- Nếu Performance $\ge 70\%$: $S_{new} = S_{old} \times 1.5$ (Giới hạn tối đa 30 ngày - 720 giờ).
- Nếu $40\% \le$ Performance $< 70\%$: $S_{new} = S_{old} \times 1.1$.
- Nếu Performance $< 40\%$: $S_{new} = S_{old} \times 0.7$ (Trí nhớ giảm mạnh, cần ôn tập gấp).

### 2.4. Động lực học & Gamification (XP Engine)
Gamification giữ người học trong trạng thái dòng chảy (Flow State) thông qua cơ chế khen thưởng và hình phạt nhẹ:
- **XP Gained = Base XP $\times$ Streak Multiplier**.
- **Base XP:** Tùy thuộc vào hành động (Ví dụ: Câu trả lời đúng = 10 XP, Hoàn thành Socratic = 25 XP, Daily Login = 20 XP).
- **Streak Multiplier:** Tăng theo số ngày duy trì liên tục. (3 ngày = 1.2x, 7 ngày = 1.5x, 30 ngày = 2.0x).
- **Timed Challenge (Đua Tốc Độ):** Công thức điểm kết hợp thời gian và độ chuẩn xác. 
  - Trả lời đúng: $+10$ điểm $\times$ Hệ số Combo. $+3$ giây.
  - Trả lời sai: $-5$ điểm, cắt Combo. $-5$ giây.
  - Điều này ép người học phải phản xạ tự nhiên thay vì suy nghĩ quá lâu, củng cố rễ (Retrieval Strength) của trí nhớ.

---

## 3. Tương tác AI Tutor theo từng Thang Bloom

AI Tutor trong hệ thống là một mô hình Contextual AI, tức là nó biết chính xác người học đang ở Node nào, mục tiêu bài học là gì, và mức Bloom hiện tại của họ là bao nhiêu. Từ đó, AI điều chỉnh chiến lược sư phạm (Pedagogical Strategy) cho phù hợp.

### Bậc 1 & Bậc 2: Ghi nhớ (Remember) và Thấu hiểu (Understand)
- **Mục tiêu:** Xây dựng Foundation. Chuyển thông tin từ Working Memory sang Short-term Memory.
- **Hành vi của AI:** Đóng vai trò **Người kiểm tra (Examiner)**.
- **Phương pháp:** 
  - MCQ (Multiple Choice Questions) tập trung vào định nghĩa.
  - Flashcard và Fill-in-the-blank (Điền khuyết).
  - Yêu cầu người học tự tóm tắt lại khái niệm bằng ngôn từ của họ. AI sẽ chấm điểm dựa trên semantic similarity (độ tương đồng ngữ nghĩa).

### Bậc 3 & Bậc 4: Áp dụng (Apply) và Phân tích (Analyze)
- **Mục tiêu:** Xây dựng khả năng tư duy logic và giải quyết vấn đề.
- **Hành vi của AI:** Đóng vai trò **Người hướng dẫn Socratic (Socratic Guide)**.
- **Phương pháp:**
  - Cung cấp Case Study hoặc Scenario-based MCQ (Đưa ra một tình huống thực tế và hỏi cách xử lý).
  - Nếu người học chọn sai, AI sẽ *không* đưa ra câu trả lời ngay lập tức. Thay vào đó, AI dùng phương pháp Socratic để đặt các câu hỏi gợi mở, bóc tách vấn đề, giúp học viên tự nhận ra điểm sai logic trong suy nghĩ của mình.

### Bậc 5 & Bậc 6: Đánh giá (Evaluate) và Sáng tạo (Create)
- **Mục tiêu:** Phát triển tư duy phản biện (Critical Thinking) và khả năng tổng hợp tạo ra tri thức mới.
- **Hành vi của AI:** Đóng vai trò **Người phản biện (Devil's Advocate) / Đối tác thiết kế**.
- **Phương pháp:**
  - **Tranh biện (Debate):** AI cố tình đưa ra một quan điểm trái chiều hoặc sai lầm có chủ đích, yêu cầu người học tìm lỗi sai và bảo vệ lập luận của mình.
  - **Dự án thiết kế (Design Task):** Yêu cầu người học tự đề xuất một giải pháp hoặc quy trình mới. AI sẽ đóng vai trò ban giám khảo để phê bình (critique), đưa ra các lỗ hổng trong bản thiết kế để người học hoàn thiện.

---

## Tổng Kết
Cây Tri Thức không chỉ là một cấu trúc lưu trữ nội dung. Khi kết hợp với Thuật toán Bloom, mô hình Ebbinghaus và sức mạnh của AI Tutor, nó trở thành một "sinh vật sống", có khả năng tự động điều chỉnh độ khó, nhận diện điểm mù của học viên và tối ưu hóa thời điểm ôn tập nhằm mang lại hiệu quả giáo dục cao nhất với thời gian ngắn nhất.

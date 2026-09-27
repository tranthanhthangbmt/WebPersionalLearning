# Lý thuyết Chuyên sâu - Phần 2: Thuật toán Bloom, Đánh giá và Mô hình Trí nhớ Ebbinghaus

Trong hệ thống Knowledge Tree, sự tương tác của học viên không chỉ là các thao tác nhấp chuột đơn thuần mà là một tập hợp các chuỗi dữ liệu (Data Streams). Hệ thống biến các luồng dữ liệu này thành các đại lượng toán học để chạy ba động cơ cốt lõi: **Động cơ Hiệu chuẩn (Calibration Engine)**, **Động cơ Đánh giá (Scoring Engine)**, và **Động cơ Trí nhớ (Memory Engine)**.

---

## 2.1. Động cơ Hiệu chuẩn Bloom (Bloom Calibration Engine)

Động cơ này giải quyết bài toán: *Với một đơn vị kiến thức cụ thể, não bộ học viên cần vận dụng đến tầng nhận thức nào?*

**Hàm Hiệu chuẩn $B_{target}(\alpha, \rho)$:**
Gọi $\alpha$ là Độ khó sinh học (Cognitive Alpha Base) và $\rho$ là Vị trí tương đối (Position Ratio) của node. Hệ thống áp dụng chuỗi hàm điều kiện (Piecewise Function) sau để tìm tập hợp bậc Bloom mục tiêu $B_{base}$:

$$
B_{base}(\alpha) = 
\begin{cases} 
\{1, 2\} & \text{khi } \alpha \le 12 \\
\{1, 2, 3\} & \text{khi } 12 < \alpha \le 18 \\
\{2, 3, 4\} & \text{khi } 18 < \alpha \le 24 \\
\{3, 4, 5\} & \text{khi } \alpha > 24 
\end{cases}
$$

**Heuristic thưởng tiến trình (Positional Heuristic):**
Khi học viên tiến gần đến cuối khóa học ($\rho \ge 0.85$), hệ thống cho rằng họ đã tích lũy đủ các khái niệm đơn lẻ và cần phải kết nối chúng. Một hàm thưởng được áp dụng:

$$
B_{target} = 
\begin{cases} 
B_{base} \cup \{\min(6, \max(B_{base}) + 1)\} & \text{nếu } \rho \ge 0.85 \\
B_{base} & \text{nếu } \rho < 0.85 
\end{cases}
$$
*(Thuật toán này được ánh xạ 1:1 trong hàm `calibrate_bloom_from_alpha` tại file `bloom_taxonomy.py`)*

---

## 2.2. Động cơ Đánh giá và Mở khóa (Scoring & Progressive Unlock)

Sau khi $B_{target}$ được xác định, hệ thống theo dõi hiệu suất trả lời (Accuracy) tại từng bậc $i$. Gọi $s_i$ là độ chính xác tại bậc $i$ ($s_i = \frac{correct_i}{total_i}$).

### Phương trình tính điểm tổng Bloom (Overall Bloom Score)
Do các bậc cao của Bloom tốn nhiều năng lượng não bộ hơn, chúng mang trọng số $W_i$ cao hơn. Trọng số được tính theo hàm tuyến tính: $W_i = 1.0 + (i-1) \times 0.2$. Điểm tổng hợp được tính theo phương trình trung bình có trọng số:

$$ Overall\_Bloom = \frac{\sum_{i \in \text{attempted}} (i \times s_i \times W_i)}{\sum_{i \in \text{attempted}} W_i} $$

Phương trình này đảm bảo rằng: Dù học viên đạt 100% độ chính xác ở Bậc 1 (Ghi nhớ), điểm Overall của họ vẫn rất thấp so với việc đạt 60% độ chính xác ở Bậc 4 (Phân tích). Điểm tối đa giới hạn là 6.0.

### Cổng Logic Mở khóa Tiến trình (Progressive Unlock Gate)
Người học không thể truy cập một bậc Bloom cao nếu nền tảng chưa vững. Bậc Bloom $n$ được đánh giá là đã "Mở khóa" (True) thông qua biểu thức logic:

$$ Unlocked(n) \iff (n=1) \lor \Big[ \big( s_{n-1} \ge \tau_{n-1} \big) \land \big(|T_{n-1}| \ge 2 \big) \Big] $$

- $\tau_{n-1}$: Là ngưỡng Pass Threshold của bậc $n-1$ (Ví dụ: 0.70 cho Bậc 1, 0.60 cho Bậc 4).
- $|T_{n-1}|$: Số lượng loại hình bài tập khác nhau đã làm ở bậc $n-1$ (Ví dụ MCQ, Flashcard). Ràng buộc $|T_{n-1}| \ge 2$ ép người học không được "học vẹt" chỉ thông qua việc đánh lụi trắc nghiệm mà phải thực hành đa dạng.

---

## 2.3. Động cơ Trí nhớ Ebbinghaus (Memory Engine)

Để chống lại sự lãng quên tự nhiên của con người, hệ thống sử dụng biến thể số học của **Đường cong quên lãng Ebbinghaus (Ebbinghaus Forgetting Curve)**. Trạng thái trí nhớ tại một node được giám sát bởi Hệ số Duy trì $R(t)$ (Retention Factor).

### Phương trình Phân rã (Decay Equation)
$$ R(t, S) = e^{-\frac{t}{S}} $$

- **$t$**: Thời gian trôi qua kể từ lần học/ôn tập cuối (đơn vị: Giờ).
- **$S$**: Cường độ trí nhớ (Memory Strength). Trị số khởi tạo $S_0 = 2.0$. Giá trị $S$ càng lớn, đồ thị $R$ càng phẳng, người học càng lâu quên kiến thức.

**Ứng dụng vào Hệ thống:**
Mỗi khi hệ thống load trạng thái Bloom của người học, điểm số thực tế sẽ bị trừ hao tự động bởi hệ số $R$:
$$ \text{Decayed Score} = \text{Original Score} \times R(t, S) $$
Nếu $R$ tụt xuống quá thấp, thanh tiến trình của người học sẽ giảm, kích hoạt trạng thái báo động đỏ (cần phải ôn tập).

### Phương trình Cập nhật Cường độ (Strength Update Function)
Sau khi người học thực hiện Ôn tập (Review), độ chính xác của bài kiểm tra ($P$) sẽ được đưa vào hàm để cập nhật lại cường độ $S$. Điều này tương đương với thuật toán Spaced Repetition (SRS):

$$
S_{new} = 
\begin{cases} 
\min(720, S_{old} \times 1.5) & \text{khi } P \ge 0.7 \\
\max(1.0, S_{old} \times 1.1) & \text{khi } 0.4 \le P < 0.7 \\
\max(0.5, S_{old} \times 0.7) & \text{khi } P < 0.4 
\end{cases}
$$

**Phân tích thuật toán:**
- Nếu bạn trả lời đúng ($P \ge 0.7$), trí nhớ của bạn được gia cố mạnh mẽ (tăng gấp 1.5 lần thời gian chống lãng quên). Max giới hạn ở 720 giờ (30 ngày).
- Nếu bạn trả lời sai ($P < 0.4$), hệ thống đánh giá rằng cấu trúc nơ-ron liên kết kiến thức này đang sụp đổ, $S$ bị phạt giảm xuống (0.7x), vòng lặp ôn tập tiếp theo sẽ xuất hiện sớm hơn rất nhiều.

---

## 2.4. Động lực học (Gamification & XP Engine)

Hệ thống toán học Gamification dựa trên vòng lặp phản hồi (Feedback Loop) dương tính để tiết ra Dopamine cho người học:

$$ XP_{earned} = XP_{base}(\text{Action}) \times M(streak) $$

- $XP_{base}$: Biến thiên theo mức độ phức tạp của hành vi (Trả lời MCQ đúng = 10 XP; Giải quyết Socratic vấn đáp = 25 XP).
- $M(streak)$: Hàm bậc thang (Step function) tăng dần theo chuỗi ngày liên tiếp. Trọng số dao động từ $1.0$ (không có streak) đến $2.0$ (streak 30 ngày). Điều này phạt rất nặng hành vi bỏ dở học tập, vì khi rớt chuỗi, $M$ quay về 1.0, lượng XP cày cuốc mất đi một nửa lợi thế.

---
> *Đây là kết thúc Phần 2. Trong Phần 3 (cuối cùng), chúng ta sẽ phân tích lý thuyết tương tác hệ thống: AI Tutor đóng những "vai diễn" sư phạm nào để thực thi các chỉ số toán học cứng nhắc này thành những bài học cuốn hút.*

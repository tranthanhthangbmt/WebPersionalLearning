# Lý thuyết Chuyên sâu - Phần 1: Cấu trúc Đồ thị Tri thức (Knowledge Graph Structure)

Trong hệ thống WebPersonalLearning, "Cây Tri Thức" thực chất là một **Đồ thị có hướng không chu trình (DAG - Directed Acyclic Graph)**. Mô hình DAG cho phép biểu diễn các mối quan hệ đa tuyến tính (một bài học có thể yêu cầu nhiều bài học tiên quyết, và là nền tảng cho nhiều bài học tiếp theo).

---

## 1.1. Mô hình Toán học của Đồ thị (Mathematical Model)

Ký hiệu hệ thống tri thức là một đồ thị $G = (V, E)$, trong đó:
- **$V$ (Vertices)** là tập hợp tất cả các đơn vị tri thức (Nodes).
- **$E$ (Edges)** là tập hợp các mối quan hệ tiên quyết. Một cạnh có hướng $e = (u, v) \in E$ có nghĩa là node $u$ là điều kiện tiên quyết bắt buộc để mở khóa node $v$.

Vì quá trình học tập là quá trình tích lũy tiến lên phía trước, đồ thị này tuyệt đối không được có chu trình (Acyclic). Nếu $u \to \dots \to v$, thì không thể có đường đi từ $v \to u$.

### Phân rã Tập đỉnh (Vertex Partitioning)
Tập đỉnh $V$ được phân rã thành 3 tập hợp con rời rạc (disjoint sets):
$$V = V_{macro} \cup V_{micro} \cup V_{assess}$$

1. **$V_{macro}$ (Macro Nodes):**
   - Đóng vai trò là các tập hợp nhãn (Label Sets) hoặc các Hyper-nodes chứa các subgraph. 
   - Về mặt toán học, mỗi $v \in V_{macro}$ ánh xạ tới một đồ thị con $G' \subset G$. Nó biểu diễn một "Chương" hay "Mảng chủ đề".

2. **$V_{micro}$ (Micro Nodes):**
   - Là các lá (leaves) hoặc các điểm trung chuyển của đồ thị thực thi. 
   - Đây là nơi chứa nội dung học tập thực tế và dữ liệu tương tác của user. Tải trọng (payload) của đồ thị nằm ở tập hợp này.

3. **$V_{assess}$ (Assess Nodes - Nút đánh giá):**
   - Đóng vai trò là các **Gateway Nodes (Nút rào chắn)**. 
   - Tính chất đồ thị: Giả sử đồ thị con của Chương 1 là $G_1$ và Chương 2 là $G_2$. Một node $a \in V_{assess}$ được định nghĩa là một Cut-vertex (đỉnh cắt) hoặc cầu nối bắt buộc. Mọi đường đi (path) từ bất kỳ đỉnh nào trong $G_1$ đến bất kỳ đỉnh nào trong $G_2$ đều phải đi qua $a$. 
   - Nghĩa là: Người học bị "kẹt" lại tại $a$ cho đến khi vượt qua bài đánh giá tổng hợp.

---

## 1.2. Không gian Trạng thái của một Node (Node State Space)

Mỗi node $v \in V_{micro} \cup V_{assess}$ là một vector đặc trưng toán học chứa 3 tham số cốt lõi quyết định hành vi của hệ thống AI. Ký hiệu trạng thái của node $v$ là $S_v$:

$$ S_v = (\alpha_v, \rho_v, \mathcal{B}_v) $$

### 1. $\alpha_v$: Độ khó nhận thức (Cognitive Alpha Base)
- **Định nghĩa:** Một đại lượng vô hướng định lượng độ trừu tượng và sự phức tạp của kiến thức.
- **Miền giá trị:** $\alpha_v \in \mathbb{Z} \cap [10, 30]$.
- **Ý nghĩa hệ thống:** Alpha base thấp (10-15) dành cho các định nghĩa, sự kiện. Alpha base cao (20-30) dành cho các công thức phức tạp, tư duy thiết kế hệ thống. Giá trị này là hằng số được sinh ra bởi AI khi tạo cấu trúc ban đầu.

### 2. $\rho_v$: Vị trí tương đối trong Đồ thị (Position Ratio)
- **Định nghĩa:** Tỷ lệ cho biết người học đã đi được bao xa trong đồ thị khi chạm đến node $v$.
- **Toán học:** Để tính $\rho_v$, hệ thống thực hiện thuật toán **Sắp xếp Topo (Topological Sorting)** trên $G$ để gán một chỉ số thứ tự $rank(v)$ cho từng node $v \in V_{micro}$.
  
  $$\rho_v = \frac{rank(v) - 1}{|V_{micro}| - 1}$$

- **Miền giá trị:** $\rho_v \in [0, 1]$. 
- **Ý nghĩa hệ thống:** $\rho_v \approx 0$ nghĩa là nhập môn. $\rho_v \approx 1$ nghĩa là cuối khóa học. Hàm này được hiện thực hóa trong hàm `get_node_position_ratio()`.

### 3. $\mathcal{B}_v$: Hồ sơ Bloom mục tiêu (Target Bloom Profile)
- **Định nghĩa:** Một tập hợp con các bậc Bloom mà người học phải đạt được tại node đó. Tập hợp các bậc Bloom khả dĩ là $U = \{1, 2, 3, 4, 5, 6\}$.
- **Toán học:** $\mathcal{B}_v \subset U$. Nó là kết quả của một hàm ánh xạ (mapping function) $f: (\alpha_v, \rho_v) \to \mathcal{B}_v$. *(Chi tiết hàm $f$ này sẽ được trình bày ở Phần 2)*.

---

## 1.3. Ánh xạ sang Hệ thống Thực tế (System Implementation)

Cấu trúc đồ thị DAG được số hóa thành cấu trúc JSON dạng Flat List kết hợp References để tối ưu hóa việc truy xuất dữ liệu trên ứng dụng Web:

```json
{
  "course_name": "Tên khóa học",
  "macro_nodes": [
    { "id": "chap1", "title": "Chương 1" }
  ],
  "micro_nodes": [
    {
      "id": "c1.1",
      "chapter": "chap1",
      "alpha_base": 12,
      "bloom_profile": {
        "effective_levels": [1, 2]
      },
      "prerequisites": [] 
    },
    {
      "id": "c1.2",
      "chapter": "chap1",
      "alpha_base": 18,
      "prerequisites": ["c1.1"] 
    }
  ],
  "assess_nodes": [
    {
      "id": "assess_chap1",
      "type": "assess",
      "prerequisites": ["c1.1", "c1.2"]
    }
  ]
}
```

### Kiến trúc Dữ liệu
- Để giải quyết vấn đề duyệt cây (Tree Traversal), hệ thống chuyển đổi JSON này thành Flat Dictionary `{"id": node_data}` trong runtime qua hàm `_get_all_nodes_flat()`. Việc tra cứu một node và các thuộc tính của nó tốn độ phức tạp $O(1)$.
- Hệ thống Bloom State được lưu tách biệt khỏi cấu trúc cây (tại `user_data/{username}/bloom_state/{subject_id}.json`) để đảm bảo Graph là Immutable (không đổi), trong khi User State (trạng thái người học) là Mutable (thay đổi liên tục).

---
> *Đây là kết thúc Phần 1. Nếu bạn đồng ý, chúng ta sẽ tiếp tục với Phần 2: Lý thuyết Toán học của Hệ thống Hiệu chuẩn Bloom, Cơ chế Tính điểm và Đường cong Ebbinghaus.*

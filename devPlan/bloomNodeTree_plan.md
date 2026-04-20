# KẾ HOẠCH TRIỂN KHAI CHI TIẾT: HỆ THỐNG MÀU SẮC BLOOM VÀ KIẾN TRÚC ĐỒ THỊ CHUẨN MIT

## 1. THỰC TRẠNG DỮ LIỆU VÀ VẤN ĐỀ CỐT LÕI (CURRENT DATA ANALYSIS)
Qua quá trình rà soát toàn bộ `DB/JSON_Data/`, tôi phát hiện ra: **100% câu hỏi hiện tại (649 câu) đều đang được gán cứng tag `bloom_level: understand` (Thấu hiểu)**.

> [!WARNING]
> Mức độ rủi ro: Nếu chúng ta áp dụng cứng nhắc biểu đồ 6 thang điểm Bloom (Remember -> Create) dựa hoàn toàn vào tag tĩnh như kế hoạch cũ, người học sẽ **mãi mãi bị kẹt lại ở nấc thang thứ 2 (Understand)** vì hệ thống không có bất kỳ câu hỏi nào thuộc mức cao hơn để đo lường.

## 2. GIẢI PHÁP ĐỘT PHÁ: KẾT HỢP BLOOM VÀ IRT
Để giải quyết bài toán thiếu dữ liệu cấp cao, tôi đề xuất mô hình **Inferred Bloom (Bloom Suy Luận)**:
*   Mặc dù câu hỏi ở mức "Understand", nhưng nếu người học trả lời **đúng liên tục (Streak dài)** và **tốc độ cực nhanh (thời gian < 10s/câu)**.
*   Hệ thống tính toán Elo tăng vọt và **suy luận** rằng họ đã tự động nội hóa kiến thức đạt mức độ Phản xạ (Apply) hoặc Phân tích (Analyze). Màu sắc sẽ tự động leo thang tương ứng!

## 3. PHỔ MÀU HSL VÀ BẢN ĐỒ LOGIC (COLOR MAP)
Thay vì các màu tĩnh rời rạc, mọi node sẽ được "tô màu" bằng Gradient HSL kết hợp độ bão hòa (Saturation) phản ánh mức độ bền vững kiến thức.

| Trạng thái | Elo / IRT Score | Mức Bloom thực / Suy luận (Inferred) | Mã HSL Base / Hiệu ứng | Diễn giải Tâm lý học |
| :--- | :--- | :--- | :--- | :--- |
| **Uncharted** | $1200\ (Base)$ | $L0$ (Chưa có khái niệm) | `hsl(210, 20%, 30%)` (Xám tối trong suốt) | Vùng cấm, tạo sự tò mò. |
| **Exposure** | $>1200$ | $L1$ (Remember) | `hsl(200, 80%, 50%)` (Xanh thiên thanh) | Nhớ mặt chữ, có khái niệm cơ bản. |
| **Synthesis** | $>1350$ | $L2$ (Understand) | `hsl(140, 70%, 45%)` (Xanh ngọc/Emerald) | Hiểu quy luật và ý nghĩa sâu xa. |
| **Application**| $>1500$ | $L3$ (Apply) / Phản xạ nhanh | `hsl(45, 90%, 50%)` (Vàng hoàng kim) | Biến tri thức thành công cụ phản xạ. |
| **Deconstruct**| $>1650$ | $L4$ (Analyze) / Chuỗi Streak dài | `hsl(20, 85%, 55%)` (Cam sáng) | Cắt lớp vấn đề, nhìn ra góc khuất. |
| **Mastery**    | $>1800$ | $L5, L6$ / Điểm IRT tối đa | `hsl(280, 80%, 60%)` (Tím Violet - Glow) | Giai đoạn "Giác ngộ". |

---

## 4. TÁI CẤU TRÚC ĐỒ THỊ CHUẨN QUỐC TẾ (HARVARD/MIT STANDARDS)
Theo yêu cầu thiết kế mới của bạn, Cây Tri Thức không được phép hiển thị quá nhiều node lắt nhắt làm rối loạn nhận thức. Chúng ta sẽ áp dụng **Thuyết Tải Trọng Thần Kinh (Cognitive Load Theory)** thông qua cơ chế gom nhóm (Chunking):

### 4.1. Kiến trúc Phân tầng (Hierarchy Taxonomy)
*   **Macro (Chương / Topic)**: Tập hợp kiến thức vĩ mô.
*   **Meso (Phần / Module)**: Đơn vị nhỏ nhất **hiển thị trên Đồ thị 3D**. Đây là "viên gạch" tri thức nền tảng mang ý nghĩa trọn vẹn.
*   **Micro (Tiết / Lesson)**: Các bước học tập thực tế (Nội dung chi tiết bên trong). **Được ẩn đi khỏi đồ họa 3D**.

### 4.2. Cơ chế Đồng bộ và Render Đồ thị (Visualization Update)
Thay vì load mọi Tiết (Micro) lên đồ thị, tôi sẽ xây dựng một thuật toán **Auto-Chunking** trong `step2_5_visualize_tree.py`:
1.  **Gom cụm tự động**: Đọc file JSON của Chương, gộp mỗi 3 "Tiết" gần kề nhau vào chung 1 "Phần" (ví dụ: Tiết 1, 2, 3 -> Phần 1.1).
2.  **Trọng lượng tiến độ**: Tiến độ của "Phần 1.1" chính là trung bình cộng Inferred Bloom của 3 Tiết thành phần.
3.  **Tối giản hiển thị**: Nếu chương có 12 Tiết, thay vì vẽ 12 node lắt nhắt, thuật toán sẽ vẽ 4 node "Phần" lớn, rõ ràng chuẩn UI/UX của các ĐH Mỹ.

### 4.3. Nâng cấp Giao diện Quản lý Học tập (Deep-dive UI)
Khi người học click vào một Node "Phần" trên môi trường 3D:
1.  Hệ thống `main.py` sẽ nhận biết đó là Node Meso (gồm nhiều Micro kết hợp).
2.  Thanh Panel quản lý (hoặc tab Graph Studio) sẽ tự động sinh ra một giao diện kiểu **Accordion (Trình đơn xếp mở)** hoặc **Tabs**.
3.  **Khung cảnh**: Sẽ có 3 thanh Accordion tương ứng cho 3 Tiết. Nhấn mở thanh nào sẽ sổ xuống tài liệu (Video, Bài tập, Slide PDF) của chính môn chủ đề (Tiết) đó.

---

## 5. LỘ TRÌNH LẬP TRÌNH CHI TIẾT (IMPLEMENTATION STEPS)

### PHẦN 1: Tối ưu hóa Bộ Xử lý Điểm Số (Backend - `pkt_engine.py`)
- Mở rộng cấu trúc class `StudentState`:
  - Khởi tạo hàm `calculate_inferred_bloom(self, concept_id)` tính toán mức IRT dựa trên lịch sử.
  - Sửa `sync_to_json()` để xuất thuộc tính mới là `inferred_bloom`.

### PHẦN 2: Chunking Thuật Toán Đồ thị (Javascript + Python)
- Tại `step2_5_visualize_tree.py`:
  - Lặp qua Micro-nodes, gom nhóm (group by 3-4 items) tạo ra Node ảo `type: 'meso'`.
  - Loại bỏ hoàn toàn các liên kết rác.
- Áp dụng mảng HSL Color bằng hàm Javascript `getNodeColor` dọc theo trục Inferred Bloom của Node Meso.

### PHẦN 3: Giao diện UI Đa Tiết (NiceGUI)
- Cập nhật `main.py` tại khu vực Quản lý Tài nguyên (Resource Manager). 
- Dùng `ui.expansion()` (Accordion) để chứa các Panel riêng cho "Tiết 1", "Tiết 2", "Tiết 3" bên trong một "Phần" mỗi khi click Node Meso. Cập nhật Player và Quiz Component để render động theo ID của Tiết được sổ ra.

---

## 6. CÂU HỎI MỞ ĐỂ PHÊ DUYỆT
Với thiết kế gom nhóm **Chunking (Phần bao bọc các Tiết)**, cây tri thức sẽ đáp ứng tiêu chuẩn của giáo dục đẳng cấp quốc tế (ít lộn xộn, module hóa cao độ).
Tôi sẽ bắt đầu bằng cách nâng cấp `step2_5_visualize_tree.py` để phân cụm "Tiết" thành "Phần". Bạn có muốn tuỳ chỉnh logic gom nhóm (ví dụ 3 Tiết chẵn lẻ) hay cứ để hệ thống tự động gom tự động theo thứ tự trong file JSON?
# Sprint 5: Trực quan hóa Cây Tri Thức 3D & Tương tác Node

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Xây dựng một giao diện Không gian 3D (3D Knowledge Graph) tuyệt đẹp để hiển thị cấu trúc môn học. Giao diện này phải lấy dữ liệu trực tiếp từ file Single JSON (tại Local Storage), có khả năng đổi màu Node theo năng lực (Mastery/Bloom) và cho phép người dùng tương tác sâu (Click, Sửa, Thêm, Xóa Node).

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, tôi muốn nhìn thấy toàn bộ kiến thức của mình dưới dạng một "Dải ngân hà 3D", nơi các vì sao (khái niệm) tôi yếu sẽ có màu Đỏ, và những nơi tôi giỏi sẽ có màu Xanh, giúp tôi biết ngay mình cần học gì.
- **US2:** Là một người học, khi tôi nhấn vào một điểm trên không gian 3D, tôi muốn một bảng điều khiển (Omni-Drawer) hiện ra giải thích khái niệm đó và trích xuất đúng trang PDF mà hệ thống RAG đã đọc.
- **US3:** Là một người học, đôi khi AI vẽ sai lệch, tôi muốn có thể tự tay nhấp chuột phải để Đổi tên, Xóa hoặc tự vẽ thêm một đường nối giữa 2 khái niệm.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 5.1: Tích hợp Engine Đồ họa 3D (Three.js / 3d-force-graph)
- Sử dụng thư viện `3d-force-graph` (hoặc `react-force-graph-3d` nếu dùng React).
- Thay thế hoàn toàn file render cũ (`current_visual_tree.html`). 
- Viết hàm `loadGraphData()`: Đọc `nodes` và `edges` từ State nội bộ (đã lấy từ file `[Mã_Môn_Học].json`) và nhồi vào thuộc tính `graphData`.

### Task 5.2: Thuật toán Tự động Phối màu (Dynamic Styling)
- Viết hàm nội suy (interpolation) màu sắc dựa trên chỉ số của Node:
  - `mastery_score` (Độ thành thạo 0-100%): Quy định màu sắc (Color). 
    - < 30%: 🔴 Màu Đỏ cảnh báo.
    - 30% - 70%: 🟡 Màu Vàng ôn tập.
    - > 70%: 🟢 Màu Xanh hoàn thành.
  - `bloom_level` (Bậc nhận thức 1-6): Quy định kích thước (Radius) của Node. Bậc cao (Sáng tạo/Đánh giá) thì Node càng to và tỏa sáng.

### Task 5.3: Xây dựng Omni-Drawer (Bảng điều khiển Tương tác)
- Đăng ký sự kiện `onNodeClick`.
- Khi người dùng click vào 1 Node, Camera 3D sẽ bay tới cận cảnh Node đó (Fly-to animation).
- Đồng thời mở UI Omni-Drawer bên phải màn hình.
- Truy vấn JSON State để đổ dữ liệu vào Drawer: Tên khái niệm, Mô tả (do LLM gen ở Sprint 4), Điểm số hiện tại, và **Danh sách tài liệu liên kết**. Tại đây, làm nút "Mở PDF", bấm vào sẽ mở trực tiếp file từ Google Drive.

### Task 5.4: Trình chỉnh sửa Đồ thị Thủ công (Manual Graph Editor)
- Thêm tính năng Context Menu (Click chuột phải vào Node hoặc khoảng không).
- Các chức năng CRUD thủ công:
  - **Thêm Node:** Mở popup nhập tên, tự sinh ID, push vào mảng `nodes`.
  - **Nối Edge:** Bấm "Connect", chọn Node A rồi chọn Node B để sinh ra edge mới.
  - **Xóa Node:** Lọc bỏ node khỏi mảng `nodes` và xóa sạch các `edges` liên quan.
- **Quan trọng:** Mọi thao tác này đều chỉ làm thay đổi mảng JSON trên RAM (Local State). Ngay lập tức, cơ chế Auto-Sync (Sprint 2) sẽ tự động bắt tín hiệu và đẩy file JSON mới lên Google Drive sau 5 giây. Đảm bảo UI không bao giờ bị giật lag khi người dùng thao tác.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Mở ứng dụng, đồ thị 3D bung ra mượt mà ở tốc độ > 30 FPS. Các node tự động đổi màu đúng với điểm số trong file JSON.
- [ ] Click vào Node, Camera bay tới và Omni-drawer mở ra hiển thị đúng thông tin của Node đó.
- [ ] Xóa thử 1 Node bằng tay -> Đồ thị biến mất Node đó ngay lập tức -> Đợi 5 giây kiểm tra trên Google Drive thấy file JSON đã được ghi đè chính xác (Mất node đó).

## 4. Risk & Dependencies
- **Rủi ro 1 - Nút thắt cổ chai Hiệu suất (Performance Bottleneck):** Nếu AI quét ra 1 cuốn sách có tới 2000 nodes và 5000 edges, trình duyệt sẽ bị quá tải khi render 3D liên tục (Drop FPS).
- **Giải pháp:** 
  - Kích hoạt cơ chế dừng mô phỏng vật lý: Gọi `graph.pauseAnimation()` sau khi đồ thị đã bung ra ổn định (khoảng 3 giây).
  - Triển khai **LOD (Level of Detail)**: Khi zoom xa, các node nhỏ sẽ ẩn đi, chỉ hiện các "Chương" (Node lớn). Khi zoom lại gần cụm nào, cụm đó mới hiện ra các Node con chi tiết.
- **Phụ thuộc:** Yêu cầu cấu trúc JSON từ Sprint 2 và 4 phải chuẩn xác thì engine 3D mới render được.

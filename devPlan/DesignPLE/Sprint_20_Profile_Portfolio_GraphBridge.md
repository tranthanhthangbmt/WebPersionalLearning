# Sprint 20: Hồ sơ Năng lực (Portfolio) & Mở rộng Không gian Đa Môn học (Graph Bridge)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Chuyển đổi những nỗ lực học tập thành tài sản thực tế bằng cách nâng cấp `profile_page.py` thành một CV điện tử (Portfolio) có thể chia sẻ cho nhà tuyển dụng. Đồng thời, cung cấp công cụ nâng cao cho phép người dùng ghép nối (Bridge) Cây tri thức của nhiều môn học khác nhau lại thành một Vũ trụ Kiến thức khổng lồ, đi kèm bộ công cụ gỡ lỗi (Debug Tree) cho hệ thống.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một sinh viên chuẩn bị ra trường, tôi muốn xuất toàn bộ những "Điểm Xanh" (Mastery) và Huy hiệu của mình trên ứng dụng thành một đường link Hồ sơ Năng lực (Portfolio) cực kỳ ngầu để gửi cho nhà tuyển dụng.
- **US2:** Là một người ham học, tôi nhận ra môn "Toán cao cấp" và môn "Vật lý đại cương" có nhiều điểm chung. Tôi muốn có một công cụ ghép nối (Bridge) 2 Cây tri thức này lại với nhau để thấy được sự giao thoa kiến thức.
- **US3:** Là một quản trị viên / power-user, đôi khi AI vẽ ra các Node bị mồ côi (không kết nối với ai) hoặc bị lặp vòng tròn (Infinite Loop). Tôi muốn có công cụ `debug_tree` để quét và sửa lỗi cấu trúc file JSON chỉ bằng 1 cú click.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 20.1: Xây dựng Hồ sơ Năng lực Công khai (Public Portfolio - profile_page.py)
- Nâng cấp `profile_page.py` và `profile.json`.
- Thiết kế một giao diện Web tĩnh (Public View) được tối ưu hóa SEO.
- Dữ liệu hiển thị: 
  - Tổng số giờ học, Tổng XP, Chuỗi Streak dài nhất.
  - Sơ đồ Radar Chart thể hiện mức độ thành thạo ở các lĩnh vực (Ví dụ: Lập trình 80%, Toán 60%, Kỹ năng mềm 90%).
  - Hình ảnh xoay 3D thu nhỏ của các Cây tri thức mà người dùng đã đạt 100% Mastery.

### Task 20.2: Công cụ Nối Đồ thị Đa Môn học (Graph Bridging - patch_bridge.py)
- Triển khai logic trong `patch_bridge.py`.
- **Cơ chế hoạt động:** 
  - Người dùng chọn 2 môn học (Ví dụ: `Math.json` và `Physics.json`).
  - Thuật toán trích xuất toàn bộ Labels của cả 2 mảng `nodes`.
  - Đưa danh sách này qua LLM (Gemini) với Prompt: *"Hãy tìm các cặp khái niệm có sự tương đồng hoặc liên kết logic giữa Môn A và Môn B"*.
  - Hệ thống tự động tạo ra các `edges` mới (Màu tím, nét đứt) để nối các Node giao thoa lại với nhau.
  - Render cả 2 môn học chung trên một Không gian 3D khổng lồ (Meta-Graph).

### Task 20.3: Công cụ Gỡ lỗi & Dọn rác Đồ thị (Tree Debugger - debug_tree.py)
- Triển khai thuật toán trong `debug_tree.py`.
- Viết các hàm phân tích cấu trúc Đồ thị có hướng (DAG):
  - **Quét Node Mồ côi (Orphan Scanner):** Tìm các Node có bậc (degree) = 0 và gộp chúng vào cụm "Misc" (Khác).
  - **Quét Vòng lặp (Cycle Detection):** Tìm các đường đi tạo thành vòng tròn vô tận (A -> B -> C -> A) làm thuật toán Pathfinder (Sprint 10) bị treo, và tự động cắt bỏ một cạnh (edge) dư thừa.
  - **Giao diện sửa nhanh:** Một bảng Table/Tree-view đơn giản cho phép click đúp vào đổi tên Node mà không cần load 3D engine.

### Task 20.4: Tối ưu hóa Hiệu năng (Meta-Graph Performance)
- Khi ghép nối 2 môn học (Ví dụ: 2000 Nodes + 2000 Nodes = 4000 Nodes), trình duyệt sẽ quá tải.
- Cập nhật Engine Three.js (Sprint 5): Tích hợp kỹ thuật **Octree** hoặc **GPU Instancing** để render số lượng cực lớn các điểm sáng (Particles) trên không gian 3D mà vẫn giữ được > 60 FPS.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Truy cập đường link Public Profile ẩn danh, trang web hiện ra biểu đồ Radar và Cây tri thức thành quả của sinh viên cực kỳ chuyên nghiệp.
- [ ] Chạy lệnh `patch_bridge.py` giữa Toán và Lý, hệ thống tự vẽ ra một đường link màu tím nối node "Đạo hàm" và "Vận tốc".
- [ ] Cố tình tạo một vòng lặp A->B->C->A. Chạy `debug_tree.py`, hệ thống báo *"Đã phát hiện và gỡ 1 vòng lặp vô hạn"*.

## 4. Risk & Dependencies
- **Rủi ro 1 - Phình to dữ liệu (Data Bloat):** Khi tạo Meta-Graph, file JSON lưu trên RAM có thể lên tới hàng chục MB, gây crash tab trình duyệt (Out of Memory).
- **Giải pháp:** Đối với chế độ Meta-Graph (Nhiều môn học), không tải `description` hay cấu hình hiển thị chi tiết của Node vào RAM. Chỉ tải `id` và tọa độ `x, y, z` để vẽ đồ thị (Lazy loading data). Khi người dùng click vào cụm nào, mới call API Local Storage để lấy thông tin chi tiết của Node đó lên.

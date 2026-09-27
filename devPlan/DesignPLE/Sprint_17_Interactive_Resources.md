# Sprint 17: Hệ sinh thái Tài nguyên Tương tác (Interactive Resource Manager)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Biến các Khái niệm (Nodes) khô khan thành những trải nghiệm tương tác (Interactive Experiences). Thay vì chỉ đọc chữ sinh ra từ RAG, hệ thống sẽ cho phép ghim (đính kèm) các Tài nguyên bên ngoài như: Mô phỏng vật lý, Script tương tác (CodePen/JS), Mini-game, hoặc liên kết Website trực tiếp vào từng Node thông qua một Resource Manager.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một sinh viên học môn Vật lý, khi tôi bấm vào Node "Lực hấp dẫn", tôi không chỉ muốn đọc text, mà tôi muốn thấy một mô phỏng 3D thả rơi quả táo có thể tương tác được ngay trên màn hình.
- **US2:** Là một tác giả (Creator) của Cây tri thức, tôi muốn dùng công cụ `add_script_resources.py` để nhúng các đoạn mã JavaScript hoặc iFrame của riêng tôi vào các Node cụ thể để minh họa bài học sinh động hơn.
- **US3:** Là một hệ thống, tôi muốn đảm bảo rằng các đoạn mã (Script) do người dùng khác tải lên phải được chạy trong một môi trường cách ly (Sandbox) để không làm sập (crash) ứng dụng hay đánh cắp dữ liệu của tôi.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 17.1: Cập nhật Schema cho Resource Manager
- Dựa vào file `resource_manager.py` (hoặc `_test_rm.py`), cập nhật cấu trúc JSON của từng Môn học.
- Mỗi phần tử trong mảng `nodes` sẽ có thêm trường `resources`:
  ```json
  "resources": [
    {
      "id": "res_01",
      "type": "iframe_simulation",
      "title": "Mô phỏng Con lắc đơn",
      "url": "https://phet.colorado.edu/sims/...",
      "is_safe": true
    },
    {
      "id": "res_02",
      "type": "custom_script",
      "title": "Script tính toán ma trận",
      "script_content": "console.log('Running matrix math...');"
    }
  ]
  ```

### Task 17.2: Phát triển Công cụ Đính kèm (Add Script Resources)
- Hoàn thiện luồng logic trong `add_script_resources.py`.
- Tạo Giao diện (UI) ở Context Menu (Chuột phải vào Node -> "Thêm Tài nguyên Tương tác").
- Cho phép người dùng dán Link (URL), dán mã nhúng (Embed Code) hoặc tải lên file `.js` / `.html` cục bộ.
- File tài nguyên cục bộ này cũng sẽ được đồng bộ lên Google Drive cùng với Cây tri thức (Kế thừa Sprint 3).

### Task 17.3: Môi trường Thực thi Cách ly (Sandbox Security)
- **Cực kỳ quan trọng:** Không được dùng hàm `eval()` hoặc chèn `<script>` trực tiếp vào DOM của ứng dụng React/Vue chính, sẽ gây ra lố hổng bảo mật XSS (Cross-Site Scripting).
- Sử dụng thẻ `<iframe>` với thuộc tính `sandbox="allow-scripts allow-same-origin"` để kết xuất (render) các mô phỏng/script này.
- Thiết lập Content Security Policy (CSP) chặt chẽ cho trình duyệt.

### Task 17.4: Giao diện Tương tác Tài nguyên (Omni-Drawer Update)
- Nâng cấp Omni-Drawer (Trợ lý ảo - Sprint 5/10).
- Khi người dùng bấm vào Node có gắn Resource, ngoài Tab "Giải thích AI", sẽ có thêm Tab "Thực hành/Mô phỏng" (Kèm icon sáng nhấp nháy thu hút sự chú ý).
- Bấm vào Tab đó, iFrame sẽ bung ra toàn màn hình hoặc nằm gọn trong Drawer để sinh viên trực tiếp thao tác kéo/thả/chơi mini-game minh họa.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Dùng tool `add_script_resources.py` đính kèm thành công một mô phỏng PhET (vật lý) vào Node A.
- [ ] Mở Node A trên ứng dụng, bấm Tab "Mô phỏng", iframe chạy mượt mà không làm chậm ứng dụng chính.
- [ ] Cố tình đính kèm một Script độc hại (Chứa lệnh lấy cắp LocalStorage `window.localStorage`), hệ thống Sandbox chặn lại thành công và in lỗi ra Console.
- [ ] Xuất bản (Publish) Cây tri thức này lên Public Library (Sprint 16), người khác tải về vẫn mở được Mô phỏng đó.

## 4. Risk & Dependencies
- **Rủi ro 1 - Link chết (Dead Links):** Nếu tài nguyên là URL trỏ ra ngoài mạng (VD: một trang web cá nhân), trang web đó có thể sập sau vài tháng, làm hỏng trải nghiệm học tập.
- **Giải pháp:** Viết một Worker chạy ngầm mỗi tháng 1 lần: Gửi request `PING` tới tất cả các URL trong Resource Manager. Nếu trả về lỗi 404 (Not Found), đánh dấu cảnh báo (Icon Cờ đỏ) trên giao diện để tác giả biết và sửa lại link.

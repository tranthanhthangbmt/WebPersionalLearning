# Sprint 9: Thuật toán Chống quên lãng (Spaced Repetition System - SRS)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Hoàn thiện khâu "Cá nhân hóa" bằng cách giải quyết bài toán cốt lõi nhất của việc học: Sự quên lãng. Tích hợp thuật toán Lặp lại ngắt quãng (dựa trên đường cong Ebbinghaus hoặc SM-2) trực tiếp vào file JSON của người học. Hệ thống sẽ chủ động tìm ra những kiến thức sắp bị quên để nhắc nhở và tự động giảm điểm Mastery nếu người học bỏ bẵng quá lâu.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, khi tôi vừa mở ứng dụng lên vào buổi sáng, tôi muốn trợ lý AI chỉ ngay cho tôi 3 khái niệm tôi đang có nguy cơ quên nhất để tôi ôn tập trong 5 phút, thay vì phải tự tìm.
- **US2:** Là một người học, nếu tôi đạt màu Xanh (Mastery 100%) nhưng 2 tuần sau tôi không đụng tới, tôi muốn Node đó từ từ phai màu về Vàng hoặc Đỏ để tôi biết mình cần học lại.
- **US3:** Là một người học, nếu tôi ôn tập đúng hạn, khoảng thời gian chờ đến lần ôn tập tiếp theo sẽ dài ra (ví dụ: từ 1 ngày lên 3 ngày, rồi 7 ngày, rồi 1 tháng) để tôi không bị học vẹt.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 9.1: Cập nhật Cấu trúc JSON cho SRS
- Cập nhật định nghĩa Node trong file `schema.md` (Sprint 2). Thêm các trường dữ liệu sau vào mỗi Node:
  - `last_reviewed_at`: Timestamp (chuẩn UTC) của lần làm Quiz đúng gần nhất.
  - `interval`: Khoảng cách thời gian (tính bằng ngày) cho lần ôn tập tiếp theo.
  - `ease_factor`: Hệ số độ khó (mặc định 2.5 theo chuẩn SM-2, giảm nếu làm sai, tăng nếu làm đúng).

### Task 9.2: Thuật toán Đường cong quên lãng (Decay Algorithm)
- Viết hàm `calculate_retention(node)`. Hàm này chạy mỗi khi người dùng tải file `[Mã_Môn_Học].json` vào RAM:
  - Tính thời gian đã trôi qua: `days_elapsed = (current_time - last_reviewed_at)`.
  - Nếu `days_elapsed > interval`, tính năng lực hiện tại bị suy giảm.
  - **Tác động:** Thuật toán không sửa `mastery_score` gốc, mà sinh ra một biến ảo `effective_mastery` dùng để hiển thị UI. Nếu quá hạn lâu, `effective_mastery` tụt từ 100% xuống dưới 70%, khiến Node chuyển từ Xanh về Vàng trên Đồ thị 3D.

### Task 9.3: Thuật toán Tính lịch Lặp lại (SM-2 Logic)
- Cập nhật hàm chấm điểm (Sprint 8). Khi user làm Quiz:
  - Nếu làm đúng (Chất lượng >= 80%):
    - Lần 1: `interval = 1` ngày.
    - Lần 2: `interval = 6` ngày.
    - Từ lần 3: `interval = old_interval * ease_factor`.
  - Nếu làm sai: Đặt lại `interval = 1` ngày và giảm `ease_factor`.
- Ghi đè các trường này vào JSON và kích hoạt Auto-sync lên Drive.

### Task 9.4: Giao diện Hàng đợi Ôn tập (Daily Review Queue)
- Viết vòng lặp lọc qua toàn bộ Cây tri thức: Tìm những Node có `current_time > (last_reviewed_at + interval)`.
- Sắp xếp độ ưu tiên theo Bậc Bloom (Ưu tiên ôn các khái niệm nền tảng trước).
- Hiển thị danh sách này ở màn hình Dashboard dưới dạng "Nhiệm vụ hôm nay".
- Tích hợp với Omni-Drawer (Trợ lý ảo): Khi vào môn học, AI popup: *"Bạn có 3 khái niệm sắp quên lãng (VD: Khái niệm Y). Bấm vào đây để làm Quiz ôn tập 2 phút nhé!"*

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Chỉnh sửa thời gian hệ thống (Hoặc can thiệp sửa trực tiếp file JSON giả lập thời gian trôi qua 7 ngày): Đồ thị 3D tự động chuyển màu một số Node từ Xanh về Vàng.
- [ ] Khung "Nhiệm vụ hôm nay" xuất hiện chính xác các Node bị quá hạn.
- [ ] Làm thành công Quiz của Node quá hạn: Màu xanh lập tức phục hồi, và `interval` trong JSON tăng lên thành số ngày dài hơn.

## 4. Risk & Dependencies
- **Rủi ro 1 - Lỗi múi giờ (Timezone Bug):** Sinh viên có thể học ở VN, sau đó đi du lịch nước ngoài khiến timestamp bị nhảy, làm hỏng lịch SRS.
- **Giải pháp:** Bắt buộc lưu timestamp ở định dạng `UTC (ISO 8601)` trên file JSON, và chỉ dùng thư viện JS (`Date` hoặc `date-fns`) để quy đổi ra giờ địa phương khi tính toán `days_elapsed`.
- **Rủi ro 2 - Quá tải bài tập (Review Hell):** Nếu sinh viên bỏ học 1 tháng, khi quay lại sẽ có hàng trăm Node cần ôn, gây nản chí.
- **Giải pháp:** Giới hạn (Cap) "Nhiệm vụ hôm nay" ở con số tối đa 20 bài (20 Nodes), ưu tiên các Node gốc (Root nodes) có ảnh hưởng lớn nhất.

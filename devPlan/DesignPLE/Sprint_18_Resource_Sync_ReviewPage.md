# Sprint 18: Đồng bộ Tài nguyên (Resource Sync) & Không gian Ôn tập Tập trung (Review Page)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Giải quyết triệt để bài toán đồng bộ hóa các file vật lý đính kèm (Ảnh, Script, Mô phỏng HTML) lên Google Drive bằng luồng chạy ngầm. Đồng thời, xây dựng một "Không gian ôn tập" (Review Page) hoàn toàn tối giản, không gây xao nhãng, giúp sinh viên tập trung tối đa vào việc giải quyết các nhiệm vụ Spaced Repetition hàng ngày.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một tác giả bài giảng, khi tôi chèn một bức ảnh minh họa hoặc một file Script Mini-game từ ổ cứng máy tính vào Khái niệm, tôi muốn hệ thống tự động đưa file đó lên Google Drive để người khác tải về Cây tri thức của tôi cũng sẽ xem được ảnh đó.
- **US2:** Là một người học, tôi muốn khi mở môn học ra, các hình ảnh và mô phỏng đính kèm đã được tải sẵn ở chế độ nền (Pre-fetched) để tôi không phải chờ đợi vòng xoay "Loading..." mỗi khi click vào.
- **US3:** Là một người học, khi làm bài tập ôn tập hàng ngày (Daily Review), tôi muốn giao diện ẩn đi toàn bộ Cây 3D phức tạp, chỉ hiện duy nhất từng câu hỏi Flashcard một để tôi không bị phân tâm.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 18.1: Thuật toán Đồng bộ Tài nguyên (resource_sync.py)
- Khi người dùng thêm một tài nguyên (Resource) dạng File Local:
  - Tạo thuật toán Băm (Hashing - MD5/SHA256) file đó để kiểm tra trùng lặp.
  - Tự động tạo thư mục con `KnowledgeGalaxy_Data/[Mã_Môn_Học]/Resources` trên Google Drive.
  - Gọi API Upload file lên thư mục này.
  - Cập nhật url trong file `[Mã_Môn_Học].json` trỏ tới `drive_file_id`.
- Tích hợp logic xử lý lỗi: Nếu rớt mạng khi đang upload, đưa vào hàng đợi `offline_sync_queue` (từ Sprint 11).

### Task 18.2: Cơ chế Tải trước & Lưu Cache (Pre-fetching & IndexedDB)
- Viết một Web Worker chạy ngầm (Background Worker) khởi động ngay khi sinh viên truy cập vào môn học.
- Quét toàn bộ mảng `resources` trong file JSON.
- So sánh với `IndexedDB` của trình duyệt. Nếu phát hiện file Drive ID chưa có trong máy, Worker sẽ âm thầm gọi Google Drive API để tải file đó về lưu cục bộ.
- Nhờ vậy, khi sinh viên click vào Node, hình ảnh/mô phỏng sẽ bung ra lập tức ở tốc độ 0 mili-giây.

### Task 18.3: Giao diện Không gian Ôn tập (Review Page)
- Thiết kế riêng file `review_page.py` (hoặc giao diện React/Vue tương ứng).
- Lấy danh sách các Node cần ôn tập trong ngày từ thuật toán Spaced Repetition (Sprint 9).
- Chuyển giao diện sang chế độ "Zen Mode" (Ẩn thanh công cụ, ẩn đồ thị 3D).
- Áp dụng UI dạng **Thẻ Flashcard Swipe** (Giao diện vuốt giống Tinder hoặc Anki):
  - Mặt trước thẻ: Tên Khái niệm + Chèn ngay iFrame Mô phỏng (từ Sprint 17) để sinh viên có thể tương tác trước khi trả lời.
  - Mặt sau thẻ: Các câu hỏi trắc nghiệm (từ Sprint 7) và Nút "Hiện giải thích".

### Task 18.4: Cập nhật Trạng thái & Chuyển thẻ
- Khi làm xong 1 thẻ, gọi hàm chấm điểm (Sprint 8) để cập nhật Mastery/Bloom ở bộ nhớ RAM.
- Tự động trượt (slide) sang thẻ tiếp theo với hiệu ứng âm thanh nhỏ để tạo động lực.
- Hoàn thành toàn bộ số thẻ trong ngày -> Bắn pháo hoa (Confetti effect) -> Kích hoạt ghi file JSON lên Drive.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Upload một file HTML mô phỏng (Size 2MB) vào Node. Đợi 5 giây, kiểm tra Google Drive thấy file đã nằm ngoan ngoãn trong thư mục `Resources`.
- [ ] Share Cây tri thức này cho bạn bè. Khi bạn bè Import, Web Worker ngầm tải file HTML 2MB đó về máy tính của họ thành công.
- [ ] Bấm nút "Ôn tập Hôm nay", trình duyệt chuyển sang màn hình Flashcard tối giản. Mô phỏng HTML chạy mượt mà ngay trên mặt thẻ Flashcard mà không cần kết nối mạng.

## 4. Risk & Dependencies
- **Rủi ro 1 - Đầy bộ nhớ trình duyệt:** Nếu tải trước (pre-fetch) quá nhiều file âm thanh, hình ảnh, IndexedDB của trình duyệt sẽ bị đầy (Giới hạn khoảng 50MB-500MB tùy trình duyệt).
- **Giải pháp:** Xây dựng cơ chế **Dọn rác tự động (Garbage Collection)**. Khi khởi động app, quét IndexedDB: Những file tài nguyên thuộc về các Node đã Mastery 100% và không cần ôn tập trong 30 ngày tới sẽ bị xóa khỏi cache để giải phóng dung lượng.
- **Phụ thuộc:** Kết hợp chặt chẽ với logic Resource Manager (Sprint 17) và SRS (Sprint 9).

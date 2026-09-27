# Sprint 6: Mạng Lưới Học Tập (Share & Import qua Google Drive)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Hoàn thiện yếu tố "Learner-to-Learner" (Tương tác giữa người học với nhau) trong khung PLiF. Cho phép sinh viên A chia sẻ Cây tri thức và Vector DB của mình cho sinh viên B. Sinh viên B có thể Clone (sao chép) toàn bộ dữ liệu đó về làm tài sản riêng của mình và bắt đầu học ngay lập tức.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một sinh viên vừa cất công upload và để AI vẽ xong bản đồ tư duy cho môn "Nhập môn Lập trình", tôi muốn chia sẻ thành quả này cho nhóm học tập của mình để các bạn không phải tốn thời gian (và tiền API) chạy lại từ đầu.
- **US2:** Là một người nhận link chia sẻ, tôi muốn dán link đó vào hệ thống và lập tức "kế thừa" toàn bộ Cây tri thức, sách PDF và khả năng RAG.
- **US3:** Là người kế thừa, tôi muốn khi mở Cây tri thức ra, cấu trúc bài học vẫn giữ nguyên nhưng điểm số (Mastery, Bloom) của tôi phải bị reset về 0 (Màu Đỏ), vì tôi chưa bắt đầu học.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 6.1: Giao diện Sharing (Tạo Link)
- Thêm nút "Share (Chia sẻ)" ở góc màn hình của môn học.
- Khi người dùng bấm vào, ứng dụng gọi Google Drive API cập nhật quyền (Permissions) của thư mục môn học đó thành `anyone with the link can read`.
- Trích xuất `folder_id` và sinh ra đường link nội bộ (Ví dụ: `knowledgegalaxy.com/import?id=abc123xyz`).
- Hiển thị QR Code hoặc Nút Copy Link.

### Task 6.2: Giao diện & Xử lý Import
- Thêm ô nhập "Paste Share Link" ở màn hình Dashboard (Trang chủ chọn môn học).
- Khi user dán link và bấm Import, hệ thống trích xuất `folder_id` của người chia sẻ.
- Gọi Google Drive API để xác thực quyền đọc thư mục đó.

### Task 6.3: Thuật toán Clone (Sao chép vật lý)
- **Vấn đề:** Không thể để User B đọc chung file với User A, vì nếu User A xóa thư mục hoặc User B làm bài tập thì điểm sẽ bị ghi đè lẫn nhau.
- **Giải pháp:** Sử dụng API `POST https://www.googleapis.com/drive/v3/files/[fileId]/copy`.
- Ứng dụng sẽ tạo một thư mục môn học mới trên Drive của User B.
- Sau đó, lặp qua tất cả các file PDF, `.faiss`, và `.pkl` trong thư mục của User A và thực hiện lệnh **Copy** sang thư mục của User B.

### Task 6.4: Graph Sanitization (Tẩy trắng dữ liệu cá nhân)
- Đối với file `[Mã_Môn_Học].json` chứa cấu trúc Cây tri thức, ứng dụng không copy nguyên xi mà sẽ tải về RAM của User B.
- Chạy hàm `sanitize_graph(json_data)`:
  - Lặp qua mảng `nodes`: Đặt lại `mastery_score = 0`, `bloom_level = 0`.
  - Xóa bỏ lịch sử chat, các ghi chú cá nhân (personal notes) của User A nếu có.
- Gọi API Auto-sync (từ Sprint 2) để đẩy file JSON đã "tẩy trắng" này lên Drive của User B.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] User A bấm nút Share, Google Drive tự động chuyển thư mục đó sang chế độ Public Read.
- [ ] User B dán link. Đợi khoảng 10-15 giây (quá trình copy files trên Drive).
- [ ] Môn học hiện ra ở Dashboard của User B. Khi User B bấm vào, Đồ thị 3D hiện ra với toàn bộ Node màu Đỏ (0 điểm).
- [ ] User B chat thử, RAG vẫn hoạt động bình thường, trả lời chính xác thông tin dựa vào file `.faiss` vừa được copy mà không tốn 1 đồng phí API gọi Gemini Embedding.

## 4. Risk & Dependencies
- **Rủi ro 1 - Vi phạm bản quyền PDF:** Nếu User A chia sẻ sách lậu, Google Drive có thuật toán quét bản quyền ngầm. Nếu tài liệu bị Google block, User B sẽ không copy được.
- **Giải pháp:** Hệ thống cần xử lý lỗi try-catch khi gọi lệnh Copy. Nếu lỗi do Drive, hiển thị thông báo thân thiện: "Tài liệu này không thể copy do vi phạm chính sách của Google Drive. Hãy yêu cầu tác giả chia sẻ trực tiếp sách".
- **Rủi ro 2 - Quá giới hạn lưu trữ:** Copy sách dày 1000 trang + Faiss Index (Khoảng 200MB) có thể làm đầy Google Drive 15GB miễn phí của User B.
- **Giải pháp:** Hiển thị dung lượng ước tính trước khi bấm nút Import để User B kiểm tra.

# Sprint 21: Di chuyển Dữ liệu (Portability) & Hệ thống Tự phục hồi (Self-Healing)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Đảm bảo tính "Sở hữu dữ liệu" (Data Ownership) tuyệt đối cho người dùng thông qua khả năng Import/Export đa định dạng (như CSV của Anki). Đồng thời, triển khai các kịch bản (scripts) sửa lỗi tự động như `full_fix.py` và `fix_syntax.py` để đảm bảo hệ thống không bao giờ bị sập (crash) ngay cả khi AI sinh ra dữ liệu JSON bị hỏng cấu trúc.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một sinh viên đã dùng Anki nhiều năm, tôi muốn tải lên một file `.csv` chứa 500 thẻ Flashcard cũ của tôi để hệ thống tự động vẽ chúng thành một Cây tri thức 3D mà tôi không cần nhập lại từ đầu.
- **US2:** Là một người dùng, tôi muốn xuất (Export) toàn bộ Cây tri thức của tôi ra định dạng Excel/CSV để tôi có thể in ra giấy hoặc chuyển sang nền tảng khác học (Không bị trói buộc - Vendor Lock-in).
- **US3:** Là một hệ thống, đôi khi API của Gemini trả về chuỗi JSON bị thiếu dấu phẩy `,` hoặc ngoặc nhọn `}` làm lỗi toàn bộ ứng dụng. Tôi muốn hệ thống tự động phát hiện và "vá" lại các lỗi cú pháp này trước khi hiển thị cho người dùng.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 21.1: Trình biên dịch CSV sang Đồ thị (fix_csv.py / Data Importer)
- Xây dựng giao diện Upload file CSV.
- Thuật toán xử lý:
  - Đọc file CSV (Cột A: Khái niệm, Cột B: Định nghĩa).
  - Vì CSV là danh sách phẳng (Flat list), hệ thống sẽ gửi danh sách này qua Gemini API.
  - Prompt: *"Dựa vào 500 khái niệm này, hãy nhóm chúng lại theo chủ đề và tạo ra các mối liên kết (edges) logic để dựng thành Cây đồ thị JSON"*.
  - Lưu kết quả vào `[Mã_Môn_Học].json` trên Google Drive.

### Task 21.2: Công cụ Xuất Dữ Liệu (Data Exporter)
- Viết thuật toán đảo ngược: Quét toàn bộ Cây tri thức hiện tại.
- Xuất dữ liệu dưới dạng file CSV chuẩn Anki (Mặt trước: Tên Node, Mặt sau: Description + AI Explanation).
- Cho phép xuất khẩu dưới dạng Markdown (`.md`) để làm tài liệu tóm tắt ôn thi in ra giấy.

### Task 21.3: Cơ chế Tự phục hồi Cú pháp (fix_syntax.py & full_fix.py)
- Sử dụng `ajv` (hoặc thư viện JSON Schema Validator tương đương).
- Khi nhận JSON từ LLM (Sprint 4, Sprint 7), hệ thống luôn chạy qua bước Validator.
- Nếu Validator báo lỗi `SyntaxError`:
  - Khởi chạy luồng `fix_syntax.py`: Dùng Regex để tự động thêm dấu ngoặc kép thiếu, hoặc bỏ các ký tự Markdown rác (như ` ```json `).
  - Nếu Regex thất bại, gọi lại API LLM giá rẻ (như Gemini Flash) với Prompt: *"Sửa lỗi cú pháp cho chuỗi JSON bị hỏng này"*.

### Task 21.4: Vá dữ liệu đầu vào (patch_input_v1.py)
- Người dùng có thể vô tình nhập các ký tự đặc biệt (như `<script>` hoặc ký tự Unicode lạ) vào ô Tên Khái niệm khi họ sửa bằng tay.
- Triển khai hàm Sanitization (Làm sạch) mọi dữ liệu text đầu vào trước khi đẩy vào RAM để đảm bảo Engine 3D không bị treo do lỗi Font chữ hoặc XSS.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Tải lên một file `vocab.csv` gồm 50 từ vựng tiếng Anh. Hệ thống tự động phân loại chúng thành 5 cụm Node (Ví dụ: Động từ, Danh từ) và nối lại thành Cây 3D.
- [ ] Cố tình bắt HTTP Request và chèn một file JSON thiếu dấu `]` ở cuối mảng. Ứng dụng tự động kích hoạt `fix_syntax.py` ở chế độ ngầm và vẫn bung Cây 3D bình thường mà không hiện màn hình Trắng (White Screen of Death).
- [ ] Bấm nút "Export to CSV", trình duyệt tự động tải xuống file Excel chứa toàn bộ nội dung của môn học.

## 4. Risk & Dependencies
- **Rủi ro 1 - CSV rác:** Người dùng tải lên file CSV không có cấu trúc chuẩn (Lỗi Encoding UTF-8, cột dữ liệu bị lệch).
- **Giải pháp:** Cung cấp tính năng "Preview & Map Columns" (Xem trước và Gắn cột). Giao diện hiển thị 3 dòng đầu tiên của file CSV để người dùng tự chọn xem Cột nào là "Tên Khái niệm", cột nào là "Giải thích" trước khi bấm nút Import.

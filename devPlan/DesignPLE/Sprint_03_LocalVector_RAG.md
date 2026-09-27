# Sprint 3: RAG Động Cá Nhân (Local FAISS & PDF Upload)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Xây dựng thành công luồng "Hấp thụ tri thức" (Ingestion). Người dùng có thể upload file PDF, hệ thống tự động băm nhỏ (chunking), tạo Vector bằng Gemini, lưu vào cấu trúc FAISS cục bộ và đồng bộ các file cấu trúc này (`.faiss`, `.pkl`) lên thư mục Google Drive của họ.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, tôi muốn tải một cuốn sách giáo khoa PDF lên môn học của mình để trợ lý AI có thể "đọc" và trả lời câu hỏi dựa trên cuốn sách đó.
- **US2:** Là một người học, tôi muốn bộ não AI (Vector DB) của sách này được lưu trên Drive của tôi để bảo mật và không tốn phí duy trì server trung tâm.
- **US3:** Là một hệ thống, tôi muốn quá trình truy xuất (hỏi đáp) phải diễn ra nhanh chóng, bằng cách tự động tải file Vector từ Drive xuống bộ nhớ tạm (RAM) khi cần thiết.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 3.1: Giao diện Upload & Xử lý File tạm (Frontend -> Backend)
- Xây dựng giao diện Drag & Drop để upload PDF.
- Backend Python (Flask/FastAPI) nhận file PDF, lưu tạm vào thư mục `temp/` của máy chủ/máy trạm nội bộ.
- Hiển thị thanh tiến trình (Progress Bar) cho các bước: Đang đọc chữ -> Đang tạo nhúng (Embedding) -> Đang lưu lên Drive.

### Task 3.2: Parsing & Semantic Chunking (LangChain)
- Tích hợp `PyPDFLoader` từ thư viện `langchain_community.document_loaders`.
- Tích hợp `RecursiveCharacterTextSplitter`: 
  - Khuyến nghị `chunk_size = 1000`, `chunk_overlap = 200` để bảo toàn ngữ cảnh câu.
  - Gắn metadata cho mỗi chunk: `source` (Tên file), `page` (Trang số mấy) để phục vụ việc trích dẫn nguồn sau này.

### Task 3.3: Embedding & Tạo Local FAISS Index
- Cấu hình mô hình `Gemini text-embedding-004` (hoặc mô hình mới nhất của Google) thông qua `langchain_google_genai`.
- Truyền danh sách chunks vào mô hình để lấy vectors.
- Khởi tạo FAISS Vector Store nội bộ: `vectorstore = FAISS.from_documents(chunks, embeddings)`.
- Lưu cấu trúc FAISS xuống file tạm trên ổ cứng (Thường sẽ sinh ra 2 file: `index.faiss` và `index.pkl`).

### Task 3.4: Đồng bộ PDF và Vector Index lên Google Drive
- Sử dụng hàm Upload đã viết ở Sprint 2.
- Gọi API đẩy 3 file sau lên thư mục `KnowledgeGalaxy_Data/[Mã_Môn_Học]/`:
  1. `[TenSach].pdf`
  2. `index.faiss`
  3. `index.pkl`
- Cập nhật ID của 3 file này vào mảng `documents_list` trong file `[Mã_Môn_Học].json` (Cấu trúc Single JSON ở Sprint 2).
- Xóa các file trong thư mục `temp/` cục bộ sau khi upload thành công.

### Task 3.5: Thuật toán Tải động (Dynamic RAG Query)
- Khi user gửi câu hỏi vào Chatbox, kích hoạt luồng sau:
  - **Check Cache:** Kiểm tra trong máy local đã có file `index.faiss` mới nhất chưa.
  - **Download:** Nếu chưa, dùng `drive_service` tải 2 file `.faiss` và `.pkl` từ Drive về thư mục `temp/`.
  - **Load to RAM:** Load cấu trúc FAISS vào RAM: `FAISS.load_local()`.
  - **Query:** Tìm kiếm (Similarity Search) lấy top 3 chunks gần nhất.
  - Cung cấp context cho Gemini để trả lời.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [x] Tính năng upload hoạt động ổn định với file PDF > 50 trang (Xử lý Timeout nếu cần).
- [x] Kiểm tra Google Drive: File PDF và các file cấu trúc `.faiss`, `.pkl` xuất hiện đúng trong thư mục môn học.
- [x] Chat thử: AI trả lời chính xác nội dung lấy từ trong file PDF vừa tải lên và có trích dẫn trang nguồn (Page number).

## 4. Risk & Dependencies
- **Rủi ro 1 - Thời gian tải (Latency):** Nếu file `.faiss` quá lớn (Vài trăm MB cho thư viện sách khổng lồ), việc tải từ Drive về máy mỗi lần hỏi sẽ mất nhiều thời gian. 
- **Giải pháp (Mitigation):** Bắt buộc triển khai Task 3.5 với cơ chế Local Cache. Nếu ID file trên Drive không đổi (không có sách mới upload thêm), hệ thống ưu tiên đọc file `.faiss` đã cache ở ổ cứng máy nội bộ, chỉ tải lại nếu Timestamp thay đổi.
- **Rủi ro 2 - Quá tải API Embedding:** Gemini API có giới hạn số token/phút (RPM, TPM). Cần xây dựng hàm `sleep` hoặc chia lô (batching) khi tạo embedding cho cuốn sách dày 1000 trang để tránh lỗi HTTP 429.

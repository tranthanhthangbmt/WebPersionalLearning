# Sprint 4: Trích xuất & Hợp nhất Cây Tri thức Tự động (Knowledge Graph Generation)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Xây dựng một "bộ não phân tích". Khi người dùng tải một tài liệu lên, hệ thống sẽ sử dụng AI (Gemini 1.5 Pro) để tự động đọc tài liệu, rút trích ra các Khái niệm cốt lõi (Nodes) và Mối quan hệ (Edges), sau đó "Móc nối" (Merge) một cách thông minh vào Cây tri thức gốc trong file JSON của người học.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, tôi muốn AI tự động vẽ cho tôi một bản đồ tư duy/cây tri thức từ cuốn sách tôi vừa tải lên, để tôi biết cuốn sách này bao gồm những mảng kiến thức nào.
- **US2:** Là một người học, nếu cuốn sách mới nói về một khái niệm mà tôi đã học ở sách cũ (ví dụ: "Đạo hàm"), tôi muốn khái niệm đó hợp nhất vào Node cũ để điểm số Mastery của tôi không bị phân mảnh.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 4.1: Prompt Engineering & LLM Structured Output
- Cấu hình `Gemini 1.5 Pro` sử dụng chế độ `response_mime_type="application/json"` để ép AI trả về dữ liệu chuẩn xác, không bị lẫn text giải thích.
- Xây dựng Prompt kỹ thuật cao. Yêu cầu AI đọc đoạn văn bản và trả về định dạng:
  ```json
  {
    "nodes": [{"id": "concept_abc", "label": "Khái niệm ABC", "description": "Tóm tắt ngắn gọn"}],
    "edges": [{"from": "concept_abc", "to": "concept_xyz", "relation": "is_prerequisite_of"}]
  }
  ```

### Task 4.2: Thuật toán Trích xuất Cuốn chiếu (Map-Reduce Graph Extraction)
- **Vấn đề:** Không thể nhét nguyên cuốn sách 1000 trang vào một lần gọi AI để vẽ đồ thị (sẽ gây nhiễu và sót thông tin).
- **Giải pháp:** Viết vòng lặp xử lý:
  - Chia tài liệu ra từng phần nhỏ (khoảng 30-50 trang/chunk).
  - Gọi LLM trích xuất Đồ thị (Sub-graph) cho từng phần.
  - Sau khi có tất cả Sub-graph, gom lại thành một tập hợp khổng lồ.

### Task 4.3: Thuật toán Hợp nhất (Entity Resolution & Merging)
- Đây là phần cốt lõi của Sprint. Viết hàm `merge_graphs(existing_json, new_sub_graphs)`.
- **Bước 1 - Lọc trùng lặp cục bộ (Deduplication):** Gom các node giống nhau trong các Sub-graph mới (VD: "Machine Learning" và "Học Máy") thành 1 node duy nhất. Có thể gọi một lần LLM nhanh hoặc dùng fuzzy string matching để nhận diện trùng lặp.
- **Bước 2 - Hợp nhất vào Cây gốc:** Đối chiếu Sub-graph với file `[Mã_Môn_Học].json` đang có.
  - Nếu khái niệm đã tồn tại -> Giữ nguyên Node ID cũ, thêm ID tài liệu mới vào mảng `documents_list` của node đó.
  - Nếu khái niệm hoàn toàn mới -> Thêm Node mới vào JSON.
  - Cập nhật lại các mảng `edges` để nối các Node mới và cũ lại với nhau.

### Task 4.4: Lưu trữ & Kích hoạt Sync
- Ghi đè cấu trúc JSON đã được Merge lại vào Local State.
- Cơ chế Auto-Sync (đã làm ở Sprint 2) sẽ tự động bắt được sự thay đổi này và đẩy file `[Mã_Môn_Học].json` mới nhất lên Google Drive.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Xử lý thành công một file PDF mẫu (khoảng 100 trang). Sau 2-3 phút chờ đợi, file `subject.json` tự động được bổ sung hàng chục Node và Edge mới.
- [ ] Không có hiện tượng rác dữ liệu: LLM trả về JSON hợp lệ 100%, không bị lỗi parse `JSONDecodeError`.
- [ ] Thuật toán Merge hoạt động đúng: Các khái niệm trùng tên không sinh ra 2 ô vuông riêng biệt trên hệ thống.

## 4. Risk & Dependencies
- **Rủi ro 1 - Lỗi Parse JSON (Hallucinations):** Dù ép kiểu, đôi khi AI vẫn sinh ra JSON sai cấu trúc hoặc lặp vòng (Circular JSON).
- **Giải pháp:** Viết hàm Try-Catch khi parse JSON. Cài đặt cơ chế Auto-Retry (Gọi lại API tối đa 3 lần nếu JSON hỏng), sử dụng thêm thư viện `pydantic` để validate cấu trúc đầu ra.
- **Rủi ro 2 - Chi phí API & Thời gian chờ:** Chạy Map-Reduce toàn bộ cuốn sách có thể tốn rất nhiều token và kéo dài 3-5 phút.
- **Giải pháp:** Ở UI (Giao diện), cần làm một bảng thông báo "AI đang đọc sách và xây dựng đồ thị... Vui lòng đi uống ly cafe và quay lại sau", xử lý tác vụ này bằng Background Worker (như Celery hoặc luồng Async) để không treo trình duyệt của người dùng.

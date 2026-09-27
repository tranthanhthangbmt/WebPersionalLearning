# Sprint 22: Tìm kiếm Toàn cục (Omni-Search) & Trợ lý Giọng nói AI (Voice Tutor)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Nâng cấp trải nghiệm người dùng (UX) lên mức hoàn hảo. Trang bị cho hệ thống công cụ Tìm kiếm Toàn cục (Global Omni-Search) kiểu "God-mode" để truy xuất kiến thức xuyên suốt hàng chục môn học. Đồng thời, tích hợp Trợ lý Giọng nói AI (Voice Tutor) và Tối ưu hóa Tiêu chuẩn Tiếp cận (Accessibility) để phục vụ đa dạng đối tượng người học (bao gồm cả người khiếm thị hoặc người thích học qua thính giác).

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một sinh viên có 15 môn học khác nhau, tôi muốn nhấn tổ hợp phím `Ctrl + K` để mở thanh tìm kiếm chung. Khi gõ từ khóa, hệ thống sẽ chỉ ra ngay khái niệm đó nằm ở môn nào và đưa tôi đến đúng điểm sáng đó trên Không gian 3D.
- **US2:** Là một người thích học trong lúc đi bộ hoặc làm việc nhà, tôi muốn bấm nút Micro để nói chuyện trực tiếp với Trợ lý AI, và AI sẽ đọc đáp án (Text-to-Speech) cho tôi nghe thay vì phải dán mắt vào màn hình đọc chữ.
- **US3:** Là một người dùng bị mù màu, tôi muốn hệ thống có chế độ hiển thị "Độ tương phản cao" (High Contrast) và cho phép tôi điều hướng Cây tri thức 3D hoàn toàn bằng bàn phím (Phím Tab / Phím Mũi tên) mà không cần dùng chuột.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 22.1: Động cơ Tìm kiếm Toàn cục (Omni-Search Engine)
- Tích hợp thư viện tìm kiếm mờ (Fuzzy Search) như `Fuse.js` ở Frontend.
- Khi khởi động ứng dụng, viết một Background Worker quét ngầm qua tất cả các file `[Mã_Môn_Học].json` trên Google Drive/Local Storage để lập chỉ mục (Indexing) toàn bộ mảng `nodes`.
- Xây dựng giao diện thanh tìm kiếm trung tâm (gọi bằng phím tắt `Ctrl + K` / `Cmd + K`).
- Khi user chọn một kết quả, thực hiện chuyển trang (Routing) sang môn học đó và kích hoạt hàm `Camera.flyTo(node)` (Sprint 5) để bay thẳng đến Node mục tiêu.

### Task 22.2: Tích hợp Trợ lý Giọng nói AI (Voice Tutor)
- Thêm biểu tượng Microphone vào Omni-Drawer.
- **Speech-to-Text (Nghe):** Sử dụng `Web Speech API` (hoặc API Whisper nếu cần độ chính xác tiếng Việt cao) để chuyển đổi giọng nói người dùng thành văn bản (Text) và đưa vào ô nhập liệu RAG.
- **Text-to-Speech (Nói):** Nâng cấp hàm gọi LLM (Gemini). Khi có đáp án JSON trả về, trích xuất phần `explanation` và đưa qua API Text-to-Speech (Ví dụ: Google Cloud TTS hoặc Web Speech Synthesis) để AI cất tiếng đọc đáp án. Hiển thị sóng âm (Audio visualizer) mượt mà lúc AI đang nói.

### Task 22.3: Tối ưu Tiêu chuẩn Tiếp cận (Accessibility - A11y)
- Rà soát lại toàn bộ UI (Buttons, Modals, Forms) và bổ sung các thuộc tính `aria-label`, `role` chuẩn WCAG.
- **Keyboard Navigation trên 3D:** Khá khó vì 3D canvas thường chặn bàn phím. Giải pháp: Viết logic khi người dùng bấm phím `Tab`, camera sẽ tuần tự di chuyển theo thứ tự mảng `nodes` hoặc nhảy theo các đường `edges` (từ Khái niệm mẹ xuống Khái niệm con).
- Thêm nút Toggle "Chế độ mù màu": Đổi dải màu Xanh/Đỏ/Vàng của thuật toán Mastery (Sprint 8) sang dạng họa tiết hoặc dải màu thân thiện hơn (Ví dụ: Xanh dương / Cam / Vạch kẻ).

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Bấm `Ctrl+K` ở trang chủ, gõ từ "Gia tốc", kết quả trả về: *Nằm trong môn Vật lý 1*. Bấm Enter, màn hình chuyển sang 3D môn Vật lý và bay thẳng đến Node Gia tốc.
- [ ] Bấm nút Micro và nói "Giải thích định luật Newton". Trợ lý AI trả lời bằng văn bản kết hợp với giọng đọc rõ ràng, tự nhiên.
- [ ] Dùng công cụ Google Lighthouse chấm điểm Accessibility (A11y) đạt > 90 điểm.

## 4. Risk & Dependencies
- **Rủi ro 1 - Độ trễ Giọng nói (Voice Latency):** Phải mất vài giây AI mới sinh xong đáp án text, sau đó mất thêm 1-2 giây để chuyển Text sang Speech, gây cảm giác AI bị "đơ".
- **Giải pháp:** Sử dụng cơ chế Streaming (Trả kết quả từng chữ). Bất cứ khi nào Gemini sinh xong một câu hoàn chỉnh (nhận diện bằng dấu chấm câu `.`), hệ thống lập tức cắt câu đó gửi cho TTS để đọc ngay lập tức trong lúc LLM vẫn đang sinh các câu tiếp theo ở dưới nền.

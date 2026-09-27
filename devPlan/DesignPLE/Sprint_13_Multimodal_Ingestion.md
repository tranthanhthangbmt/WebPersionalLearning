# Sprint 13: Hấp thụ Tri thức Đa phương tiện (Multi-modal Ingestion)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Mở rộng khả năng "Tiêu hóa tri thức" của hệ thống vượt ra khỏi giới hạn của văn bản (PDF/Website). Tích hợp các luồng xử lý Video (MP4), Âm thanh (MP3/Podcast) và link YouTube, cho phép AI nghe, xem, bóc băng (Transcript), và nhúng vào Vector DB cũng như trích xuất Cây tri thức như một tài liệu bình thường.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một người học, tôi muốn dán một đường link video bài giảng trên YouTube vào hệ thống để AI tự động xem, tóm tắt và vẽ Cây tri thức cho tôi.
- **US2:** Là một người học, tôi muốn tải lên một file ghi âm (Podcast hoặc file ghi âm bài giảng trên lớp) để RAG có thể trả lời các câu hỏi dựa trên lời giảng của thầy cô.
- **US3:** Là một người học, khi tôi click vào một Node kiến thức được tạo từ Video, tôi muốn hệ thống có trình phát video (Video Player) và tự động tua (seek) đến đúng giây mà khái niệm đó được nhắc tới.

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 13.1: Module Xử lý YouTube (YouTube Transcript API)
- Tích hợp thư viện `youtube-transcript-api` (hoặc `yt-dlp` để lấy metadata).
- Khi người dùng dán Link YouTube, hệ thống ngầm tải về file Phụ đề (Transcript) kèm theo dấu thời gian (Timestamps).
- Gắn metadata cho mỗi đoạn chunk: `{"source": "YouTube Video URL", "start_time": 120, "end_time": 150}`.

### Task 13.2: Module Xử lý Audio/Video Local (Speech-to-Text)
- Xây dựng giao diện upload file MP3/MP4 (Sử dụng luồng upload lên Drive tương tự Sprint 3).
- Tích hợp API `Whisper` (của OpenAI) hoặc sử dụng tính năng Multi-modal của `Gemini 1.5 Pro` để trực tiếp nghe và bóc băng file Audio/Video thành văn bản.
- Kết xuất file Transcript (VTT/SRT) và lưu đồng bộ lên thư mục Google Drive của môn học.

### Task 13.3: Tích hợp RAG Đa phương tiện
- Dùng `LangChain` Document Loaders chuyên dụng cho Video/Audio để xử lý file Transcript vừa tạo.
- Đưa qua `RecursiveCharacterTextSplitter` và `Gemini text-embedding` để lưu vào FAISS Index hiện có.
- Cập nhật hàm Query (Sprint 7): Khi AI giải thích, ngoài việc trích dẫn "Trang số 45", giờ AI có thể trích dẫn "Tại phút 02:15 trong Video X".

### Task 13.4: Xây dựng AI Video Player (Tích hợp UI)
- Tích hợp file `ai_video_player.py` / Component React tương ứng vào Omni-Drawer.
- Khi người dùng chọn trích dẫn là một Video, Omni-Drawer sẽ hiển thị khung phát Video.
- Viết Javascript để tự động gọi hàm `player.seekTo(135)` (Tua đến giây thứ 135) dựa trên metadata thời gian của chunk đang được RAG sử dụng.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Dán link YouTube vào ô Ingestion, hệ thống tải được phụ đề và tạo thành công file cấu trúc JSON/FAISS lưu lên Drive.
- [ ] Hỏi AI một câu về nội dung video, AI trả lời đúng và kèm theo nút "Xem tại 05:20".
- [ ] Bấm vào nút trích dẫn, khung Video hiện ra và tự động bắt đầu phát từ phút 05:20.
- [ ] Cây tri thức 3D xuất hiện thêm các Khái niệm (Nodes) được AI trích xuất tự động từ lời thoại trong Video.

## 4. Risk & Dependencies
- **Rủi ro 1 - Video không có phụ đề:** Rất nhiều video YouTube tiếng Việt không có phụ đề (CC) sẵn, thư viện `youtube-transcript-api` sẽ bị lỗi.
- **Giải pháp:** Nếu video không có CC, hiển thị thông báo: *"Video này chưa có phụ đề đóng. Bạn có muốn dùng AI (Whisper) để tự động bóc băng không? Việc này có thể tốn 3-5 phút."*
- **Rủi ro 2 - Dung lượng file Video:** Tải MP4 lên Local Storage hoặc chuyển qua API bóc băng sẽ rất nặng.
- **Giải pháp:** Tối ưu hóa ở Frontend, nén âm thanh hoặc chỉ tách xuất luồng Audio (chiết xuất MP3 từ MP4 bằng FFmpeg WASM ngay trên trình duyệt) rồi mới gửi đi xử lý để giảm tải băng thông.

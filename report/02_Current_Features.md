# PHẦN 2: CÁC CHỨC NĂNG ĐÃ HOÀN THÀNH VÀ ĐANG VẬN HÀNH (SPRINTS 1-3)

Tính đến thời điểm hiện tại, dự án đã hoàn tất xuất sắc Giai đoạn Nền tảng (Foundation) bao gồm 3 Sprint đầu tiên. Hệ thống đã có khả năng hoạt động độc lập, khép kín từ khâu xác thực, lưu trữ đến xử lý tri thức bằng Trí tuệ Nhân tạo. Dưới đây là mô tả chi tiết về các cụm chức năng đang vận hành:

## 2.1. Phân quyền Xác thực & Khởi tạo Môi trường (Sprint 1)

Hệ thống đã loại bỏ hoàn toàn việc lưu trữ mật khẩu nội bộ, thay vào đó sử dụng tiêu chuẩn bảo mật toàn cầu:
- **Xác thực qua Google OAuth 2.0:** Người dùng đăng nhập chỉ với một click chuột an toàn tuyệt đối. Hệ thống thu thập và xử lý các Access Token và Refresh Token để duy trì phiên làm việc liên tục.
- **Tự động Khởi tạo Không gian Dữ liệu (Auto-Provisioning):** Ngay lần đăng nhập đầu tiên, hệ thống sẽ gọi API tự động sinh ra một cấu trúc thư mục khép kín mang tên `KnowledgeGalaxy_Data` ngay trên Google Drive của cá nhân người dùng. Cấu trúc này bao gồm một thư mục chứa dữ liệu Môn học (`Subjects/`) và file cấu hình cá nhân `profile.json`.

## 2.2. Cơ chế Đồng bộ Tự động (Single JSON Auto-Sync) (Sprint 2)

Thay vì liên tục tạo kết nối Database (gây trễ và tốn chi phí máy chủ), ứng dụng áp dụng quy trình đồng bộ không trạng thái:
- **Kiến trúc Single JSON:** Toàn bộ thông tin từ lịch sử điểm số, Mức độ thuần thục (Mastery), hay Cấu trúc cây tri thức đều được gói gọn vào những file JSON độc lập.
- **Vòng lặp Debounce (Background Async Loop):** Trình quản lý trạng thái (`SyncStateManager`) sẽ ghi nhận mọi thao tác học tập ngay lập tức lên RAM để giao diện phản hồi 0ms. Sau đó, một tiến trình chạy ngầm sẽ đếm ngược 5 giây kể từ thao tác cuối cùng để tiến hành "Ghi đè" (Update) file lên Google Drive, chống hiện tượng sinh ra rác dữ liệu.
- **Cơ chế Tự phục hồi (Auto-Rehydrate):** Nếu người học tải lại trang hoặc mở trình duyệt ẩn danh, hệ thống tự động quét và tải file JSON mới nhất từ Drive về máy, đảm bảo tính liên tục của quá trình học tập.

## 2.3. Hấp thụ Tri thức và Kho lưu trữ Vector (Local RAG) (Sprint 3)

Đây là chức năng thể hiện sức mạnh của AI trong việc chuyển hóa tài liệu thô thành tài liệu tương tác:
- **Ingestion Pipeline:** Hệ thống cung cấp giao diện tải lên (Drag & Drop) cho file PDF học thuật. Tích hợp `PyPDFLoader` và công cụ băm nhỏ văn bản (`RecursiveCharacterTextSplitter`) nhằm cắt văn bản thành các đoạn có ý nghĩa, bảo toàn ngữ cảnh.
- **Tạo Vector Cục bộ (Local FAISS):** Tận dụng sức mạnh từ mô hình nhúng (Embedding) của Google Gemini 1.5, hệ thống chuyển hóa văn bản thành mảng vector siêu chiều và lưu trữ trực tiếp vào ổ cứng cục bộ (`.faiss` và `.pkl`). Thuật toán Batching (chia lô nhỏ) cũng đã được tối ưu để xử lý sách hàng ngàn trang mà không bị lỗi giới hạn API (HTTP 429).
- **Lưu trữ AI dài hạn (Vector Backup):** Không chỉ giữ trên máy, hệ thống sẽ đẩy toàn bộ cấu trúc não bộ AI này lên chung thư mục môn học trên Google Drive.

## 2.4. Trợ lý Ảo Omni-Tutor & Truy vấn Động (Dynamic Query)

- **Chatbot Tương tác (Omni-Tutor):** Một giao diện hội thoại được gắn chặt vào quá trình học tập. 
- **Tự động Tải tài liệu RAG:** Khi người dùng đặt câu hỏi, nếu máy chưa có sẵn sách, hệ thống tự động kết nối lên Drive để tải bản sao lưu file Vector về RAM.
- **Cơ chế Trích dẫn (Citation System):** Trợ lý AI kết hợp kỹ thuật Tìm kiếm tương đồng (Similarity Search) lấy ra top 3 đoạn văn liên quan nhất để sinh câu trả lời. Điều đặc biệt là AI bị ép buộc phải tuân thủ nghiêm ngặt dữ liệu sách giáo khoa và luôn **có trích dẫn trang nguồn (Page Number)** một cách minh bạch cho sinh viên kiểm chứng.

## 2.5. Hệ thống Trò chơi hóa Cơ bản (Gamification Core)

Mọi thao tác của hệ thống đều đã được thiết kế ngầm để tạo động lực:
- **Động cơ Điểm số (XP Engine):** Mọi sự kiện đều kích hoạt `add_xp`. Điểm số XP tự động cập nhật và hiển thị một cách sinh động ở thanh điều hướng.
- **Chuỗi học tập (Streak) & Daily Check-in:** Xây dựng ý thức kỷ luật bằng cách trao thưởng Bonus đăng nhập mỗi ngày và cảnh báo người dùng duy trì chuỗi Streak.

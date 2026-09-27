# PHẦN 3: LỘ TRÌNH PHÁT TRIỂN VÀ CÁC CHỨC NĂNG DỰ TRÙ (SPRINTS 4-24)

Nhờ vào việc đã hoàn thành bộ khung nền tảng vô cùng vững chắc về xác thực và lưu trữ phân tán, 21 Sprints tiếp theo của dự án sẽ tập trung vào việc áp dụng các công nghệ AI tiên tiến nhất để cá nhân hóa việc học tập, được chia thành 4 Giai đoạn (Phases) chiến lược:

## GIAI ĐOẠN 1: SỐ HÓA VÀ TRÍCH XUẤT TRI THỨC (Sprints 4 - 7)
Mục tiêu là biến các file văn bản tĩnh thành dữ liệu tương tác động.

- **Sprint 4: Tự động Trích xuất Cây Tri thức (Graph Extraction & Merge)**
  Sử dụng mô hình Gemini 1.5 Pro với thuật toán Map-Reduce để đọc toàn bộ sách giáo khoa, tự động vẽ ra hệ thống Cây Tri thức (Knowledge Graph - gồm Nodes và Edges). Hệ thống sẽ tự động đối chiếu và hợp nhất (Entity Resolution) với Cây tri thức hiện có để không bị trùng lặp khái niệm.
  
- **Sprint 5: Trực quan hóa Không gian 3D (3D Knowledge Graph)**
  Chuyển đổi các file JSON thành một vũ trụ 3D sinh động trên trình duyệt, nơi sinh viên có thể "bay lượn" và tương tác trực quan với các vì sao tri thức của mình.

- **Sprint 6: Chia sẻ Tri thức ngang hàng (Learner Sharing P2P)**
  Xây dựng cơ chế cho phép sinh viên đóng gói cây tri thức của mình và gửi cho bạn bè qua dạng một file mã hóa, thúc đẩy việc học nhóm.

- **Sprint 7: Máy phát sinh Trắc nghiệm tự động (Auto Quiz Generator)**
  Hệ thống AI tự động nhặt các khái niệm từ Cây tri thức để tạo ra các đề kiểm tra theo chuẩn trắc nghiệm/tự luận, kèm lời giải chi tiết giúp đánh giá năng lực liên tục.

## GIAI ĐOẠN 2: KHOA HỌC NHẬN THỨC VÀ ĐÁNH GIÁ (Sprints 8 - 12)
Mục tiêu là tích hợp các học thuyết giáo dục vào đo lường điểm số.

- **Sprint 8: Đánh giá theo Thang Bloom (Mastery & Bloom Scoring)**
  Chuyển đổi điểm số thông thường sang đánh giá chi tiết theo 6 bậc nhận thức Bloom (Nhớ, Hiểu, Vận dụng, Phân tích, Đánh giá, Sáng tạo).
  
- **Sprint 9: Lặp lại ngắt quãng (Spaced Repetition System - SRS)**
  Tích hợp các thuật toán trí nhớ (như SuperMemo/Anki). Hệ thống sẽ tính toán "Đường cong quên lãng" (Ebbinghaus Forgetting Curve) để nhắc nhở ôn luyện đúng vào thời điểm sinh viên sắp quên kiến thức.

- **Sprint 10: AI Dẫn đường Chủ động (Proactive Pathfinder)**
  Phát triển AI chủ động: Thay vì đợi sinh viên hỏi, AI sẽ quét toàn bộ cây tri thức để vạch ra "Chặng đường học hôm nay", điều hướng vào những Node đang bị hổng kiến thức.

- **Sprint 11: Học tập Ngoại tuyến (PWA & Offline Gamification)**
  Cấu hình Progressive Web App, biến nền tảng web thành ứng dụng có thể hoạt động ngoại tuyến. Sinh viên có thể học và nhận XP khi đi xe buýt không có mạng, hệ thống tự động đồng bộ khi có Internet.

- **Sprint 12: Đánh giá hiệu quả Kirkpatrick (Beta Eval)**
  Tích hợp bộ chỉ số đo lường hiệu quả đào tạo dựa trên mô hình Kirkpatrick, cung cấp cái nhìn tổng quan về chất lượng chương trình cho giảng viên.

## GIAI ĐOẠN 3: ĐA PHƯƠNG TIỆN VÀ XÃ HỘI HÓA (Sprints 13 - 17)
Mục tiêu mở rộng nguồn dữ liệu đầu vào và tạo cộng đồng học tập.

- **Sprint 13: Hấp thụ Đa phương thức (Multimodal Ingestion)**
  Mở rộng năng lực của RAG để xử lý Audio, Video (phân tích video YouTube) và Hình ảnh bên cạnh văn bản.
  
- **Sprint 14: Hợp tác Thời gian thực (Realtime Collaboration)**
  Cho phép nhiều sinh viên cùng tham gia thảo luận và kết nối các Node trên Cây tri thức cùng lúc giống như Google Docs.

- **Sprint 15: Hệ thống Phân tích & Bảng điều khiển (Analytics Dashboards)**
  Phát triển các báo cáo biểu đồ trực quan sâu sắc (Learning Analytics) giúp sinh viên theo dõi chính xác sự tiến bộ của mình.

- **Sprint 16: Thư viện Công cộng Mở (Social Public Library)**
  Xây dựng một "Chợ Ứng dụng Tri thức" phi tập trung, nơi bất kỳ ai cũng có thể xuất bản cây tri thức của mình để cộng đồng tải về học tập.

- **Sprint 17: Tài nguyên Tương tác (Interactive Resources)**
  Tích hợp các bài thí nghiệm mô phỏng, kéo-thả, hỗ trợ tốt hơn cho khối ngành khoa học kỹ thuật.

## GIAI ĐOẠN 4: TINH CHỈNH VÀ THƯƠNG MẠI HÓA (Sprints 18 - 24)
Mục tiêu hoàn thiện các thuật toán hạch lõi và chuẩn bị ra mắt thị trường.

- **Sprint 18-19: Tinh chỉnh Trải nghiệm (Review Page & Onboarding)**
  Xây dựng màn hình tổng kết quá trình học và luồng hướng dẫn người dùng mới (Onboarding Wizard) thân thiện.
  
- **Sprint 20: Hồ sơ Năng lực Số (Portfolio Bridge)**
  Tổng hợp kết quả của Cây tri thức thành một bảng CV năng lực điện tử, minh chứng khả năng thực tế để nộp cho doanh nghiệp.

- **Sprint 21: Toàn vẹn Dữ liệu (Data Portability & Self Healing)**
  Đảm bảo tuân thủ tiêu chuẩn giáo dục (SCORM/xAPI), tăng cường cơ chế phát hiện và tự động sửa chữa file JSON bị lỗi.

- **Sprint 22: Trải nghiệm rảnh tay (OmniSearch & Voice AI)**
  Ra mắt chức năng "Ctrl+K" để tìm kiếm toàn cục (Global Search) và chức năng trò chuyện với AI bằng giọng nói tự nhiên.

- **Sprint 23: Lõi Theo dõi Tri thức Bayes (PKT Bayesian Engine)**
  Đây là nâng cấp thuật toán lớn nhất: Chuyển đổi mô hình điểm số tĩnh sang mô hình xác suất học máy (Bayesian Knowledge Tracing) để dự đoán chính xác xác suất một học viên trả lời đúng câu hỏi.

- **Sprint 24: Đóng gói Thương mại (Final Polish & Commercialization)**
  Hoàn thiện hệ thống bảo mật, dọn dẹp mã nguồn (Code Refactoring), thiết lập hệ thống thu phí bảo trì dịch vụ (SaaS/Freemium Paywall).

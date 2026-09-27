# Sprint 14: Không Gian Học Tập Cộng Tác (Real-time Multiplayer Graph)

**Thời gian dự kiến:** 2 Tuần
**Mục tiêu (Sprint Goal):** 
Nâng cấp hệ thống từ chế độ "Chơi đơn" (Single-player) sang "Chơi mạng" (Multi-player). Cho phép một nhóm sinh viên cùng tham gia vào một Không gian chung (Shared Workspace) để cùng nhau upload tài liệu, xây dựng Cây tri thức theo thời gian thực (Real-time), nhưng vẫn giữ được sự cá nhân hóa về điểm số năng lực của từng người.

## 1. User Stories (Câu chuyện người dùng)
- **US1:** Là một trưởng nhóm học tập, tôi muốn tạo một "Phòng học chung" và gửi link mời 3 người bạn vào để cùng nhau chuẩn bị ôn thi cuối kỳ môn Lịch sử Đảng.
- **US2:** Là một thành viên trong nhóm, khi bạn tôi tải lên một file PDF và AI vẽ ra 5 Khái niệm mới, tôi muốn nhìn thấy 5 Khái niệm đó "nảy mầm" ngay lập tức trên màn hình 3D của mình mà không cần tải lại trang.
- **US3:** Là một thành viên trong nhóm, dù chúng tôi dùng chung Cây tri thức, nhưng tôi muốn điểm số Mastery và tiến độ làm Quiz của tôi phải được giữ bí mật và cá nhân hóa (Node của tôi có thể màu Đỏ, trong khi Node của bạn tôi màu Xanh).

## 2. Technical Tasks (Công việc Kỹ thuật Chi tiết)

### Task 14.1: Tách biệt Trạng thái Dữ liệu (State Separation)
- Ở Sprint 2, ta dùng 1 file JSON duy nhất. Giờ cần tách kiến trúc ra làm 2 phần logic:
  - **Shared State (Cấu trúc chung):** Chứa mảng `nodes` (ID, Label, Description) và `edges`. Lưu trên thư mục Google Drive dùng chung (Shared Drive/Folder).
  - **Personal State (Trạng thái cá nhân):** Chứa `mastery_score`, `bloom_level`, `fatigue` của từng Node ứng với `user_id`. Lưu ở Google Drive cá nhân của riêng người đó.
- Khi render 3D, hệ thống sẽ chập (merge) 2 state này lại trên RAM: Lấy cấu hình Node từ Shared State và lấy Màu sắc (Color) từ Personal State.

### Task 14.2: Tích hợp Engine Thời gian thực (WebSocket / Firebase)
- Sử dụng file `realtime_sync.py` hiện có trong hệ thống hoặc tích hợp Firebase Realtime Database.
- Khi User A thực hiện thao tác (Thêm Node, Xóa Edge, Upload PDF xong), Client A sẽ gửi một sự kiện (Event: `GRAPH_MUTATION`) lên Server/Firebase.
- Server lập tức `Broadcast` sự kiện này đến tất cả các Client đang trong cùng "Phòng học" (Session Room).
- Client B nhận được sự kiện và tự động cập nhật mảng JSON Local, kích hoạt Engine 3D vẽ lại Node mới bằng hiệu ứng mượt mà (Animation).

### Task 14.3: Xử lý Xung đột Dữ liệu (CRDT Algorithm)
- Nếu User A đổi tên Node 1 thành "Toán rời rạc" và ở cùng một phần ngàn giây, User B đổi tên Node 1 thành "Discrete Math", hệ thống sẽ bị lỗi.
- Tích hợp thuật toán **CRDT (Conflict-free Replicated Data Type)** (Ví dụ thư viện Yjs) để tự động phân xử và hợp nhất các thay đổi đồng thời mà không làm hỏng cấu trúc JSON.

### Task 14.4: UI Hiện diện Cộng tác (Presence & Cursors)
- Để tạo cảm giác "Có người đang cùng học", hệ thống sẽ gửi tọa độ Camera 3D hoặc vị trí chuột của các thành viên lên WebSocket.
- Render các Avatar nhỏ (Có tên User A, User B) trôi nổi trong không gian 3D, báo hiệu cho biết User B đang tập trung đọc tài liệu ở Node nào.

## 3. Definition of Done (Tiêu chuẩn Hoàn thành)
- [ ] Mở 2 trình duyệt ẩn danh đóng vai 2 User khác nhau, cùng join vào một Link Môn học.
- [ ] User A bấm chuột phải tạo Node "Khái niệm mới". Cùng lúc đó trên màn hình User B, Node "Khái niệm mới" mọc ra với hiệu ứng phình to.
- [ ] User A làm Quiz đúng và Node chuyển màu Xanh. Trên màn hình User B, Node đó vẫn giữ màu Đỏ (Giữ nguyên tính cá nhân hóa năng lực).
- [ ] Khi tất cả người dùng thoát khỏi phòng, bản Snapshot cuối cùng của Cây tri thức được tự động Sync lên thư mục Google Drive dùng chung.

## 4. Risk & Dependencies
- **Rủi ro 1 - Nút thắt cổ chai Google Drive:** Google Drive API không được thiết kế cho thao tác đọc/ghi tính bằng mili-giây (Real-time). Nếu gọi liên tục sẽ bị khóa API ngay lập tức.
- **Giải pháp:** Trong suốt phiên học cộng tác (Session), mọi giao tiếp đều diễn ra qua WebSocket/Firebase (Task 14.2). Google Drive chỉ đóng vai trò là "Kho lưu trữ vĩnh viễn" (Cold Storage), hệ thống chỉ đẩy file JSON lên Drive một lần duy nhất khi Session kết thúc hoặc mỗi 10 phút một lần dưới dạng Backup.

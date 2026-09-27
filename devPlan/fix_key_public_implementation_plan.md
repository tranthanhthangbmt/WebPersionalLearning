# Khắc phục cảnh báo "Publicly leaked secret" cho Firebase API Key

Chào bạn, việc GitHub cảnh báo là do bạn đã để lộ API Key trực tiếp trong mã nguồn đẩy lên server công cộng. Mặc dù API Key của Firebase bản chất là "public" cho trình duyệt, nhưng việc để lộ giúp kẻ xấu có thể lợi dụng tài nguyên của bạn nếu bạn không thiết lập giới hạn (Restrictions).

## User Review Required

> [!IMPORTANT]
> Sau khi thực hiện các thay đổi mã nguồn dưới đây, bạn **BẮT BUỘC** phải thực hiện thêm 2 bước trên Google Console để xử lý triệt để cảnh báo của GitHub:
> 1. **Rotate Secret (Đổi khóa):** Tạo API Key mới và xóa Key cũ đã bị lộ.
> 2. **Restrict API Key (Giới hạn khóa):** Thiết lập chỉ cho phép Key chạy trên tên miền của bạn (ví dụ: `aiud-exam.firebaseapp.com` và `localhost`).

## Proposed Changes

Tôi sẽ tách phần cấu hình nhạy cảm ra một file riêng và dùng `.gitignore` để ngăn GitHub theo dõi file đó trong tương lai.

### [Module_1-6]

#### [NEW] [firebase-config.js](file:///i:/MY_CODE/AIUD_March2026/Module_1-6/firebase-config.js)
Tạo file chứa cấu hình Firebase thực tế (File này sẽ bị ẩn khỏi GitHub).

#### [NEW] [firebase-config.example.js](file:///i:/MY_CODE/AIUD_March2026/Module_1-6/firebase-config.example.js)
File mẫu để bạn hoặc người khác biết cách cấu hình khi tải code về.

#### [MODIFY] [midterm.html](file:///i:/MY_CODE/AIUD_March2026/Module_1-6/midterm.html)
Thay thế đoạn code cấu hình trực tiếp bằng việc gọi file `firebase-config.js`.

#### [MODIFY] [admin.html](file:///i:/MY_CODE/AIUD_March2026/Module_1-6/admin.html)
Tương tự, tách cấu hình ra khỏi file HTML.

---

### [Root]

#### [NEW] [.gitignore](file:///i:/MY_CODE/AIUD_March2026/.gitignore)
Thêm quy tắc để Git không bao giờ đẩy file `firebase-config.js` lên GitHub nữa.

## Verification Plan

### Manual Verification
1. Kiểm tra xem ứng dụng có còn hoạt động bình thường không (Firebase có kết nối được không).
2. Thử lệnh `git status` để xác nhận file `firebase-config.js` đã bị bỏ qua (không hiện trong danh sách "Untracked files").
3. Hướng dẫn người dùng các bước trên giao diện Google Cloud Console.

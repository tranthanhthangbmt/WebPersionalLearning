# KẾ HOẠCH LẬP TRÌNH: KIẾN TRÚC OMNI-DRAWER (GIA SƯ THƯỜNG TRỰC)

Dựa trên bộ não v2.0 vừa xây dựng, chúng ta cần tạo ra "Thân xác" cho Omni-Tutor. Nó không được nằm trong một Tab cố định, mà phải là một lớp phủ (Overlay) tồn tại độc lập trên mọi giao diện.

Dưới đây là bản thiết kế kỹ thuật chi tiết bằng Python (NiceGUI) chuẩn MIT.

---

## 1. PHÂN TÍCH KIẾN TRÚC MÃ NGUỒN (CODE ARCHITECTURE)

### 1.1. Cấu trúc Giao diện Toàn cục (Global UI Overlay)
Trong `main.py`, chúng ta sẽ bổ sung hai thành phần UI tồn tại ngoài vòng lặp của các Tabs:
1. **Omni-FAB (Floating Action Button):** Một nút tròn tinh tế lơ lửng ở góc dưới cùng bên phải màn hình `fixed bottom-6 right-6 z-[100]`. Tích hợp hiệu ứng `pulse` (đập nhịp nhàng) khi có cảnh báo Ebbinghaus.
2. **Omni-Drawer (Khung trượt lề phải):** `ui.right_drawer(value=False)`. Khung này sẽ chứa toàn bộ logic Chatbot. Khi mở ra, nó đổ bóng (shadow-2xl) và không đẩy nội dung chính sang trái (Overlay mode).

### 1.2. Bộ máy Nhận thức Ngữ cảnh (Context Awareness Engine)
Làm sao để AI ở trong Drawer biết sinh viên đang xem tab nào hay bài học nào?
Chúng ta cần xây dựng một "Trạm gác" lưu trữ trạng thái toàn cục (Global State) trong Session của người dùng:
```python
app.storage.user['omni_context'] = {
    'current_tab': 'dashboard',     # dashboard, graph_studio, library, assessment...
    'subject_id': None,             # ID của môn học đang mở
    'node_id': None,                # ID của bài học/tiết học
    'node_content': None,           # Tóm tắt text/script đang đọc
    'error_streak': 0               # Đếm số lần sai liên tiếp
}
```
**Cơ chế bắt sự kiện (Event Hooking):**
Mỗi khi người dùng bấm vào một Tab ở lề trái, hoặc bấm vào một Nút trên Graph Studio, hàm `on_click` tương ứng sẽ tự động ghi đè dữ liệu mới vào `app.storage.user['omni_context']`.

### 1.3. Động cơ Phản hồi (Persona Engine Update)
Cập nhật `persona_engine.py` để nó đọc file `Tutor AI Instruction v2.0 - Contextual Omni-Agent.md`.
Khi sinh viên chat, hàm xử lý sẽ gói tin nhắn của sinh viên kèm theo toàn bộ biến số từ `omni_context` để bắn lên Google API (Gemini).

---

## 2. KẾ HOẠCH THỰC THI TỪNG BƯỚC (STEP-BY-STEP EXECUTION)

### Bước 1: Tạo Module Omni-Drawer độc lập (`omni_tutor_ui.py`)
Thay vì nhồi nhét code chat vào `main.py` vốn đã nặng, tôi sẽ tạo một file riêng biệt `omni_tutor_ui.py`. 
File này sẽ xuất ra một class hoặc hàm `build_omni_drawer()`. 
*Thiết kế UX:*
- Thanh Header của Drawer: Hiển thị một nhãn (Badge) chỉ báo ngữ cảnh (Ví dụ: `📍 Đang theo dõi: Môn Trí tuệ Nhân tạo - Nút: Vòng lặp For`).
- Khung Chat: Box tin nhắn kiểu iMessage hiện đại, render Markdown mượt mà.

### Bước 2: Tích hợp vào `main.py`
- Khởi tạo nút FAB (Floating Button) và Drawer ở cấp độ layout cao nhất.
- Bắt sự kiện chuyển Tab (Dashboard, Graph Studio, Library) để cập nhật biến `omni_context['current_tab']`.

### Bước 3: Đẩy Ngữ cảnh Chi tiết (Deep Context Injection)
- Mở file `bloom_hub_page.py` và `node_content_engine.py` (Nơi render bài giảng và Quiz).
- Thêm logic: Khi sinh viên mở một Node, lập tức copy toàn bộ nội dung của Node đó (Tiêu đề, Tóm tắt lý thuyết/Video script) ném vào biến `omni_context['node_content']`.

### Bước 4: Chế tạo Bộ phân giải JSON (JSON Payload Resolver)
Trong hàm nhận phản hồi từ Gemini của Omni-Drawer, viết một đoạn Regex để tách khối `---SYSTEM_JSON_START---`.
Viết logic điều khiển: 
- Nếu `json_data['trigger_fireworks'] == True` -> Chạy lệnh Javascript bắn pháo hoa.
- Nếu `json_data['fatigue_level'] == "high_critical"` -> Khóa thẻ `ui.input()` của khung chat.

---

## 🙋‍♂️ Yêu Cầu Phê Duyệt (User Review Required)

> [!WARNING]
> Việc tạo Right-Drawer sẽ thay đổi bố cục tổng thể của ứng dụng. Tuy nhiên, nó sẽ biến nền tảng của bạn trông cực kỳ "Pro" (giống như Copilot trên Windows hay thanh công cụ của Notion AI).

Bạn có đồng ý với phương án: **Tạo một file mới `omni_tutor_ui.py` để đóng gói toàn bộ giao diện Chat, sau đó `import` vào `main.py` để tránh làm phình to mã nguồn không?**
Nếu đồng ý, tôi sẽ tiến hành Code Bước 1 và 2 ngay bây giờ!

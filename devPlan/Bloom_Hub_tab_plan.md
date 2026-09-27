# Integration of Bloom Hub into Main Layout with Improved UI/UX

Hiện tại tính năng "Bloom Hub" (Học tập sâu) đang mở ra dưới dạng một cửa sổ popup/tab trình duyệt riêng biệt (thông qua `window.open` và endpoint `@ui.page`). Người dùng muốn tích hợp tính năng này trực tiếp vào giao diện chính của ứng dụng dưới dạng một Tab mới (giống như "Tổng quan", "Graph Studio", v.v.) và nâng cấp UI/UX đẹp mắt hơn.

## User Review Required
> [!IMPORTANT]
> Việc tích hợp này sẽ thay đổi luồng trải nghiệm (user flow). Khi nhấn "BLOOM HUB" trên mô hình 3D, ứng dụng sẽ tự động chuyển sang tab "Bloom Hub" ngay trong màn hình thay vì bật popup mới. Bạn hãy xem xét và xác nhận luồng này có phù hợp với mong muốn không nhé.

## Kế hoạch triển khai

### 1. Refactor `bloom_hub_page.py` thành một UI Component
- Loại bỏ `@ui.page('/bloom_hub/...')` và hàm `register_bloom_hub_page()`.
- Chuyển logic thành một hàm Async Component: `async def build_bloom_hub_ui(container, subject_id, node_id, user, switch_back_callback)`.
- Nâng cấp UI/UX bên trong:
  - Áp dụng **Glassmorphism** (nền trong suốt, đổ bóng mờ) cho các thẻ (cards).
  - Sử dụng dải màu gradient sang trọng (ví dụ: `bg-gradient-to-br from-[#0f172a] to-[#1e1b4b]`).
  - Thiết kế lại các nút bấm, thanh tiến trình (progress bar), và các biểu tượng (icons) sắc nét, có hiệu ứng hover mượt mà.
  - Thay thế nút "Back" (`window.close()`) thành chức năng quay lại Tab 3D (`switch_back_callback`).

### 2. Sửa đổi `main.py` để chứa Tab mới
- Thêm định nghĩa `tab_bloom = ui.tab('Bloom Hub', icon='psychology').classes('justify-start px-6 hidden')` (Tab này sẽ bị ẩn mặc định, chỉ hiện hoặc được tự động trỏ đến khi click từ Graph Studio).
- Thêm `ui.tab_panel(tab_bloom)` vào khu vực hiển thị nội dung chính với một `bloom_container` rỗng.
- Cập nhật cầu nối giao tiếp 3D (`handle_studio_bridge_action`): Khi hành động là `bloom_hub`, ứng dụng sẽ:
  1. Xóa nội dung cũ trong `bloom_container`.
  2. Hiển thị Loading spinner đẹp mắt.
  3. Chuyển `tabs.value = tab_bloom`.
  4. Gọi `build_bloom_hub_ui` để nạp và render dữ liệu Bloom Hub mới.

### 3. Verification Plan
- Chạy ứng dụng (`main.py`).
- Mở "Graph Studio", chọn một node có nội dung.
- Nhấn nút "📚 BLOOM HUB".
- Xác minh ứng dụng lập tức chuyển sang Tab Bloom Hub, hiển thị hoạt ảnh mượt mà, render tài liệu học tập, và giao diện đánh giá (Assess) chuẩn thẩm mỹ.
- Nhấn nút "Quay lại" trong Bloom Hub để đảm bảo nó trả người dùng về trang Graph Studio.

# Cập nhật Script Video vào Tài nguyên Node

Dựa trên yêu cầu của bạn, chúng ta cần bổ sung kịch bản (script) của các video vào danh sách tài nguyên (resources) của mỗi node. Đặc biệt, đối với các node tổng (Macro node) có chứa nhiều tiết học, chúng ta sẽ liên kết đầy đủ tất cả các kịch bản của các tiết học con và đặt tên phân biệt rõ ràng. Đồng thời, tải toàn bộ nội dung text của các script này về và nhúng trực tiếp làm dữ liệu cho node.

## User Review Required

> [!IMPORTANT]
> Mình sẽ thực hiện các bước sau để đáp ứng yêu cầu của bạn. Bạn vui lòng xem qua và phê duyệt để mình bắt đầu tiến hành viết code:
> 
> 1. Nội dung script (`script.txt`) sẽ được tải xuống từ Github và lưu thẳng vào tệp JSON của các tiết học tương ứng trong thư mục `DB/JSON_Data/` (dưới dạng một trường dữ liệu `script_content`).
> 2. Cập nhật `resource_sync.py` để bổ sung link tới file `script.txt` trên Github cho tất cả các môn học (cả AIUD và Thương mại Điện tử).
> 3. Bạn có đồng ý với việc nhúng thẳng nội dung `script.txt` vào file JSON của bài học không, hay bạn muốn lưu nó thành các file `.txt` rời trong một thư mục nào đó ở máy cục bộ? Mình đề xuất lưu thẳng vào JSON để dữ liệu đồng nhất.

## Proposed Changes

---

### Quản lý Đồng bộ Tài nguyên (Resource Sync)

#### [MODIFY] [resource_sync.py](file:///i:/MY_CODE/WebPersionalLearning/resource_sync.py)
- Cập nhật logic `_sync_aiud_node` và `_sync_generic_node`.
- **Đối với Micro Nodes** (Các tiết học như `c1.1` hoặc `Chuong_1_Tiet_1`): Thêm link `script.txt` trên Github vào mảng `resources`.
- **Đối với Macro Nodes** (Các chương/module như `m1` hoặc `Chuong_1`): Quét và tự động thêm tất cả các link `script.txt` của các tiết học trực thuộc vào `resources` của node tổng. Mỗi link sẽ có tiêu đề phân biệt, ví dụ: `📄 Kịch bản Video: Khai phá Đại dương Số (c1.1)`.

---

### Kịch bản Tải & Cập nhật Dữ liệu hàng loạt

#### [NEW] [update_scripts_to_nodes.py](file:///i:/MY_CODE/WebPersionalLearning/update_scripts_to_nodes.py)
- Viết một kịch bản Python độc lập để chạy 1 lần.
- Kịch bản này sẽ quét qua toàn bộ thư mục `DB/JSON_Data/*.json`.
- Xác định đường dẫn URL Github của `script.txt` tương ứng với mỗi bài học.
- Tải nội dung text về và lưu trực tiếp vào file JSON dưới trường `"script_content"`.
- Cập nhật mảng `"resources"` của file JSON đó với link trỏ tới Github.

## Verification Plan

### Automated Tests
- Chạy thử `update_scripts_to_nodes.py` và kiểm tra file JSON trong `DB/JSON_Data/` xem nội dung script có được tải về thành công và lưu lại không.
- Chạy ứng dụng (`main.py`) và mở một Macro Node, kiểm tra tab Tài liệu (Resources) xem có hiển thị đầy đủ và phân biệt các kịch bản của các tiết học con không.

### Manual Verification
- Kiểm tra lại các URL script trên Github có trỏ đúng file text không bằng cách click trực tiếp trên ứng dụng.

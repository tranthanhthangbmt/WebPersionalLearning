# Kế hoạch Triển khai: Nâng cấp File Mô tả và Auto-Sync Tài nguyên AIUD

Nhằm đáp ứng yêu cầu đồng bộ hóa tài nguyên từ website `https://tranthanhthangbmt.github.io/AIUD_March2026/` vào thẳng Cây Tri thức (Bước 3) và giúp Bước 1 tạo ra cấu trúc "Tiết học" chi tiết, chuẩn xác, tôi đề xuất kế hoạch gồm 2 giai đoạn sau:

## GIAI ĐOẠN 1: Tái cấu trúc file Đề cương (Syllabus)
Để định hướng AI (Gemini) trong Bước 1 phân rã chính xác các Node (Macro -> Meso -> Micro).
Tôi sẽ chỉnh sửa lại file `CNTT.2025. TriTueNhanTaoUngDung...txt`.

**Cấu trúc sắp xếp lại:**
- Chuẩn hóa lại các `Mô-đun 1-6` từ file gốc và các `Buổi 6-15` thành hệ thống các **Chương (Macro Node)** thống nhất.
- Tại mỗi Chương, chia đều các **Bài học / Tiết học (Meso Node)** theo định dạng rõ ràng (Ví dụ: `Tiết 1: Lý thuyết, Tiết 2: Thực hành`).
- Bổ sung các cụm từ khóa (Keywords) liên quan trực tiếp đến tên file/thư mục tài nguyên (như `MD1`, `Buổi 13`, `Word`, `Excel`...) vào phần mô tả của các tiết học để tối ưu hóa quá trình nhận diện tự động ở Giai đoạn 2.

## GIAI ĐOẠN 2: Cập nhật thuật toán Nhúng Tài nguyên (Resource Sync)
Hiện tại tính năng đồng bộ ở Bước 3 quét các file trong hệ thống và gán link tĩnh.
Để tích hợp toàn bộ tài nguyên trên Internet từ domain `tranthanhthangbmt.github.io`, tôi sẽ cập nhật module `resource_sync.py`:

1. **Mapping Video (Từ thư mục Module_1-6/Video):**
   Tự động nhận diện các "Tiết học" thuộc Module 1->6 và đính kèm đường dẫn Video Web với format:
   `https://tranthanhthangbmt.github.io/AIUD_March2026/Module_1-6/Video/Module_{id}/...`

2. **Mapping Bài kiểm tra Trắc nghiệm (Quiz):**
   Gắn link thẳng đến ứng dụng Quiz trên web cho từng Module:
   `https://tranthanhthangbmt.github.io/AIUD_March2026/Module_1-6/index.html?module=MD{id}`

3. **Mapping Tài liệu Hướng dẫn (Slides / Buổi học):**
   Sử dụng regex phân tích tên các thư mục `TaiLieuHuongDan/Buổi {x}` để lấy các Slide (Word, Excel, PPT) và gán cho các node tương ứng từ Buổi 6 đến 15:
   `https://tranthanhthangbmt.github.io/AIUD_March2026/TaiLieuHuongDan/...`

## Lợi ích
- **Bước 1:** Cây sinh ra sẽ có chuẩn các Tiết học (Lý thuyết / Thực hành) đan xen hợp lý, không bị gộp chung thành một node đồ hoạ lớn.
- **Bước 3:** Gần như 100% các node trong đồ hoạ 3D sẽ có link bấm thẳng tới Video, Quiz, Slide trên URL chuẩn mà không cần gán bằng tay.

> [!IMPORTANT]
> **REVIEW BẮT BUỘC:** 
> Bạn có đồng ý với cấu trúc link tài liệu và cách tôi sắp xếp cấu trúc "Tiết học" như ở Giai đoạn 1 không? Hãy phê duyệt để tôi tiến hành chạy Script tự động xử lý.

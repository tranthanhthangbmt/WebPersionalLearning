# PHÂN TÍCH CoT & SYSTEM PROMPT - MODULE 4: HỆ THỐNG OUTPUT RULES (JSON TRIGGERS)

## 1. Phân Tích Chuỗi Tư Duy (Chain of Thought - CoT)
Sự khác biệt lớn nhất giữa một "Chatbot thông thường" và một "Gia sư AI Hiện diện (Omni-Tutor)" nằm ở khả năng **Tương tác trực tiếp với Giao diện ứng dụng (UI/UX)**. Lời nói của AI phải có sức mạnh thay đổi thực tại trên màn hình của sinh viên.

*   **Tính Minh bạch Bản thể luận (Ontological Transparency):** Khi sinh viên vừa hiểu ra một vấn đề, nếu AI chỉ khen "Bạn làm tốt lắm", lượng Dopamine tiết ra rất thấp. Nhưng nếu AI ra lệnh cho giao diện ĐỔI MÀU NÚT đó trên Graph Studio từ Đỏ sang Xanh, kèm theo HIỆU ỨNG PHÁO HOA, sinh viên sẽ có cảm giác "Thành tựu" mãnh liệt (Micro-achievements).
*   **Vòng lặp Phản hồi Sinh học (Bio-Cybernetic Loop):** UI cần biết khi nào sinh viên mệt mỏi để tự động mờ đi (dim) hoặc hiện nút "Giải lao". Chỉ có AI, người đang trực tiếp nói chuyện với sinh viên, mới đo lường được mức độ kiệt sức này. Do đó, AI phải truyền tín hiệu (Signal) về cho UI.
*   **Giải pháp Kỹ thuật:** Ép AI luôn luôn "chốt hạ" mọi câu trả lời bằng một khối mã JSON bí mật. Frontend (NiceGUI) sẽ dùng Regex bóc tách khối JSON này ra, ẩn nó khỏi mắt sinh viên, và dùng nó làm lệnh điều khiển UI (API Payload).

---

## 2. ĐOẠN PROMPT HOÀN CHỈNH (Chèn vào cuối System Message của AI)

*Đây là Module "Kỷ luật Thép". Bắt buộc đặt ở cuối cùng của mọi Prompt để đảm bảo mô hình LLM không bao giờ quên xuất JSON.*

```text
=== MODULE 4: STRICT OUTPUT FORMAT (JSON PAYLOAD) ===

[QUAN TRỌNG TỐI THƯỢNG]: Bạn không chỉ là người trò chuyện, bạn là HỆ ĐIỀU HÀNH của giao diện người dùng. Mọi câu trả lời của bạn BẮT BUỘC phải tuân thủ cấu trúc 2 phần:

PHẦN 1: NATURAL LANGUAGE (VĂN BẢN TRẢ LỜI)
- Là nội dung bạn giao tiếp với sinh viên dựa trên Module 1, 2 và 3.
- Sử dụng Markdown chuẩn để làm nổi bật từ khóa.

PHẦN 2: SYSTEM JSON PAYLOAD (MÃ ĐIỀU KHIỂN GIAO DIỆN)
- Ở DÒNG CUỐI CÙNG của câu trả lời, bạn BẮT BUỘC phải xuất ra một khối JSON nằm giữa hai thẻ ---SYSTEM_JSON_START--- và ---SYSTEM_JSON_END---.
- Khối JSON này dùng để ra lệnh cho giao diện UI/UX bên ngoài thay đổi.

CẤU TRÚC JSON BẮT BUỘC:
{
  "sentiment": "neutral" | "confused" | "frustrated" | "excited",
  "fatigue_level": "low" | "medium" | "high_critical",
  "prerequisite_gap": "Tên khái niệm bị hổng" | null,
  "node_color_update": "green" | "yellow" | "red" | null,
  "trigger_fireworks": true | false
}

HƯỚNG DẪN KÍCH HOẠT BIẾN JSON:
1. [fatigue_level]: Nếu sinh viên than mệt, hoặc trả lời sai 3 lần liên tiếp, set = "high_critical". Giao diện sẽ tự động khóa khung chat.
2. [node_color_update] & [trigger_fireworks]: Nếu sinh viên vừa giải quyết xong một lỗi logic quan trọng, hoặc vượt qua câu hỏi Socratic của bạn, HÃY CHỦ ĐỘNG set [node_color_update] = "green" và [trigger_fireworks] = true. Giao diện sẽ bắn pháo hoa để ăn mừng Vi-thành tựu này.
3. [prerequisite_gap]: Nếu phát hiện lỗ hổng ngoài bài, ghi tên vào đây để hệ thống tự đẻ ra Micro-Node mới (Auto-Node Injector).

VÍ DỤ OUTPUT CHUẨN:

Chính xác! Bạn đã phát hiện ra điều kiện dừng của vòng lặp bị sai. Tư duy của bạn rất nhạy bén!
Với đà này, bạn định gán giá trị biến count tiếp theo như thế nào?

---SYSTEM_JSON_START---
{
  "sentiment": "excited",
  "fatigue_level": "low",
  "prerequisite_gap": null,
  "node_color_update": "green",
  "trigger_fireworks": true
}
---SYSTEM_JSON_END---
```

---

> [!TIP]
> **Quy trình hoạt động trên Frontend:** Khi nhận được output này từ Gemini, hàm `process_ai_response` trong `main.py` của bạn sẽ dùng Regular Expression (Regex) cắt toàn bộ khối `---SYSTEM_JSON_START---` đến hết. Người dùng sẽ chỉ thấy lời khen của Gem, và ngay sau đó là giao diện bừng sáng với pháo hoa ảo, mà không hề biết rằng chính Gem vừa gửi mã điều khiển (Payload) để kích hoạt chúng!

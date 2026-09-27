"""
AI Description Generator — Tự động sinh mô tả chi tiết cho Node/Chương 
bằng Gemini AI, dựa trên bối cảnh môn học.

Sử dụng: 
    from ai_description_generator import generate_node_description
    md_text = generate_node_description(tree_path, node_id)
"""

from resource_manager import get_node_detail


def _build_prompt_micro(detail: dict) -> str:
    """Xây dựng prompt cho micro node (Bài học)."""
    course = detail.get("course_name", "Không rõ")
    chapter = detail.get("chapter_title", "Không rõ")
    title = detail.get("title", "")
    content = detail.get("content", "")
    description_md = detail.get("description_md", "")
    siblings = detail.get("sibling_titles", [])
    
    siblings_text = ""
    if siblings:
        siblings_text = "\n".join(f"  - {s}" for s in siblings[:8])
        siblings_text = f"\nCác bài học cùng chương:\n{siblings_text}"
    
    # Include existing detailed content if available
    existing_content_block = ""
    if description_md:
        existing_content_block = f"""\n**Nội dung chi tiết hiện có (description_md):**
```markdown
{description_md}
```
"""
    
    return f"""Bạn là chuyên gia giáo dục, hãy viết mô tả chi tiết cho bài học sau.

**Môn học:** {course}
**Chương:** {chapter}
**Bài học:** {title}
**Tóm tắt hiện có:** {content if content else '(Chưa có)'}
{existing_content_block}{siblings_text}

YÊU CẦU:
1. Viết bằng tiếng Việt, dạng Markdown.
2. Cấu trúc gồm:
   ## Mục tiêu bài học
   (3-5 gạch đầu dòng mô tả người học sẽ đạt được gì)
   
   ## Nội dung chính
   (Tóm tắt 3-6 ý chính, mỗi ý 1-2 câu)
   
   ## Khái niệm trọng tâm
   (Liệt kê 3-5 thuật ngữ/khái niệm quan trọng nhất)
   
   ## Công thức & Quy tắc (nếu có)
   (Nếu bài học liên quan đến toán/lý/hóa/tin, viết các công thức dùng cú pháp LaTeX: `$...$` cho inline, `$$...$$` cho block)

3. BÁM SÁT nội dung tóm tắt và nội dung chi tiết hiện có (nếu có). Hãy MỞ RỘNG, LÀM PHONG PHÚ và CHI TIẾT HƠN nội dung đã có, KHÔNG bịa thêm kiến thức ngoài phạm vi bài học.
4. Nếu đã có nội dung chi tiết, hãy giữ lại những phần tốt, bổ sung thêm ví dụ cụ thể, giải thích sâu hơn, và hoàn thiện cấu trúc.
5. Nếu bài học không liên quan đến toán/khoa học, BỎ QUA phần Công thức.
6. Tổng độ dài: 300-600 từ.
7. KHÔNG viết tiêu đề lớn (h1 #). Bắt đầu từ h2 (##).
"""


def _build_prompt_macro(detail: dict) -> str:
    """Xây dựng prompt cho macro node (Chương)."""
    course = detail.get("course_name", "Không rõ")
    title = detail.get("title", "")
    content = detail.get("content", "")
    description_md = detail.get("description_md", "")
    children = detail.get("children_titles", [])
    children_details = detail.get("children_details", [])
    
    children_text = ""
    if children_details:
        # Use detailed children info if available
        lines = []
        for cd in children_details[:10]:
            child_title = cd.get("title", "")
            child_content = cd.get("content", "")
            child_desc_md = cd.get("description_md", "")
            line = f"  - **{child_title}**"
            if child_content:
                line += f": {child_content[:150]}"
            if child_desc_md:
                # Include a brief excerpt of existing detailed description
                excerpt = child_desc_md[:200].replace('\n', ' ').strip()
                line += f"\n    _Nội dung chi tiết:_ {excerpt}..."
            lines.append(line)
        children_text = f"\nCác bài học thuộc chương này (kèm nội dung hiện có):\n" + "\n".join(lines)
    elif children:
        children_text = "\n".join(f"  - {c}" for c in children[:10])
        children_text = f"\nCác bài học thuộc chương này:\n{children_text}"
    
    # Include existing detailed content if available
    existing_content_block = ""
    if description_md:
        existing_content_block = f"""\n**Nội dung chi tiết hiện có (description_md):**
```markdown
{description_md}
```
"""
    
    return f"""Bạn là chuyên gia giáo dục, hãy viết mô tả tổng quan cho chương học sau.

**Môn học:** {course}
**Tên chương:** {title}
**Tóm tắt hiện có:** {content if content else '(Chưa có)'}
{existing_content_block}{children_text}

YÊU CẦU:
1. Viết bằng tiếng Việt, dạng Markdown.
2. Cấu trúc gồm:
   ## Tổng quan chương
   (1-2 đoạn văn ngắn giới thiệu nội dung và tầm quan trọng của chương)
   
   ## Mục tiêu học tập
   (4-6 gạch đầu dòng mô tả kết quả đầu ra sau khi hoàn thành chương)
   
   ## Cấu trúc nội dung
   (Tóm tắt ngắn gọn từng bài học con, mỗi bài 1-2 câu, dựa trên nội dung chi tiết nếu có)
   
   ## Năng lực đạt được
   (Liệt kê 3-5 năng lực/kỹ năng người học sẽ có sau khi hoàn thành chương)

3. BÁM SÁT danh sách bài học con và nội dung hiện có để viết. Hãy MỞ RỘNG và LÀM PHONG PHÚ hơn nội dung đã có. KHÔNG bịa thêm nội dung ngoài phạm vi.
4. Nếu đã có nội dung chi tiết, hãy giữ lại những phần tốt, bổ sung thêm ví dụ, giải thích sâu hơn mối liên hệ giữa các bài học.
5. Tổng độ dài: 300-600 từ.
6. KHÔNG viết tiêu đề lớn (h1 #). Bắt đầu từ h2 (##).
"""


def generate_node_description(tree_path: str, node_id: str) -> str:
    """
    Sinh mô tả chi tiết cho 1 node bằng Gemini AI.
    
    Args:
        tree_path: Đường dẫn file JSON cây tri thức
        node_id: ID của node cần sinh mô tả
    
    Returns:
        Chuỗi Markdown mô tả chi tiết. Trả về chuỗi lỗi nếu thất bại.
    """
    detail = get_node_detail(tree_path, node_id)
    if not detail:
        return f"> ⚠️ Không tìm thấy node `{node_id}` trong cây tri thức."
    
    node_type = detail.get("type", "micro")
    
    if node_type == "macro":
        prompt = _build_prompt_macro(detail)
    else:
        prompt = _build_prompt_micro(detail)
    
    try:
        from gemini_helper import get_chat_model
        model = get_chat_model()
        if not model:
            return "> ⚠️ Không có API key Gemini. Vui lòng cấu hình trong GeminiKey/geminiKey.txt."
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up: remove markdown code fences if AI wraps output
        if text.startswith("```markdown"):
            text = text[len("```markdown"):].strip()
        if text.startswith("```"):
            text = text[3:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        
        return text
    except Exception as e:
        return f"> ⚠️ Lỗi khi gọi AI: {str(e)}"

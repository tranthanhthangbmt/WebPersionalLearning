# tree_editor_ai.py — AI-powered Knowledge Tree Refinement Engine
"""
Sử dụng Gemini AI để mở rộng, cập nhật, và bổ sung cây tri thức.
Tất cả hàm trả về JSON chuẩn để merge vào cây hiện tại.

Modes:
  - expand:  Tách nhỏ 1 node thành nhiều sub-nodes
  - update:  Cập nhật nội dung node hiện tại
  - refine:  Làm chi tiết toàn bộ 1 chương
  - add:     Phân tích tài liệu mới và merge vào cây
"""

import json
import copy
import google.generativeai as genai
from gemini_helper import get_chat_model


# ═══════════════════════════════════════════════════════════
#  INTERNAL: Gemini Call Helper
# ═══════════════════════════════════════════════════════════

def _call_gemini_json(prompt: str) -> dict:
    """Gọi Gemini và parse JSON response."""
    model = get_chat_model()
    if not model:
        raise RuntimeError("Không tìm thấy API Key Gemini.")

    generation_config = genai.types.GenerationConfig(
        response_mime_type="application/json",
    )
    response = model.generate_content(prompt, generation_config=generation_config)

    if not response.parts:
        raise RuntimeError("Gemini trả về kết quả rỗng (có thể bị chặn bởi bộ lọc an toàn).")

    text = response.text.strip()
    # Clean markdown fences
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())


def _summarize_tree(tree: dict) -> str:
    """Rút gọn cây thành text context cho prompt (tránh quá dài)."""
    lines = [f"Khóa học: {tree.get('course_name', 'N/A')}"]
    for m in tree.get('macro_nodes', []):
        lines.append(f"\nChương {m['id']}: {m.get('title', '')}")
        children = [c for c in tree.get('micro_nodes', []) if c.get('parent_macro') == m['id']]
        for c in children:
            lines.append(f"  Bài {c['id']}: {c.get('title', '')} (alpha={c.get('alpha_base', 15)})")
            lines.append(f"    Nội dung: {c.get('content', '')[:100]}")
    edges = tree.get('edges', [])
    if edges:
        lines.append(f"\nEdges ({len(edges)}):")
        for e in edges[:15]:
            lines.append(f"  {e['source']} → {e['target']}: {e.get('reason', '')[:60]}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
#  MODE 1: EXPAND NODE
# ═══════════════════════════════════════════════════════════

def ai_expand_node(existing_tree: dict, target_node_id: str, user_prompt: str,
                   extra_document_text: str = None) -> dict:
    """
    Tách nhỏ 1 micro_node thành nhiều micro_nodes chi tiết hơn.
    Node gốc sẽ bị thay thế bởi các node mới.

    Returns: {"new_micro_nodes": [...], "new_assess_nodes": [...], "new_edges": [...],
              "remove_node_id": "..."}
    """
    target_node = next((n for n in existing_tree.get('micro_nodes', [])
                        if n['id'] == target_node_id), None)
    if not target_node:
        raise ValueError(f"Không tìm thấy node '{target_node_id}'")

    tree_context = _summarize_tree(existing_tree)
    existing_ids = {n['id'] for n in existing_tree.get('micro_nodes', [])}

    doc_section = ""
    if extra_document_text:
        doc_section = f"""
TÀI LIỆU BỔ SUNG:
---
{extra_document_text[:8000]}
---"""

    prompt = f"""Bạn là chuyên gia Khoa học Dữ liệu Giáo dục tại MIT.

CÂY TRI THỨC HIỆN TẠI:
{tree_context}

NODE CẦN TÁCH NHỎ:
- ID: {target_node['id']}
- Title: {target_node.get('title', '')}
- Content: {target_node.get('content', '')}
- Parent: {target_node.get('parent_macro', '')}
- Alpha: {target_node.get('alpha_base', 15)}
{doc_section}

YÊU CẦU CỦA NGƯỜI DÙNG: {user_prompt}

Hãy tách node trên thành nhiều micro_nodes nhỏ hơn, chi tiết hơn.
KHÔNG được dùng các ID đã tồn tại: {list(existing_ids)}

Trả về JSON với cấu trúc:
{{
  "new_micro_nodes": [
    {{"id": "c...", "parent_macro": "{target_node.get('parent_macro', '')}", "title": "...", "content": "...(3-4 câu)", "alpha_base": 10-30}}
  ],
  "new_assess_nodes": [
    {{"id": "a...", "target_micro": "c...", "theta_pass": 0.6}}
  ],
  "new_edges": [
    {{"source": "c...", "target": "c...", "reason": "..."}}
  ]
}}
Chỉ trả về JSON, không giải thích."""

    print(f"🤖 AI Expand: Tách node {target_node_id}...")
    result = _call_gemini_json(prompt)
    result['remove_node_id'] = target_node_id
    return result


# ═══════════════════════════════════════════════════════════
#  MODE 2: UPDATE NODE
# ═══════════════════════════════════════════════════════════

def ai_update_node(existing_tree: dict, target_node_id: str, user_prompt: str,
                   extra_document_text: str = None) -> dict:
    """
    Cập nhật nội dung 1 node (title, content, assess).

    Returns: {"updated_node": {id, title, content, alpha_base},
              "updated_assess": {questions: [...]}}
    """
    target_node = next((n for n in existing_tree.get('micro_nodes', [])
                        if n['id'] == target_node_id), None)
    if not target_node:
        raise ValueError(f"Không tìm thấy node '{target_node_id}'")

    tree_context = _summarize_tree(existing_tree)
    existing_assess = next((a for a in existing_tree.get('assess_nodes', [])
                            if a.get('target_micro') == target_node_id), None)

    doc_section = ""
    if extra_document_text:
        doc_section = f"""
TÀI LIỆU BỔ SUNG:
---
{extra_document_text[:8000]}
---"""

    prompt = f"""Bạn là chuyên gia Khoa học Dữ liệu Giáo dục tại MIT.

CÂY TRI THỨC HIỆN TẠI:
{tree_context}

NODE CẦN CẬP NHẬT:
- ID: {target_node['id']}
- Title: {target_node.get('title', '')}
- Content: {target_node.get('content', '')}
- Alpha: {target_node.get('alpha_base', 15)}
{doc_section}

YÊU CẦU: {user_prompt}

Hãy cập nhật node trên theo yêu cầu. Giữ nguyên ID và parent_macro.

Trả về JSON:
{{
  "updated_node": {{
    "id": "{target_node_id}",
    "title": "...(có thể sửa hoặc giữ nguyên)",
    "content": "...(3-4 câu, nội dung mới)",
    "alpha_base": 10-30
  }},
  "updated_assess": {{
    "id": "{existing_assess['id'] if existing_assess else f'a{target_node_id[1:]}'}",
    "target_micro": "{target_node_id}",
    "theta_pass": 0.6
  }}
}}
Chỉ trả về JSON."""

    print(f"🤖 AI Update: Cập nhật node {target_node_id}...")
    return _call_gemini_json(prompt)


# ═══════════════════════════════════════════════════════════
#  MODE 3: REFINE REGION (MACRO)
# ═══════════════════════════════════════════════════════════

def ai_refine_region(existing_tree: dict, macro_node_id: str, user_prompt: str,
                     extra_document_text: str = None) -> dict:
    """
    Làm chi tiết toàn bộ 1 chương — thêm micro nodes mới.

    Returns: {"new_micro_nodes": [...], "new_assess_nodes": [...], "new_edges": [...]}
    """
    macro = next((m for m in existing_tree.get('macro_nodes', [])
                  if m['id'] == macro_node_id), None)
    if not macro:
        raise ValueError(f"Không tìm thấy chương '{macro_node_id}'")

    tree_context = _summarize_tree(existing_tree)
    existing_ids = {n['id'] for n in existing_tree.get('micro_nodes', [])}

    doc_section = ""
    if extra_document_text:
        doc_section = f"""
TÀI LIỆU BỔ SUNG:
---
{extra_document_text[:8000]}
---"""

    prompt = f"""Bạn là chuyên gia Khoa học Dữ liệu Giáo dục tại MIT.

CÂY TRI THỨC HIỆN TẠI:
{tree_context}

CHƯƠNG CẦN LÀM CHI TIẾT:
- ID: {macro['id']}
- Title: {macro.get('title', '')}
- Các bài học hiện có: {[n['id'] for n in existing_tree.get('micro_nodes', []) if n.get('parent_macro') == macro_node_id]}
{doc_section}

YÊU CẦU: {user_prompt}

Hãy thêm các micro_nodes MỚI vào chương này. KHÔNG trùng ID đã có: {list(existing_ids)}

Trả về JSON:
{{
  "new_micro_nodes": [
    {{"id": "c...", "parent_macro": "{macro_node_id}", "title": "...", "content": "...(3-4 câu)", "alpha_base": 10-30}}
  ],
  "new_assess_nodes": [
    {{"id": "a...", "target_micro": "c...", "theta_pass": 0.6}}
  ],
  "new_edges": [
    {{"source": "c...", "target": "c...", "reason": "..."}}
  ]
}}
Chỉ trả về JSON."""

    print(f"🤖 AI Refine: Làm chi tiết chương {macro_node_id}...")
    return _call_gemini_json(prompt)


# ═══════════════════════════════════════════════════════════
#  MODE 4: ADD FROM DOCUMENT
# ═══════════════════════════════════════════════════════════

def ai_add_from_document(existing_tree: dict, document_text: str, user_prompt: str) -> dict:
    """
    Phân tích tài liệu bổ sung và merge vào cây hiện tại.

    Returns: {"new_macro_nodes": [...], "new_micro_nodes": [...],
              "new_assess_nodes": [...], "new_edges": [...]}
    """
    tree_context = _summarize_tree(existing_tree)
    existing_macro_ids = {m['id'] for m in existing_tree.get('macro_nodes', [])}
    existing_micro_ids = {n['id'] for n in existing_tree.get('micro_nodes', [])}

    prompt = f"""Bạn là chuyên gia Khoa học Dữ liệu Giáo dục tại MIT.

CÂY TRI THỨC HIỆN TẠI:
{tree_context}

TÀI LIỆU BỔ SUNG MỚI:
---
{document_text[:10000]}
---

YÊU CẦU: {user_prompt}

Phân tích tài liệu mới và bổ sung vào cây hiện tại. Có thể:
- Thêm chương mới (nếu nội dung khác biệt hoàn toàn)
- Thêm bài học mới vào chương đã có (nếu liên quan)
- Tạo edges giữa nội dung mới và cũ

KHÔNG dùng ID đã có:
- Macro: {list(existing_macro_ids)}
- Micro: {list(existing_micro_ids)}

Trả về JSON:
{{
  "new_macro_nodes": [{{"id": "m...", "title": "..."}}],
  "new_micro_nodes": [{{"id": "c...", "parent_macro": "m...", "title": "...", "content": "...(3-4 câu)", "alpha_base": 10-30}}],
  "new_assess_nodes": [{{"id": "a...", "target_micro": "c...", "theta_pass": 0.6}}],
  "new_edges": [{{"source": "c...", "target": "c...", "reason": "..."}}]
}}
Nếu không cần thêm chương mới, để "new_macro_nodes" là mảng rỗng.
Chỉ trả về JSON."""

    print("🤖 AI Add: Phân tích tài liệu bổ sung...")
    return _call_gemini_json(prompt)


# ═══════════════════════════════════════════════════════════
#  MERGE UTILITY
# ═══════════════════════════════════════════════════════════

def merge_ai_result_into_tree(tree_data: dict, ai_result: dict, mode: str = 'expand') -> dict:
    """
    Merge kết quả AI vào tree_data.

    Args:
        tree_data: Cây tri thức gốc (sẽ được modify in-place)
        ai_result: Kết quả từ hàm AI
        mode: 'expand' | 'update' | 'refine' | 'add'

    Returns: tree_data đã cập nhật
    """
    tree = tree_data  # modify in-place

    if mode == 'update':
        # Cập nhật node hiện tại
        updated = ai_result.get('updated_node', {})
        if updated and updated.get('id'):
            nid = updated['id']
            for i, n in enumerate(tree.get('micro_nodes', [])):
                if n['id'] == nid:
                    tree['micro_nodes'][i]['title'] = updated.get('title', n['title'])
                    tree['micro_nodes'][i]['content'] = updated.get('content', n['content'])
                    tree['micro_nodes'][i]['alpha_base'] = updated.get('alpha_base', n.get('alpha_base', 15))
                    break

        # Cập nhật assess
        updated_assess = ai_result.get('updated_assess', {})
        if updated_assess and updated_assess.get('target_micro'):
            target = updated_assess['target_micro']
            found = False
            for i, a in enumerate(tree.get('assess_nodes', [])):
                if a.get('target_micro') == target:
                    tree['assess_nodes'][i] = updated_assess
                    found = True
                    break
            if not found:
                tree.setdefault('assess_nodes', []).append(updated_assess)

    elif mode == 'expand':
        # Xóa node gốc
        remove_id = ai_result.get('remove_node_id')
        if remove_id:
            tree['micro_nodes'] = [n for n in tree['micro_nodes'] if n['id'] != remove_id]
            tree['assess_nodes'] = [a for a in tree.get('assess_nodes', [])
                                     if a.get('target_micro') != remove_id]
            # Re-map edges pointing to removed node
            old_edges = tree.get('edges', [])
            tree['edges'] = [e for e in old_edges
                             if e.get('source') != remove_id and e.get('target') != remove_id]

        # Add new nodes
        _append_new_nodes(tree, ai_result)

    elif mode in ('refine', 'add'):
        # Add new macro nodes (only for 'add' mode)
        for macro in ai_result.get('new_macro_nodes', []):
            if macro.get('id') and not any(m['id'] == macro['id'] for m in tree.get('macro_nodes', [])):
                tree.setdefault('macro_nodes', []).append(macro)

        _append_new_nodes(tree, ai_result)

    return tree


def _append_new_nodes(tree: dict, ai_result: dict):
    """Append new micro, assess, and edge nodes, skipping duplicates."""
    existing_micro = {n['id'] for n in tree.get('micro_nodes', [])}
    for node in ai_result.get('new_micro_nodes', []):
        if node.get('id') and node['id'] not in existing_micro:
            tree.setdefault('micro_nodes', []).append(node)
            existing_micro.add(node['id'])

    existing_assess = {a['id'] for a in tree.get('assess_nodes', [])}
    for assess in ai_result.get('new_assess_nodes', []):
        if assess.get('id') and assess['id'] not in existing_assess:
            tree.setdefault('assess_nodes', []).append(assess)
            existing_assess.add(assess['id'])

    existing_edges = {(e['source'], e['target']) for e in tree.get('edges', [])}
    for edge in ai_result.get('new_edges', []):
        key = (edge.get('source'), edge.get('target'))
        if key[0] and key[1] and key not in existing_edges:
            tree.setdefault('edges', []).append(edge)
            existing_edges.add(key)


# ═══════════════════════════════════════════════════════════
#  PREVIEW HELPER
# ═══════════════════════════════════════════════════════════

def format_ai_result_preview(ai_result: dict, mode: str) -> str:
    """Tạo text preview cho kết quả AI (hiển thị trong UI)."""
    lines = []

    if mode == 'update':
        updated = ai_result.get('updated_node', {})
        lines.append(f"📝 Cập nhật node: {updated.get('id', '?')}")
        lines.append(f"   Title: {updated.get('title', '?')}")
        lines.append(f"   Alpha: {updated.get('alpha_base', '?')}")
        ua = ai_result.get('updated_assess', {})
        if ua.get('questions'):
            lines.append(f"   + {len(ua['questions'])} câu hỏi kiểm tra")
    else:
        if ai_result.get('remove_node_id'):
            lines.append(f"🗑️ Xóa node gốc: {ai_result['remove_node_id']}")

        new_macros = ai_result.get('new_macro_nodes', [])
        if new_macros:
            lines.append(f"📌 + {len(new_macros)} chương mới:")
            for m in new_macros:
                lines.append(f"   • {m.get('id', '?')}: {m.get('title', '?')}")

        new_micros = ai_result.get('new_micro_nodes', [])
        if new_micros:
            lines.append(f"📖 + {len(new_micros)} bài học mới:")
            for n in new_micros:
                lines.append(f"   • {n.get('id', '?')}: {n.get('title', '?')} (α={n.get('alpha_base', '?')})")

        new_assess = ai_result.get('new_assess_nodes', [])
        if new_assess:
            total_q = sum(len(a.get('questions', [])) for a in new_assess)
            lines.append(f"📝 + {len(new_assess)} kiểm tra ({total_q} câu hỏi)")

        new_edges = ai_result.get('new_edges', [])
        if new_edges:
            lines.append(f"🔗 + {len(new_edges)} edges mới")

    return "\n".join(lines)

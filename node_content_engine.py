# node_content_engine.py
"""
Node Content Engine — Quản lý nội dung học tập + Bloom calibration + Library sync.
JSON-first architecture: nhẹ, scalable, hỗ trợ multi-user.
"""

import os
import json
import time
from datetime import datetime
from bloom_taxonomy import (
    BLOOM_LEVELS, calibrate_bloom_from_alpha, get_node_position_ratio,
    create_bloom_profile, create_node_bloom_scores, get_effective_levels
)

LIBRARY_DIR = os.path.join("DB", "bloom_content_library")
LIBRARY_INDEX = os.path.join(LIBRARY_DIR, "index.json")


# ============================================================
#  CONTENT PACK SCHEMA
# ============================================================

def _empty_content_pack(node_id: str, course_id: str) -> dict:
    return {
        "node_id": node_id,
        "course_id": course_id,
        "version": 1,
        "updated_at": datetime.now().isoformat(),
        "author": "system",
        "study_material": {
            "learning_objectives": [],
            "key_concepts": [],
            "detailed_content": "",
            "summary": "",
            "practical_examples": [],
        },
        "bloom_profile": create_bloom_profile([1, 2]),
        "question_bank": {},
    }


# ============================================================
#  LIBRARY I/O
# ============================================================

def _ensure_library():
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    if not os.path.exists(LIBRARY_INDEX):
        with open(LIBRARY_INDEX, 'w', encoding='utf-8') as f:
            json.dump({"packs": {}, "updated_at": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)


def _load_index() -> dict:
    _ensure_library()
    with open(LIBRARY_INDEX, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_index(index: dict):
    index["updated_at"] = datetime.now().isoformat()
    with open(LIBRARY_INDEX, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _content_pack_path(course_id: str, node_id: str) -> str:
    safe_course = course_id.replace(" ", "_").replace("/", "_")[:50]
    safe_node = node_id.replace(" ", "_").replace("/", "_")[:80]
    return os.path.join(LIBRARY_DIR, safe_course, f"{safe_node}.json")


def load_from_library(course_id: str, node_id: str) -> dict | None:
    """Load content pack from shared library. Returns None if not found."""
    path = _content_pack_path(course_id, node_id)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def publish_to_library(content_pack: dict, author: str = "system") -> str:
    """
    Publish content pack to shared library.
    Returns path of saved file.
    """
    _ensure_library()
    course_id = content_pack.get("course_id", "unknown")
    node_id = content_pack.get("node_id", "unknown")

    content_pack["author"] = author
    content_pack["updated_at"] = datetime.now().isoformat()
    content_pack["version"] = content_pack.get("version", 0) + 1

    path = _content_pack_path(course_id, node_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(content_pack, f, ensure_ascii=False, indent=2)

    # Update index
    index = _load_index()
    key = f"{course_id}/{node_id}"
    index["packs"][key] = {
        "course_id": course_id,
        "node_id": node_id,
        "author": author,
        "version": content_pack["version"],
        "updated_at": content_pack["updated_at"],
        "bloom_levels": content_pack.get("bloom_profile", {}).get("effective_levels", []),
        "question_count": sum(len(v) for v in content_pack.get("question_bank", {}).values()),
    }
    _save_index(index)
    print(f"📤 Published content pack: {key} (v{content_pack['version']})")
    return path


# ============================================================
#  USER CONTENT CACHE
# ============================================================

def _user_cache_path(username: str, course_id: str, node_id: str) -> str:
    safe_course = course_id.replace(" ", "_")[:50]
    safe_node = node_id.replace(" ", "_")[:80]
    return os.path.join("user_data", username, "content_cache", safe_course, f"{safe_node}.json")


def _load_user_cache(username: str, course_id: str, node_id: str) -> dict | None:
    path = _user_cache_path(username, course_id, node_id)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def _save_user_cache(username: str, content_pack: dict):
    course_id = content_pack.get("course_id", "unknown")
    node_id = content_pack.get("node_id", "unknown")
    path = _user_cache_path(username, course_id, node_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(content_pack, f, ensure_ascii=False, indent=2)


def delete_content_pack(username: str, course_name: str, node_id: str):
    """Xóa cache bài học để AI có thể sinh lại từ đầu."""
    course_id = _make_course_id(course_name)
    path = _user_cache_path(username, course_id, node_id)
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"🗑️ Đã xóa cache nội dung: {path}")
            return True
        except Exception as e:
            print(f"❌ Lỗi xóa cache {path}: {e}")
    return False


# ============================================================
#  RESOURCE GATHERING — Collect all available context for a node
# ============================================================

def _gather_node_context(node_id: str, node_info: dict, tree_data: dict) -> str:
    """Aggregate all available reference materials for a node.
    
    Sources checked (priority order):
    0. description_md (existing detailed Markdown description)
    1. data_manager lesson data (script_content field)
    2. Local script file: DB/Video/{node_id}/script.txt
    3. Resource files & scripts (local documents, remote scripts)
    4. Resource listing (YouTube, PDF, Drive links — as context metadata)
    5. Node content/description from tree JSON
    6. Sibling/child node summaries (for broader context)
    """
    import re
    context_parts = []
    
    # --- Source 0: Existing detailed description (description_md) ---
    description_md = node_info.get('description_md', '')
    if description_md and len(description_md) > 20:
        context_parts.append(f"[MÔ TẢ CHI TIẾT HIỆN CÓ (description_md)]\n{description_md}")
        print(f"[ContentEngine] 📝 Found description_md for {node_id} ({len(description_md)} chars)")
    
    # --- Source 1: data_manager (JSON_Data) ---
    try:
        from data_manager import data_manager
        lesson = data_manager.get_lesson(node_id)
        if lesson:
            sc = lesson.get('script_content', '')
            if sc and len(sc) > 50:
                context_parts.append(f"[KỊCH BẢN THUYẾT TRÌNH]\n{sc}")
                print(f"[ContentEngine] 📄 Found script_content from data_manager for {node_id} ({len(sc)} chars)")
            # Also check questions for topic hints
            qs = lesson.get('questions', [])
            if qs:
                q_texts = []
                for q in qs:
                    q_text = q.get('content', q.get('sentence', q.get('question', '')))
                    opts = q.get('options', {})
                    if opts:
                        q_text += f"\nOptions: {opts}"
                    if q_text:
                        q_texts.append(q_text)
                
                if q_texts:
                    context_parts.append(f"[CÂU HỎI TRẮC NGHIỆM ĐÃ HỌC]\n" + '\n---\n'.join(q_texts))
    except Exception as e:
        print(f"[ContentEngine] data_manager lookup error: {e}")
    
    # --- Source 2: Local script file ---
    local_script = os.path.join('DB', 'Video', node_id, 'script.txt')
    if os.path.exists(local_script):
        try:
            with open(local_script, 'r', encoding='utf-8-sig') as f:
                script = f.read().strip()
            if script and len(script) > 50:
                context_parts.append(f"[KỊCH BẢN THUYẾT TRÌNH]\n{script}")
                print(f"[ContentEngine] 📄 Found local script.txt for {node_id} ({len(script)} chars)")
        except Exception as e:
            print(f"[ContentEngine] Local script read error: {e}")
    
    # --- Collect all resources from node, parent, and children ---
    all_resources = list(node_info.get('resources', []))
    nodes = tree_data.get('nodes', {})
    
    # Also check macro parent resources
    m = re.match(r'^(?:Chuong_|c)(\d+)', node_id)
    if m:
        macro_key = f"m{m.group(1)}"
        macro_node = nodes.get(macro_key, {})
        all_resources.extend(macro_node.get('resources', []))
        
    # Also check child resources (if this is a macro/parent node)
    edges = tree_data.get('edges', [])
    for edge in edges:
        source_id = edge.get('source') if isinstance(edge, dict) else (edge[0] if isinstance(edge, list) and len(edge) >= 2 else None)
        target_id = edge.get('target') if isinstance(edge, dict) else (edge[1] if isinstance(edge, list) and len(edge) >= 2 else None)
        if source_id == node_id and target_id:
            child_node = nodes.get(target_id, {})
            all_resources.extend(child_node.get('resources', []))
    
    # --- Source 3: Parse resource files & fetch remote scripts ---
    processed_urls = set()  # Avoid duplicates
    for r in all_resources:
        url = r.get('url', '')
        title = r.get('title', '')
        
        if not url or url in processed_urls:
            continue
        processed_urls.add(url)
            
        # If it's a local file in user_data
        if url.startswith('user_data/') and os.path.exists(url):
            try:
                from document_parser import parse_document
                with open(url, 'rb') as f:
                    file_bytes = f.read()
                text = parse_document(url, file_bytes, max_chars=30000)
                if text and len(text) > 50:
                    context_parts.append(f"[TÀI LIỆU ĐÍNH KÈM: {title}]\n{text}")
                    print(f"[ContentEngine] 📄 Extracted local document {url} ({len(text)} chars)")
            except Exception as e:
                print(f"[ContentEngine] Local doc parse error {url}: {e}")
                
        # If it's a remote URL for text/script
        elif ('script' in url.lower() or 'kịch bản' in title.lower()) and url.endswith('.txt'):
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                resp = urllib.request.urlopen(req, timeout=8)
                script = resp.read().decode('utf-8-sig').strip()
                if script and len(script) > 50:
                    context_parts.append(f"[KỊCH BẢN THUYẾT TRÌNH {title}]\n{script}")
                    print(f"[ContentEngine] 📄 Fetched remote script for {node_id} from {url[:60]}")
            except Exception as e:
                print(f"[ContentEngine] Remote script fetch error: {e}")
    
    # --- Source 4: Resource listing (titles & URLs as context metadata) ---
    if all_resources:
        res_lines = []
        for r in all_resources:
            r_icon = r.get('icon', '🔗')
            r_title = r.get('title', '')
            r_url = r.get('url', '')
            r_type = r.get('type', 'web')
            if r_title or r_url:
                res_lines.append(f"  {r_icon} [{r_type.upper()}] {r_title}: {r_url}")
        if res_lines:
            context_parts.append(f"[DANH SÁCH TÀI NGUYÊN ĐÍNH KÈM ({len(res_lines)} tài nguyên)]\n" + '\n'.join(res_lines))
            print(f"[ContentEngine] 📎 Listed {len(res_lines)} resource links for {node_id}")
    
    # --- Source 5: Node content/description fallback ---
    node_content = node_info.get('content') or node_info.get('description') or ''
    if node_content and len(node_content) > 10:
        # Don't add if it's just a file reference
        if not node_content.startswith('Tài liệu tương ứng với:'):
            context_parts.append(f"[MÔ TẢ NODE]\n{node_content}")
    
    # --- Source 6: Sibling/child node content (for broader context) ---
    sibling_context = []
    
    # [NEW] Handle macro/meso node dynamic aggregation
    m_macro = re.match(r'^m(\d+)', node_id)
    if m_macro:
        macro_num = m_macro.group(1)
        prefix_chuong = f"Chuong_{macro_num}_"
        prefix_c = f"c{macro_num}."
        for nid, child in nodes.items():
            if nid.startswith(prefix_chuong) or nid.startswith(prefix_c):
                child_title = child.get('label') or child.get('title') or nid
                child_content = child.get('content') or child.get('description') or ''
                child_desc_md = child.get('description_md', '')
                parts = [f"**{child_title}**"]
                if child_content:
                    parts.append(child_content[:200])
                if child_desc_md:
                    parts.append(child_desc_md[:300])
                
                # Try to get local script text for this child
                local_script = os.path.join('DB', 'Video', nid, 'script.txt')
                if os.path.exists(local_script):
                    try:
                        with open(local_script, 'r', encoding='utf-8-sig') as f:
                            script = f.read().strip()
                        if script:
                            parts.append(f"Kịch bản bài giảng: {script[:400]}")
                    except: pass
                
                sibling_context.append(' — '.join(parts))

    for edge in edges:
        if isinstance(edge, dict):
            src, tgt = edge.get('source'), edge.get('target')
        elif isinstance(edge, list) and len(edge) >= 2:
            src, tgt = edge[0], edge[1]
        else:
            continue
        
        # Collect children content if this node is a parent
        if src == node_id and tgt in nodes:
            child = nodes[tgt]
            child_title = child.get('label') or child.get('title') or tgt
            child_content = child.get('content') or child.get('description') or ''
            child_desc_md = child.get('description_md', '')
            parts = [f"**{child_title}**"]
            if child_content:
                parts.append(child_content[:200])
            if child_desc_md:
                parts.append(child_desc_md[:300])
            sibling_context.append(' — '.join(parts))
        
        # Collect sibling summaries (nodes under same parent) 
        if tgt == node_id and src in nodes:
            # src is the parent — find other children of this parent
            parent_id = src
            for edge2 in edges:
                if isinstance(edge2, dict):
                    s2, t2 = edge2.get('source'), edge2.get('target')
                else:
                    continue
                if s2 == parent_id and t2 != node_id and t2 in nodes:
                    sib = nodes[t2]
                    sib_title = sib.get('label') or sib.get('title') or t2
                    sib_content = sib.get('content') or sib.get('description') or ''
                    sibling_context.append(f"[Bài cùng chương] **{sib_title}**: {sib_content[:100]}")
    
    if sibling_context:
        context_parts.append(f"[NỘI DUNG CÁC BÀI LIÊN QUAN]\n" + '\n'.join(sibling_context[:8]))
    
    # Combine and truncate
    full_context = '\n\n'.join(context_parts)
    if len(full_context) > 50000:
        full_context = full_context[:50000] + '\n[...đã cắt bớt...]'
    
    if context_parts:
        print(f"[ContentEngine] ✅ Gathered {len(full_context)} chars of context for {node_id} ({len(context_parts)} sources)")
    else:
        print(f"[ContentEngine] ⚠️ No reference materials found for {node_id}, using title only")
    
    return full_context


# ============================================================
#  AI CONTENT GENERATION
# ============================================================

def _build_study_material_prompt(node_title: str, node_content: str,
                                  course_name: str, bloom_levels: list,
                                  reference_materials: str = '') -> str:
    bloom_names = [f"L{l} {BLOOM_LEVELS[l]['vi']}" for l in bloom_levels if l in BLOOM_LEVELS]
    
    ref_section = ''
    if reference_materials:
        ref_section = f"""\n\n═══ TÀI LIỆU THAM KHẢO (dùng làm nguồn chính để tạo nội dung) ═══
{reference_materials}
═══ HẾT TÀI LIỆU THAM KHẢO ═══\n"""
    
    return f"""Bạn là chuyên gia giáo dục đại học. Tạo tài liệu học tập chuẩn MIT cho bài học sau.

MÔN HỌC: {course_name}
BÀI HỌC: {node_title}
NỘI DUNG GỐC: {node_content[:500]}
{ref_section}
MỨC BLOOM MỤC TIÊU: {', '.join(bloom_names)}

HƯỚNG DẪN: {'Hãy DỰA VÀO tài liệu tham khảo ở trên để tạo nội dung chính xác, chi tiết, bám sát nội dung bài giảng thực tế.' if reference_materials else 'Tạo nội dung dựa trên kiến thức chuyên môn.'}

OUTPUT FORMAT (JSON, KHÔNG có text khác):
{{
    "learning_objectives": ["CLO1: ...", "CLO2: ...", "CLO3: ..."],
    "key_concepts": [
        {{"term": "Thuật ngữ 1", "definition": "Định nghĩa ngắn gọn"}},
        {{"term": "Thuật ngữ 2", "definition": "Định nghĩa ngắn gọn"}}
    ],
    "detailed_content": "## Nội dung chi tiết (Markdown, 300-500 từ)\\n...",
    "summary": "Tóm tắt 2-3 câu",
    "practical_examples": ["Ví dụ 1...", "Ví dụ 2..."],
    "multimedia_diagram": "Mã Mermaid.js hợp lệ để vẽ Mindmap hoặc Flowchart tóm tắt bài học. (ví dụ: mindmap\\n  root((Chủ đề chính))\\n    Nhánh 1\\n      Ý nhỏ 1\\n    Nhánh 2). KHÔNG bọc trong markdown code block, chỉ xuất mã raw.",
    "micro_learning_flashcards": [{{"q": "Câu hỏi ôn tập siêu ngắn", "a": "Đáp án siêu ngắn"}}]
}}

QUY TẮC: Tiếng Việt, học thuật, chính xác, có tham chiếu thực tiễn."""


def _build_question_bank_prompt(node_title: str, node_content: str,
                                 course_name: str, bloom_level: int,
                                 reference_materials: str = '') -> str:
    bl = BLOOM_LEVELS.get(bloom_level, BLOOM_LEVELS[1])
    types_desc = {
        1: 'MCQ nhận diện (type: mcq_recall) và Flashcard (type: flashcard)',
        2: 'MCQ giải thích (type: mcq_comprehension), Điền từ (type: fill_blank), Nối từ (type: matching)',
        3: 'MCQ tình huống (type: scenario_mcq), Bài tập case study (type: case_study)',
        4: 'Câu hỏi Socratic phân tích (type: socratic_prompt), So sánh đối chiếu (type: compare_contrast)',
        5: 'Câu hỏi biện luận (type: debate_prompt), Phê bình (type: critique)',
        6: 'Bài tập thiết kế (type: design_task), Đề xuất sáng tạo (type: creative_proposal)',
    }
    
    ref_section = ''
    if reference_materials:
        # Truncate for question prompts (shorter than study material)
        ref_text = reference_materials[:3000]
        ref_section = f"""\n\n═══ TÀI LIỆU THAM KHẢO (dùng để tạo câu hỏi bám sát bài giảng) ═══
{ref_text}
═══ HẾT TÀI LIỆU ═══\n"""
    
    return f"""Tạo ngân hàng câu hỏi cho bài học, mức Bloom L{bloom_level} ({bl['vi']}).

MÔN HỌC: {course_name}
BÀI HỌC: {node_title}
NỘI DUNG: {node_content[:500]}
{ref_section}
BLOOM LEVEL: L{bloom_level} - {bl['vi']} ({bl['name']})
ĐỘNG TỪ: {', '.join(bl['verbs_vi'])}
LOẠI CÂU HỎI CẦN TẠO: {types_desc.get(bloom_level, types_desc[1])}

{'HƯỚNG DẪN: Tạo câu hỏi DỰA TRÊN nội dung tài liệu tham khảo, đảm bảo đáp án chính xác theo bài giảng.' if reference_materials else ''}

OUTPUT FORMAT (JSON array, tạo 5-8 câu):
[
    {{
        "type": "mcq_recall",
        "question": "Câu hỏi?",
        "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
        "correct": "A",
        "explanation": "Giải thích"
    }},
    {{
        "type": "flashcard",
        "front": "Thuật ngữ",
        "back": "Định nghĩa"
    }},
    {{
        "type": "fill_blank",
        "sentence": "Câu hoàn chỉnh với [BLANK] thay chỗ trống",
        "answer": "từ đúng",
        "explanation": "Giải thích"
    }},
    {{
        "type": "matching",
        "pairs": [{{"term": "A", "definition": "1"}}, {{"term": "B", "definition": "2"}}]
    }},
    {{
        "type": "socratic_prompt",
        "initial_question": "Câu hỏi mở để thảo luận sâu",
        "follow_ups": ["Câu hỏi tiếp 1", "Câu hỏi tiếp 2"],
        "key_points": ["Điểm chính cần đạt"]
    }}
]

QUY TẮC: Tiếng Việt, đa dạng loại, phù hợp mức Bloom {bl['vi']}."""


async def generate_study_material(node_title: str, node_content: str,
                                   course_name: str, bloom_levels: list,
                                   reference_materials: str = '') -> dict:
    """AI sinh nội dung học tập. Returns study_material dict."""
    from gemini_helper import get_chat_model
    import re
    model = get_chat_model()
    if not model:
        return {"learning_objectives": [], "key_concepts": [],
                "detailed_content": f"# {node_title}\n\n{node_content}",
                "summary": node_content[:200], "practical_examples": []}

    prompt = _build_study_material_prompt(node_title, node_content, course_name, bloom_levels, reference_materials)
    try:
        from nicegui import run
        response = await run.io_bound(model.generate_content, prompt)
        text = response.text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"[ContentEngine] Study material generation error: {e}")

    return {"learning_objectives": [], "key_concepts": [],
            "detailed_content": f"# {node_title}\n\n{node_content}",
            "summary": node_content[:200], "practical_examples": []}


async def generate_question_bank(node_title: str, node_content: str,
                                  course_name: str, bloom_levels: list,
                                  reference_materials: str = '') -> dict:
    """AI sinh ngân hàng câu hỏi cho tất cả bloom levels (chạy song song). Returns {L1: [...], L2: [...]}. """
    from gemini_helper import get_chat_model
    import re
    import asyncio
    from nicegui import run
    model = get_chat_model()
    if not model:
        return {}

    async def _gen_for_level(level):
        prompt = _build_question_bank_prompt(node_title, node_content, course_name, level, reference_materials)
        try:
            response = await run.io_bound(model.generate_content, prompt)
            text = response.text
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                questions = json.loads(match.group(0))
                return f"L{level}", [q for q in questions if isinstance(q, dict) and "type" in q]
            else:
                return f"L{level}", []
        except Exception as e:
            print(f"[ContentEngine] Question bank L{level} error: {e}")
            return f"L{level}", []

    tasks = [_gen_for_level(lvl) for lvl in bloom_levels]
    results = await asyncio.gather(*tasks)
    return dict(results)


# ============================================================
#  MAIN API — get_or_create_content_pack
# ============================================================

async def get_or_create_content_pack(
    node_id: str, node_info: dict, tree_data: dict,
    username: str, auto_publish: bool = True
) -> dict:
    """
    Main entry point. Lấy hoặc tạo content pack cho 1 node.
    
    Priority:
    1. User cache (đã generate trước đó)
    2. Shared library (người khác đã publish)
    3. AI generate → cache + optional auto-publish
    """
    course_name = tree_data.get("course_name", "Môn học")
    course_id = _make_course_id(course_name)

    # 1. Check user cache
    cached = _load_user_cache(username, course_id, node_id)
    if cached and cached.get("study_material", {}).get("detailed_content"):
        return cached

    # 2. Check shared library
    lib_pack = load_from_library(course_id, node_id)
    if lib_pack and lib_pack.get("study_material", {}).get("detailed_content"):
        _save_user_cache(username, lib_pack)  # Cache locally
        print(f"📥 Loaded from library: {course_id}/{node_id}")
        return lib_pack

    # 3. AI Generate
    print(f"🤖 Generating content for {node_id}...")
    node_title = node_info.get("title") or node_info.get("label") or node_id
    node_content = node_info.get("content") or node_info.get("description") or node_title
    alpha_base = node_info.get("alpha_base", 15)

    # ═══ GATHER REFERENCE MATERIALS ═══
    reference_materials = _gather_node_context(node_id, node_info, tree_data)

    # Get all micro node IDs for position calculation
    all_ids = _get_all_micro_ids(tree_data)
    position = get_node_position_ratio(node_id, all_ids)

    # Bloom calibration
    bloom_levels = calibrate_bloom_from_alpha(alpha_base, position)
    bloom_profile = create_bloom_profile(bloom_levels, "alpha_base", alpha_base)

    # Generate study material first
    study_material = await generate_study_material(node_title, node_content, course_name, bloom_levels, reference_materials)
    
    # Enrich node_content for question generation
    enriched_content = node_content + f"\n\n[NỘI DUNG BÀI HỌC]\n{study_material.get('detailed_content', '')}"
    
    # Generate question bank using the enriched content
    question_bank = await generate_question_bank(node_title, enriched_content, course_name, bloom_levels, reference_materials)

    # Assemble content pack
    pack = _empty_content_pack(node_id, course_id)
    pack["author"] = username
    pack["study_material"] = study_material
    pack["bloom_profile"] = bloom_profile
    pack["question_bank"] = question_bank

    # Save to user cache
    _save_user_cache(username, pack)

    # Auto-publish to library
    if auto_publish:
        publish_to_library(pack, author=username)

    return pack


def get_content_pack_sync(node_id: str, node_info: dict, tree_data: dict,
                           username: str) -> dict | None:
    """
    Synchronous version — chỉ đọc từ cache/library, KHÔNG gọi AI.
    Returns None nếu chưa có content.
    """
    course_name = tree_data.get("course_name", "Môn học")
    course_id = _make_course_id(course_name)

    cached = _load_user_cache(username, course_id, node_id)
    if cached:
        return cached

    lib_pack = load_from_library(course_id, node_id)
    if lib_pack:
        _save_user_cache(username, lib_pack)
        return lib_pack

    return None


# ============================================================
#  SYNC ALL NODES — Batch sync từ library
# ============================================================

def sync_bloom_content_for_tree(tree_path: str, username: str) -> int:
    """
    Quét toàn bộ nodes trong tree, sync content từ library nếu có.
    Returns: số nodes đã sync.
    """
    if not os.path.exists(tree_path):
        return 0

    with open(tree_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)

    course_name = tree_data.get("course_name", "Môn học")
    course_id = _make_course_id(course_name)
    synced = 0

    all_ids = _get_all_micro_ids(tree_data)
    nodes = _get_all_nodes(tree_data)

    for node_id, node_info in nodes.items():
        # Skip if already cached
        if _load_user_cache(username, course_id, node_id):
            continue

        # Try library
        lib_pack = load_from_library(course_id, node_id)
        if lib_pack:
            _save_user_cache(username, lib_pack)
            synced += 1

    if synced > 0:
        print(f"📥 Synced {synced} content packs from library for {username}")
    return synced


# ============================================================
#  HELPERS
# ============================================================

def _make_course_id(course_name: str) -> str:
    """Create a filesystem-safe course ID from name."""
    import re
    safe = re.sub(r'[^\w\s-]', '', course_name).strip().lower()
    safe = re.sub(r'[\s]+', '_', safe)
    return safe[:60] or "unknown_course"


def _get_all_micro_ids(tree_data: dict) -> list:
    """Get all micro node IDs from tree data."""
    ids = []
    if "nodes" in tree_data and isinstance(tree_data["nodes"], dict):
        for nid, ninfo in tree_data["nodes"].items():
            if ninfo.get("type") in ("micro", None):
                ids.append(nid)
    else:
        for n in tree_data.get("micro_nodes", []):
            ids.append(n.get("id", ""))
    return ids


def _get_all_nodes(tree_data: dict) -> dict:
    """Get all nodes as {id: info} dict."""
    if "nodes" in tree_data and isinstance(tree_data["nodes"], dict):
        return tree_data["nodes"]
    nodes = {}
    for key in ["macro_nodes", "micro_nodes", "assess_nodes"]:
        for n in tree_data.get(key, []):
            nodes[n.get("id", "")] = n
    return nodes

import os
import re
import json
import uuid
from resource_manager import detect_resource_type

# ============================================================
# AIUD COURSE LESSON MAP (from https://tranthanhthangbmt.github.io/AIUD_March2026/)
# ============================================================
# Mapping: node_id -> list of {url, title, type}
# Based on actual website structure verified 2026-04-19

AIUD_BASE = "https://tranthanhthangbmt.github.io/AIUD_March2026"

# Module lesson URLs: lesson.html?sessionId=X&id=XY
AIUD_LESSON_MAP = {
    # Module 1: Khai thác dữ liệu và thông tin
    "c1.1": {"session": 1, "lesson": 11, "title": "Khai phá Đại dương Số"},
    "c1.2": {"session": 1, "lesson": 12, "title": "Hành trình công dân số"},
    "c1.3": {"session": 1, "lesson": 13, "title": "LÀM CHỦ DỮ LIỆU SỐ"},
    # Module 2: Giao tiếp và hợp tác trong môi trường số
    "c2.1": {"session": 2, "lesson": 21, "title": "Hành trình công dân số"},
    "c2.2": {"session": 2, "lesson": 22, "title": "Làm chủ tương tác"},
    # Module 3: Sáng tạo nội dung số
    "c3.1": {"session": 3, "lesson": 31, "title": "Content Development"},
    "c3.2": {"session": 3, "lesson": 32, "title": "Content Repurposing"},
    "c3.3": {"session": 3, "lesson": 33, "title": "Digital Rights"},
    # Module 4: An toàn Không gian số
    "c4.1": {"session": 4, "lesson": 41, "title": "Safety Blueprint"},
    "c4.2": {"session": 4, "lesson": 42, "title": "An toàn Mạng"},
    "c4.3": {"session": 4, "lesson": 43, "title": "Digital Sustainability"},
    # Module 5: Giải quyết vấn đề bằng công nghệ
    "c5.1": {"session": 5, "lesson": 51, "title": "Giải quyết vấn đề"},
    # Module 6: Nhập môn Trí tuệ Nhân tạo
    "c6.1": {"session": 6, "lesson": 61, "title": "AI Foundations"},
    "c6.2": {"session": 6, "lesson": 62, "title": "AI Blueprint"},
}

# Quiz URLs: quiz.html?file=data%2Fquiz%2FMDX.csv
AIUD_QUIZ_MAP = {
    1: "quiz.html?file=data%2Fquiz%2FMD1.csv",
    2: "quiz.html?file=data%2Fquiz%2FMD2.csv",
    3: "quiz.html?file=data%2Fquiz%2FMD3.csv",
    4: "quiz.html?file=data%2Fquiz%2FMD4.csv",
    5: "quiz.html?file=data%2Fquiz%2FMD5.csv",
    6: "quiz.html?file=data%2Fquiz%2FMD6.csv",
}


def get_base_repo_url(tree_path=""):
    """Lấy URL base từ DB/videosLinksCourse.txt hoặc tự động đoán theo file tree"""
    # Case-insensitive check for AIUD course
    tp_upper = tree_path.upper()
    if "TRITUE" in tp_upper or "AIUD" in tp_upper or "TRÍ TUỆ" in tp_upper or "NHÂN TẠO" in tp_upper or "AI ỨNG DỤNG" in tp_upper:
        return AIUD_BASE
    
    links_file = os.path.join('DB', 'videosLinksCourse.txt')
    if os.path.exists(links_file):
        with open(links_file, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'https?://[^\s\n]+', content)
            if match:
                return match.group(0).rstrip('/')
    # Fallback
    return AIUD_BASE


def _is_aiud_course(tree_path, tree_data):
    """Kiểm tra xem cây này có phải AIUD không (case-insensitive)."""
    tp_upper = tree_path.upper()
    if "TRITUE" in tp_upper or "AIUD" in tp_upper or "TRÍ TUỆ" in tp_upper or "NHÂN TẠO" in tp_upper or "AI ỨNG DỤNG" in tp_upper:
        return True
    course_name = tree_data.get("course_name", "").upper()
    if "TRÍ TUỆ" in course_name or "AIUD" in course_name or "AI ỨNG DỤNG" in course_name:
        return True
    return False


def sync_resources_to_tree(tree_path):
    """
    Quét qua tất cả các node trong cây tri thức, tự động thêm tài nguyên:
    - Cho AIUD: dùng bản đồ lesson chính xác từ website thực
    - Cho các khóa khác: dùng logic keyword cũ 
    """
    if not os.path.exists(tree_path):
        print(f"[Sync] Không tìm thấy file cây: {tree_path}")
        return False

    with open(tree_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)

    nodes_to_process = []
    if "nodes" in tree_data and isinstance(tree_data["nodes"], dict):
        for nid, ninfo in tree_data["nodes"].items():
            ninfo["_id_for_sync"] = nid
            nodes_to_process.append(ninfo)
    else:
        for list_key in ["macro_nodes", "micro_nodes", "assess_nodes"]:
            for ninfo in tree_data.get(list_key, []):
                ninfo["_id_for_sync"] = ninfo.get("id", "")
                nodes_to_process.append(ninfo)

    changed = False
    is_aiud = _is_aiud_course(tree_path, tree_data)
    repo_url = AIUD_BASE if is_aiud else get_base_repo_url(tree_path)

    for node_info in nodes_to_process:
        node_id = node_info.get('_id_for_sync', '')
        if 'resources' not in node_info:
            node_info['resources'] = []
        
        # --- XÓA resource auto-sync cũ (sai URL) để ghi lại từ đầu ---
        old_count = len(node_info['resources'])
        node_info['resources'] = [r for r in node_info['resources'] if r.get('added_at') != 'auto-sync']
        if len(node_info['resources']) != old_count:
            changed = True
            
        res_list = node_info['resources']
        
        if is_aiud:
            # ============ AIUD COURSE: Dùng bản đồ chính xác ============
            changed = _sync_aiud_node(node_id, node_info, res_list, repo_url) or changed
        else:
            # ============ GENERIC COURSE: Dùng keyword detection ============
            changed = _sync_generic_node(node_id, node_info, res_list, repo_url) or changed

        # Clean loop transient state
        if "_id_for_sync" in node_info:
            del node_info["_id_for_sync"]

    if changed:
        with open(tree_path, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=4)
        print(f"[Sync] Đã cập nhật xong tài nguyên cho: {tree_path}")
    
    return changed


def _sync_aiud_node(node_id, node_info, res_list, repo_url):
    """Đồng bộ tài nguyên cho một node của khóa AIUD dựa trên bản đồ chính xác."""
    changed = False
    
    # --- MICRO NODE: Gắn bài giảng video + quiz ---
    if node_id in AIUD_LESSON_MAP:
        info = AIUD_LESSON_MAP[node_id]
        session_id = info["session"]
        lesson_id = info["lesson"]
        title = info["title"]
        
        # Bài giảng Video (lesson.html)
        vid_url = f"{repo_url}/lesson.html?sessionId={session_id}&id={lesson_id}"
        if not any(r.get('url') == vid_url for r in res_list):
            res_list.insert(0, {
                "id": f"res_lesson_{node_id}_{uuid.uuid4().hex[:4]}",
                "url": vid_url,
                "title": f"🎬 Bài giảng: {title}",
                "type": "youtube", "icon": "🎬", "added_at": "auto-sync"
            })
            changed = True
        
        # Trắc nghiệm (quiz.html)
        if session_id in AIUD_QUIZ_MAP:
            quiz_url = f"{repo_url}/{AIUD_QUIZ_MAP[session_id]}"
            if not any(r.get('url') == quiz_url for r in res_list):
                res_list.append({
                    "id": f"res_quiz_{node_id}_{uuid.uuid4().hex[:4]}",
                    "url": quiz_url,
                    "title": f"📝 Trắc nghiệm Module {session_id}",
                    "type": "link", "icon": "📝", "added_at": "auto-sync"
                })
                changed = True
        
        # Mục lục Module (session.html)
        session_url = f"{repo_url}/session.html?id={session_id}"
        if not any(r.get('url') == session_url for r in res_list):
            res_list.append({
                "id": f"res_session_{node_id}_{uuid.uuid4().hex[:4]}",
                "url": session_url,
                "title": f"📋 Mục lục Module {session_id}",
                "type": "link", "icon": "📋", "added_at": "auto-sync"
            })
            changed = True
    
    # --- MACRO NODE (mX): Gắn mục lục module + quiz ---
    m_match = re.match(r'^m(\d+)$', node_id)
    if m_match:
        mod_num = int(m_match.group(1))
        if 1 <= mod_num <= 6:
            session_url = f"{repo_url}/session.html?id={mod_num}"
            if not any(r.get('url') == session_url for r in res_list):
                res_list.append({
                    "id": f"res_session_m{mod_num}_{uuid.uuid4().hex[:4]}",
                    "url": session_url,
                    "title": f"📋 Mục lục Module {mod_num}",
                    "type": "link", "icon": "📋", "added_at": "auto-sync"
                })
                changed = True
            
            if mod_num in AIUD_QUIZ_MAP:
                quiz_url = f"{repo_url}/{AIUD_QUIZ_MAP[mod_num]}"
                if not any(r.get('url') == quiz_url for r in res_list):
                    res_list.append({
                        "id": f"res_quiz_m{mod_num}_{uuid.uuid4().hex[:4]}",
                        "url": quiz_url,
                        "title": f"📝 Trắc nghiệm Module {mod_num}",
                        "type": "link", "icon": "📝", "added_at": "auto-sync"
                    })
                    changed = True
    
    return changed


def _sync_generic_node(node_id, node_info, res_list, repo_url):
    """Đồng bộ tài nguyên cho các khóa học generic (không phải AIUD)."""
    changed = False
    desc = (node_info.get('title', '') + ' ' + node_info.get('content', '') + ' ' + node_info.get('description', '')).upper()
    
    # 1. Nhận diện Module (MD1 -> MD6)
    mod_id = None
    module_match = re.search(r'MD(\d)|MODULE\s*(\d)', desc)
    if module_match:
        mod_id = module_match.group(1) or module_match.group(2)
    else:
        pid = node_info.get('parent_macro') or node_id
        if isinstance(pid, str):
            m_num = re.search(r'^m(\d+)', pid.lower())
            if m_num:
                mod_id = m_num.group(1)
    
    if mod_id and mod_id.isdigit():
        mod_int = int(mod_id)
        if 1 <= mod_int <= 6:
            vid_url = f"{repo_url}/Module_1-6/Video/Module_{mod_id}/index.html"
            if not any(r.get('url') == vid_url for r in res_list):
                res_list.insert(0, {
                    "id": f"res_vid_MD{mod_id}_{uuid.uuid4().hex[:4]}",
                    "url": vid_url, "title": f"🎬 Bài giảng Video (Module {mod_id})",
                    "type": "youtube", "icon": "🎬", "added_at": "auto-sync"
                })
                changed = True
                 
            quiz_url = f"{repo_url}/Module_1-6/index.html?module=MD{mod_id}"
            if not any(r.get('url') == quiz_url for r in res_list):
                res_list.append({
                    "id": f"res_quiz_MD{mod_id}_{uuid.uuid4().hex[:4]}",
                    "url": quiz_url, "title": f"📝 Trắc nghiệm - Module {mod_id}",
                    "type": "link", "icon": "📝", "added_at": "auto-sync"
                })
                changed = True
        elif mod_int == 7:
            desc += ' WORD'
        elif mod_int == 8:
            desc += ' EXCEL'
        elif mod_int == 9:
            desc += ' POWERPOINT'

    # 2. Nhận diện Buổi học
    buoi_match = re.search(r'BUỔI\s*(\d+)', desc)
    if buoi_match:
        buoi_id = buoi_match.group(1)
        slide_url = f"{repo_url}/TaiLieuHuongDan/Buổi%20{buoi_id}/"
        if not any('Buổi' in r.get('title', '') for r in res_list):
             res_list.append({
                 "id": f"res_slide_B{buoi_id}_{uuid.uuid4().hex[:4]}",
                 "url": slide_url, "title": f"📄 Tài liệu Thực hành Buổi {buoi_id}",
                 "type": "pdf", "icon": "📄", "added_at": "auto-sync"
             })
             changed = True

    # 3. Slide kỹ năng
    if 'WORD' in desc and not any('Word' in r.get('title', '') for r in res_list):
        res_list.append({
            "id": f"res_doc_w_{uuid.uuid4().hex[:4]}", "url": f"{repo_url}/TaiLieuHuongDan/Slide/Slide_Word.pdf",
            "title": "📄 Slide Bài giảng Word", "type": "pdf", "icon": "📄", "added_at": "auto-sync"
        })
        changed = True
        
    if 'EXCEL' in desc and not any('Excel' in r.get('title', '') for r in res_list):
        res_list.append({
            "id": f"res_doc_e_{uuid.uuid4().hex[:4]}", "url": f"{repo_url}/TaiLieuHuongDan/Slide/Slide_Excel.pdf",
            "title": "📄 Slide Bài giảng Excel", "type": "pdf", "icon": "📄", "added_at": "auto-sync"
        })
        changed = True
        
    if 'POWERPOINT' in desc and not any('PowerPoint' in r.get('title', '') for r in res_list):
        res_list.append({
            "id": f"res_doc_p_{uuid.uuid4().hex[:4]}", "url": f"{repo_url}/TaiLieuHuongDan/Slide/Slide_PowerPoint.pdf",
            "title": "📄 Slide Bài giảng PowerPoint", "type": "pdf", "icon": "📄", "added_at": "auto-sync"
        })
        changed = True
    
    return changed

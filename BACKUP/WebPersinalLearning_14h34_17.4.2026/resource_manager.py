"""
Resource Manager — Quản lý tài nguyên học tập cho các Node trong Cây Tri Thức.
Mỗi node (micro/assess) có trường "resources" chứa danh sách link tài nguyên.
Hỗ trợ: YouTube, PDF, Google Docs, Google Colab, Google Drive, Website tùy chỉnh.
"""

import os
import json
import uuid
import re
from datetime import datetime


# ============================================================
#  AUTO-DETECT RESOURCE TYPE TỪ URL
# ============================================================

RESOURCE_TYPE_PATTERNS = [
    (r'(youtube\.com|youtu\.be)', 'youtube', '🎬', 'YouTube'),
    (r'colab\.research\.google\.com', 'colab', '🧪', 'Google Colab'),
    (r'docs\.google\.com/document', 'gdoc', '📝', 'Google Docs'),
    (r'docs\.google\.com/spreadsheets', 'gsheet', '📊', 'Google Sheets'),
    (r'docs\.google\.com/presentation', 'gslide', '📽️', 'Google Slides'),
    (r'drive\.google\.com', 'gdrive', '📁', 'Google Drive'),
    (r'github\.com', 'github', '🐙', 'GitHub'),
    (r'kaggle\.com', 'kaggle', '📈', 'Kaggle'),
    (r'\.pdf(\?|$|#)', 'pdf', '📄', 'PDF'),
    (r'wikipedia\.org', 'wiki', '📚', 'Wikipedia'),
    (r'arxiv\.org', 'arxiv', '🔬', 'arXiv Paper'),
]

def detect_resource_type(url: str) -> tuple:
    """Phát hiện loại tài nguyên từ URL. Trả về (type_key, icon, display_name)."""
    url_lower = url.lower()
    for pattern, type_key, icon, display_name in RESOURCE_TYPE_PATTERNS:
        if re.search(pattern, url_lower):
            return type_key, icon, display_name
    return 'web', '🌐', 'Website'


# ============================================================
#  ĐỌC / GHI FILE JSON CÂY TRI THỨC (THREAD-SAFE)
# ============================================================

def _read_tree(tree_path: str) -> dict:
    """Đọc file JSON cây tri thức."""
    if not os.path.exists(tree_path):
        raise FileNotFoundError(f"Không tìm thấy file: {tree_path}")
    with open(tree_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_tree(tree_path: str, data: dict):
    """Ghi lại file JSON cây tri thức."""
    with open(tree_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ============================================================
#  TRUY CẬP NODES (Hỗ trợ cả format cũ và mới)
# ============================================================

def _get_nodes_dict(tree_data: dict) -> dict:
    """Lấy dict nodes từ tree data, hỗ trợ cả format phẳng mới và format cũ."""
    # Format mới: {"nodes": {"id": {...}, ...}}
    if "nodes" in tree_data and isinstance(tree_data["nodes"], dict):
        return tree_data["nodes"]
    
    # Format cũ: {"macro_nodes": [...], "micro_nodes": [...], "assess_nodes": [...]}
    nodes = {}
    for m in tree_data.get("macro_nodes", []):
        nodes[m["id"]] = m
    for c in tree_data.get("micro_nodes", []):
        nodes[c["id"]] = c
    for a in tree_data.get("assess_nodes", []):
        nodes[a["id"]] = a
    return nodes


# ============================================================
#  API CHÍNH
# ============================================================

def get_all_nodes_summary(tree_path: str) -> list:
    """
    Trả về danh sách tóm tắt tất cả node trong cây.
    [{id, label, type, resource_count, parent_id}]
    """
    tree_data = _read_tree(tree_path)
    nodes = _get_nodes_dict(tree_data)
    edges = tree_data.get("edges", [])
    
    # Map để tra cứu parent nhanh từ edges (ưu tiên relation 'contains' và 'assessed_by')
    parent_map = {}
    for e in edges:
        rel = e.get("relation")
        src = e.get("source")
        tgt = e.get("target")
        if rel == "contains":
            parent_map[tgt] = src
        elif rel == "assessed_by":
            parent_map[tgt] = src
        
    # Map để tra cứu các node TIỀN ĐỀ (Prerequisites)
    prereq_map = {}
    for e in edges:
        if e.get("relation") == "prerequisite_for" or "reason" in e:
            src = e.get("source")
            tgt = e.get("target")
            if tgt not in prereq_map: prereq_map[tgt] = []
            prereq_map[tgt].append(src)

    result = []
    for node_id, node_data in nodes.items():
        node_type = node_data.get("type", "unknown")
        label = node_data.get("label") or node_data.get("title") or node_id
        resources = node_data.get("resources", [])
        
        # Thử lấy parent_id từ data node hoặc từ map edges
        parent_id = node_data.get("parent_macro") or node_data.get("target_micro") or parent_map.get(node_id)
        
        # Heuristic: Nếu ID có dạng Chuong_X_Tiet_Y, thử đoán parent là mX
        if not parent_id and node_type != 'macro':
            match = re.search(r'Chuong_(\d+)', node_id)
            if match:
                parent_id = f"m{match.group(1)}"
        
        result.append({
            "id": node_id,
            "label": label,
            "type": node_type,
            "resource_count": len(resources),
            "parent_id": parent_id,
            "prerequisites": prereq_map.get(node_id, [])
        })
    
    # Sắp xếp mặc định
    type_order = {"macro": 0, "micro": 1, "assess": 2}
    result.sort(key=lambda x: (type_order.get(x["type"], 9), x["id"]))
    
    return result


def get_hierarchical_nodes(tree_path: str) -> list:
    """
    Xây dựng cấu trúc cây lồng nhau cho Sidebar:
    Chapters -> Lessons -> Assessments
    """
    summaries = get_all_nodes_summary(tree_path)
    
    # Khởi tạo các nhóm
    chapters = []
    lessons_by_parent = {}
    assess_by_parent = {}
    standalone_micros = []
    
    # Phân loại
    for n in summaries:
        if n['type'] == 'macro':
            n['children'] = []
            chapters.append(n)
        elif n['type'] == 'micro':
            pid = n['parent_id']
            if pid:
                if pid not in lessons_by_parent: lessons_by_parent[pid] = []
                lessons_by_parent[pid].append(n)
            else:
                standalone_micros.append(n)
        elif n['type'] == 'assess':
            pid = n['parent_id']
            if pid:
                if pid not in assess_by_parent: assess_by_parent[pid] = []
                assess_by_parent[pid].append(n)
            else:
                standalone_micros.append(n) # Coi như micro nếu mồ côi

    # Ráp các mảng con vào Chapter
    for chap in chapters:
        lessons = lessons_by_parent.get(chap['id'], [])
        for les in lessons:
            les['children'] = assess_by_parent.get(les['id'], [])
        chap['children'] = lessons
        
        # Cập nhật resource_count tổng hợp cho Chapter
        total_res = chap['resource_count']
        for les in lessons:
            total_res += les['resource_count']
            for ass in les.get('children', []):
                total_res += ass['resource_count']
        chap['total_resource_count'] = total_res

    # Trình bày kết quả: Chapter có con -> Standalone (nếu có)
    final_tree = chapters
    if standalone_micros:
        # Nhóm các bài mồ côi vào 1 "Chương ảo" nếu cần, hoặc để phẳng
        other_chap = {
            "id": "standalone",
            "label": "Tài liệu khác",
            "type": "macro",
            "children": standalone_micros,
            "resource_count": 0,
            "total_resource_count": sum(m['resource_count'] for m in standalone_micros)
        }
        final_tree.append(other_chap)
        
    return final_tree



def get_node_resources(tree_path: str, node_id: str) -> list:
    """Lấy danh sách resources của 1 node cụ thể."""
    tree_data = _read_tree(tree_path)
    nodes = _get_nodes_dict(tree_data)
    
    node = nodes.get(node_id)
    if not node:
        return []
    
    return node.get("resources", [])


def add_resource(tree_path: str, node_id: str, url: str, title: str = "", res_type: str = "") -> dict:
    """
    Thêm 1 resource link vào node.
    
    Args:
        tree_path: Đường dẫn file JSON cây
        node_id: ID của node
        url: URL tài nguyên
        title: Tiêu đề (nếu trống sẽ auto-generate)
        res_type: Loại tài nguyên (nếu trống sẽ auto-detect)
    
    Returns:
        Dict resource vừa thêm
    """
    tree_data = _read_tree(tree_path)
    nodes = _get_nodes_dict(tree_data)
    
    if node_id not in nodes:
        raise ValueError(f"Node '{node_id}' không tồn tại trong cây")
    
    # Auto-detect type nếu không cung cấp
    detected_type, icon, display_name = detect_resource_type(url)
    if not res_type:
        res_type = detected_type
    
    # Auto-generate title nếu trống
    if not title:
        title = f"{display_name} — {node_id}"
    
    resource = {
        "id": f"res_{uuid.uuid4().hex[:8]}",
        "url": url.strip(),
        "title": title.strip(),
        "type": res_type,
        "icon": icon,
        "added_at": datetime.now().isoformat()
    }
    
    # Đảm bảo trường resources tồn tại
    if "resources" not in nodes[node_id]:
        nodes[node_id]["resources"] = []
    
    # Kiểm tra trùng URL
    existing_urls = [r.get("url", "") for r in nodes[node_id]["resources"]]
    if url.strip() in existing_urls:
        raise ValueError(f"URL này đã tồn tại trong node '{node_id}'")
    
    nodes[node_id]["resources"].append(resource)
    
    _write_tree(tree_path, tree_data)
    
    return resource


def remove_resource(tree_path: str, node_id: str, resource_id: str) -> bool:
    """
    Xóa 1 resource theo ID.
    
    Returns:
        True nếu xóa thành công, False nếu không tìm thấy
    """
    tree_data = _read_tree(tree_path)
    nodes = _get_nodes_dict(tree_data)
    
    if node_id not in nodes:
        return False
    
    resources = nodes[node_id].get("resources", [])
    original_len = len(resources)
    
    nodes[node_id]["resources"] = [r for r in resources if r.get("id") != resource_id]
    
    if len(nodes[node_id]["resources"]) < original_len:
        _write_tree(tree_path, tree_data)
        return True
    
    return False


def update_resource(tree_path: str, node_id: str, resource_id: str, 
                    url: str = None, title: str = None) -> bool:
    """Cập nhật thông tin 1 resource."""
    tree_data = _read_tree(tree_path)
    nodes = _get_nodes_dict(tree_data)
    
    if node_id not in nodes:
        return False
    
    resources = nodes[node_id].get("resources", [])
    for res in resources:
        if res.get("id") == resource_id:
            if url is not None:
                res["url"] = url.strip()
                # Re-detect type
                detected_type, icon, _ = detect_resource_type(url)
                res["type"] = detected_type
                res["icon"] = icon
            if title is not None:
                res["title"] = title.strip()
            
            _write_tree(tree_path, tree_data)
            return True
    
    return False


def get_resource_stats(tree_path: str) -> dict:
    """Thống kê tổng quan tài nguyên của toàn bộ cây."""
    tree_data = _read_tree(tree_path)
    nodes = _get_nodes_dict(tree_data)
    
    total_resources = 0
    nodes_with_resources = 0
    type_counts = {}
    
    for node_id, node_data in nodes.items():
        resources = node_data.get("resources", [])
        if resources:
            nodes_with_resources += 1
            total_resources += len(resources)
            for r in resources:
                rtype = r.get("type", "web")
                type_counts[rtype] = type_counts.get(rtype, 0) + 1
    
    return {
        "total_resources": total_resources,
        "nodes_with_resources": nodes_with_resources,
        "total_nodes": len(nodes),
        "type_counts": type_counts
    }

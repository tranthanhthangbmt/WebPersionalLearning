# bloom_taxonomy.py
"""
Bloom Taxonomy Framework — Tiêu chuẩn quốc tế (MIT-level)
Quản lý 6 bậc Bloom cho mỗi node trong Cây Tri Thức.

Features:
- BLOOM_LEVELS: Config chuẩn 6 bậc với icon, color, assessment types
- auto_calibrate_bloom(): AI tự gán mức Bloom dựa trên yêu cầu môn học
- user_adjust_bloom(): Cho phép user nâng (không hạ) mức Bloom
- calculate_overall_bloom(): Tính overall bloom score 0.0-6.0 từ per-level scores
"""

import json
import os
import copy
from datetime import datetime
import time
import math

# ============================================================
#  BLOOM LEVELS CONFIG — 6 bậc chuẩn Anderson & Krathwohl (2001)
# ============================================================

BLOOM_LEVELS = {
    1: {
        "name": "Remember", "vi": "Ghi nhớ",
        "icon": "🧠", "color": "hsl(200, 80%, 50%)",
        "hex": "#2196F3",
        "verbs_vi": ["liệt kê", "nhận diện", "xác định", "gọi tên", "nhớ lại"],
        "verbs_en": ["list", "identify", "define", "name", "recall"],
        "assessment_types": ["mcq_recall", "flashcard", "matching_basic", "socratic"],
        "description": "Nhớ lại các thuật ngữ, định nghĩa, sự kiện cơ bản",
        "weight": 1.0,
        "pass_threshold": 0.70,
    },
    2: {
        "name": "Understand", "vi": "Thấu hiểu",
        "icon": "💡", "color": "hsl(140, 70%, 45%)",
        "hex": "#4CAF50",
        "verbs_vi": ["giải thích", "so sánh", "phân biệt", "tóm tắt", "diễn giải"],
        "verbs_en": ["explain", "compare", "distinguish", "summarize", "interpret"],
        "assessment_types": ["mcq_comprehension", "fill_blank", "matching", "explain", "practice_exercise", "socratic"],
        "description": "Hiểu ý nghĩa, giải thích được bằng lời của mình",
        "weight": 1.2,
        "pass_threshold": 0.70,
    },
    3: {
        "name": "Apply", "vi": "Áp dụng",
        "icon": "🔧", "color": "hsl(45, 90%, 50%)",
        "hex": "#FF9800",
        "verbs_vi": ["áp dụng", "sử dụng", "thực hiện", "giải quyết", "tính toán"],
        "verbs_en": ["apply", "use", "implement", "solve", "calculate"],
        "assessment_types": ["scenario_mcq", "case_study", "fill_blank_advanced", "practice_exercise", "socratic"],
        "description": "Áp dụng kiến thức vào tình huống cụ thể",
        "weight": 1.4,
        "pass_threshold": 0.65,
    },
    4: {
        "name": "Analyze", "vi": "Phân tích",
        "icon": "🔬", "color": "hsl(20, 85%, 55%)",
        "hex": "#F44336",
        "verbs_vi": ["phân tích", "so sánh", "đối chiếu", "phân loại", "tách biệt"],
        "verbs_en": ["analyze", "compare", "contrast", "classify", "differentiate"],
        "assessment_types": ["socratic", "compare_contrast", "analysis_essay", "practice_exercise"],
        "description": "Phân tích mối quan hệ, nguyên nhân, cấu trúc",
        "weight": 1.6,
        "pass_threshold": 0.60,
    },
    5: {
        "name": "Evaluate", "vi": "Đánh giá",
        "icon": "⚖️", "color": "hsl(300, 70%, 55%)",
        "hex": "#9C27B0",
        "verbs_vi": ["đánh giá", "phê bình", "biện luận", "lựa chọn", "bảo vệ"],
        "verbs_en": ["evaluate", "critique", "argue", "justify", "defend"],
        "assessment_types": ["debate", "critique", "socratic_advanced", "practice_exercise"],
        "description": "Đánh giá, phê bình, đưa ra quyết định có lý lẽ",
        "weight": 1.8,
        "pass_threshold": 0.55,
    },
    6: {
        "name": "Create", "vi": "Sáng tạo",
        "icon": "🎨", "color": "hsl(280, 80%, 60%)",
        "hex": "#7C4DFF",
        "verbs_vi": ["thiết kế", "sáng tạo", "đề xuất", "xây dựng", "tổng hợp"],
        "verbs_en": ["design", "create", "propose", "construct", "synthesize"],
        "assessment_types": ["design_task", "project", "creative_proposal", "practice_exercise"],
        "description": "Sáng tạo giải pháp mới, thiết kế, tổng hợp",
        "weight": 2.0,
        "pass_threshold": 0.50,
    },
}


# ============================================================
#  BLOOM CALIBRATION — Tự động gán mức Bloom cho node
# ============================================================

def calibrate_bloom_from_alpha(alpha_base: int, node_position_ratio: float = 0.5) -> list:
    """
    Gán target bloom levels dựa trên alpha_base và vị trí node trong curriculum.
    
    Args:
        alpha_base: Độ khó sinh học (10-30) từ AI khi tạo tree
        node_position_ratio: Vị trí tương đối trong khóa (0.0 = đầu, 1.0 = cuối)
    
    Returns:
        List of target bloom levels (ints 1-6)
    """
    if alpha_base <= 12:
        # Rất dễ — lý thuyết cơ bản
        levels = [1, 2]
    elif alpha_base <= 18:
        # Trung bình — lý thuyết + hiểu
        levels = [1, 2, 3]
    elif alpha_base <= 24:
        # Khó — ứng dụng + phân tích
        levels = [2, 3, 4]
    else:
        # Rất khó — phân tích + đánh giá
        levels = [3, 4, 5]
    
    # Bonus: nodes cuối khóa → thêm mức cao hơn
    if node_position_ratio >= 0.85:
        max_level = max(levels)
        if max_level < 6:
            levels.append(max_level + 1)
    
    return sorted(set(levels))


def get_node_position_ratio(node_id: str, all_node_ids: list) -> float:
    """Tính vị trí tương đối của node trong danh sách."""
    if not all_node_ids or node_id not in all_node_ids:
        return 0.5
    idx = all_node_ids.index(node_id)
    return idx / max(1, len(all_node_ids) - 1)


def user_adjust_bloom(current_levels: list, requested_levels: list) -> list:
    """
    Cho phép user điều chỉnh Bloom levels.
    Quy tắc: chỉ được THÊM mức cao hơn, không được BỎ mức đã có.
    
    Args:
        current_levels: Mức Bloom hiện tại (auto-calibrated)
        requested_levels: Mức Bloom user muốn
    
    Returns:
        Effective levels (union, đảm bảo superset)
    """
    # Union: giữ tất cả mức cũ + thêm mức mới (nếu cao hơn hoặc bằng)
    effective = set(current_levels)
    for lvl in requested_levels:
        if 1 <= lvl <= 6:
            effective.add(lvl)
    return sorted(effective)


# ============================================================
#  BLOOM SCORING — Tính overall bloom từ per-level scores
# ============================================================

def calculate_overall_bloom(level_scores: dict) -> float:
    """
    Tính overall bloom score (0.0 → 6.0) từ per-level assessment results.
    
    Args:
        level_scores: {
            "1": {"score": 0.8, "types_done": ["mcq", "flashcard"]},
            "2": {"score": 0.6, "types_done": ["matching"]},
            ...
        }
    
    Returns:
        Weighted average bloom score (0.0 → 6.0)
    """
    if not level_scores:
        return 0.0
    
    weighted_sum = 0.0
    weight_total = 0.0
    
    for level_str, data in level_scores.items():
        level = int(level_str)
        if level not in BLOOM_LEVELS:
            continue
        
        score = data.get("score", 0.0)
        weight = BLOOM_LEVELS[level]["weight"]
        
        # Only count levels that have been attempted
        if data.get("total", 0) > 0:
            weighted_sum += level * score * weight
            weight_total += weight
    
    if weight_total == 0:
        return 0.0
    
    return min(6.0, weighted_sum / weight_total)


def check_level_unlocked(level: int, level_scores: dict, target_levels: list,
                         bloom_ceiling: int = 6) -> bool:
    """
    Kiểm tra xem một mức Bloom có được mở khóa chưa.
    
    Rules:
    - L1 luôn mở (nếu nằm trong target_levels)
    - L(n) mở khi L(n-1) đạt pass_threshold VÀ đã làm >= 2 loại đánh giá
    - Chỉ xét các levels trong target_levels
    - NEW: Level > bloom_ceiling → luôn khóa (Soft Prerequisite)
    
    Args:
        level: Bloom level cần kiểm tra (1-6)
        level_scores: Dict scores cho từng level
        target_levels: List Bloom levels mục tiêu của node
        bloom_ceiling: Bloom level tối đa cho phép bởi Soft Prerequisite
                       (default=6, backward-compatible — không giới hạn)
    """
    # NEW: Soft Prerequisite ceiling — levels above ceiling are locked
    if level > bloom_ceiling:
        return False
    
    if level == 1:
        return True
    
    if level not in target_levels:
        return False
    
    # Check previous level
    prev_level = level - 1
    # Tìm mức trước đó thực sự trong target_levels
    lower_levels = [l for l in target_levels if l < level]
    if not lower_levels:
        return True  # Không có mức thấp hơn → mở
    
    prev_level = max(lower_levels)
    prev_data = level_scores.get(str(prev_level), {})
    prev_score = prev_data.get("score", 0.0)
    prev_types = prev_data.get("types_done", [])
    
    threshold = BLOOM_LEVELS.get(prev_level, {}).get("pass_threshold", 0.70)
    
    return prev_score >= threshold and len(prev_types) >= 2


def calculate_bloom_ceiling_from_prereqs(node_id: str, tree_data: dict,
                                          bloom_state: dict,
                                          policy: str = "university_flexible") -> int:
    """
    Tính Bloom ceiling dựa trên prerequisite mastery.
    Wrapper gọi soft_prerequisite module.
    
    Args:
        node_id: ID node cần tính ceiling
        tree_data: Tree data chứa edges
        bloom_state: Bloom state của user
        policy: Access policy (k12_strict / university_flexible / professional_open)
    
    Returns:
        Bloom level tối đa được phép (1-6)
    """
    try:
        from soft_prerequisite import calculate_bloom_ceiling
        from bloom_taxonomy import get_effective_levels, _find_node
        
        node_info = _find_node(tree_data, node_id)
        if node_info and node_info.get("bloom_profile"):
            target_levels = get_effective_levels(node_info["bloom_profile"])
        else:
            target_levels = [1, 2, 3]  # Default
        
        edges = tree_data.get("edges", [])
        return calculate_bloom_ceiling(node_id, target_levels, edges,
                                       bloom_state, policy)
    except ImportError:
        return 6  # Fallback: no ceiling


def get_bloom_color(overall_bloom: float) -> str:
    """
    Trả về màu HSL tương ứng với overall bloom score.
    Dùng cho 3D visualization.
    """
    if overall_bloom < 0.1:
        return "hsl(210, 20%, 30%)"   # Uncharted — xám tối
    elif overall_bloom < 1.0:
        return "hsl(210, 20%, 40%)"   # Exposure — xám sáng
    elif overall_bloom < 2.0:
        return BLOOM_LEVELS[1]["color"]  # Remember
    elif overall_bloom < 3.0:
        return BLOOM_LEVELS[2]["color"]  # Understand
    elif overall_bloom < 4.0:
        return BLOOM_LEVELS[3]["color"]  # Apply
    elif overall_bloom < 5.0:
        return BLOOM_LEVELS[4]["color"]  # Analyze
    elif overall_bloom < 5.5:
        return BLOOM_LEVELS[5]["color"]  # Evaluate
    else:
        return BLOOM_LEVELS[6]["color"]  # Create


# ============================================================
#  BLOOM PROFILE — Cấu trúc dữ liệu cho mỗi node
# ============================================================

def create_bloom_profile(target_levels: list, method: str = "alpha_base", 
                         alpha_base: int = 15) -> dict:
    """
    Tạo bloom_profile mặc định cho 1 node.
    """
    return {
        "auto_calibrated_levels": sorted(target_levels),
        "user_adjusted_levels": None,
        "effective_levels": sorted(target_levels),
        "calibration_method": method,
        "alpha_base": alpha_base,
        "created_at": datetime.now().isoformat(),
    }


def get_effective_levels(bloom_profile: dict) -> list:
    """Trả về effective bloom levels (ưu tiên user-adjusted)."""
    if bloom_profile.get("user_adjusted_levels"):
        return bloom_profile["user_adjusted_levels"]
    return bloom_profile.get("effective_levels", 
                             bloom_profile.get("auto_calibrated_levels", [1, 2]))


# ============================================================
#  USER BLOOM STATE — Trạng thái học tập per-user per-subject
# ============================================================

def create_empty_bloom_state(subject_id: str) -> dict:
    """Tạo bloom state rỗng cho 1 subject."""
    return {
        "subject_id": subject_id,
        "created_at": datetime.now().isoformat(),
        "nodes": {},
        "ebbinghaus": {},
    }


def create_node_bloom_scores(target_levels: list) -> dict:
    """Tạo bloom scores rỗng cho 1 node."""
    scores = {}
    for lvl in target_levels:
        scores[str(lvl)] = {
            "correct": 0,
            "total": 0,
            "score": 0.0,
            "types_done": [],
        }
    return {
        "bloom_scores": scores,
        "overall_bloom": 0.0,
        "highest_unlocked": min(target_levels) if target_levels else 1,
        "last_activity": None,
        "study_completed": False,
        "total_time_sec": 0,
    }


def update_bloom_score(node_state: dict, bloom_level: int, 
                       is_correct: bool, assessment_type: str,
                       target_levels: list) -> dict:
    """
    Cập nhật bloom score sau khi hoàn thành 1 câu đánh giá.
    
    Args:
        node_state: Node bloom state dict
        bloom_level: Mức Bloom (1-6)
        is_correct: Đúng/Sai
        assessment_type: Loại đánh giá (mcq_recall, matching, etc.)
        target_levels: Target bloom levels của node
    
    Returns:
        Updated node_state
    """
    level_key = str(bloom_level)
    
    if "bloom_scores" not in node_state:
        node_state["bloom_scores"] = {}
    
    if level_key not in node_state["bloom_scores"]:
        node_state["bloom_scores"][level_key] = {
            "correct": 0, "total": 0, "score": 0.0, "types_done": []
        }
    
    level_data = node_state["bloom_scores"][level_key]
    level_data["total"] += 1
    if is_correct:
        level_data["correct"] += 1
    
    # Recalculate score
    level_data["score"] = round(level_data["correct"] / max(1, level_data["total"]), 3)
    
    # Track assessment type diversity
    if assessment_type not in level_data["types_done"]:
        level_data["types_done"].append(assessment_type)
    
    # Update overall bloom
    node_state["overall_bloom"] = round(
        calculate_overall_bloom(node_state["bloom_scores"]), 3
    )
    
    # Update highest unlocked
    for lvl in sorted(target_levels):
        if check_level_unlocked(lvl, node_state["bloom_scores"], target_levels):
            node_state["highest_unlocked"] = lvl
    
    node_state["last_activity"] = datetime.now().isoformat()
    
    return node_state


# ============================================================
#  BLOOM STATE FILE I/O
# ============================================================

def get_bloom_state_path(username: str, subject_id: str) -> str:
    """Get path to user's bloom state file."""
    return os.path.join("user_data", username, "bloom_state", f"{subject_id}.json")


def load_bloom_state(username: str, subject_id: str) -> dict:
    """Load bloom state from JSON file and apply Ebbinghaus decay."""
    path = get_bloom_state_path(username, subject_id)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
                # Apply Ebbinghaus decay automatically on load
                if "nodes" in state and "ebbinghaus" in state:
                    eb_data = state["ebbinghaus"]
                    for node_id, node_data in state["nodes"].items():
                        if node_id in eb_data:
                            # We pass True to is_loading so it doesn't try to update last_review
                            state["nodes"][node_id] = apply_ebbinghaus_decay(node_data, eb_data, node_id)
                return state
        except (json.JSONDecodeError, IOError):
            pass
    return create_empty_bloom_state(subject_id)


def save_bloom_state(username: str, subject_id: str, state: dict):
    """Save bloom state to JSON file."""
    path = get_bloom_state_path(username, subject_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_node_bloom_data(username: str, subject_id: str, node_id: str) -> dict:
    """Get bloom data for a specific node."""
    state = load_bloom_state(username, subject_id)
    return state.get("nodes", {}).get(node_id, {})


def get_all_bloom_scores(username: str, subject_id: str) -> dict:
    """Get {node_id: overall_bloom} for all nodes — used by 3D visualizer."""
    state = load_bloom_state(username, subject_id)
    result = {}
    for node_id, node_data in state.get("nodes", {}).items():
        result[node_id] = node_data.get("overall_bloom", 0.0)
    return result


def get_all_bloom_level_scores(username: str, subject_id: str) -> dict:
    """Get {node_id: {L1: score%, L2: score%, ...}} for 3D graph mini-bloom bars."""
    state = load_bloom_state(username, subject_id)
    result = {}
    for node_id, node_data in state.get("nodes", {}).items():
        bloom_scores = node_data.get("bloom_scores", {})
        levels = {}
        for lvl_str, lvl_data in bloom_scores.items():
            if lvl_data.get("total", 0) > 0:
                levels[lvl_str] = round(lvl_data.get("score", 0.0) * 100)
            else:
                levels[lvl_str] = 0
        result[node_id] = levels
    return result


# ============================================================
#  PHASE 2: TREE-LEVEL BLOOM CALIBRATION
# ============================================================

def calibrate_tree_bloom(tree_path: str, force: bool = False) -> dict:
    """
    Batch-calibrate Bloom profiles cho TẤT CẢ nodes trong 1 tree JSON.
    Ghi trường 'bloom_profile' vào mỗi node.
    
    Args:
        tree_path: Path to tree JSON file
        force: Nếu True, ghi đè bloom_profile cũ. Nếu False, chỉ ghi cho node chưa có.
    
    Returns:
        {"calibrated": int, "skipped": int, "total": int}
    """
    if not os.path.exists(tree_path):
        return {"calibrated": 0, "skipped": 0, "total": 0, "error": "File not found"}
    
    with open(tree_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)
    
    # Collect all micro node IDs for position calculation
    all_micro_ids = _collect_micro_ids(tree_data)
    stats = {"calibrated": 0, "skipped": 0, "total": 0}
    changed = False
    
    # Process both old format (list) and new format (dict)
    node_lists = []
    if "nodes" in tree_data and isinstance(tree_data["nodes"], dict):
        node_lists = [("nodes_dict", tree_data["nodes"])]
    else:
        for key in ["micro_nodes", "macro_nodes", "assess_nodes"]:
            if key in tree_data:
                node_lists.append((key, tree_data[key]))
    
    for list_key, nodes_source in node_lists:
        if isinstance(nodes_source, dict):
            items = nodes_source.items()
        else:
            items = [(n.get("id", f"idx_{i}"), n) for i, n in enumerate(nodes_source)]
        
        for node_id, node_info in items:
            stats["total"] += 1
            
            # Skip if already calibrated and not forcing
            if not force and node_info.get("bloom_profile"):
                stats["skipped"] += 1
                continue
            
            # Get alpha_base (default 15 for macro nodes)
            node_type = node_info.get("type", "")
            if list_key == "macro_nodes" or node_type == "macro":
                alpha = 15  # Macro nodes get default
            elif list_key == "assess_nodes" or node_type == "assess":
                alpha = node_info.get("alpha_base", 20)  # Assess nodes slightly higher
            else:
                alpha = node_info.get("alpha_base", 15)
            
            # Position ratio
            position = get_node_position_ratio(node_id, all_micro_ids)
            
            # Calibrate
            levels = calibrate_bloom_from_alpha(alpha, position)
            profile = create_bloom_profile(levels, "alpha_base", alpha)
            
            node_info["bloom_profile"] = profile
            stats["calibrated"] += 1
            changed = True
    
    # Save back
    if changed:
        with open(tree_path, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=4)
    
    return stats


def adjust_node_bloom_in_tree(tree_path: str, node_id: str, 
                               new_levels: list) -> dict:
    """
    User điều chỉnh Bloom levels cho 1 node trong tree JSON.
    Chỉ cho phép THÊM mức, không bỏ mức đã có.
    
    Returns:
        {"success": bool, "effective_levels": list, "message": str}
    """
    if not os.path.exists(tree_path):
        return {"success": False, "effective_levels": [], 
                "message": "Tree file not found"}
    
    with open(tree_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)
    
    # Find the node
    node_info = _find_node(tree_data, node_id)
    if not node_info:
        return {"success": False, "effective_levels": [],
                "message": f"Node '{node_id}' not found"}
    
    # Ensure bloom_profile exists
    if not node_info.get("bloom_profile"):
        alpha = node_info.get("alpha_base", 15)
        levels = calibrate_bloom_from_alpha(alpha)
        node_info["bloom_profile"] = create_bloom_profile(levels, "alpha_base", alpha)
    
    profile = node_info["bloom_profile"]
    current = profile.get("auto_calibrated_levels", [1, 2])
    
    # Apply user adjustment (union — can only add, never remove)
    effective = user_adjust_bloom(current, new_levels)
    profile["user_adjusted_levels"] = sorted(new_levels)
    profile["effective_levels"] = effective
    
    # Save
    with open(tree_path, 'w', encoding='utf-8') as f:
        json.dump(tree_data, f, ensure_ascii=False, indent=4)
    
    level_names = [f"L{l} {BLOOM_LEVELS[l]['vi']}" for l in effective]
    return {"success": True, "effective_levels": effective,
            "message": f"Updated: {', '.join(level_names)}"}


def get_course_bloom_summary(tree_path: str, username: str = None, 
                              subject_id: str = None) -> dict:
    """
    Thống kê tổng quan Bloom cho toàn bộ khóa học.
    
    Returns:
        {
            "course_name": str,
            "total_nodes": int,
            "nodes_calibrated": int,
            "bloom_distribution": {1: count, 2: count, ...},
            "user_progress": {node_id: overall_bloom, ...} (if username provided)
        }
    """
    if not os.path.exists(tree_path):
        return {"error": "Tree not found"}
    
    with open(tree_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)
    
    course_name = tree_data.get("course_name", "Unknown")
    all_nodes = _get_all_nodes_flat(tree_data)
    
    bloom_dist = {i: 0 for i in range(1, 7)}
    calibrated = 0
    
    for node_id, node_info in all_nodes.items():
        profile = node_info.get("bloom_profile")
        if profile:
            calibrated += 1
            for lvl in get_effective_levels(profile):
                if lvl in bloom_dist:
                    bloom_dist[lvl] += 1
    
    result = {
        "course_name": course_name,
        "total_nodes": len(all_nodes),
        "nodes_calibrated": calibrated,
        "bloom_distribution": bloom_dist,
    }
    
    # Add user progress if available
    if username and subject_id:
        result["user_progress"] = get_all_bloom_scores(username, subject_id)
    
    return result


# ============================================================
#  EBBINGHAUS FORGETTING CURVE — Bloom score decay
# ============================================================

import math

def apply_ebbinghaus_decay(node_state: dict, ebbinghaus_data: dict,
                           node_id: str) -> dict:
    """
    Apply Ebbinghaus forgetting curve decay to bloom scores.
    
    Formula: retention = e^(-t/S)
    where t = time since last review (hours), S = memory strength
    
    Args:
        node_state: Node bloom scores dict
        ebbinghaus_data: {"last_review": timestamp, "strength": float, "reviews": int}
        node_id: Node ID for lookup
    
    Returns:
        Updated node_state with decayed scores
    """
    node_eb = ebbinghaus_data.get(node_id, {})
    last_review = node_eb.get("last_review", 0)
    strength = node_eb.get("strength", 2.0)  # Initial strength in hours
    
    if last_review == 0:
        return node_state  # Never reviewed, no decay
    
    hours_elapsed = (time.time() - last_review) / 3600.0
    if hours_elapsed < 0.1:
        return node_state  # Less than 6 minutes, no decay
    
    # Retention factor (0.0 to 1.0)
    retention = math.exp(-hours_elapsed / max(0.5, strength))
    retention = max(0.1, min(1.0, retention))  # Clamp
    
    # Apply decay to each level score
    for level_key, level_data in node_state.get("bloom_scores", {}).items():
        if level_data.get("total", 0) > 0:
            original_score = level_data["score"]
            level_data["decayed_score"] = round(original_score * retention, 3)
    
    # Recalculate overall with decayed scores
    decayed_scores = {}
    for lk, ld in node_state.get("bloom_scores", {}).items():
        decayed_scores[lk] = {
            "score": ld.get("decayed_score", ld.get("score", 0.0)),
            "total": ld.get("total", 0),
        }
    node_state["overall_bloom_decayed"] = round(
        calculate_overall_bloom(decayed_scores), 3
    )
    node_state["retention"] = round(retention, 3)
    
    return node_state


def update_ebbinghaus_after_review(ebbinghaus_data: dict, node_id: str,
                                    performance: float) -> dict:
    """
    Update memory strength after a review session.
    Good performance → strength increases (longer retention).
    
    Args:
        performance: 0.0 to 1.0 (accuracy of the review)
    """
    node_eb = ebbinghaus_data.get(node_id, {
        "last_review": 0, "strength": 2.0, "reviews": 0
    })
    
    # Update strength based on performance
    if performance >= 0.7:
        node_eb["strength"] = min(720.0, node_eb["strength"] * 1.5)  # Max 30 days
    elif performance >= 0.4:
        node_eb["strength"] = max(1.0, node_eb["strength"] * 1.1)
    else:
        node_eb["strength"] = max(0.5, node_eb["strength"] * 0.7)
    
    node_eb["last_review"] = time.time()
    node_eb["reviews"] = node_eb.get("reviews", 0) + 1
    
    ebbinghaus_data[node_id] = node_eb
    return ebbinghaus_data


# ============================================================
#  INTERNAL HELPERS
# ============================================================

import time

def _collect_micro_ids(tree_data: dict) -> list:
    """Collect all micro node IDs from tree."""
    ids = []
    if "nodes" in tree_data and isinstance(tree_data["nodes"], dict):
        for nid, ninfo in tree_data["nodes"].items():
            if ninfo.get("type") in ("micro", None):
                ids.append(nid)
    else:
        for n in tree_data.get("micro_nodes", []):
            ids.append(n.get("id", ""))
    return ids


def _find_node(tree_data: dict, node_id: str) -> dict | None:
    """Find a node by ID in tree data."""
    if "nodes" in tree_data and isinstance(tree_data["nodes"], dict):
        return tree_data["nodes"].get(node_id)
    for key in ["micro_nodes", "macro_nodes", "assess_nodes"]:
        for n in tree_data.get(key, []):
            if n.get("id") == node_id:
                return n
    return None


def _get_all_nodes_flat(tree_data: dict) -> dict:
    """Get all nodes as flat {id: info} dict."""
    if "nodes" in tree_data and isinstance(tree_data["nodes"], dict):
        return tree_data["nodes"]
    result = {}
    for key in ["macro_nodes", "micro_nodes", "assess_nodes"]:
        for n in tree_data.get(key, []):
            result[n.get("id", "")] = n
    return result

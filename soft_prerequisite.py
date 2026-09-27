# soft_prerequisite.py
"""
Soft Prerequisite & Conditional Access System
==============================================
Thay thế Hard Lock bằng Bloom Ceiling — cho phép học viên truy cập
chương sau với Bloom level giới hạn nếu chương trước chưa hoàn thành.

VẤN ĐỀ CỐT LÕI:
  Sinh viên đang học Chương 3 nhưng Chương 1 chưa hoàn thành.
  → Hard Lock (cũ): Khóa hoàn toàn Ch3 → Frustration, dropout
  → Soft Lock (mới): Mở Ch3 nhưng GIỚI HẠN Bloom Level tối đa

CÔNG THỨC BLOOM CEILING:
  max_bloom(node) = min(
      target_bloom_max,
      floor(avg_prereq_mastery × target_max) + 1
  )

  VÍ DỤ:
    Ch1 mastery = 30%, Ch3 target = [L1, L2, L3, L4]
    → ceiling = min(4, floor(0.3 × 4) + 1) = min(4, 2) = L2
    → Ch3 chỉ mở L1 + L2, khóa L3-L4

3 ACCESS POLICIES cho đa ngữ cảnh:
  - k12_strict:            K-12 — tuần tự chặt chẽ
  - university_flexible:   Đại học — cho nhảy chương, ceiling động
  - professional_open:     Chuyên nghiệp — tự do, chỉ gợi ý

References:
  - Doignon & Falmagne (1999). Knowledge Spaces
  - Fake & Dabbagh (2023). PLiF Framework, Ch.7
"""

import math

# ============================================================
#  STORY 0.2.1 — ACCESS POLICIES & PREREQUISITE GRAPH
# ============================================================

ACCESS_POLICIES = {
    "k12_strict": {
        "name": "K-12",
        "description": "Tuần tự chặt chẽ, phù hợp K-12 (Đã mở khóa theo yêu cầu)",
        "min_prereq_mastery": 0.0,     # Mở khóa hoàn toàn
        "bloom_ceiling_enabled": False, # Tắt giới hạn Bloom
        "allow_skip_chapter": True,    # Cho phép nhảy chương
        "penalty_multiplier": 1.5,
        "contexts": ["middle_school", "high_school"],
    },
    "university_flexible": {
        "name": "Đại học",
        "description": "Cho phép học không tuần tự, Bloom ceiling động (Đã mở khóa)",
        "min_prereq_mastery": 0.0,
        "bloom_ceiling_enabled": False,
        "allow_skip_chapter": True,
        "penalty_multiplier": 1.2,
        "contexts": ["undergraduate", "graduate", "mit_ocw"],
    },
    "professional_open": {
        "name": "Chuyên nghiệp",
        "description": "Tự do hoàn toàn, chỉ gợi ý không chặn",
        "min_prereq_mastery": 0.0,
        "bloom_ceiling_enabled": False,
        "allow_skip_chapter": True,
        "penalty_multiplier": 1.0,
        "contexts": ["corporate_training", "self_learner"],
    },
}


def get_direct_prerequisites(node_id: str, edges: list) -> list:
    """
    Tìm prerequisite trực tiếp (1 bậc) của node.

    Dựa trên cấu trúc edges trong tree JSON:
      {"source": "c1.1", "target": "c1.2"} → c1.1 là prereq của c1.2

    Args:
        node_id: ID node cần tìm prereqs
        edges: List of edge dicts (source, target)

    Returns:
        List of direct prerequisite node IDs
    """
    prereqs = []
    for edge in edges:
        if edge.get("target") == node_id:
            source = edge.get("source", "")
            if source and source not in prereqs:
                prereqs.append(source)
    return prereqs


def get_all_prerequisites(node_id: str, edges: list) -> set:
    """
    Tìm TẤT CẢ prerequisite (transitive closure) bằng DFS.

    VD: c1.1→c1.2→c1.3 → get_all_prerequisites("c1.3") = {c1.1, c1.2}

    Cycle-safe: dùng visited set để tránh infinite loop.

    Args:
        node_id: ID node cần tìm prereqs
        edges: List of edge dicts

    Returns:
        Set of all prerequisite node IDs (transitive)
    """
    all_prereqs = set()
    visited = set()
    stack = [node_id]

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)

        direct = get_direct_prerequisites(current, edges)
        for prereq in direct:
            if prereq not in all_prereqs:
                all_prereqs.add(prereq)
                stack.append(prereq)

    return all_prereqs


# ============================================================
#  STORY 0.2.2 — PREREQUISITE MASTERY CALCULATION
# ============================================================

def get_prereq_mastery(node_id: str, edges: list,
                       bloom_state: dict) -> float:
    """
    Tính trung bình mastery của prerequisite nodes.

    Mastery = overall_bloom / 6.0 (scale 0-6 → 0.0-1.0)
    Nếu không có prereq → return 1.0 (root node, full access).
    Nếu prereq chưa có trong bloom_state → mastery = 0.

    Args:
        node_id: Target node
        edges: Edge list
        bloom_state: {"nodes": {"c1.1": {"overall_bloom": 3.0}, ...}}

    Returns:
        Average mastery (0.0 → 1.0)
    """
    prereqs = get_all_prerequisites(node_id, edges)

    if not prereqs:
        return 1.0  # Root node — full access

    nodes_data = bloom_state.get("nodes", {})
    total_mastery = 0.0

    for prereq_id in prereqs:
        node_data = nodes_data.get(prereq_id, {})
        overall_bloom = node_data.get("overall_bloom", 0.0)
        # Scale: 0-6 → 0-1
        mastery = min(1.0, overall_bloom / 6.0)
        total_mastery += mastery

    return total_mastery / len(prereqs)


# ============================================================
#  STORY 0.2.3 — BLOOM CEILING FORMULA
# ============================================================

def calculate_bloom_ceiling(node_id: str, target_levels: list,
                            edges: list, bloom_state: dict,
                            policy: str = "university_flexible") -> int:
    """
    Tính Bloom level tối đa được phép truy cập.

    Công thức:
      ceiling = min(target_max, floor(avg_prereq_mastery × target_max) + 1)

    Special cases:
      - Policy "professional_open" → luôn return target_max (không giới hạn)
      - Root node (no prereqs) → luôn return target_max
      - Empty target_levels → return 1

    Args:
        node_id: Target node
        target_levels: List of target Bloom levels [1,2,3,4]
        edges: Edge list
        bloom_state: Bloom state dict
        policy: Access policy key

    Returns:
        Maximum allowed Bloom level (int)
    """
    if not target_levels:
        return 1

    target_max = max(target_levels)
    target_min = min(target_levels)

    # Policy check: professional_open → no ceiling
    policy_config = ACCESS_POLICIES.get(policy, ACCESS_POLICIES["university_flexible"])
    if not policy_config.get("bloom_ceiling_enabled", True):
        return target_max

    # Get prereq mastery
    avg_mastery = get_prereq_mastery(node_id, edges, bloom_state)

    # Root node (mastery = 1.0 from get_prereq_mastery) → full access
    if avg_mastery >= 1.0:
        return target_max

    # Ceiling formula
    ceiling = min(target_max, math.floor(avg_mastery * target_max) + 1)

    # Ensure at least target_min is accessible
    return max(target_min, ceiling)


# ============================================================
#  STORY 0.2.4 — ACCESS STATUS REPORT
# ============================================================

def get_access_status(node_id: str, target_levels: list,
                      edges: list, bloom_state: dict,
                      policy: str = "university_flexible") -> dict:
    """
    Tổng hợp trạng thái truy cập đầy đủ cho UI.

    Returns:
        {
            "accessible": bool,         # Có được truy cập không
            "bloom_ceiling": int,       # Bloom max được phép
            "unlocked_levels": [1,2],   # Levels thực sự mở
            "locked_levels": [3,4],     # Levels bị khóa bởi prerequisite
            "prereq_gaps": [...],       # Prerequisite chưa đạt
            "prereq_mastery": float,    # Avg mastery of prereqs
            "policy": str,              # Policy đang dùng
            "recommendation": str,      # Gợi ý hành động
        }
    """
    policy_config = ACCESS_POLICIES.get(policy, ACCESS_POLICIES["university_flexible"])
    avg_mastery = get_prereq_mastery(node_id, edges, bloom_state)
    ceiling = calculate_bloom_ceiling(node_id, target_levels, edges,
                                      bloom_state, policy)

    # Determine accessible
    min_mastery_required = policy_config.get("min_prereq_mastery", 0.0)
    allow_skip = policy_config.get("allow_skip_chapter", True)

    # K-12 strict: block if prereq mastery < threshold
    prereqs = get_all_prerequisites(node_id, edges)
    accessible = True
    if prereqs and not allow_skip and avg_mastery < min_mastery_required:
        accessible = False

    # Split levels
    unlocked_levels = [l for l in target_levels if l <= ceiling]
    locked_levels = [l for l in target_levels if l > ceiling]

    # Find prereq gaps
    nodes_data = bloom_state.get("nodes", {})
    prereq_gaps = []
    for prereq_id in prereqs:
        node_data = nodes_data.get(prereq_id, {})
        mastery = node_data.get("overall_bloom", 0.0) / 6.0
        if mastery < 0.6:  # Below 60%
            prereq_gaps.append({
                "node_id": prereq_id,
                "mastery": round(mastery, 2),
                "needed": 0.6,
            })

    # Recommendation
    if not prereqs:
        recommendation = "Đây là node gốc — truy cập đầy đủ."
    elif not prereq_gaps:
        recommendation = "Tất cả prerequisite đã hoàn thành — truy cập đầy đủ!"
    elif not accessible:
        gap_ids = ", ".join(g["node_id"] for g in prereq_gaps[:3])
        recommendation = f"⛔ Cần hoàn thành {gap_ids} trước (yêu cầu ≥60%)."
    elif locked_levels:
        gap_ids = ", ".join(g["node_id"] for g in prereq_gaps[:3])
        lock_str = ", ".join(f"L{l}" for l in locked_levels)
        recommendation = (f"Hoàn thành {gap_ids} để mở khóa {lock_str}. "
                          f"Hiện tại chỉ truy cập được L{min(target_levels)}-L{ceiling}.")
    else:
        recommendation = "Truy cập đầy đủ tất cả Bloom levels."

    return {
        "accessible": accessible,
        "bloom_ceiling": ceiling,
        "unlocked_levels": unlocked_levels,
        "locked_levels": locked_levels,
        "prereq_gaps": prereq_gaps,
        "prereq_mastery": round(avg_mastery, 3),
        "policy": policy,
        "recommendation": recommendation,
    }


# ============================================================
#  STORY 0.5 — KNOWLEDGE SPACE: OUTER FRINGE DETECTION
# ============================================================

def get_knowledge_space_fringe(all_node_ids: list, edges: list,
                               bloom_state: dict,
                               readiness_threshold: float = 0.8) -> list:
    """
    Knowledge Space Theory: Tìm 'outer fringe' — tập node mà
    người học SẴN SÀNG học tiếp theo.

    Fringe = nodes có ≥readiness_threshold% prereqs đã mastered (≥60%)
             VÀ bản thân node chưa mastered.

    Args:
        all_node_ids: Tất cả micro node IDs trong tree
        edges: Edge list
        bloom_state: Bloom state dict
        readiness_threshold: Tỷ lệ prereqs đã đạt (default 0.8 = 80%)

    Returns:
        List of dicts: [{"node_id": str, "readiness": float, "prereq_met": int,
                         "prereq_total": int}, ...]
        Sorted by readiness descending.
    """
    nodes_data = bloom_state.get("nodes", {})
    fringe = []

    for node_id in all_node_ids:
        # Skip if already mastered (overall_bloom >= 3.6 = 60% of 6)
        node_data = nodes_data.get(node_id, {})
        if node_data.get("overall_bloom", 0.0) >= 3.6:
            continue

        prereqs = get_all_prerequisites(node_id, edges)

        # Root node with no prereqs → always ready
        if not prereqs:
            # Only include if not yet started
            if node_data.get("overall_bloom", 0.0) < 0.1:
                fringe.append({
                    "node_id": node_id,
                    "readiness": 1.0,
                    "prereq_met": 0,
                    "prereq_total": 0,
                })
            continue

        # Count how many prereqs are mastered (>=60% = overall_bloom >= 3.6)
        met = 0
        for prereq_id in prereqs:
            prereq_data = nodes_data.get(prereq_id, {})
            if prereq_data.get("overall_bloom", 0.0) >= 3.6:
                met += 1

        readiness = met / len(prereqs) if prereqs else 1.0

        if readiness >= readiness_threshold:
            fringe.append({
                "node_id": node_id,
                "readiness": round(readiness, 2),
                "prereq_met": met,
                "prereq_total": len(prereqs),
            })

    # Sort by readiness descending
    fringe.sort(key=lambda x: x["readiness"], reverse=True)
    return fringe

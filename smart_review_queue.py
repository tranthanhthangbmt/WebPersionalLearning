# smart_review_queue.py
"""
Smart Review Queue — Hàng đợi ôn tập thông minh dựa trên Ebbinghaus
====================================================================

Sử dụng Ebbinghaus Forgetting Curve để ưu tiên nodes cần ôn tập:

CÔNG THỨC PRIORITY:
  R(t) = e^(-t/S)                          — Retention (độ nhớ)
  priority = (1 - R) × bloom_weight × recency_bonus

Trong đó:
  - t: Thời gian từ lần ôn cuối (giờ)
  - S: Sức mạnh lưu giữ (strength, tăng qua mỗi lần ôn)
  - bloom_weight: Trọng số Bloom (L1=1.0 → L6=3.5)
  - recency_bonus: Phạt nếu lâu không ôn

References:
  - Ebbinghaus (1885). Über das Gedächtnis
  - Leitner (1972). Spaced Repetition System
"""

import math
import time

# ============================================================
#  BLOOM WEIGHTS — Kiến thức bậc cao quên nhanh hơn, cần ôn hơn
# ============================================================

BLOOM_WEIGHTS = {
    1: 1.0,    # Remember
    2: 1.5,    # Understand
    3: 2.0,    # Apply
    4: 2.5,    # Analyze
    5: 3.0,    # Evaluate
    6: 3.5,    # Create
}


# ============================================================
#  STORY 1.3.1 — REVIEW PRIORITY SCORING
# ============================================================

def calculate_retention(last_review_time: float, strength: float,
                        current_time: float = None) -> float:
    """
    Tính Retention (độ nhớ) theo Ebbinghaus.

    R(t) = e^(-t/S)
      - t: giờ từ lần ôn cuối
      - S: strength (sức nhớ)

    Returns:
        float: 0.0 → 1.0
    """
    if current_time is None:
        current_time = time.time()

    hours = (current_time - last_review_time) / 3600.0
    if hours <= 0:
        return 1.0

    effective_strength = max(0.5, strength)
    retention = math.exp(-hours / effective_strength)
    return max(0.0, min(1.0, retention))


def calculate_review_priority(retention: float, bloom_weight: float,
                              hours_since_review: float) -> float:
    """
    Tính priority score cho review queue.

    priority = (1 - retention) × bloom_weight × recency_bonus

    recency_bonus: Lâu không ôn → bonus cao hơn
      - < 24h: 1.0
      - 24-72h: 1.2
      - > 72h: 1.5

    Args:
        retention: 0.0 → 1.0
        bloom_weight: Từ BLOOM_WEIGHTS
        hours_since_review: Giờ từ lần ôn cuối

    Returns:
        float: Priority score (cao hơn = cần ôn gấp hơn)
    """
    if hours_since_review < 24:
        recency_bonus = 1.0
    elif hours_since_review < 72:
        recency_bonus = 1.2
    else:
        recency_bonus = 1.5

    priority = (1.0 - retention) * bloom_weight * recency_bonus
    return round(priority, 4)


# ============================================================
#  STORY 1.3.2 — REVIEW QUEUE GENERATOR
# ============================================================

def get_review_queue(bloom_state: dict, max_items: int = 10,
                     current_time: float = None) -> list:
    """
    Tạo danh sách nodes cần ôn tập, sorted by priority.

    Args:
        bloom_state: {
            "nodes": {"c1.1": {"overall_bloom": 3.0, ...}},
            "ebbinghaus": {"c1.1": {"last_review": float, "strength": float, "reviews": int}}
        }
        max_items: Số items tối đa
        current_time: Override time (for testing)

    Returns:
        List of review items, sorted by priority (descending)
    """
    if current_time is None:
        current_time = time.time()

    nodes = bloom_state.get("nodes", {})
    ebbinghaus = bloom_state.get("ebbinghaus", {})

    queue = []

    for node_id, node_data in nodes.items():
        overall_bloom = node_data.get("overall_bloom", 0.0)

        # Skip nodes chưa học
        if overall_bloom < 0.1:
            continue

        eb = ebbinghaus.get(node_id, {})
        last_review = eb.get("last_review", 0)

        # Skip nodes chưa có lịch sử ôn tập
        if last_review <= 0:
            continue

        strength = eb.get("strength", 2.0)
        reviews = eb.get("reviews", 0)

        # Tính retention
        retention = calculate_retention(last_review, strength, current_time)

        # Skip nếu retention vẫn cao (chưa cần ôn)
        if retention > 0.95:
            continue

        hours = (current_time - last_review) / 3600.0

        # Bloom weight dựa trên overall_bloom
        bloom_level = max(1, min(6, round(overall_bloom)))
        bloom_weight = BLOOM_WEIGHTS.get(bloom_level, 1.0)

        priority = calculate_review_priority(retention, bloom_weight, hours)

        queue.append({
            "node_id": node_id,
            "priority": priority,
            "retention": round(retention, 3),
            "bloom_level": bloom_level,
            "hours_since_review": round(hours, 1),
            "strength": strength,
            "reviews": reviews,
        })

    # Sort by priority descending
    queue.sort(key=lambda x: x["priority"], reverse=True)
    return queue[:max_items]


# ============================================================
#  STORY 1.3.3 — REVIEW SESSION UPDATE
# ============================================================

def update_after_review(bloom_state: dict, node_id: str,
                        accuracy: float) -> dict:
    """
    Cập nhật Ebbinghaus sau khi ôn tập.

    - Accuracy >= 0.7: Tăng strength (nhớ lâu hơn)
    - Accuracy < 0.7: Giảm nhẹ strength (quên nhanh hơn)
    - Cập nhật last_review và reviews count

    Args:
        bloom_state: Bloom state dict (mutated in-place)
        node_id: Node đã ôn
        accuracy: Độ chính xác (0.0 → 1.0)

    Returns:
        Updated bloom_state
    """
    ebbinghaus = bloom_state.setdefault("ebbinghaus", {})
    eb = ebbinghaus.setdefault(node_id, {
        "last_review": 0,
        "strength": 2.0,
        "reviews": 0,
    })

    old_strength = eb.get("strength", 2.0)
    reviews = eb.get("reviews", 0) + 1

    if accuracy >= 0.7:
        # Tăng strength: nhớ lâu hơn
        # Mỗi lần ôn thành công: strength × 1.3
        new_strength = old_strength * (1.0 + 0.3 * accuracy)
    else:
        # Giảm nhẹ: quên nhanh hơn nhưng không quá harsh
        new_strength = max(1.0, old_strength * 0.85)

    eb["strength"] = round(new_strength, 2)
    eb["last_review"] = time.time()
    eb["reviews"] = reviews

    return bloom_state


def get_daily_review_summary(bloom_state: dict,
                             current_time: float = None) -> dict:
    """
    Tóm tắt ôn tập hàng ngày.

    Returns:
        {
            "total_nodes_learned": int,
            "nodes_need_review": int,
            "critical_nodes": int (retention < 0.3),
            "avg_retention": float,
            "next_review_hours": float (estimated),
        }
    """
    queue = get_review_queue(bloom_state, max_items=100,
                             current_time=current_time)

    nodes = bloom_state.get("nodes", {})
    learned = sum(1 for n in nodes.values()
                  if n.get("overall_bloom", 0) >= 0.1)

    retentions = [q["retention"] for q in queue]
    critical = sum(1 for r in retentions if r < 0.3)

    return {
        "total_nodes_learned": learned,
        "nodes_need_review": len(queue),
        "critical_nodes": critical,
        "avg_retention": round(
            sum(retentions) / len(retentions), 3
        ) if retentions else 1.0,
    }

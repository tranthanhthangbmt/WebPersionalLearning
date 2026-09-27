# tests/test_smart_review.py
"""
Test script cho smart_review_queue.py — Sprint 1.3
Bao gồm: Priority Scoring, Review Queue, Review Update, Daily Summary

Chạy: python tests/test_smart_review.py
"""

import os
import sys
import time
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_review_queue import (
    BLOOM_WEIGHTS, calculate_retention, calculate_review_priority,
    get_review_queue, update_after_review, get_daily_review_summary,
)

PASS = 0
FAIL = 0


def test(name, func):
    global PASS, FAIL
    try:
        func()
        print(f"  ✅ {name}")
        PASS += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        FAIL += 1


# ============================================================
#  STORY 1.3.1 — REVIEW PRIORITY SCORING
# ============================================================

def run_priority_tests():
    print("\n" + "=" * 60)
    print("📊 STORY 1.3.1 — Review Priority Scoring")
    print("=" * 60)

    now = time.time()

    def test_retention_recent():
        """Vừa ôn xong → retention gần 1.0"""
        r = calculate_retention(now - 60, 2.0, now)  # 1 phút trước
        assert r > 0.99, f"Expected >0.99, got {r}"

    def test_retention_old():
        """Lâu rồi → retention thấp"""
        r = calculate_retention(now - 86400, 2.0, now)  # 24h trước
        assert r < 0.01, f"Expected <0.01, got {r}"

    def test_retention_bounds():
        """Retention nằm trong [0, 1]"""
        for hours in [0, 1, 5, 24, 168, 720]:
            r = calculate_retention(now - hours*3600, 5.0, now)
            assert 0 <= r <= 1, f"Out of bounds at {hours}h: {r}"

    def test_priority_low_retention():
        """Low retention → high priority"""
        p_low = calculate_review_priority(0.2, 2.0, 48)
        p_high = calculate_review_priority(0.9, 2.0, 48)
        assert p_low > p_high, f"Low ret ({p_low}) should > High ret ({p_high})"

    def test_priority_higher_bloom():
        """Higher Bloom → higher priority"""
        p_l1 = calculate_review_priority(0.5, 1.0, 24)
        p_l4 = calculate_review_priority(0.5, 2.5, 24)
        assert p_l4 > p_l1, f"L4 ({p_l4}) should > L1 ({p_l1})"

    def test_priority_full_retention():
        """Retention 100% → priority = 0"""
        p = calculate_review_priority(1.0, 2.0, 24)
        assert p == 0.0, f"Expected 0, got {p}"

    def test_priority_recency_bonus():
        """Lâu hơn → recency bonus cao hơn"""
        p_12h = calculate_review_priority(0.5, 2.0, 12)   # < 24h → 1.0
        p_48h = calculate_review_priority(0.5, 2.0, 48)   # 24-72h → 1.2
        p_96h = calculate_review_priority(0.5, 2.0, 96)   # > 72h → 1.5
        assert p_48h > p_12h, f"48h ({p_48h}) should > 12h ({p_12h})"
        assert p_96h > p_48h, f"96h ({p_96h}) should > 48h ({p_48h})"

    def test_bloom_weights():
        """6 bloom weights defined"""
        assert len(BLOOM_WEIGHTS) == 6
        assert BLOOM_WEIGHTS[1] < BLOOM_WEIGHTS[6]

    test("Recent review → high retention", test_retention_recent)
    test("Old review → low retention", test_retention_old)
    test("Retention always [0, 1]", test_retention_bounds)
    test("Low retention → high priority", test_priority_low_retention)
    test("Higher Bloom → higher priority", test_priority_higher_bloom)
    test("Full retention → priority 0", test_priority_full_retention)
    test("Recency bonus scaling", test_priority_recency_bonus)
    test("6 Bloom weights defined", test_bloom_weights)


# ============================================================
#  STORY 1.3.2 — REVIEW QUEUE GENERATOR
# ============================================================

def run_queue_tests():
    print("\n" + "=" * 60)
    print("📋 STORY 1.3.2 — Review Queue Generator")
    print("=" * 60)

    now = time.time()

    mock_state = {
        "nodes": {
            "c1.1": {"overall_bloom": 3.0},  # Learned
            "c1.2": {"overall_bloom": 5.0},  # Learned, high bloom
            "c1.3": {"overall_bloom": 0.0},  # Not learned
            "c2.1": {"overall_bloom": 2.0},  # Learned
        },
        "ebbinghaus": {
            "c1.1": {"last_review": now - 7200, "strength": 2.0, "reviews": 2},     # 2h ago
            "c1.2": {"last_review": now - 86400, "strength": 3.0, "reviews": 5},    # 24h ago
            "c2.1": {"last_review": now - 172800, "strength": 1.5, "reviews": 1},   # 48h ago
        }
    }

    def test_queue_sorted():
        queue = get_review_queue(mock_state, current_time=now)
        for i in range(len(queue) - 1):
            assert queue[i]["priority"] >= queue[i+1]["priority"], \
                f"Not sorted: {queue[i]['priority']} < {queue[i+1]['priority']}"

    def test_queue_excludes_unlearned():
        queue = get_review_queue(mock_state, current_time=now)
        ids = [q["node_id"] for q in queue]
        assert "c1.3" not in ids, "Unlearned node should be excluded"

    def test_queue_max_items():
        queue = get_review_queue(mock_state, max_items=2, current_time=now)
        assert len(queue) <= 2

    def test_empty_state():
        empty = {"nodes": {}, "ebbinghaus": {}}
        queue = get_review_queue(empty, current_time=now)
        assert queue == []

    def test_queue_has_fields():
        queue = get_review_queue(mock_state, current_time=now)
        if queue:
            item = queue[0]
            for field in ["node_id", "priority", "retention", "bloom_level", "hours_since_review"]:
                assert field in item, f"Missing '{field}'"

    test("Queue sorted by priority desc", test_queue_sorted)
    test("Excludes unlearned nodes", test_queue_excludes_unlearned)
    test("Respects max_items", test_queue_max_items)
    test("Empty state → empty queue", test_empty_state)
    test("Queue items have all fields", test_queue_has_fields)


# ============================================================
#  STORY 1.3.3 — REVIEW SESSION UPDATE
# ============================================================

def run_update_tests():
    print("\n" + "=" * 60)
    print("🔄 STORY 1.3.3 — Review Session Update")
    print("=" * 60)

    def test_strength_increase():
        bs = {"ebbinghaus": {"c1.1": {"last_review": 100, "strength": 2.0, "reviews": 1}}}
        old = bs["ebbinghaus"]["c1.1"]["strength"]
        update_after_review(bs, "c1.1", accuracy=0.9)
        new = bs["ebbinghaus"]["c1.1"]["strength"]
        assert new > old, f"Strength should increase: {old} → {new}"

    def test_strength_decrease_on_fail():
        bs = {"ebbinghaus": {"c1.1": {"last_review": 100, "strength": 5.0, "reviews": 3}}}
        old = bs["ebbinghaus"]["c1.1"]["strength"]
        update_after_review(bs, "c1.1", accuracy=0.3)
        new = bs["ebbinghaus"]["c1.1"]["strength"]
        assert new < old, f"Strength should decrease: {old} → {new}"

    def test_last_review_updated():
        bs = {"ebbinghaus": {"c1.1": {"last_review": 100, "strength": 2.0, "reviews": 1}}}
        update_after_review(bs, "c1.1", accuracy=0.8)
        assert bs["ebbinghaus"]["c1.1"]["last_review"] > 100

    def test_review_count():
        bs = {"ebbinghaus": {"c1.1": {"last_review": 100, "strength": 2.0, "reviews": 3}}}
        update_after_review(bs, "c1.1", accuracy=0.8)
        assert bs["ebbinghaus"]["c1.1"]["reviews"] == 4

    def test_new_node_review():
        bs = {"ebbinghaus": {}}
        update_after_review(bs, "new_node", accuracy=0.9)
        assert "new_node" in bs["ebbinghaus"]
        assert bs["ebbinghaus"]["new_node"]["reviews"] == 1

    def test_strength_floor():
        """Strength không xuống dưới 1.0"""
        bs = {"ebbinghaus": {"c1.1": {"last_review": 100, "strength": 1.0, "reviews": 1}}}
        update_after_review(bs, "c1.1", accuracy=0.1)
        assert bs["ebbinghaus"]["c1.1"]["strength"] >= 1.0

    test("Strength increases on good review", test_strength_increase)
    test("Strength decreases on bad review", test_strength_decrease_on_fail)
    test("Last review timestamp updated", test_last_review_updated)
    test("Review count incremented", test_review_count)
    test("New node gets ebbinghaus entry", test_new_node_review)
    test("Strength floor = 1.0", test_strength_floor)


# ============================================================
#  BONUS: DAILY SUMMARY
# ============================================================

def run_summary_tests():
    print("\n" + "=" * 60)
    print("📅 BONUS — Daily Review Summary")
    print("=" * 60)

    now = time.time()

    mock_state = {
        "nodes": {
            "c1.1": {"overall_bloom": 3.0},
            "c1.2": {"overall_bloom": 5.0},
        },
        "ebbinghaus": {
            "c1.1": {"last_review": now - 86400, "strength": 2.0, "reviews": 2},
            "c1.2": {"last_review": now - 3600, "strength": 10.0, "reviews": 5},
        }
    }

    def test_summary_fields():
        summary = get_daily_review_summary(mock_state, current_time=now)
        for field in ["total_nodes_learned", "nodes_need_review", "critical_nodes", "avg_retention"]:
            assert field in summary, f"Missing '{field}'"

    def test_summary_learned_count():
        summary = get_daily_review_summary(mock_state, current_time=now)
        assert summary["total_nodes_learned"] == 2

    def test_empty_summary():
        summary = get_daily_review_summary({"nodes": {}, "ebbinghaus": {}})
        assert summary["total_nodes_learned"] == 0
        assert summary["avg_retention"] == 1.0

    test("Summary has all fields", test_summary_fields)
    test("Correct learned count", test_summary_learned_count)
    test("Empty state summary", test_empty_summary)


# ============================================================
#  MAIN
# ============================================================

def main():
    global PASS, FAIL

    run_priority_tests()
    run_queue_tests()
    run_update_tests()
    run_summary_tests()

    print("\n" + "=" * 60)
    total = PASS + FAIL
    if FAIL == 0:
        print(f"🎉 TẤT CẢ {total} TEST ĐỀU PASS!")
    else:
        print(f"📊 Kết quả: {PASS}/{total} PASS, {FAIL} FAIL")
    print("=" * 60)
    return FAIL == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

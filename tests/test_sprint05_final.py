# tests/test_sprint05_final.py
"""
Test script cho Sprint 0.5 — Learning Engine + Knowledge Space
Bao gồm:
  - Story 0.5.1: Policy-aware alpha penalty
  - Story 0.5.2: Knowledge Space fringe detection

Chạy: python tests/test_sprint05_final.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
#  STORY 0.5.1 — POLICY-AWARE ALPHA PENALTY
# ============================================================

def run_alpha_tests():
    print("\n" + "=" * 60)
    print("⚡ STORY 0.5.1 — Policy-Aware Alpha Penalty")
    print("=" * 60)

    from step3_learning_engine import calculate_alpha_cost

    tree = {
        "micro_nodes": [
            {"id": "c1.1", "alpha_base": 10},
            {"id": "c1.2", "alpha_base": 15},
        ],
        "edges": [
            {"source": "c1.1", "target": "c1.2"},
        ]
    }

    def test_no_penalty_mastered():
        """Prereq mastered (≥0.6) → no penalty"""
        state = {"knowledge_states": {"c1.1": {"k_score": 0.8}}}
        alpha = calculate_alpha_cost("c1.2", tree, state)
        assert alpha == 15.0, f"Expected 15.0, got {alpha}"

    def test_penalty_gap():
        """Prereq not mastered → penalty applied"""
        state = {"knowledge_states": {"c1.1": {"k_score": 0.2}}}
        alpha = calculate_alpha_cost("c1.2", tree, state)
        # gap = 0.6 - 0.2 = 0.4, default penalty = 1.5 (university)
        # alpha = 15 * (1 + 1.5 * 0.4) = 15 * 1.6 = 24.0
        assert alpha == 24.0, f"Expected 24.0, got {alpha}"

    def test_k12_higher_penalty():
        """K-12 strict → higher penalty (2.0x)"""
        state = {"knowledge_states": {"c1.1": {"k_score": 0.2}}}
        alpha_k12 = calculate_alpha_cost("c1.2", tree, state, "k12_strict")
        alpha_uni = calculate_alpha_cost("c1.2", tree, state, "university_flexible")
        assert alpha_k12 > alpha_uni, f"K-12 ({alpha_k12}) should > Uni ({alpha_uni})"

    def test_professional_no_penalty():
        """Professional open → penalty_multiplier=1.0 (lighter)"""
        state = {"knowledge_states": {"c1.1": {"k_score": 0.2}}}
        alpha_pro = calculate_alpha_cost("c1.2", tree, state, "professional_open")
        alpha_k12 = calculate_alpha_cost("c1.2", tree, state, "k12_strict")
        assert alpha_pro < alpha_k12, f"Pro ({alpha_pro}) should < K-12 ({alpha_k12})"

    def test_root_no_penalty():
        """Root node (no prereqs) → base alpha only"""
        state = {"knowledge_states": {}}
        alpha = calculate_alpha_cost("c1.1", tree, state)
        assert alpha == 10.0, f"Expected 10.0, got {alpha}"

    def test_missing_node():
        """Non-existent node → 0"""
        state = {"knowledge_states": {}}
        alpha = calculate_alpha_cost("c99.9", tree, state)
        assert alpha == 0, f"Expected 0, got {alpha}"

    def test_backward_compatible():
        """Gọi không có policy → hoạt động bình thường"""
        state = {"knowledge_states": {"c1.1": {"k_score": 0.8}}}
        alpha = calculate_alpha_cost("c1.2", tree, state)
        assert alpha == 15.0

    test("No penalty when prereq mastered", test_no_penalty_mastered)
    test("Penalty applied with gap", test_penalty_gap)
    test("K-12 higher penalty than Uni", test_k12_higher_penalty)
    test("Professional lighter than K-12", test_professional_no_penalty)
    test("Root node → base alpha", test_root_no_penalty)
    test("Missing node → 0", test_missing_node)
    test("Backward compatible (no policy)", test_backward_compatible)


# ============================================================
#  STORY 0.5.2 — KNOWLEDGE SPACE FRINGE DETECTION
# ============================================================

def run_fringe_tests():
    print("\n" + "=" * 60)
    print("🧩 STORY 0.5.2 — Knowledge Space Fringe Detection")
    print("=" * 60)

    from soft_prerequisite import get_knowledge_space_fringe

    edges = [
        {"source": "c1.1", "target": "c1.2"},
        {"source": "c1.2", "target": "c1.3"},
        {"source": "c1.3", "target": "c2.1"},
    ]
    all_nodes = ["c1.1", "c1.2", "c1.3", "c2.1"]

    def test_empty_state_roots():
        """Trạng thái rỗng → root nodes là fringe"""
        fringe = get_knowledge_space_fringe(all_nodes, edges, {"nodes": {}})
        fringe_ids = [f["node_id"] for f in fringe]
        assert "c1.1" in fringe_ids, "Root c1.1 should be in fringe"
        # Non-roots should NOT be in fringe (prereqs not met)
        assert "c2.1" not in fringe_ids, "c2.1 should NOT be in fringe"

    def test_after_mastering_c1():
        """Sau khi master c1.1 → c1.2 vào fringe"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 4.0}}}  # mastered
        fringe = get_knowledge_space_fringe(all_nodes, edges, bs)
        fringe_ids = [f["node_id"] for f in fringe]
        assert "c1.2" in fringe_ids, "c1.2 should be in fringe after c1.1 mastered"
        assert "c1.1" not in fringe_ids, "c1.1 mastered → not in fringe"

    def test_chain_progress():
        """Master c1.1+c1.2 → c1.3 vào fringe"""
        bs = {"nodes": {
            "c1.1": {"overall_bloom": 4.0},
            "c1.2": {"overall_bloom": 5.0},
        }}
        fringe = get_knowledge_space_fringe(all_nodes, edges, bs)
        fringe_ids = [f["node_id"] for f in fringe]
        assert "c1.3" in fringe_ids, "c1.3 should be ready"

    def test_partial_prereq_excluded():
        """c2.1 cần c1.1+c1.2+c1.3 mastered, chỉ có 1 → excluded"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 4.0}}}
        fringe = get_knowledge_space_fringe(all_nodes, edges, bs)
        fringe_ids = [f["node_id"] for f in fringe]
        assert "c2.1" not in fringe_ids, "c2.1 needs 3 prereqs, only 1 met"

    def test_all_mastered_empty_fringe():
        """Tất cả mastered → fringe rỗng"""
        bs = {"nodes": {nid: {"overall_bloom": 5.0} for nid in all_nodes}}
        fringe = get_knowledge_space_fringe(all_nodes, edges, bs)
        assert len(fringe) == 0, f"All mastered → empty fringe, got {len(fringe)}"

    def test_readiness_score():
        """Readiness = prereqs_met / prereqs_total"""
        bs = {"nodes": {
            "c1.1": {"overall_bloom": 4.0},
            "c1.2": {"overall_bloom": 4.0},
            "c1.3": {"overall_bloom": 4.0},
        }}
        fringe = get_knowledge_space_fringe(all_nodes, edges, bs)
        c21 = next((f for f in fringe if f["node_id"] == "c2.1"), None)
        assert c21 is not None, "c2.1 should be in fringe"
        assert c21["readiness"] == 1.0, f"All prereqs met → readiness=1.0, got {c21['readiness']}"
        assert c21["prereq_met"] == 3
        assert c21["prereq_total"] == 3

    def test_sorted_by_readiness():
        """Fringe sorted by readiness descending"""
        # 5 nodes, various readiness
        edges5 = [
            {"source": "a", "target": "b"},
            {"source": "a", "target": "c"},
            {"source": "b", "target": "c"},  # c has 2 prereqs: a, b
        ]
        bs = {"nodes": {"a": {"overall_bloom": 4.0}}}
        fringe = get_knowledge_space_fringe(["a", "b", "c"], edges5, bs)
        if len(fringe) > 1:
            for i in range(len(fringe) - 1):
                assert fringe[i]["readiness"] >= fringe[i+1]["readiness"]

    test("Empty state → root nodes in fringe", test_empty_state_roots)
    test("After mastering c1.1 → c1.2 ready", test_after_mastering_c1)
    test("Chain: c1.1+c1.2 mastered → c1.3 ready", test_chain_progress)
    test("Partial prereqs → excluded", test_partial_prereq_excluded)
    test("All mastered → empty fringe", test_all_mastered_empty_fringe)
    test("Readiness score calculation", test_readiness_score)
    test("Sorted by readiness desc", test_sorted_by_readiness)


# ============================================================
#  MAIN
# ============================================================

def main():
    global PASS, FAIL

    run_alpha_tests()
    run_fringe_tests()

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

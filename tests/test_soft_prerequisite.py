# tests/test_soft_prerequisite.py
"""
Test script cho soft_prerequisite.py — Sprint 0.2: Soft Prerequisite Engine
Bao gồm: Access Policy, Prerequisite Graph, Mastery Calc, Bloom Ceiling, Access Status

Chạy: python tests/test_soft_prerequisite.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soft_prerequisite import (
    ACCESS_POLICIES,
    get_direct_prerequisites,
    get_all_prerequisites,
    get_prereq_mastery,
    calculate_bloom_ceiling,
    get_access_status,
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


# ── Sample data (mirrors real tree edge structure) ──
EDGES = [
    {"source": "c1.1", "target": "c1.2", "relation": "prerequisite_for"},
    {"source": "c1.2", "target": "c1.3", "relation": "prerequisite_for"},
    {"source": "c1.3", "target": "c2.1", "relation": "prerequisite_for"},
    {"source": "c2.1", "target": "c2.2", "relation": "prerequisite_for"},
    {"source": "c6.1", "target": "c7.4", "reason": "AI knowledge needed"},
]


# ============================================================
#  STORY 0.2.1 — ACCESS POLICY & PREREQUISITE GRAPH
# ============================================================

def run_graph_tests():
    print("\n" + "=" * 60)
    print("🔗 STORY 0.2.1 — Access Policy & Prerequisite Graph")
    print("=" * 60)

    def test_policies_exist():
        """3 policies phải tồn tại"""
        assert "k12_strict" in ACCESS_POLICIES
        assert "university_flexible" in ACCESS_POLICIES
        assert "professional_open" in ACCESS_POLICIES

    def test_direct_prereq_basic():
        """c1.2 prereq trực tiếp = [c1.1]"""
        result = get_direct_prerequisites("c1.2", EDGES)
        assert result == ["c1.1"], f"Expected ['c1.1'], got {result}"

    def test_direct_prereq_root():
        """c1.1 (root) → không có prereq"""
        result = get_direct_prerequisites("c1.1", EDGES)
        assert result == [], f"Expected [], got {result}"

    def test_direct_prereq_multi():
        """Node với nhiều edges vào"""
        edges_multi = EDGES + [{"source": "c3.1", "target": "c7.4"}]
        result = get_direct_prerequisites("c7.4", edges_multi)
        assert set(result) == {"c6.1", "c3.1"}, f"Expected c6.1+c3.1, got {result}"

    def test_all_prereqs_transitive():
        """c2.1 transitive prereqs = {c1.1, c1.2, c1.3}"""
        result = get_all_prerequisites("c2.1", EDGES)
        assert result == {"c1.1", "c1.2", "c1.3"}, f"Expected 3 prereqs, got {result}"

    def test_all_prereqs_root():
        """Root → empty set"""
        result = get_all_prerequisites("c1.1", EDGES)
        assert result == set(), f"Expected empty, got {result}"

    def test_all_prereqs_deep():
        """c2.2 transitive = {c1.1, c1.2, c1.3, c2.1}"""
        result = get_all_prerequisites("c2.2", EDGES)
        assert result == {"c1.1", "c1.2", "c1.3", "c2.1"}, f"Got {result}"

    def test_cycle_safe():
        """Graph có cycle → không infinite loop"""
        cyclic = EDGES + [{"source": "c2.1", "target": "c1.1"}]
        result = get_all_prerequisites("c2.1", cyclic)
        assert isinstance(result, set), "Should return set"
        # Should still find c1.1, c1.2, c1.3
        assert "c1.1" in result

    test("3 access policies exist", test_policies_exist)
    test("Direct prereq: c1.2 → [c1.1]", test_direct_prereq_basic)
    test("Direct prereq: root → []", test_direct_prereq_root)
    test("Direct prereq: multi-parent", test_direct_prereq_multi)
    test("Transitive: c2.1 → {c1.1, c1.2, c1.3}", test_all_prereqs_transitive)
    test("Transitive: root → ∅", test_all_prereqs_root)
    test("Transitive: deep chain c2.2", test_all_prereqs_deep)
    test("Cycle-safe: no infinite loop", test_cycle_safe)


# ============================================================
#  STORY 0.2.2 — PREREQUISITE MASTERY CALCULATION
# ============================================================

def run_mastery_tests():
    print("\n" + "=" * 60)
    print("📊 STORY 0.2.2 — Prerequisite Mastery Calculation")
    print("=" * 60)

    bloom_state = {
        "nodes": {
            "c1.1": {"overall_bloom": 3.0},   # 3.0/6 = 50%
            "c1.2": {"overall_bloom": 1.2},   # 1.2/6 = 20%
        }
    }

    def test_root_mastery():
        """Root node → 1.0 (full access)"""
        m = get_prereq_mastery("c1.1", EDGES, bloom_state)
        assert m == 1.0, f"Expected 1.0, got {m}"

    def test_single_prereq():
        """c1.2 prereq=c1.1 (bloom 3.0/6=0.5)"""
        m = get_prereq_mastery("c1.2", EDGES, bloom_state)
        assert abs(m - 0.5) < 0.01, f"Expected 0.5, got {m}"

    def test_multi_prereq_avg():
        """c2.1 prereqs=c1.1+c1.2+c1.3 → avg"""
        # c1.1=0.5, c1.2=0.2, c1.3=0.0 (missing) → avg = 0.233...
        m = get_prereq_mastery("c2.1", EDGES, bloom_state)
        expected = (0.5 + 0.2 + 0.0) / 3.0
        assert abs(m - expected) < 0.01, f"Expected {expected:.3f}, got {m}"

    def test_missing_prereq_zero():
        """Prereq chưa có bloom_state → mastery = 0"""
        empty_state = {"nodes": {}}
        m = get_prereq_mastery("c1.2", EDGES, empty_state)
        assert m == 0.0, f"Expected 0.0, got {m}"

    def test_full_mastery():
        """Prereq đã hoàn thành → mastery cao"""
        full_state = {"nodes": {"c1.1": {"overall_bloom": 6.0}}}
        m = get_prereq_mastery("c1.2", EDGES, full_state)
        assert abs(m - 1.0) < 0.01, f"Expected 1.0, got {m}"

    test("Root node → mastery 1.0", test_root_mastery)
    test("Single prereq: c1.2 → 0.5", test_single_prereq)
    test("Multi prereq avg: c2.1 → 0.233", test_multi_prereq_avg)
    test("Missing prereq → 0.0", test_missing_prereq_zero)
    test("Full mastery prereq → 1.0", test_full_mastery)


# ============================================================
#  STORY 0.2.3 — BLOOM CEILING FORMULA
# ============================================================

def run_ceiling_tests():
    print("\n" + "=" * 60)
    print("🏗️ STORY 0.2.3 — Bloom Ceiling Formula")
    print("=" * 60)

    target = [1, 2, 3, 4]
    edges = [{"source": "c1.1", "target": "c3.1"}]

    def test_ceiling_30_pct():
        """Mastery 30% → ceiling=2"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 1.8}}}  # 1.8/6=0.3
        c = calculate_bloom_ceiling("c3.1", target, edges, bs, "university_flexible")
        assert c == 2, f"Expected 2, got {c}"

    def test_ceiling_70_pct():
        """Mastery 70% → ceiling=3"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 4.2}}}  # 4.2/6=0.7
        c = calculate_bloom_ceiling("c3.1", target, edges, bs, "university_flexible")
        assert c == 3, f"Expected 3, got {c}"

    def test_ceiling_100_pct():
        """Mastery 100% → ceiling=4 (full)"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 6.0}}}
        c = calculate_bloom_ceiling("c3.1", target, edges, bs, "university_flexible")
        assert c == 4, f"Expected 4, got {c}"

    def test_ceiling_0_pct():
        """Mastery 0% → ceiling=1 (min target)"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 0.0}}}
        c = calculate_bloom_ceiling("c3.1", target, edges, bs, "university_flexible")
        assert c == 1, f"Expected 1, got {c}"

    def test_professional_open():
        """Policy open → always max"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 0.0}}}
        c = calculate_bloom_ceiling("c3.1", target, edges, bs, "professional_open")
        assert c == 4, f"Expected 4, got {c}"

    def test_root_always_full():
        """Root node → always max"""
        bs = {"nodes": {}}
        c = calculate_bloom_ceiling("c1.1", target, edges, bs, "university_flexible")
        assert c == 4, f"Expected 4, got {c}"

    def test_higher_target():
        """Target [2,3,4,5] with 50% mastery"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 3.0}}}  # 0.5
        c = calculate_bloom_ceiling("c3.1", [2,3,4,5], edges, bs, "university_flexible")
        # floor(0.5*5)+1 = 3 → min(5, 3) = 3
        assert c == 3, f"Expected 3, got {c}"

    test("30% mastery → ceiling L2", test_ceiling_30_pct)
    test("70% mastery → ceiling L3", test_ceiling_70_pct)
    test("100% mastery → ceiling L4 (full)", test_ceiling_100_pct)
    test("0% mastery → ceiling L1 (min)", test_ceiling_0_pct)
    test("Policy open → always max", test_professional_open)
    test("Root node → always full", test_root_always_full)
    test("Higher target levels [2-5]", test_higher_target)


# ============================================================
#  STORY 0.2.4 — ACCESS STATUS REPORT
# ============================================================

def run_status_tests():
    print("\n" + "=" * 60)
    print("📋 STORY 0.2.4 — Access Status Report")
    print("=" * 60)

    target = [1, 2, 3, 4]
    edges = [{"source": "c1.1", "target": "c3.1"}]

    def test_partial_access():
        """30% mastery → partial access"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 1.8}}}
        status = get_access_status("c3.1", target, edges, bs, "university_flexible")
        assert status["accessible"] == True
        assert status["bloom_ceiling"] == 2
        assert status["unlocked_levels"] == [1, 2]
        assert status["locked_levels"] == [3, 4]
        assert len(status["prereq_gaps"]) > 0

    def test_full_access():
        """100% mastery → full access"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 6.0}}}
        status = get_access_status("c3.1", target, edges, bs, "university_flexible")
        assert status["bloom_ceiling"] == 4
        assert status["locked_levels"] == []
        assert status["prereq_gaps"] == []

    def test_k12_strict_blocks():
        """K-12 strict: mastery < 60% → blocked"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 1.8}}}  # 30%
        status = get_access_status("c3.1", target, edges, bs, "k12_strict")
        assert status["accessible"] == False, f"K-12 should block, got accessible"

    def test_k12_strict_allows():
        """K-12 strict: mastery ≥ 60% → allowed"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 4.0}}}  # 66%
        status = get_access_status("c3.1", target, edges, bs, "k12_strict")
        assert status["accessible"] == True

    def test_root_full_access():
        """Root node → full access regardless"""
        bs = {"nodes": {}}
        status = get_access_status("c1.1", target, edges, bs, "university_flexible")
        assert status["accessible"] == True
        assert status["bloom_ceiling"] == 4
        assert status["locked_levels"] == []

    def test_report_has_all_keys():
        """Report có đầy đủ keys"""
        bs = {"nodes": {}}
        status = get_access_status("c1.1", target, edges, bs, "university_flexible")
        required = ["accessible", "bloom_ceiling", "unlocked_levels",
                     "locked_levels", "prereq_gaps", "prereq_mastery",
                     "policy", "recommendation"]
        for key in required:
            assert key in status, f"Missing key: {key}"

    def test_recommendation_text():
        """Recommendation chứa node_id cần hoàn thành"""
        bs = {"nodes": {"c1.1": {"overall_bloom": 1.0}}}
        status = get_access_status("c3.1", target, edges, bs, "university_flexible")
        assert "c1.1" in status["recommendation"], \
            f"Recommendation should mention c1.1: {status['recommendation']}"

    test("Partial access: 30% → L1-L2 only", test_partial_access)
    test("Full access: 100% → all levels", test_full_access)
    test("K-12 strict blocks < 60%", test_k12_strict_blocks)
    test("K-12 strict allows ≥ 60%", test_k12_strict_allows)
    test("Root node → full access", test_root_full_access)
    test("Report has all required keys", test_report_has_all_keys)
    test("Recommendation mentions gap node", test_recommendation_text)


# ============================================================
#  MAIN
# ============================================================

def main():
    global PASS, FAIL

    run_graph_tests()
    run_mastery_tests()
    run_ceiling_tests()
    run_status_tests()

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

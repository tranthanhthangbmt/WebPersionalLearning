# tests/test_sprint03_integration.py
"""
Test script cho Sprint 0.3 — Integration vào Bloom System
Bao gồm:
  - Story 0.3.1: check_level_unlocked với bloom_ceiling
  - Story 0.3.2: calculate_bloom_ceiling_from_prereqs
  - Story 0.3.3: CAT state trong knowledge_tracing

Chạy: python tests/test_sprint03_integration.py
"""

import os
import sys
import json
import time
import shutil

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
#  STORY 0.3.1 — check_level_unlocked + bloom_ceiling
# ============================================================

def run_ceiling_unlock_tests():
    print("\n" + "=" * 60)
    print("🔓 STORY 0.3.1 — check_level_unlocked + bloom_ceiling")
    print("=" * 60)

    from bloom_taxonomy import check_level_unlocked

    # Scores where L1 and L2 are passed
    scores_passed = {
        "1": {"score": 0.85, "total": 5, "types_done": ["mcq", "tf"]},
        "2": {"score": 0.80, "total": 3, "types_done": ["mcq", "essay"]},
    }
    target = [1, 2, 3, 4]

    def test_backward_compatible():
        """Không truyền ceiling → hoạt động như cũ (default=6)"""
        assert check_level_unlocked(1, {}, target) == True
        assert check_level_unlocked(3, scores_passed, target) == True

    def test_ceiling_blocks_above():
        """ceiling=2 → L3 bị khóa dù score đủ"""
        assert check_level_unlocked(3, scores_passed, target, bloom_ceiling=2) == False

    def test_ceiling_allows_below():
        """ceiling=2 → L1, L2 vẫn mở"""
        assert check_level_unlocked(1, {}, target, bloom_ceiling=2) == True
        assert check_level_unlocked(2, scores_passed, target, bloom_ceiling=2) == True

    def test_ceiling_at_exact_level():
        """ceiling=3 → L3 mở (nếu score đủ), L4 khóa"""
        assert check_level_unlocked(3, scores_passed, target, bloom_ceiling=3) == True
        assert check_level_unlocked(4, scores_passed, target, bloom_ceiling=3) == False

    def test_ceiling_1_only_l1():
        """ceiling=1 → chỉ L1 mở"""
        assert check_level_unlocked(1, {}, target, bloom_ceiling=1) == True
        assert check_level_unlocked(2, scores_passed, target, bloom_ceiling=1) == False

    def test_ceiling_6_no_limit():
        """ceiling=6 → không giới hạn (mặc định)"""
        assert check_level_unlocked(1, {}, [1,2,3,4,5,6], bloom_ceiling=6) == True
        # L6 chỉ mở nếu L5 pass
        scores_all = {str(i): {"score": 0.9, "total": 5, "types_done": ["mcq", "tf"]} for i in range(1, 6)}
        assert check_level_unlocked(6, scores_all, [1,2,3,4,5,6], bloom_ceiling=6) == True

    test("Backward compatible (no ceiling arg)", test_backward_compatible)
    test("Ceiling=2 blocks L3+", test_ceiling_blocks_above)
    test("Ceiling=2 allows L1-L2", test_ceiling_allows_below)
    test("Ceiling=3: L3 open, L4 locked", test_ceiling_at_exact_level)
    test("Ceiling=1: only L1 open", test_ceiling_1_only_l1)
    test("Ceiling=6: no limit", test_ceiling_6_no_limit)


# ============================================================
#  STORY 0.3.2 — calculate_bloom_ceiling_from_prereqs
# ============================================================

def run_ceiling_wrapper_tests():
    print("\n" + "=" * 60)
    print("🏗️ STORY 0.3.2 — calculate_bloom_ceiling_from_prereqs")
    print("=" * 60)

    from bloom_taxonomy import calculate_bloom_ceiling_from_prereqs

    tree_data = {
        "nodes": {
            "c1.1": {
                "type": "micro",
                "bloom_profile": {
                    "effective_levels": [1, 2, 3, 4],
                }
            },
            "c3.1": {
                "type": "micro",
                "bloom_profile": {
                    "effective_levels": [1, 2, 3, 4],
                }
            },
        },
        "edges": [
            {"source": "c1.1", "target": "c3.1"},
        ]
    }

    def test_ceiling_with_low_prereq():
        """Prereq 30% → ceiling < max"""
        bloom_state = {"nodes": {"c1.1": {"overall_bloom": 1.8}}}
        ceiling = calculate_bloom_ceiling_from_prereqs("c3.1", tree_data, bloom_state)
        assert ceiling == 2, f"Expected 2, got {ceiling}"

    def test_ceiling_root_node():
        """Root node → full (no prereqs)"""
        bloom_state = {"nodes": {}}
        ceiling = calculate_bloom_ceiling_from_prereqs("c1.1", tree_data, bloom_state)
        assert ceiling == 4, f"Expected 4, got {ceiling}"

    def test_ceiling_full_mastery():
        """Prereq 100% → full access"""
        bloom_state = {"nodes": {"c1.1": {"overall_bloom": 6.0}}}
        ceiling = calculate_bloom_ceiling_from_prereqs("c3.1", tree_data, bloom_state)
        assert ceiling == 4, f"Expected 4, got {ceiling}"

    def test_ceiling_professional_open():
        """Policy open → always max"""
        bloom_state = {"nodes": {"c1.1": {"overall_bloom": 0.0}}}
        ceiling = calculate_bloom_ceiling_from_prereqs("c3.1", tree_data,
                                                        bloom_state, "professional_open")
        assert ceiling == 4, f"Expected 4, got {ceiling}"

    test("Low prereq → ceiling limited", test_ceiling_with_low_prereq)
    test("Root node → full access", test_ceiling_root_node)
    test("Full mastery → full access", test_ceiling_full_mastery)
    test("Professional open → always max", test_ceiling_professional_open)


# ============================================================
#  STORY 0.3.3 — CAT state in knowledge_tracing
# ============================================================

def run_cat_state_tests():
    print("\n" + "=" * 60)
    print("💾 STORY 0.3.3 — CAT State in knowledge_tracing")
    print("=" * 60)

    from knowledge_tracing import (
        get_cat_prior_theta,
        update_theta_from_cat,
        get_all_cat_thetas,
        get_cat_state_path,
    )

    # Use temp test user
    test_user = "__test_sprint03__"
    test_subject = "test_subject_01"
    test_dir = f"user_data/{test_user}"

    # Cleanup before tests
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    def test_prior_no_history():
        """Chưa có lịch sử → θ = 0.0"""
        theta = get_cat_prior_theta(test_user, test_subject, "c1.1")
        assert theta == 0.0, f"Expected 0.0, got {theta}"

    def test_save_and_load():
        """Lưu θ rồi đọc lại"""
        update_theta_from_cat(test_user, test_subject, "c1.1",
                              theta=1.5, se=0.25, bloom_level=4, items_used=8)
        theta = get_cat_prior_theta(test_user, test_subject, "c1.1")
        assert theta == 1.5, f"Expected 1.5, got {theta}"

    def test_multiple_nodes():
        """Lưu θ cho nhiều nodes"""
        update_theta_from_cat(test_user, test_subject, "c2.1",
                              theta=-0.5, se=0.3, bloom_level=2, items_used=5)
        all_thetas = get_all_cat_thetas(test_user, test_subject)
        assert "c1.1" in all_thetas, "c1.1 should exist"
        assert "c2.1" in all_thetas, "c2.1 should exist"
        assert all_thetas["c1.1"]["theta"] == 1.5
        assert all_thetas["c2.1"]["theta"] == -0.5

    def test_overwrite_node():
        """Cập nhật θ cho node đã có"""
        update_theta_from_cat(test_user, test_subject, "c1.1",
                              theta=2.0, se=0.2, bloom_level=5, items_used=10)
        theta = get_cat_prior_theta(test_user, test_subject, "c1.1")
        assert theta == 2.0, f"Expected 2.0 after overwrite, got {theta}"

    def test_state_file_structure():
        """File JSON có cấu trúc đúng"""
        cat_path = get_cat_state_path(test_user, test_subject)
        with open(cat_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "nodes" in data
        node = data["nodes"]["c1.1"]
        for key in ["theta", "se", "bloom_level", "items_used", "last_cat_session"]:
            assert key in node, f"Missing key: {key}"

    def test_auto_bloom_level():
        """bloom_level=None → auto-calc từ theta"""
        update_theta_from_cat(test_user, test_subject, "c3.1",
                              theta=0.8, se=0.3)  # No bloom_level
        all_thetas = get_all_cat_thetas(test_user, test_subject)
        bl = all_thetas["c3.1"]["bloom_level"]
        assert bl == 4, f"θ=0.8 should map to L4, got {bl}"

    test("No history → θ = 0.0", test_prior_no_history)
    test("Save and load θ", test_save_and_load)
    test("Multiple nodes storage", test_multiple_nodes)
    test("Overwrite existing θ", test_overwrite_node)
    test("State file JSON structure", test_state_file_structure)
    test("Auto bloom_level from θ", test_auto_bloom_level)

    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"  🧹 Cleaned up {test_dir}")


# ============================================================
#  MAIN
# ============================================================

def main():
    global PASS, FAIL

    run_ceiling_unlock_tests()
    run_ceiling_wrapper_tests()
    run_cat_state_tests()

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

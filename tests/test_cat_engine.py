# tests/test_cat_engine.py
"""
Test script cho cat_engine.py — Sprint 0.1: IRT Math Core
Bao gồm: test IRT probability, Fisher Info, EAP estimation, 
          Item Selection, CATSession, θ→Bloom mapping

Chạy: python tests/test_cat_engine.py
"""

import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cat_engine import (
    irt_probability,
    fisher_information,
    log_likelihood,
    estimate_theta_eap,
    get_standard_error,
    select_next_item,
    map_theta_to_bloom,
    CATSession,
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
#  STORY 0.1.1 — IRT 2PL CORE FUNCTIONS
# ============================================================

def run_irt_core_tests():
    print("\n" + "=" * 60)
    print("🧮 STORY 0.1.1 — IRT 2PL Core Functions")
    print("=" * 60)

    def test_prob_equal():
        """P(θ=0, a=1, b=0) = 0.5"""
        p = irt_probability(0, 1, 0)
        assert abs(p - 0.5) < 0.001, f"Expected 0.5, got {p}"

    def test_prob_high_ability():
        """P(θ=2, a=1, b=0) > 0.88"""
        p = irt_probability(2, 1, 0)
        assert p > 0.88, f"Expected > 0.88, got {p}"

    def test_prob_low_ability():
        """P(θ=-2, a=1, b=0) < 0.12"""
        p = irt_probability(-2, 1, 0)
        assert p < 0.12, f"Expected < 0.12, got {p}"

    def test_prob_symmetry():
        """P(θ=x, b=0) + P(θ=-x, b=0) ≈ 1.0 (đối xứng)"""
        p1 = irt_probability(1.5, 1, 0)
        p2 = irt_probability(-1.5, 1, 0)
        assert abs(p1 + p2 - 1.0) < 0.001, f"Expected sum=1.0, got {p1+p2}"

    def test_prob_high_discrimination():
        """a cao → đường cong dốc hơn"""
        p_low_a = irt_probability(0.5, 0.5, 0)
        p_high_a = irt_probability(0.5, 2.5, 0)
        # Cả hai > 0.5, nhưng a cao → gần 1.0 hơn
        assert p_high_a > p_low_a, f"High a should give higher P above b"

    def test_prob_extreme_no_crash():
        """θ rất lớn/nhỏ → không crash"""
        p1 = irt_probability(100, 1, 0)
        p2 = irt_probability(-100, 1, 0)
        assert 0.99 < p1 <= 1.0
        assert 0.0 <= p2 < 0.01

    def test_fisher_max_at_b():
        """Fisher Info cao nhất khi θ ≈ b"""
        info_at_b = fisher_information(0, 1, 0)
        info_far = fisher_information(3, 1, 0)
        assert info_at_b > info_far, f"Info at b ({info_at_b}) should > info far ({info_far})"

    def test_fisher_nonneg():
        """Fisher Info luôn ≥ 0"""
        for theta in [-3, -1, 0, 1, 3]:
            info = fisher_information(theta, 1.5, 0.5)
            assert info >= 0, f"Info should be >= 0, got {info}"

    def test_log_likelihood_basic():
        """Log-likelihood: đúng hết + θ cao → ll cao hơn đúng hết + θ thấp"""
        items = [{"a": 1, "b": 0}, {"a": 1, "b": 0.5}]
        ll_high = log_likelihood(2.0, items, [True, True])
        ll_low = log_likelihood(-2.0, items, [True, True])
        assert ll_high > ll_low, f"Higher θ should have higher ll for all-correct"

    test("P(θ=0, a=1, b=0) = 0.5", test_prob_equal)
    test("P(θ=2) > 0.88 (giỏi → xác suất cao)", test_prob_high_ability)
    test("P(θ=-2) < 0.12 (yếu → xác suất thấp)", test_prob_low_ability)
    test("Symmetry: P(x) + P(-x) = 1", test_prob_symmetry)
    test("High discrimination → steeper curve", test_prob_high_discrimination)
    test("Extreme θ → no crash", test_prob_extreme_no_crash)
    test("Fisher Info max at θ=b", test_fisher_max_at_b)
    test("Fisher Info always ≥ 0", test_fisher_nonneg)
    test("Log-likelihood ordering", test_log_likelihood_basic)


# ============================================================
#  STORY 0.1.2 — EAP THETA ESTIMATION
# ============================================================

def run_eap_tests():
    print("\n" + "=" * 60)
    print("📐 STORY 0.1.2 — EAP Theta Estimation")
    print("=" * 60)

    def test_all_correct_positive():
        """Đúng hết 3 câu dễ → θ > 0"""
        items = [{"a": 1, "b": -1}, {"a": 1, "b": 0}, {"a": 1, "b": -0.5}]
        theta = estimate_theta_eap(items, [True, True, True])
        assert theta > 0, f"All correct → θ should > 0, got {theta}"

    def test_all_wrong_negative():
        """Sai hết → θ < 0"""
        items = [{"a": 1, "b": -1}, {"a": 1, "b": 0}, {"a": 1, "b": -0.5}]
        theta = estimate_theta_eap(items, [False, False, False])
        assert theta < 0, f"All wrong → θ should < 0, got {theta}"

    def test_mixed_moderate():
        """Hỗn hợp → θ gần 0"""
        items = [{"a": 1, "b": -1}, {"a": 1, "b": 0}, {"a": 1, "b": 1}]
        theta = estimate_theta_eap(items, [True, False, True])
        assert -1.5 < theta < 1.5, f"Mixed → θ near 0, got {theta}"

    def test_empty_returns_prior():
        """Không có response → θ = 0 (prior mean)"""
        theta = estimate_theta_eap([], [])
        assert abs(theta) < 0.01, f"Empty → θ = 0, got {theta}"

    def test_more_correct_higher_theta():
        """Đúng nhiều hơn → θ cao hơn"""
        items = [{"a": 1, "b": b} for b in [-1, -0.5, 0, 0.5, 1]]
        theta_4 = estimate_theta_eap(items, [True, True, True, True, False])
        theta_2 = estimate_theta_eap(items, [True, True, False, False, False])
        assert theta_4 > theta_2, f"4 correct ({theta_4}) should > 2 correct ({theta_2})"

    def test_se_decreases_with_items():
        """SE giảm khi thêm items"""
        items_3 = [{"a": 1, "b": 0}] * 3
        items_10 = [{"a": 1, "b": 0}] * 10
        se_3 = get_standard_error(0, items_3, [True]*3)
        se_10 = get_standard_error(0, items_10, [True]*10)
        assert se_10 < se_3, f"More items → lower SE: {se_10} should < {se_3}"

    test("All correct → θ > 0", test_all_correct_positive)
    test("All wrong → θ < 0", test_all_wrong_negative)
    test("Mixed → θ moderate", test_mixed_moderate)
    test("Empty → θ = 0 (prior)", test_empty_returns_prior)
    test("More correct → higher θ", test_more_correct_higher_theta)
    test("SE decreases with more items", test_se_decreases_with_items)


# ============================================================
#  STORY 0.1.3 — ADAPTIVE ITEM SELECTION
# ============================================================

def run_selection_tests():
    print("\n" + "=" * 60)
    print("🎯 STORY 0.1.3 — Adaptive Item Selection")
    print("=" * 60)

    pool = [
        {"id": "q1", "a": 1.0, "b": -2.0},  # rất dễ
        {"id": "q2", "a": 1.0, "b": 0.0},    # vừa phải
        {"id": "q3", "a": 1.0, "b": 2.0},    # rất khó
    ]

    def test_select_matching_difficulty():
        """θ=0 → chọn item b gần 0 nhất (q2)"""
        selected = select_next_item(0, pool, set())
        assert selected["id"] == "q2", f"Expected q2, got {selected['id']}"

    def test_select_excludes_administered():
        """Sau khi hỏi q2, không chọn lại"""
        selected = select_next_item(0, pool, {"q2"})
        assert selected["id"] != "q2", f"Should not re-select q2"

    def test_select_high_theta():
        """θ=2 → chọn item khó (q3)"""
        selected = select_next_item(2.0, pool, set())
        assert selected["id"] == "q3", f"Expected q3, got {selected['id']}"

    def test_select_low_theta():
        """θ=-2 → chọn item dễ (q1)"""
        selected = select_next_item(-2.0, pool, set())
        assert selected["id"] == "q1", f"Expected q1, got {selected['id']}"

    def test_select_exhausted():
        """Hết item → None"""
        result = select_next_item(0, pool, {"q1", "q2", "q3"})
        assert result is None, f"Expected None, got {result}"

    def test_select_empty_pool():
        """Pool rỗng → None"""
        result = select_next_item(0, [], set())
        assert result is None

    test("θ=0 → select item b≈0 (q2)", test_select_matching_difficulty)
    test("Excludes administered items", test_select_excludes_administered)
    test("θ=2 → select hard item (q3)", test_select_high_theta)
    test("θ=-2 → select easy item (q1)", test_select_low_theta)
    test("Pool exhausted → None", test_select_exhausted)
    test("Empty pool → None", test_select_empty_pool)


# ============================================================
#  STORY 0.1.4 — CAT SESSION & θ→BLOOM MAPPING
# ============================================================

def run_session_tests():
    print("\n" + "=" * 60)
    print("🤖 STORY 0.1.4 — CATSession & θ→Bloom Mapping")
    print("=" * 60)

    def test_theta_to_bloom():
        """Mapping θ → Bloom Level"""
        assert map_theta_to_bloom(-2.0) == 1, "θ=-2 → L1"
        assert map_theta_to_bloom(-1.0) == 2, "θ=-1 → L2"
        assert map_theta_to_bloom(0.0) == 3,  "θ=0 → L3"
        assert map_theta_to_bloom(1.0) == 4,  "θ=1 → L4"
        assert map_theta_to_bloom(2.0) == 5,  "θ=2 → L5"
        assert map_theta_to_bloom(3.0) == 6,  "θ=3 → L6"

    def test_theta_bloom_boundary():
        """Biên: θ=-1.5 → L2 (not L1)"""
        assert map_theta_to_bloom(-1.5) == 2, "θ=-1.5 → L2"
        assert map_theta_to_bloom(-1.51) == 1, "θ=-1.51 → L1"

    def test_session_basic():
        """Session cơ bản: 5 câu, đúng 4"""
        pool = [{"id": f"q{i}", "a": 1.0, "b": (i-5)/2.0} for i in range(10)]
        session = CATSession(item_pool=pool, max_items=5)

        for i in range(5):
            item = session.get_next_item()
            assert item is not None, f"Item {i} should not be None"
            session.record_response(item, is_correct=(i < 4))

        report = session.get_report()
        assert report["items_used"] == 5
        assert report["correct"] == 4
        assert report["accuracy"] == 0.8
        assert 1 <= report["bloom_level"] <= 6

    def test_session_all_correct_high_theta():
        """Đúng hết → θ dương"""
        pool = [{"id": f"q{i}", "a": 1.0, "b": (i-3)/2.0} for i in range(7)]
        session = CATSession(item_pool=pool, max_items=7)

        for _ in range(7):
            item = session.get_next_item()
            if item is None:
                break
            session.record_response(item, is_correct=True)

        report = session.get_report()
        assert report["theta"] > 0, f"All correct → θ>0, got {report['theta']}"

    def test_session_should_stop_max():
        """Stop khi đạt max_items"""
        pool = [{"id": f"q{i}", "a": 1.0, "b": 0} for i in range(20)]
        session = CATSession(item_pool=pool, max_items=5)

        for i in range(5):
            item = session.get_next_item()
            session.record_response(item, is_correct=True)

        assert session.should_stop() == True, "Should stop after max_items"

    def test_session_report_structure():
        """Report có đầy đủ keys"""
        pool = [{"id": "q1", "a": 1, "b": 0}]
        session = CATSession(item_pool=pool)
        item = session.get_next_item()
        session.record_response(item, True)
        report = session.get_report()
        for key in ["theta", "se", "bloom_level", "items_used", "accuracy", "correct", "total"]:
            assert key in report, f"Missing key: {key}"

    test("θ → Bloom mapping (all levels)", test_theta_to_bloom)
    test("θ → Bloom boundary cases", test_theta_bloom_boundary)
    test("Session basic: 5 items, 4 correct", test_session_basic)
    test("Session all correct → θ > 0", test_session_all_correct_high_theta)
    test("Session stops at max_items", test_session_should_stop_max)
    test("Report has all required keys", test_session_report_structure)


# ============================================================
#  MAIN
# ============================================================

def main():
    global PASS, FAIL

    run_irt_core_tests()
    run_eap_tests()
    run_selection_tests()
    run_session_tests()

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

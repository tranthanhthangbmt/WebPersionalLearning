# tests/test_socratic_engine.py
"""
Test script cho socratic_tutor_engine.py — Sprint 1.1 + 1.2
Bao gồm: Persona, Prompt Builder, GROW, Verdict, SocraticSession, CAT, Persistence

Chạy: python tests/test_socratic_engine.py
"""

import os
import sys
import json
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from socratic_tutor_engine import (
    PERSONAS, GROW_PHASES, select_persona,
    build_system_prompt, get_grow_phase_prompt, advance_grow_phase,
    extract_verdict, calculate_socratic_score,
    SocraticSession, get_adaptive_context,
    save_session_result, get_session_history,
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
#  STORY 1.1.1 — PERSONA DEFINITIONS & BLOOM MAPPING
# ============================================================

def run_persona_tests():
    print("\n" + "=" * 60)
    print("🎭 STORY 1.1.1 — Persona Definitions & Bloom Mapping")
    print("=" * 60)

    def test_three_personas():
        assert len(PERSONAS) == 3
        assert "examiner" in PERSONAS
        assert "socratic_guide" in PERSONAS
        assert "devils_advocate" in PERSONAS

    def test_l1_l2_examiner():
        assert select_persona(1)["id"] == "examiner"
        assert select_persona(2)["id"] == "examiner"

    def test_l3_l4_socratic():
        assert select_persona(3)["id"] == "socratic_guide"
        assert select_persona(4)["id"] == "socratic_guide"

    def test_l5_l6_devil():
        assert select_persona(5)["id"] == "devils_advocate"
        assert select_persona(6)["id"] == "devils_advocate"

    def test_persona_fields():
        for pid, p in PERSONAS.items():
            for field in ["id", "name", "icon", "tone", "strategy", "bloom_range", "system_instruction"]:
                assert field in p, f"Missing '{field}' in {pid}"

    test("3 personas exist", test_three_personas)
    test("L1-L2 → examiner", test_l1_l2_examiner)
    test("L3-L4 → socratic_guide", test_l3_l4_socratic)
    test("L5-L6 → devils_advocate", test_l5_l6_devil)
    test("All persona fields present", test_persona_fields)


# ============================================================
#  STORY 1.1.2 — SYSTEM PROMPT BUILDER
# ============================================================

def run_prompt_tests():
    print("\n" + "=" * 60)
    print("📝 STORY 1.1.2 — System Prompt Builder")
    print("=" * 60)

    ctx = {"title": "Thương mại điện tử", "content": "Khái niệm TMĐT"}
    persona = PERSONAS["examiner"]

    def test_prompt_has_persona():
        prompt = build_system_prompt(persona, ctx, 1, 30)
        assert "Kiểm tra" in prompt or "examiner" in prompt.lower()

    def test_prompt_has_verdict():
        prompt = build_system_prompt(persona, ctx, 1, 30)
        assert '{"verdict"' in prompt

    def test_prompt_has_content():
        prompt = build_system_prompt(persona, ctx, 1, 30)
        assert "Thương mại điện tử" in prompt

    def test_prompt_has_difficulty():
        prompt = build_system_prompt(persona, ctx, 2, 90)
        assert "90" in prompt

    def test_prompt_has_bloom_verbs():
        prompt = build_system_prompt(persona, ctx, 1, 50)
        assert "nhận biết" in prompt or "liệt kê" in prompt

    def test_prompt_with_adaptive():
        prompt = build_system_prompt(persona, ctx, 1, 50, adaptive_hint="Scaffolding mode")
        assert "Scaffolding" in prompt

    test("Prompt contains persona info", test_prompt_has_persona)
    test("Prompt contains verdict format", test_prompt_has_verdict)
    test("Prompt contains node content", test_prompt_has_content)
    test("Prompt reflects difficulty", test_prompt_has_difficulty)
    test("Prompt has Bloom verbs", test_prompt_has_bloom_verbs)
    test("Prompt with adaptive hint", test_prompt_with_adaptive)


# ============================================================
#  STORY 1.1.3 — GROW COACHING FRAMEWORK
# ============================================================

def run_grow_tests():
    print("\n" + "=" * 60)
    print("🌱 STORY 1.1.3 — GROW Coaching Framework")
    print("=" * 60)

    def test_four_phases():
        assert len(GROW_PHASES) == 4
        assert GROW_PHASES[0]["id"] == "goal"
        assert GROW_PHASES[3]["id"] == "will"

    def test_advance_normal():
        assert advance_grow_phase("goal") == "reality"
        assert advance_grow_phase("reality") == "options"
        assert advance_grow_phase("options") == "will"

    def test_advance_end():
        assert advance_grow_phase("will") is None

    def test_advance_invalid():
        result = advance_grow_phase("nonexistent")
        assert result == "goal"  # Reset to first

    def test_phase_prompt():
        prompt = get_grow_phase_prompt("goal", {"title": "AI"})
        assert "mục tiêu" in prompt.lower() or "Goal" in prompt

    def test_phase_prompt_empty():
        prompt = get_grow_phase_prompt("invalid", {"title": "AI"})
        assert prompt == ""

    test("4 GROW phases exist", test_four_phases)
    test("Phase advancement: goal→reality→options→will", test_advance_normal)
    test("Will → None (end)", test_advance_end)
    test("Invalid phase → reset to goal", test_advance_invalid)
    test("Phase prompt contains instruction", test_phase_prompt)
    test("Invalid phase → empty prompt", test_phase_prompt_empty)


# ============================================================
#  STORY 1.1.4 — VERDICT EXTRACTION & SCORING
# ============================================================

def run_verdict_tests():
    print("\n" + "=" * 60)
    print("⚖️ STORY 1.1.4 — Verdict Extraction & Scoring")
    print("=" * 60)

    def test_extract_passed():
        result = extract_verdict('Rất giỏi! {"verdict": "passed"} Chúc mừng.')
        assert result["verdict"] == "passed"
        assert '{"verdict"' not in result["clean_text"]

    def test_extract_failed():
        result = extract_verdict('Chưa đạt {"verdict": "failed"}')
        assert result["verdict"] == "failed"

    def test_extract_continue():
        result = extract_verdict('Hãy giải thích thêm {"verdict": "continue"}')
        assert result["verdict"] == "continue"

    def test_no_verdict():
        result = extract_verdict("Hãy giải thích thêm đi.")
        assert result["verdict"] == "continue"
        assert result["clean_text"] == "Hãy giải thích thêm đi."

    def test_malformed_json():
        result = extract_verdict('Sai rồi {"verdict": "fail')
        assert result["verdict"] == "continue"

    def test_normalize_pass():
        result = extract_verdict('{"verdict": "pass"}')
        assert result["verdict"] == "passed"

    def test_scoring_all_passed():
        score = calculate_socratic_score(["passed", "passed"], 3)
        assert score == 1.0

    def test_scoring_all_failed():
        score = calculate_socratic_score(["failed", "failed"], 3)
        assert score == 0.0

    def test_scoring_mixed():
        score = calculate_socratic_score(["passed", "continue", "failed"], 3)
        assert 0.3 < score < 0.7

    def test_scoring_empty():
        assert calculate_socratic_score([], 3) == 0.0

    test("Extract 'passed' verdict", test_extract_passed)
    test("Extract 'failed' verdict", test_extract_failed)
    test("Extract 'continue' verdict", test_extract_continue)
    test("No verdict → 'continue'", test_no_verdict)
    test("Malformed JSON → 'continue'", test_malformed_json)
    test("Normalize 'pass' → 'passed'", test_normalize_pass)
    test("Scoring: all passed → 1.0", test_scoring_all_passed)
    test("Scoring: all failed → 0.0", test_scoring_all_failed)
    test("Scoring: mixed → moderate", test_scoring_mixed)
    test("Scoring: empty → 0.0", test_scoring_empty)


# ============================================================
#  STORY 1.2.1 — SOCRATIC SESSION CLASS
# ============================================================

def run_session_tests():
    print("\n" + "=" * 60)
    print("🤖 STORY 1.2.1 — SocraticSession Class")
    print("=" * 60)

    ctx = {"title": "TMĐT", "content": "Khái niệm TMĐT cơ bản"}

    def test_session_start():
        s = SocraticSession(bloom_level=3)
        prompt = s.start(ctx)
        assert s.persona["id"] == "socratic_guide"
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_session_process_passed():
        s = SocraticSession(bloom_level=3)
        s.start(ctx)
        result = s.process_ai_response('Giỏi! {"verdict": "passed"}')
        assert result["verdict"] == "passed"
        assert result["should_stop"] == True

    def test_session_process_continue():
        s = SocraticSession(bloom_level=3)
        s.start(ctx)
        result = s.process_ai_response('Hãy giải thích thêm {"verdict": "continue"}')
        assert result["verdict"] == "continue"
        assert result["should_stop"] == False

    def test_session_max_turns():
        s = SocraticSession(bloom_level=3, max_turns=3)
        s.start(ctx)
        s.process_ai_response('{"verdict": "continue"}')
        s.process_ai_response('{"verdict": "continue"}')
        result = s.process_ai_response('{"verdict": "continue"}')
        assert result["should_stop"] == True  # Hit max_turns

    def test_session_report():
        s = SocraticSession(bloom_level=4)
        s.start(ctx)
        s.process_ai_response('{"verdict": "continue"}')
        s.process_ai_response('{"verdict": "passed"}')
        report = s.get_report()
        assert report["persona_used"] == "socratic_guide"
        assert report["turns"] == 2
        assert report["final_verdict"] == "passed"
        assert "score" in report

    def test_session_grow_mode():
        s = SocraticSession(bloom_level=3, use_grow=True)
        prompt = s.start(ctx)
        assert "Goal" in prompt or "mục tiêu" in prompt.lower()
        s.process_ai_response('{"verdict": "continue"}')
        assert s.grow_phase == "reality"  # Advanced to next phase

    test("Session start → correct persona + prompt", test_session_start)
    test("Process 'passed' → should_stop", test_session_process_passed)
    test("Process 'continue' → keep going", test_session_process_continue)
    test("Max turns → force stop", test_session_max_turns)
    test("Report has all fields", test_session_report)
    test("GROW mode advances phases", test_session_grow_mode)


# ============================================================
#  STORY 1.2.2 — CAT-ADAPTIVE CONTEXT
# ============================================================

def run_adaptive_tests():
    print("\n" + "=" * 60)
    print("🎯 STORY 1.2.2 — CAT-Adaptive Context")
    print("=" * 60)

    class MockCATSession:
        def __init__(self, theta):
            self.theta = theta

    ctx = {"title": "TMĐT"}

    def test_low_theta_scaffolding():
        cat = MockCATSession(theta=-2.0)
        result = get_adaptive_context(cat, ctx)
        assert result["difficulty_level"] == "scaffolding"
        assert "cơ bản" in result["difficulty_hint"].lower() or \
               "scaffolding" in result["difficulty_hint"].lower()

    def test_mid_theta_normal():
        cat = MockCATSession(theta=0.0)
        result = get_adaptive_context(cat, ctx)
        assert result["difficulty_level"] == "normal"

    def test_high_theta_advanced():
        cat = MockCATSession(theta=1.0)
        result = get_adaptive_context(cat, ctx)
        assert result["difficulty_level"] == "advanced"
        assert "nâng cao" in result["difficulty_hint"].lower() or \
               "advanced" in result["difficulty_hint"].lower()

    def test_very_high_theta_challenge():
        cat = MockCATSession(theta=2.0)
        result = get_adaptive_context(cat, ctx)
        assert result["difficulty_level"] == "challenge"

    def test_has_theta():
        cat = MockCATSession(theta=1.5)
        result = get_adaptive_context(cat, ctx)
        assert result["theta"] == 1.5

    test("θ=-2 → scaffolding", test_low_theta_scaffolding)
    test("θ=0 → normal", test_mid_theta_normal)
    test("θ=1 → advanced", test_high_theta_advanced)
    test("θ=2 → challenge", test_very_high_theta_challenge)
    test("Result contains theta value", test_has_theta)


# ============================================================
#  STORY 1.2.3 — SESSION PERSISTENCE
# ============================================================

def run_persistence_tests():
    print("\n" + "=" * 60)
    print("💾 STORY 1.2.3 — Session Persistence")
    print("=" * 60)

    test_user = "__test_socratic__"
    test_dir = f"user_data/{test_user}"

    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    def test_save_and_load():
        save_session_result(test_user, "subj1", "c1.1",
                            {"score": 0.8, "bloom_level": 3, "turns": 4})
        history = get_session_history(test_user, "subj1", "c1.1")
        assert len(history) >= 1
        assert history[-1]["score"] == 0.8

    def test_multiple_sessions():
        save_session_result(test_user, "subj1", "c1.1",
                            {"score": 0.5, "bloom_level": 3, "turns": 2})
        history = get_session_history(test_user, "subj1", "c1.1")
        assert len(history) >= 2

    def test_empty_history():
        history = get_session_history(test_user, "subj1", "nonexistent")
        assert history == []

    def test_has_timestamp():
        history = get_session_history(test_user, "subj1", "c1.1")
        assert "timestamp" in history[-1]

    test("Save and load session", test_save_and_load)
    test("Multiple sessions accumulate", test_multiple_sessions)
    test("Empty history → []", test_empty_history)
    test("Session has timestamp", test_has_timestamp)

    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"  🧹 Cleaned up {test_dir}")


# ============================================================
#  MAIN
# ============================================================

def main():
    global PASS, FAIL

    run_persona_tests()
    run_prompt_tests()
    run_grow_tests()
    run_verdict_tests()
    run_session_tests()
    run_adaptive_tests()
    run_persistence_tests()

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

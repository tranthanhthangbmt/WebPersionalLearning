# 🏃 Scrum Execution Plan — Phase 1: Socratic Tutor Engine

> **Phụ thuộc:** Phase 0 ✅ DONE (84/84 tests PASS)
> **Gồm 4 Sprint** — Mỗi sprint kết thúc = có test PASS

---

## Chain of Thought: Phân tích Dependency

```
Bước 1: Xác định modules hiện có liên quan

  quiz_page.py ──── Đã có render_socratic() cơ bản (chat + verdict)
       │              Prompt cố định, 1 persona, không CAT
       │
  bloom_hub_page.py ── Bloom Ladder + assessment flow
       │                  Đã tích hợp bloom_ceiling (Sprint 0.4)
       │                  start_assessment() → MCQ only
       │
  gemini_helper.py ── RobustGeminiModel + RobustChatSession
       │               start_chat(), send_message() — sẵn dùng
       │
  knowledge_tracing.py ── Ebbinghaus decay + CAT state (Sprint 0.3)
       │                    update_theta_from_cat() — sẵn dùng
       │
  gamification/ ── socratic_passed/failed actions đã define
                   xp_engine, achievement_service — sẵn dùng

Bước 2: Xác định modules cần tạo/sửa

  socratic_tutor_engine.py (NEW)
    ├── PersonaSelector: Bloom → persona mapping
    ├── PromptBuilder: Tạo system prompt theo persona + context
    ├── SocraticSession: Session management + verdict tracking
    └── GROWCoachingFlow: Goal→Reality→Options→Will framework
  
  smart_review_queue.py (NEW)
    ├── ReviewPriorityScorer: (1-Retention) × Bloom_Weight
    ├── get_review_queue(): Danh sách node cần ôn
    └── update_review_after_session(): Cập nhật sau ôn tập
  
  bloom_hub_page.py (MODIFY)
    ├── Thêm CAT assessment mode (thay vì random MCQ)
    └── Thêm Smart Review widget

Bước 3: Dependency graph → Sprint order

  Sprint 1.1: Persona Engine (pure logic, không phụ thuộc AI)
       │
  Sprint 1.2: SocraticSession + CAT integration
       │         (phụ thuộc 1.1 + cat_engine.py)
       │
  Sprint 1.3: Smart Review Queue
       │         (phụ thuộc knowledge_tracing.py, song song 1.2 được)
       │
  Sprint 1.4: UI Integration vào Bloom Hub
              (phụ thuộc 1.1 + 1.2 + 1.3)
```

---

## Sprint 1.1 — Persona Engine Core (`socratic_tutor_engine.py`)
**Mục tiêu:** Pure logic cho persona selection + prompt generation, test 100% offline.
**Thời gian ước tính:** 2-3 giờ

### User Stories

#### Story 1.1.1 — Persona Definitions & Bloom Mapping
**File:** `socratic_tutor_engine.py` (NEW)

**Tasks:**
- [ ] Tạo file với 3 persona definitions (examiner, socratic_guide, devils_advocate)
- [ ] Implement `select_persona(bloom_level)` → persona dict
- [ ] Mỗi persona có: name, icon, tone, strategy, bloom_range, question_style

**Acceptance Criteria:**
```python
# AC1: L1-L2 → examiner
persona = select_persona(1)
assert persona["id"] == "examiner"
assert select_persona(2)["id"] == "examiner"

# AC2: L3-L4 → socratic_guide
assert select_persona(3)["id"] == "socratic_guide"
assert select_persona(4)["id"] == "socratic_guide"

# AC3: L5-L6 → devils_advocate
assert select_persona(5)["id"] == "devils_advocate"
assert select_persona(6)["id"] == "devils_advocate"

# AC4: Persona có đầy đủ fields
for field in ["id", "name", "icon", "tone", "strategy", "bloom_range"]:
    assert field in persona
```

---

#### Story 1.1.2 — System Prompt Builder
**File:** `socratic_tutor_engine.py`

**Tasks:**
- [ ] Implement `build_system_prompt(persona, node_context, bloom_level, difficulty_alpha)` → str
- [ ] Prompt chứa: persona instructions, node content, Bloom verb targeting, difficulty calibration
- [ ] Prompt format tương thích với existing `quiz_page.py` verdict format `{"verdict": "passed/failed/continue"}`

**Acceptance Criteria:**
```python
# AC1: Prompt chứa persona tone
prompt = build_system_prompt(examiner, {"title": "TMĐT", "content": "..."}, 1, 30)
assert "examiner" in prompt.lower() or "kiểm tra" in prompt.lower()

# AC2: Prompt chứa verdict format
assert '{"verdict"' in prompt

# AC3: Prompt chứa node content
assert "TMĐT" in prompt

# AC4: Difficulty scaling
prompt_hard = build_system_prompt(examiner, context, 2, 90)
assert "90" in prompt_hard  # Alpha reflected in prompt
```

---

#### Story 1.1.3 — GROW Coaching Framework
**File:** `socratic_tutor_engine.py`

**Tasks:**
- [ ] Implement GROW model phases: `GROW_PHASES = [Goal, Reality, Options, Will]`
- [ ] Implement `get_grow_phase_prompt(phase, context)` → str thêm vào system prompt
- [ ] Implement `advance_grow_phase(current_phase)` → next phase or None

**Acceptance Criteria:**
```python
# AC1: 4 phases exist
assert len(GROW_PHASES) == 4
assert GROW_PHASES[0]["id"] == "goal"
assert GROW_PHASES[3]["id"] == "will"

# AC2: Phase advancement
assert advance_grow_phase("goal") == "reality"
assert advance_grow_phase("will") is None  # Kết thúc

# AC3: Phase prompt contains coaching instruction
prompt = get_grow_phase_prompt("goal", {"title": "AI"})
assert "mục tiêu" in prompt.lower() or "goal" in prompt.lower()
```

---

#### Story 1.1.4 — Verdict Extraction & Scoring
**File:** `socratic_tutor_engine.py`

**Tasks:**
- [ ] Implement `extract_verdict(ai_response_text)` → {"verdict": str, "clean_text": str}
- [ ] Implement `calculate_socratic_score(verdicts_history, bloom_level)` → float (0-1)
- [ ] Handle edge cases: no verdict, malformed JSON, multiple verdicts

**Acceptance Criteria:**
```python
# AC1: Extract verdict from response
result = extract_verdict('Rất giỏi! {"verdict": "passed"} Chúc mừng.')
assert result["verdict"] == "passed"
assert '{"verdict"' not in result["clean_text"]

# AC2: No verdict → "continue"
result = extract_verdict("Hãy giải thích thêm đi.")
assert result["verdict"] == "continue"

# AC3: Malformed JSON → "continue"
result = extract_verdict('Sai rồi {"verdict": "fail')
assert result["verdict"] == "continue"

# AC4: Scoring — more passes = higher score
score = calculate_socratic_score(["passed", "passed", "continue"], 3)
assert score > 0.5
```

---

#### Story 1.1.5 — Test File
**File:** `tests/test_socratic_engine.py` (NEW)

**Definition of Done Sprint 1.1:**
```bash
python tests/test_socratic_engine.py
# Expected: 🎉 TẤT CẢ XX TEST ĐỀU PASS!
```

---

## Sprint 1.2 — Socratic Session + CAT Integration
**Mục tiêu:** SocraticSession class kết hợp CATSession, test offline với mock.
**Thời gian ước tính:** 2-3 giờ
**Dependency:** Sprint 1.1 + cat_engine.py (Phase 0)

### User Stories

#### Story 1.2.1 — SocraticSession Class
**File:** `socratic_tutor_engine.py`

**Tasks:**
- [ ] Implement `class SocraticSession` với state: persona, messages, verdicts, grow_phase
- [ ] Method `start(node_context, bloom_level)` → system_prompt
- [ ] Method `process_ai_response(response_text)` → {verdict, clean_text, should_stop}
- [ ] Method `get_report()` → {score, bloom_level, verdicts, turns, persona_used}

**Acceptance Criteria:**
```python
# AC1: Session lifecycle
session = SocraticSession(bloom_level=3)
prompt = session.start({"title": "TMĐT", "content": "..."})
assert session.persona["id"] == "socratic_guide"
assert isinstance(prompt, str)

# AC2: Process responses
result = session.process_ai_response('Giỏi! {"verdict": "passed"}')
assert result["verdict"] == "passed"
assert result["should_stop"] == True

# AC3: Report
report = session.get_report()
assert "score" in report
assert report["persona_used"] == "socratic_guide"
assert report["turns"] >= 1
```

---

#### Story 1.2.2 — CAT-Adaptive Question Selection
**File:** `socratic_tutor_engine.py`

**Tasks:**
- [ ] Implement `get_adaptive_context(cat_session, node_context)` → dict thêm thông tin θ vào prompt
- [ ] Nếu θ thấp → gợi ý AI hỏi dễ hơn; θ cao → gợi ý AI hỏi khó hơn
- [ ] Implement `update_theta_from_socratic(session, cat_session)` → cập nhật θ dựa trên verdict

**Acceptance Criteria:**
```python
# AC1: Adaptive context chứa difficulty hint
from cat_engine import CATSession
cat = CATSession(item_pool=[{"id": "q1", "a": 1, "b": 0}])
ctx = get_adaptive_context(cat, {"title": "TMĐT"})
assert "theta" in str(ctx) or "difficulty" in str(ctx).lower()

# AC2: Low θ → easier prompt hint
cat.theta = -2.0
ctx_easy = get_adaptive_context(cat, {"title": "TMĐT"})
assert "cơ bản" in ctx_easy.get("difficulty_hint", "").lower() or \
       "scaffolding" in ctx_easy.get("difficulty_hint", "").lower()

# AC3: High θ → harder prompt hint
cat.theta = 2.0
ctx_hard = get_adaptive_context(cat, {"title": "TMĐT"})
assert "nâng cao" in ctx_hard.get("difficulty_hint", "").lower() or \
       "challenge" in ctx_hard.get("difficulty_hint", "").lower()
```

---

#### Story 1.2.3 — Session Persistence
**File:** `socratic_tutor_engine.py`

**Tasks:**
- [ ] Implement `save_session_result(user_id, subject_id, node_id, report)` → lưu kết quả
- [ ] Implement `get_session_history(user_id, subject_id, node_id)` → list of reports
- [ ] Tích hợp với `update_theta_from_cat()` từ knowledge_tracing

**Acceptance Criteria:**
```python
# AC1: Save and load
save_session_result("__test__", "subj1", "c1.1", {"score": 0.8, "bloom_level": 3})
history = get_session_history("__test__", "subj1", "c1.1")
assert len(history) >= 1
assert history[-1]["score"] == 0.8

# AC2: Multiple sessions accumulate
save_session_result("__test__", "subj1", "c1.1", {"score": 0.5, "bloom_level": 3})
history = get_session_history("__test__", "subj1", "c1.1")
assert len(history) >= 2
```

---

#### Story 1.2.4 — Test File
**File:** `tests/test_socratic_session.py` (NEW)

**Definition of Done Sprint 1.2:**
```bash
python tests/test_socratic_session.py
# Expected: 🎉 TẤT CẢ XX TEST ĐỀU PASS!
```

---

## Sprint 1.3 — Smart Review Queue (`smart_review_queue.py`)
**Mục tiêu:** Review priority scoring dựa trên Ebbinghaus + Bloom Weight, test offline.
**Thời gian ước tính:** 1.5-2 giờ
**Dependency:** knowledge_tracing.py (Ebbinghaus) — chạy song song Sprint 1.2 được

### User Stories

#### Story 1.3.1 — Review Priority Scoring
**File:** `smart_review_queue.py` (NEW)

**Tasks:**
- [ ] Implement `calculate_retention(last_review_time, strength)` → float (0-1)
- [ ] Implement `calculate_review_priority(retention, bloom_weight, recency_hours)` → float
- [ ] Công thức: `priority = (1 - retention) × bloom_weight × recency_bonus`
- [ ] Bloom weight: L1=1, L2=1.5, L3=2, L4=2.5, L5=3, L6=3.5

**Acceptance Criteria:**
```python
# AC1: Low retention → high priority
p_low = calculate_review_priority(0.2, 2.0, 48)
p_high = calculate_review_priority(0.9, 2.0, 48)
assert p_low > p_high  # Quên nhiều → cần ôn gấp

# AC2: Higher Bloom → higher priority
p_bloom1 = calculate_review_priority(0.5, 1.0, 24)
p_bloom4 = calculate_review_priority(0.5, 2.5, 24)
assert p_bloom4 > p_bloom1  # Kiến thức khó quên → ưu tiên

# AC3: Retention 100% → priority gần 0
p_full = calculate_review_priority(1.0, 2.0, 24)
assert p_full < 0.01
```

---

#### Story 1.3.2 — Review Queue Generator
**File:** `smart_review_queue.py`

**Tasks:**
- [ ] Implement `get_review_queue(bloom_state, max_items=10)` → list of review items
- [ ] Mỗi item: `{node_id, priority, retention, bloom_level, hours_since_review}`
- [ ] Sorted by priority descending
- [ ] Chỉ include nodes đã học (overall_bloom > 0)

**Acceptance Criteria:**
```python
# AC1: Returns sorted list
queue = get_review_queue(mock_bloom_state, max_items=5)
assert len(queue) <= 5
for i in range(len(queue)-1):
    assert queue[i]["priority"] >= queue[i+1]["priority"]

# AC2: Skips unlearned nodes
assert all(q["retention"] < 1.0 for q in queue)

# AC3: Empty state → empty queue
assert get_review_queue({"nodes": {}, "ebbinghaus": {}}) == []
```

---

#### Story 1.3.3 — Review Session Update
**File:** `smart_review_queue.py`

**Tasks:**
- [ ] Implement `update_after_review(bloom_state, node_id, accuracy)` → updated bloom_state
- [ ] Tăng strength (sức nhớ) khi ôn tập thành công
- [ ] Cập nhật last_review timestamp

**Acceptance Criteria:**
```python
# AC1: Strength increases after review
old_strength = bloom_state["ebbinghaus"]["c1.1"]["strength"]
update_after_review(bloom_state, "c1.1", accuracy=0.9)
new_strength = bloom_state["ebbinghaus"]["c1.1"]["strength"]
assert new_strength > old_strength

# AC2: Last review updated
assert bloom_state["ebbinghaus"]["c1.1"]["last_review"] > 0
```

---

#### Story 1.3.4 — Test File
**File:** `tests/test_smart_review.py` (NEW)

**Definition of Done Sprint 1.3:**
```bash
python tests/test_smart_review.py
# Expected: 🎉 TẤT CẢ XX TEST ĐỀU PASS!
```

---

## Sprint 1.4 — UI Integration vào Bloom Hub
**Mục tiêu:** Tích hợp Socratic + Review vào giao diện Bloom Hub.
**Thời gian ước tính:** 2-3 giờ
**Dependency:** Sprint 1.1 + 1.2 + 1.3

### User Stories

#### Story 1.4.1 — Socratic Assessment trong Bloom Ladder
**File:** `bloom_hub_page.py` (MODIFY)

**Tasks:**
- [ ] Sửa `start_assessment()`: khi type là `socratic`/`socratic_advanced` → dùng SocraticSession
- [ ] Render chat UI inline trong assess_area (thay vì redirect sang quiz_page)
- [ ] Tích hợp persona icon + name vào chat header

---

#### Story 1.4.2 — Smart Review Widget trong Tab Progress
**File:** `bloom_hub_page.py` (MODIFY)

**Tasks:**
- [ ] Thêm "📅 Cần ôn tập" section trong Tab 3 (Progress)
- [ ] Hiển thị top 3 nodes cần review với retention bar
- [ ] Nút "Ôn tập ngay" → redirect sang assessment

---

#### Story 1.4.3 — Verification
**Tasks:**
- [ ] Syntax check bloom_hub_page.py
- [ ] Full regression: tất cả test files cũ vẫn PASS
- [ ] Browser test (nếu server chạy được)

**Definition of Done Sprint 1.4:**
```bash
python -c "import py_compile; py_compile.compile('bloom_hub_page.py', doraise=True); print('OK')"
python tests/test_cat_engine.py
python tests/test_soft_prerequisite.py
python tests/test_sprint03_integration.py
python tests/test_sprint05_final.py
python tests/test_socratic_engine.py
python tests/test_socratic_session.py
python tests/test_smart_review.py
# ALL PASS — no regression
```

---

## Burndown Tracking

| Sprint | Status | Stories | Tests Pass |
|---|---|---|---|
| 1.1 Persona Engine | `[ ]` Ready | 0/5 | — |
| 1.2 Socratic Session | `[ ]` Blocked by 1.1 | 0/4 | — |
| 1.3 Smart Review | `[ ]` Ready (parallel 1.2) | 0/4 | — |
| 1.4 UI Integration | `[ ]` Blocked by 1.1+1.2+1.3 | 0/3 | — |

---

## So sánh với quiz_page.py hiện tại

| Tính năng | quiz_page.py (hiện tại) | socratic_tutor_engine.py (mới) |
|---|---|---|
| Persona | 1 (Giáo sư Socrates cố định) | 3 persona theo Bloom level |
| Prompt | Hardcoded trong render_socratic | Template builder + GROW coaching |
| Difficulty | alpha cố định | CAT-adaptive θ → difficulty hint |
| Verdict | Extract inline | Dedicated extractor + scoring |
| Persistence | update_node_mastery only | Full session history + θ update |
| Review | Không có | Smart Review Queue + Ebbinghaus |

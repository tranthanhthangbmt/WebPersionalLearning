# 🏃 Scrum Execution Plan — Phase 2: Multi-Subject Dashboard

> **Phụ thuộc:** Phase 0 ✅ (84 tests) + Phase 1 ✅ (64 tests) = **148/148 PASS**
> **Gồm 4 Sprint** — Mỗi sprint kết thúc = có test PASS

---

## Chain of Thought: Phân tích Dependency + Gap

```
Bước 1: Phân tích Data Layer hiện tại

  user_data/{username}/subjects.json
  ├── format: { "subjects": [{"id", "title", "filename", "total_nodes"}] }
  ├── Ví dụ: sv01 có 2 môn (TMĐT, Thị giác máy tính)
  └── ❌ GAP: Không có tổng hợp cross-subject (overall progress)

  user_data/{username}/trees/{subject_id}.json
  ├── format: { macro_nodes, micro_nodes, assess_nodes, edges }
  └── ✅ Sẵn: tree_data cho mỗi subject

  bloom_taxonomy.py
  ├── load_bloom_state(username, subject_id) → per-subject
  ├── get_all_bloom_scores(username, subject_id) → per-node scores
  └── ❌ GAP: Không có aggregate across subjects

  knowledge_tracing.py
  ├── get_all_cat_thetas(user_id, subject_id) → per-subject thetas
  └── ❌ GAP: Không có get_all_subjects_state()

  smart_review_queue.py
  ├── get_review_queue(bloom_state) → per-subject queue
  ├── get_daily_review_summary(bloom_state) → per-subject summary
  └── ❌ GAP: Không có cross-subject aggregated queue

  soft_prerequisite.py
  ├── get_knowledge_space_fringe(username) → per-subject fringe
  └── ❌ GAP: Không có cross-subject fringe

Bước 2: Phân tích UI Layer hiện tại (main.py)

  main.py:988 → tab_dashboard
  ├── Hardcoded: gamification_stats, Bio Battery, "Nhiệm vụ trong ngày"
  ├── ❌ GAP: Không load subjects.json → không hiển thị course cards
  ├── ❌ GAP: Không tính real-time bloom progress per-subject
  ├── ❌ GAP: Không có Access Policy selector
  └── ❌ GAP: "Nhiệm vụ trong ngày" là static, cần dynamic từ KST fringe

  main.py:233-265 → Tabs sidebar
  └── ✅ Có tab_dashboard, tab_studio, tab_quiz (đủ navigation targets)

Bước 3: Xác định modules cần tạo/sửa

  multi_subject_dashboard.py (NEW)
  ├── SubjectAggregator: Load tất cả subjects + bloom states
  ├── get_cross_subject_summary(): Overall stats
  ├── get_subject_card_data(): Per-subject card info
  ├── get_unified_review_queue(): Merged review queue
  ├── get_recommended_next_nodes(): KST fringe top-N
  └── save/load_access_policy(): Policy persistence

  main.py (MODIFY)
  ├── Tab "Tổng quan": Gọi multi_subject_dashboard functions
  └── Replace hardcoded UI với dynamic data

Bước 4: Dependency graph → Sprint order

  Sprint 2.1: Data Aggregator (pure logic, không UI)
       │        Load subjects → aggregate bloom + ebbinghaus
       │
  Sprint 2.2: Bloom Radar + Heatmap Data
       │        (phụ thuộc 2.1, tạo chart data structures)
       │
  Sprint 2.3: Policy Selector + KST Recommendations
       │        (phụ thuộc 2.1, dùng soft_prerequisite)
       │
  Sprint 2.4: UI Integration vào main.py tab_dashboard
              (phụ thuộc 2.1 + 2.2 + 2.3)
```

---

## Sprint 2.1 — Multi-Subject Data Aggregator (`multi_subject_dashboard.py`)
**Mục tiêu:** Pure logic thu thập + tổng hợp dữ liệu tất cả môn học, test offline.
**Thời gian ước tính:** 2 giờ

### User Stories

#### Story 2.1.1 — Subject Loader
**File:** `multi_subject_dashboard.py` (NEW)

**Tasks:**
- [ ] Implement `load_all_subjects(username)` → list of subject dicts
- [ ] Load từ `user_data/{username}/subjects.json`
- [ ] Mỗi subject: `{id, title, filename, total_nodes}`
- [ ] Handle: file không tồn tại → empty list

**Acceptance Criteria:**
```python
# AC1: Load existing subjects
subjects = load_all_subjects("sv01")
assert len(subjects) >= 1
assert "id" in subjects[0] and "title" in subjects[0]

# AC2: Missing user → empty
assert load_all_subjects("nonexistent_user") == []
```

---

#### Story 2.1.2 — Per-Subject Progress Summary
**File:** `multi_subject_dashboard.py`

**Tasks:**
- [ ] Implement `get_subject_card_data(username, subject)` → dict
- [ ] Tính: total_nodes, nodes_learned, overall_bloom_avg, completion_pct
- [ ] Tính: review_urgency (từ smart_review_queue)
- [ ] Tính: last_activity timestamp

**Acceptance Criteria:**
```python
# AC1: Card data has all fields
card = get_subject_card_data("__test__", {"id": "s1", "title": "Test", "filename": "..."})
for field in ["subject_id", "title", "total_nodes", "nodes_learned",
              "completion_pct", "avg_bloom", "review_urgency", "last_activity"]:
    assert field in card

# AC2: completion_pct in [0, 100]
assert 0 <= card["completion_pct"] <= 100

# AC3: Empty bloom state → 0% completion
card_empty = get_subject_card_data("__test__", {"id": "empty", ...})
assert card_empty["completion_pct"] == 0
```

---

#### Story 2.1.3 — Cross-Subject Aggregation
**File:** `multi_subject_dashboard.py`

**Tasks:**
- [ ] Implement `get_cross_subject_summary(username)` → dict
- [ ] Tổng hợp: total_subjects, total_nodes_all, total_learned, overall_pct
- [ ] Aggregated: avg_bloom across all subjects
- [ ] Aggregated: total_review_needed, critical_review_count

**Acceptance Criteria:**
```python
# AC1: Summary has required fields
summary = get_cross_subject_summary("sv01")
for field in ["total_subjects", "total_nodes", "total_learned",
              "overall_pct", "avg_bloom", "total_review_needed"]:
    assert field in summary

# AC2: total_subjects >= 0
assert summary["total_subjects"] >= 0
```

---

#### Story 2.1.4 — Unified Review Queue
**File:** `multi_subject_dashboard.py`

**Tasks:**
- [ ] Implement `get_unified_review_queue(username, max_items=10)` → list
- [ ] Merge review queues từ tất cả subjects
- [ ] Mỗi item thêm: subject_title, subject_id
- [ ] Sorted by priority descending (cross-subject)

**Acceptance Criteria:**
```python
# AC1: Items have subject info
queue = get_unified_review_queue("sv01", max_items=5)
if queue:
    assert "subject_title" in queue[0]
    assert "subject_id" in queue[0]

# AC2: Sorted by priority
for i in range(len(queue)-1):
    assert queue[i]["priority"] >= queue[i+1]["priority"]

# AC3: Max items respected
assert len(queue) <= 5
```

---

#### Story 2.1.5 — Test File
**File:** `tests/test_multi_subject.py` (NEW)

**Definition of Done Sprint 2.1:**
```bash
python tests/test_multi_subject.py
# Expected: 🎉 TẤT CẢ XX TEST ĐỀU PASS!
```

---

## Sprint 2.2 — Bloom Radar & Heatmap Data
**Mục tiêu:** Chuẩn bị data structures cho radar chart + heatmap, test offline.
**Thời gian ước tính:** 1.5 giờ
**Dependency:** Sprint 2.1

### User Stories

#### Story 2.2.1 — Bloom Radar Data per Subject
**File:** `multi_subject_dashboard.py`

**Tasks:**
- [ ] Implement `get_bloom_radar_data(username, subject_id)` → dict
- [ ] Output: 6 axes (L1-L6), mỗi axis = avg score across all nodes
- [ ] Format tương thích với Chart.js radar: `{labels: [...], data: [...]}`

**Acceptance Criteria:**
```python
# AC1: 6 axes
radar = get_bloom_radar_data("sv01", "e69bf65f")
assert len(radar["labels"]) == 6
assert len(radar["data"]) == 6
assert all(0 <= v <= 1 for v in radar["data"])

# AC2: Labels match Bloom levels
assert "Remember" in radar["labels"][0] or "L1" in radar["labels"][0]
```

---

#### Story 2.2.2 — Ebbinghaus Heatmap Data
**File:** `multi_subject_dashboard.py`

**Tasks:**
- [ ] Implement `get_ebbinghaus_heatmap(username, subject_id)` → list
- [ ] Mỗi item: `{node_id, node_title, retention, status: "critical"|"warning"|"good"|"excellent"}`
- [ ] Sorted by retention ascending (cần ôn nhất trước)

**Acceptance Criteria:**
```python
# AC1: Items have retention + status
heatmap = get_ebbinghaus_heatmap("sv01", "e69bf65f")
if heatmap:
    item = heatmap[0]
    assert "retention" in item
    assert item["status"] in ("critical", "warning", "good", "excellent")

# AC2: Sorted by retention
for i in range(len(heatmap)-1):
    assert heatmap[i]["retention"] <= heatmap[i+1]["retention"]
```

---

#### Story 2.2.3 — Study Activity Stats
**File:** `multi_subject_dashboard.py`

**Tasks:**
- [ ] Implement `get_study_streak_data(username)` → dict
- [ ] Tổng hợp: total_sessions (socratic + quiz), active_days, streak_estimate
- [ ] Weekly activity array (7 days): `[sessions_count, ...]`

**Acceptance Criteria:**
```python
# AC1: Has required fields
stats = get_study_streak_data("sv01")
for field in ["total_sessions", "active_days", "weekly_activity"]:
    assert field in stats

# AC2: Weekly has 7 slots
assert len(stats["weekly_activity"]) == 7
```

---

#### Story 2.2.4 — Test File
**File:** `tests/test_multi_subject.py` (UPDATE)

**Definition of Done Sprint 2.2:**
```bash
python tests/test_multi_subject.py
# Expected: 🎉 TẤT CẢ XX TEST ĐỀU PASS!
```

---

## Sprint 2.3 — Access Policy Selector + KST Recommendations
**Mục tiêu:** Policy persistence + Knowledge Space fringe across subjects.
**Thời gian ước tính:** 1.5 giờ
**Dependency:** Sprint 2.1 + soft_prerequisite.py

### User Stories

#### Story 2.3.1 — Access Policy Persistence
**File:** `multi_subject_dashboard.py`

**Tasks:**
- [ ] Implement `save_access_policy(username, policy_id)` → persists to user_data
- [ ] Implement `load_access_policy(username)` → str (default: "university_flexible")
- [ ] Validate policy_id against `ACCESS_POLICIES` keys

**Acceptance Criteria:**
```python
# AC1: Save and load
save_access_policy("__test__", "k12_strict")
assert load_access_policy("__test__") == "k12_strict"

# AC2: Default
assert load_access_policy("nonexistent") == "university_flexible"

# AC3: Invalid policy → keep default
save_access_policy("__test__", "invalid_policy")
assert load_access_policy("__test__") != "invalid_policy"
```

---

#### Story 2.3.2 — Cross-Subject KST Recommendations
**File:** `multi_subject_dashboard.py`

**Tasks:**
- [ ] Implement `get_recommended_next_nodes(username, max_items=5)` → list
- [ ] Iterate all subjects → get_knowledge_space_fringe() per subject
- [ ] Merge + rank by readiness_score descending
- [ ] Mỗi item: `{node_id, subject_id, subject_title, readiness_score, node_title}`

**Acceptance Criteria:**
```python
# AC1: Items have cross-subject info
recs = get_recommended_next_nodes("sv01", max_items=3)
if recs:
    assert "subject_title" in recs[0]
    assert "readiness_score" in recs[0]

# AC2: Sorted by readiness desc
for i in range(len(recs)-1):
    assert recs[i]["readiness_score"] >= recs[i+1]["readiness_score"]
```

---

#### Story 2.3.3 — Daily Tasks Generator
**File:** `multi_subject_dashboard.py`

**Tasks:**
- [ ] Implement `get_daily_tasks(username, max_tasks=5)` → list
- [ ] Task types: "review_node", "learn_next", "socratic_practice", "complete_quiz"
- [ ] Dựa trên: review_queue urgency + KST fringe + completion gaps
- [ ] Mỗi task: `{type, title, description, subject_id, node_id, priority, xp_reward}`

**Acceptance Criteria:**
```python
# AC1: Tasks have required fields
tasks = get_daily_tasks("sv01", max_tasks=3)
if tasks:
    task = tasks[0]
    for field in ["type", "title", "description", "priority"]:
        assert field in task

# AC2: Max tasks respected
assert len(tasks) <= 3
```

---

#### Story 2.3.4 — Test File
**File:** `tests/test_multi_subject.py` (UPDATE)

**Definition of Done Sprint 2.3:**
```bash
python tests/test_multi_subject.py
# Expected: 🎉 TẤT CẢ XX TEST ĐỀU PASS!
```

---

## Sprint 2.4 — UI Integration vào main.py
**Mục tiêu:** Replace hardcoded dashboard với dynamic data.
**Thời gian ước tính:** 2-3 giờ
**Dependency:** Sprint 2.1 + 2.2 + 2.3

### User Stories

#### Story 2.4.1 — Course Cards Grid
**File:** `main.py` (MODIFY)

**Tasks:**
- [ ] Replace hardcoded "Nhiệm vụ trong ngày" với dynamic course cards
- [ ] Mỗi card: title, completion bar, avg bloom score, review alert badge
- [ ] Click card → navigate to Graph Studio cho subject đó
- [ ] Color gradient theo completion: xanh (>70%), vàng (30-70%), đỏ (<30%)

---

#### Story 2.4.2 — Access Policy Selector UI
**File:** `main.py` (MODIFY)

**Tasks:**
- [ ] Thêm Policy selector dropdown trong dashboard header
- [ ] 3 options: K-12 Nghiêm ngặt / Đại học Linh hoạt / Chuyên nghiệp Mở
- [ ] Persist on change → ảnh hưởng Bloom Ceiling + Alpha penalty

---

#### Story 2.4.3 — Dynamic Tasks + Review Alerts
**File:** `main.py` (MODIFY)

**Tasks:**
- [ ] Replace static tasks với `get_daily_tasks()` output
- [ ] Thêm review alert banner nếu có critical_review_count > 0
- [ ] "Ôn tập ngay" button → navigate to relevant Bloom Hub

---

#### Story 2.4.4 — Verification
**Tasks:**
- [ ] Syntax check main.py
- [ ] Full regression: tất cả Phase 0 + 1 + 2 tests vẫn PASS
- [ ] Browser test (nếu có server)

**Definition of Done Sprint 2.4:**
```bash
python -c "import py_compile; py_compile.compile('main.py', doraise=True); print('OK')"
python -c "import py_compile; py_compile.compile('multi_subject_dashboard.py', doraise=True); print('OK')"
python tests/test_cat_engine.py
python tests/test_soft_prerequisite.py
python tests/test_sprint03_integration.py
python tests/test_sprint05_final.py
python tests/test_socratic_engine.py
python tests/test_smart_review.py
python tests/test_multi_subject.py
# ALL PASS — no regression
```

---

## Burndown Tracking

| Sprint | Status | Stories | Tests Pass | Phụ thuộc |
|---|---|---|---|---|
| 2.1 Data Aggregator | `[ ]` Ready | 0/5 | — | — |
| 2.2 Radar + Heatmap | `[ ]` Blocked by 2.1 | 0/4 | — | 2.1 |
| 2.3 Policy + KST | `[ ]` Blocked by 2.1 | 0/4 | — | 2.1 |
| 2.4 UI Integration | `[ ]` Blocked by 2.1+2.2+2.3 | 0/4 | — | 2.1+2.2+2.3 |

---

## So sánh Dashboard: Hiện tại vs. Mới

| Feature | main.py hiện tại | Mới (Phase 2) |
|---|---|---|
| Subject list | ❌ Hardcoded | ✅ Dynamic từ subjects.json |
| Progress bars | ❌ Không có | ✅ Per-subject completion % |
| Bloom overview | ❌ Không có | ✅ Radar chart data (6 axes) |
| Review alerts | ❌ Không có | ✅ Ebbinghaus-based urgency |
| Policy selector | ❌ Không có | ✅ K-12/Uni/Pro dropdown |
| Daily tasks | Hardcoded 2 tasks | ✅ AI-generated từ KST fringe |
| Cross-subject | ❌ 1 môn/lần | ✅ Merged view + unified review |

---

## Cấu trúc dữ liệu User Data

```
user_data/{username}/
├── subjects.json                    ← subject registry
├── trees/{subject_id}.json          ← tree data per subject
├── states/{subject_id}_state.json   ← knowledge tracing
├── states/{subject_id}_cat.json     ← CAT θ estimates
├── bloom/{subject_id}_bloom.json    ← Bloom scores
├── socratic_sessions/               ← Session history
└── settings.json                    ← NEW: policy, preferences
```

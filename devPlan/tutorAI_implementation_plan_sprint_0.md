# 🏃 Scrum Execution Plan — Phase 0: CAT + Soft Prerequisite

> **Phần 1/3** — Sprint 0.1 & 0.2 (Nền tảng toán học + Logic truy cập)
> Phần 2: Sprint 0.3-0.4 (Integration + UI) — sẽ viết sau khi Part 1 hoàn thành
> Phần 3: Sprint 0.5 + Phase 1 (Placement Test + Socratic) — sẽ viết sau

---

## Chain of Thought: Phân tích Dependency

```
Bước 1: Xác định modules cần tạo/sửa
  → cat_engine.py (NEW) — toán IRT thuần, không phụ thuộc gì
  → soft_prerequisite.py (NEW) — cần đọc edges từ tree_data + bloom_state
  → bloom_taxonomy.py (MODIFY) — thêm param bloom_ceiling vào check_level_unlocked
  → bloom_hub_page.py (MODIFY) — gọi soft_prerequisite, hiển thị ceiling
  → knowledge_tracing.py (MODIFY) — lưu theta từ CAT
  → step3_learning_engine.py (MODIFY) — policy-aware penalty

Bước 2: Xác định thứ tự (dependency graph)
  cat_engine.py ──────────────────┐
       (không phụ thuộc)          │
                                  ├─→ knowledge_tracing.py (lưu theta)
                                  │
  soft_prerequisite.py ───────────┤
       (cần tree edges, bloom)    ├─→ bloom_taxonomy.py (thêm ceiling)
                                  │
                                  └─→ bloom_hub_page.py (UI hiển thị)

Bước 3: Nhóm thành Sprint theo nguyên tắc
  - Mỗi sprint kết thúc = có thể chạy test PASS
  - Sprint nhỏ (2-4 user stories, ~2-4h mỗi sprint)
  - Không có sprint nào phụ thuộc code chưa test
```

---

## Sprint 0.1 — IRT Math Core (`cat_engine.py`)
**Mục tiêu:** Tạo engine toán học IRT 2PL thuần túy, test được 100% offline.
**Thời gian ước tính:** 2-3 giờ

### User Stories

#### Story 0.1.1 — IRT 2PL Core Functions
**Mô tả:** Implement 3 hàm toán cốt lõi của IRT 2PL model
**File:** `cat_engine.py` (NEW)

**Tasks:**
- [ ] Tạo file `cat_engine.py` với docstring mô tả lý thuyết
- [ ] Implement `irt_probability(theta, a, b)` → P(θ) = 1/(1+exp(-a(θ-b)))
- [ ] Implement `fisher_information(theta, a, b)` → I(θ) = a²·P·(1-P)
- [ ] Implement `log_likelihood(theta, items, responses)` → ΣLog-Likelihood

**Acceptance Criteria (Test):**
```python
# AC1: P(θ=0, a=1, b=0) = 0.5 (50% khi ability = difficulty)
assert abs(irt_probability(0, 1, 0) - 0.5) < 0.001

# AC2: P(θ=2, a=1, b=0) > 0.88 (giỏi hơn difficulty → xác suất cao)
assert irt_probability(2, 1, 0) > 0.88

# AC3: P(θ=-2, a=1, b=0) < 0.12 (yếu hơn difficulty → xác suất thấp)
assert irt_probability(-2, 1, 0) < 0.12

# AC4: Fisher Info cao nhất khi θ ≈ b (item phân biệt tốt nhất ở vùng năng lực = độ khó)
info_at_b = fisher_information(0, 1, 0)
info_far = fisher_information(3, 1, 0)
assert info_at_b > info_far
```

---

#### Story 0.1.2 — EAP Theta Estimation
**Mô tả:** Implement ước lượng θ bằng Expected a Posteriori (Bayesian)
**File:** `cat_engine.py`

**Tasks:**
- [ ] Implement `estimate_theta_eap(items, responses, num_quadrature=41)` 
- [ ] Sử dụng quadrature points từ -4 đến +4
- [ ] Prior: N(0, 1) — phân phối chuẩn

**Acceptance Criteria (Test):**
```python
# AC1: Trả lời đúng 3 câu dễ → θ dương (> 0)
items = [{"a": 1, "b": -1}, {"a": 1, "b": 0}, {"a": 1, "b": -0.5}]
responses = [True, True, True]
theta = estimate_theta_eap(items, responses)
assert theta > 0, f"3 đúng câu dễ → θ phải > 0, got {theta}"

# AC2: Trả lời sai hết → θ âm (< 0)
theta_bad = estimate_theta_eap(items, [False, False, False])
assert theta_bad < 0

# AC3: Hỗn hợp → θ gần 0
theta_mix = estimate_theta_eap(items, [True, False, True])
assert -1.5 < theta_mix < 1.5

# AC4: Không response → θ = 0 (prior)
theta_empty = estimate_theta_eap([], [])
assert abs(theta_empty) < 0.01
```

---

#### Story 0.1.3 — Adaptive Item Selection
**Mô tả:** Implement thuật toán chọn câu hỏi tối ưu (Maximum Fisher Information)
**File:** `cat_engine.py`

**Tasks:**
- [ ] Implement `select_next_item(theta, available_items, administered_ids)` 
- [ ] Trả về item có Fisher Info cao nhất tại θ hiện tại
- [ ] Loại trừ items đã hỏi (administered_ids)

**Acceptance Criteria (Test):**
```python
# AC1: Khi θ=0, chọn item có b gần 0 nhất
pool = [
    {"id": "q1", "a": 1, "b": -2},  # quá dễ
    {"id": "q2", "a": 1, "b": 0},   # vừa phải ← expect chọn cái này
    {"id": "q3", "a": 1, "b": 2},   # quá khó
]
selected = select_next_item(0, pool, set())
assert selected["id"] == "q2"

# AC2: Sau khi hỏi q2, chọn item khác
selected2 = select_next_item(0, pool, {"q2"})
assert selected2["id"] != "q2"

# AC3: Hết item → trả None
assert select_next_item(0, pool, {"q1", "q2", "q3"}) is None
```

---

#### Story 0.1.4 — CATSession Class & θ→Bloom Mapping
**Mô tả:** Wrapper class quản lý toàn bộ phiên CAT + ánh xạ θ sang Bloom Level
**File:** `cat_engine.py`

**Tasks:**
- [ ] Implement `class CATSession` với state management (theta, responses, SE)
- [ ] Method `record_response(item, is_correct)` → auto update theta
- [ ] Method `should_stop()` → SE < threshold hoặc hết item
- [ ] Method `get_report()` → {theta, se, bloom_level, items_used, accuracy}
- [ ] Implement `map_theta_to_bloom(theta)` → int (1-6)

**Acceptance Criteria (Test):**
```python
# AC1: Full session simulation
pool = [{"id": f"q{i}", "a": 1.0, "b": (i-5)/2} for i in range(10)]
session = CATSession(item_pool=pool)
# Simulate: đúng 7/10 → θ nên dương
for i in range(7):
    item = session.get_next_item()
    session.record_response(item, is_correct=(i < 7))
report = session.get_report()
assert report["theta"] > 0
assert 1 <= report["bloom_level"] <= 6
assert report["items_used"] == 7

# AC2: θ → Bloom mapping
assert map_theta_to_bloom(-2.0) == 1   # Remember
assert map_theta_to_bloom(-1.0) == 2   # Understand  
assert map_theta_to_bloom(0.0) == 3    # Apply
assert map_theta_to_bloom(1.0) == 4    # Analyze
assert map_theta_to_bloom(2.0) == 5    # Evaluate
assert map_theta_to_bloom(3.0) == 6    # Create
```

---

#### Story 0.1.5 — Test File
**Mô tả:** Tạo file test tổng hợp, chạy được offline
**File:** `tests/test_cat_engine.py` (NEW)

**Tasks:**
- [ ] Tạo file test theo convention hiện tại (vanilla Python, PASS/FAIL counter)
- [ ] Gộp tất cả AC từ Story 0.1.1 → 0.1.4
- [ ] Thêm edge case: a=0 (no discrimination), b rất lớn/nhỏ

**Definition of Done Sprint 0.1:**
```bash
python tests/test_cat_engine.py
# Expected: 🎉 TẤT CẢ XX TEST ĐỀU PASS!
```

---

## Sprint 0.2 — Soft Prerequisite Engine (`soft_prerequisite.py`)
**Mục tiêu:** Logic Conditional Access + Bloom Ceiling, test offline với mock data.
**Thời gian ước tính:** 2-3 giờ
**Dependency:** Không phụ thuộc Sprint 0.1 (chạy song song được)

### User Stories

#### Story 0.2.1 — Access Policy Config & Prerequisite Graph
**Mô tả:** Tạo 3 access policies + hàm trích xuất prerequisite từ edges
**File:** `soft_prerequisite.py` (NEW)

**Tasks:**
- [ ] Tạo file với dict `ACCESS_POLICIES` (k12_strict, university_flexible, professional_open)
- [ ] Implement `get_direct_prerequisites(node_id, edges)` → list[str]
- [ ] Implement `get_all_prerequisites(node_id, edges)` → set[str] (transitive closure, DFS)

**Acceptance Criteria (Test):**
```python
# Sử dụng edges mẫu từ tree thật: c1.1→c1.2→c1.3→c2.1
edges = [
    {"source": "c1.1", "target": "c1.2", "relation": "prerequisite_for"},
    {"source": "c1.2", "target": "c1.3", "relation": "prerequisite_for"},
    {"source": "c1.3", "target": "c2.1", "relation": "prerequisite_for"},
]

# AC1: Direct prereqs of c1.2 = [c1.1]
assert get_direct_prerequisites("c1.2", edges) == ["c1.1"]

# AC2: Direct prereqs of c1.1 = [] (root node)
assert get_direct_prerequisites("c1.1", edges) == []

# AC3: ALL prereqs of c2.1 = {c1.1, c1.2, c1.3} (transitive)
assert get_all_prerequisites("c2.1", edges) == {"c1.1", "c1.2", "c1.3"}

# AC4: Cycle-safe (nếu có cycle trong edges, không infinite loop)
cyclic_edges = edges + [{"source": "c2.1", "target": "c1.1"}]
result = get_all_prerequisites("c2.1", cyclic_edges)  # Không crash
assert isinstance(result, set)
```

---

#### Story 0.2.2 — Prerequisite Mastery Calculation
**Mô tả:** Tính trung bình mastery của prerequisite nodes từ bloom_state
**File:** `soft_prerequisite.py`

**Tasks:**
- [ ] Implement `get_prereq_mastery(node_id, edges, bloom_state)` → float (0.0-1.0)
- [ ] Nếu không có prereq → return 1.0 (root node, full access)
- [ ] Lấy `overall_bloom / 6.0` từ bloom_state cho mỗi prereq node

**Acceptance Criteria (Test):**
```python
edges = [
    {"source": "c1.1", "target": "c1.2"},
    {"source": "c1.2", "target": "c2.1"},
]
bloom_state = {
    "nodes": {
        "c1.1": {"overall_bloom": 3.0},   # 3.0/6.0 = 50%
        "c1.2": {"overall_bloom": 1.2},   # 1.2/6.0 = 20%
    }
}

# AC1: Root node → 1.0
assert get_prereq_mastery("c1.1", edges, bloom_state) == 1.0

# AC2: c1.2 prereq = c1.1 (bloom 3.0) → 3.0/6 = 0.5
assert abs(get_prereq_mastery("c1.2", edges, bloom_state) - 0.5) < 0.01

# AC3: c2.1 prereqs = c1.1+c1.2 → avg(0.5, 0.2) = 0.35
assert abs(get_prereq_mastery("c2.1", edges, bloom_state) - 0.35) < 0.01

# AC4: Prereq node chưa có trong bloom_state → mastery = 0
bloom_empty = {"nodes": {}}
assert get_prereq_mastery("c1.2", edges, bloom_empty) == 0.0
```

---

#### Story 0.2.3 — Bloom Ceiling Formula
**Mô tả:** Công thức cốt lõi: giới hạn Bloom level dựa trên prerequisite mastery
**File:** `soft_prerequisite.py`

**Tasks:**
- [ ] Implement `calculate_bloom_ceiling(node_id, target_levels, edges, bloom_state, policy)` → int
- [ ] Công thức: `ceiling = min(target_max, floor(avg_mastery × target_max) + 1)`
- [ ] Policy "professional_open" → luôn return target_max (không giới hạn)
- [ ] Root node (no prereqs) → luôn return target_max

**Acceptance Criteria (Test):**
```python
target_levels = [1, 2, 3, 4]
edges = [{"source": "c1.1", "target": "c3.1"}]

# AC1: Prereq mastery 30% → ceiling = min(4, floor(0.3×4)+1) = min(4,2) = 2
bloom_30 = {"nodes": {"c1.1": {"overall_bloom": 1.8}}}  # 1.8/6 = 0.3
ceiling = calculate_bloom_ceiling("c3.1", target_levels, edges, bloom_30, "university_flexible")
assert ceiling == 2, f"Expected 2, got {ceiling}"

# AC2: Prereq mastery 70% → ceiling = min(4, floor(0.7×4)+1) = min(4,3) = 3
bloom_70 = {"nodes": {"c1.1": {"overall_bloom": 4.2}}}  # 4.2/6 = 0.7
ceiling = calculate_bloom_ceiling("c3.1", target_levels, edges, bloom_70, "university_flexible")
assert ceiling == 3

# AC3: Prereq mastery 100% → ceiling = 4 (full)
bloom_100 = {"nodes": {"c1.1": {"overall_bloom": 6.0}}}
ceiling = calculate_bloom_ceiling("c3.1", target_levels, edges, bloom_100, "university_flexible")
assert ceiling == 4

# AC4: Policy "professional_open" → always max regardless of prereq
ceiling = calculate_bloom_ceiling("c3.1", target_levels, edges, bloom_30, "professional_open")
assert ceiling == 4

# AC5: Root node (no prereq) → always max
ceiling = calculate_bloom_ceiling("c1.1", target_levels, edges, bloom_30, "university_flexible")
assert ceiling == 4
```

---

#### Story 0.2.4 — Access Status Report
**Mô tả:** Hàm tổng hợp trả về trạng thái truy cập đầy đủ cho UI
**File:** `soft_prerequisite.py`

**Tasks:**
- [ ] Implement `get_access_status(node_id, target_levels, edges, bloom_state, policy)` → dict
- [ ] Return: `{accessible, bloom_ceiling, unlocked_levels, locked_levels, prereq_gaps, recommendation}`
- [ ] `recommendation`: string gợi ý hành động (VD: "Hoàn thành Ch1 để mở L3-L4")

**Acceptance Criteria (Test):**
```python
# AC1: Partial access scenario
status = get_access_status("c3.1", [1,2,3,4], edges, bloom_30, "university_flexible")
assert status["accessible"] == True
assert status["bloom_ceiling"] == 2
assert status["unlocked_levels"] == [1, 2]
assert status["locked_levels"] == [3, 4]
assert len(status["prereq_gaps"]) > 0       # c1.1 chưa đủ
assert "c1.1" in str(status["recommendation"])

# AC2: Full access scenario
status_full = get_access_status("c3.1", [1,2,3,4], edges, bloom_100, "university_flexible")
assert status_full["bloom_ceiling"] == 4
assert status_full["locked_levels"] == []

# AC3: K-12 strict — node bị chặn hoàn toàn nếu prereq < 60%
status_k12 = get_access_status("c3.1", [1,2,3,4], edges, bloom_30, "k12_strict")
assert status_k12["accessible"] == False  # Hard block
```

---

#### Story 0.2.5 — Test File
**Mô tả:** Test tổng hợp cho soft_prerequisite.py
**File:** `tests/test_soft_prerequisite.py` (NEW)

**Tasks:**
- [ ] Tạo file test theo convention (vanilla Python, PASS/FAIL)
- [ ] Gộp AC từ Story 0.2.1 → 0.2.4
- [ ] Test với edges mẫu từ tree thật (faa95c0b.json pattern)

**Definition of Done Sprint 0.2:**
```bash
python tests/test_soft_prerequisite.py
# Expected: 🎉 TẤT CẢ XX TEST ĐỀU PASS!
```

---

## Tổng quan Sprint tiếp theo (Preview — chi tiết viết sau)

### Sprint 0.3 — Integration vào Bloom System
- [ ] Sửa `check_level_unlocked()` trong `bloom_taxonomy.py` thêm param `bloom_ceiling`
- [ ] Thêm `map_theta_to_bloom()` vào `bloom_taxonomy.py`
- [ ] Thêm CAT state storage vào `knowledge_tracing.py`
- [ ] **Test:** Chạy `test_cat_engine.py` + `test_soft_prerequisite.py` + test integration mới → ALL PASS

### Sprint 0.4 — UI Integration (Bloom Hub)
- [ ] Sửa `bloom_hub_page.py`: ceiling badge, prereq warning
- [ ] Thêm CAT assessment mode (thay vì random MCQ)
- [ ] **Test:** Browser test — mở Bloom Hub → verify ceiling hiển thị đúng

### Sprint 0.5 — Placement Test + Knowledge Space
- [ ] CAT Placement Test flow (5-10 items diagnostic)
- [ ] Knowledge Space outer fringe detection
- [ ] Access Policy selector trong UI
- [ ] **Test:** E2E — student skip Ch1 → Ch3 hiển thị giới hạn → hoàn thành Ch1 → Ch3 mở thêm

---

## Burndown Tracking

| Sprint | Status | Stories | Tests Pass |
|---|---|---|---|
| 0.1 CAT Math Core | `[ ]` Not Started | 0/5 | — |
| 0.2 Soft Prerequisite | `[ ]` Not Started | 0/5 | — |
| 0.3 Integration | `[ ]` Blocked by 0.1+0.2 | 0/3 | — |
| 0.4 UI Integration | `[ ]` Blocked by 0.3 | 0/3 | — |
| 0.5 Placement + KST | `[ ]` Blocked by 0.4 | 0/4 | — |

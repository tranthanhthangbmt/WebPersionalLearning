# cat_engine.py
"""
Computerized Adaptive Testing (CAT) Engine
===========================================
Dựa trên Item Response Theory (IRT) — 2-Parameter Logistic Model

Lý thuyết:
  Mô hình IRT 2PL tính xác suất trả lời đúng:
    P(θ) = 1 / (1 + exp(-a(θ - b)))

  Trong đó:
    θ (theta) : Năng lực ẩn của người học (latent ability), ước lượng real-time
    a          : Discrimination — Độ phân biệt câu hỏi (a > 0, thường 0.5-2.5)
    b          : Difficulty — Độ khó câu hỏi (thường -3 đến +3)

  Thuật toán CAT:
    1. Khởi tạo θ₀ = 0 (trung bình quần thể)
    2. Chọn item có Fisher Information cao nhất tại θ hiện tại
    3. Ghi nhận response → Cập nhật θ bằng EAP (Expected a Posteriori)
    4. Lặp lại cho đến khi SE(θ) < threshold hoặc đủ số item

References:
  - Lord, F. M. (1980). Applications of Item Response Theory
  - Doignon & Falmagne (1999). Knowledge Spaces
  - Anderson & Krathwohl (2001). Bloom Taxonomy Revised
"""

import math

# ============================================================
#  STORY 0.1.1 — IRT 2PL CORE FUNCTIONS
# ============================================================

def irt_probability(theta: float, a: float, b: float) -> float:
    """
    IRT 2PL: Xác suất trả lời đúng.

    P(θ) = 1 / (1 + exp(-a(θ - b)))

    Args:
        theta: Năng lực người học
        a: Discrimination (độ phân biệt, > 0)
        b: Difficulty (độ khó)

    Returns:
        Xác suất trả lời đúng (0.0 → 1.0)
    """
    exponent = -a * (theta - b)
    # Clamp to avoid overflow
    exponent = max(-700, min(700, exponent))
    return 1.0 / (1.0 + math.exp(exponent))


def fisher_information(theta: float, a: float, b: float) -> float:
    """
    Fisher Information tại θ cho 1 item.

    I(θ) = a² × P(θ) × (1 - P(θ))

    Item cung cấp thông tin nhiều nhất khi θ ≈ b (năng lực ≈ độ khó).

    Args:
        theta: Năng lực người học
        a: Discrimination
        b: Difficulty

    Returns:
        Fisher Information (≥ 0)
    """
    p = irt_probability(theta, a, b)
    return a * a * p * (1.0 - p)


def log_likelihood(theta: float, items: list, responses: list) -> float:
    """
    Tính Log-Likelihood của θ dựa trên lịch sử trả lời.

    ln L(θ) = Σ [uⱼ ln P(θ) + (1-uⱼ) ln(1-P(θ))]

    Args:
        theta: Năng lực ước lượng
        items: List of dicts, mỗi item có keys 'a', 'b'
        responses: List of bools (True=đúng, False=sai)

    Returns:
        Log-likelihood value
    """
    ll = 0.0
    for item, correct in zip(items, responses):
        p = irt_probability(theta, item["a"], item["b"])
        # Clamp p to avoid log(0)
        p = max(1e-10, min(1.0 - 1e-10, p))
        if correct:
            ll += math.log(p)
        else:
            ll += math.log(1.0 - p)
    return ll


# ============================================================
#  STORY 0.1.2 — EAP THETA ESTIMATION
# ============================================================

def estimate_theta_eap(items: list, responses: list,
                       num_quadrature: int = 41) -> float:
    """
    Ước lượng θ bằng Expected a Posteriori (Bayesian).

    θ_EAP = ∫ θ × L(θ|u) × π(θ) dθ  /  ∫ L(θ|u) × π(θ) dθ

    Sử dụng quadrature (tính tổng rời rạc) thay vì tích phân liên tục.
    Prior: π(θ) ~ N(0, 1) — phân phối chuẩn.

    Args:
        items: List of dicts với keys 'a', 'b'
        responses: List of bools
        num_quadrature: Số điểm lưới (41 điểm từ -4 đến +4)

    Returns:
        θ estimate (float)
    """
    if not items or not responses:
        return 0.0  # Prior mean

    # Quadrature points: -4 đến +4
    lower, upper = -4.0, 4.0
    step = (upper - lower) / (num_quadrature - 1)
    points = [lower + i * step for i in range(num_quadrature)]

    # Prior: N(0,1) density
    def normal_pdf(x):
        return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

    numerator = 0.0
    denominator = 0.0

    for q in points:
        # Log-likelihood at this quadrature point
        ll = log_likelihood(q, items, responses)
        # Posterior kernel = exp(log_likelihood) × prior
        # Work in log space to avoid underflow
        log_posterior = ll + math.log(max(1e-300, normal_pdf(q)))

        # Convert back (use offset trick for numerical stability)
        # We'll compute raw values and normalize
        posterior = math.exp(log_posterior)

        numerator += q * posterior * step
        denominator += posterior * step

    if denominator < 1e-300:
        return 0.0  # Fallback to prior

    return numerator / denominator


def get_standard_error(theta: float, items: list, responses: list) -> float:
    """
    Standard Error of θ estimate.

    SE(θ) = 1 / √(Σ Iⱼ(θ))

    Args:
        theta: Current θ estimate
        items: Administered items
        responses: Responses (used to confirm items were administered)

    Returns:
        Standard error (smaller = more precise)
    """
    if not items:
        return 10.0  # Very uncertain

    total_info = sum(fisher_information(theta, item["a"], item["b"])
                     for item in items)

    if total_info < 1e-10:
        return 10.0

    return 1.0 / math.sqrt(total_info)


# ============================================================
#  STORY 0.1.3 — ADAPTIVE ITEM SELECTION
# ============================================================

def select_next_item(theta: float, available_items: list,
                     administered_ids: set) -> dict | None:
    """
    Chọn item tối ưu: Maximum Fisher Information tại θ hiện tại.

    Thuật toán:
      1. Lọc bỏ items đã hỏi (administered_ids)
      2. Tính Fisher Information cho mỗi item còn lại
      3. Chọn item có I(θ) cao nhất

    Args:
        theta: Current ability estimate
        available_items: Full item pool (list of dicts with 'id', 'a', 'b')
        administered_ids: Set of item IDs already used

    Returns:
        Best item dict, or None if pool exhausted
    """
    candidates = [item for item in available_items
                  if item.get("id") not in administered_ids]

    if not candidates:
        return None

    best_item = None
    best_info = -1.0

    for item in candidates:
        info = fisher_information(theta, item["a"], item["b"])
        if info > best_info:
            best_info = info
            best_item = item

    return best_item


# ============================================================
#  STORY 0.1.4 — CAT SESSION CLASS & θ→BLOOM MAPPING
# ============================================================

# Mapping θ → Bloom Level thresholds
THETA_BLOOM_THRESHOLDS = [
    (-1.5, 1),   # θ < -1.5  → L1 Remember
    (-0.5, 2),   # θ < -0.5  → L2 Understand
    (0.5,  3),   # θ < 0.5   → L3 Apply
    (1.5,  4),   # θ < 1.5   → L4 Analyze
    (2.5,  5),   # θ < 2.5   → L5 Evaluate
]
# θ ≥ 2.5 → L6 Create


def map_theta_to_bloom(theta: float) -> int:
    """
    Ánh xạ IRT θ estimate → Bloom Level (1-6).

    | θ Range       | Bloom | Ý nghĩa        |
    |---------------|-------|----------------|
    | θ < -1.5      | L1    | Remember       |
    | -1.5 ≤ θ < -0.5 | L2 | Understand     |
    | -0.5 ≤ θ < 0.5  | L3 | Apply          |
    | 0.5 ≤ θ < 1.5   | L4 | Analyze        |
    | 1.5 ≤ θ < 2.5   | L5 | Evaluate       |
    | θ ≥ 2.5         | L6  | Create         |
    """
    for threshold, level in THETA_BLOOM_THRESHOLDS:
        if theta < threshold:
            return level
    return 6


class CATSession:
    """
    Quản lý một phiên CAT hoàn chỉnh.

    Usage:
        pool = [{"id": "q1", "a": 1.0, "b": 0.5, ...}, ...]
        session = CATSession(item_pool=pool)

        while not session.should_stop():
            item = session.get_next_item()
            if item is None:
                break
            # Present item to student, get response
            session.record_response(item, is_correct=True)

        report = session.get_report()
        # → {"theta": 1.2, "se": 0.28, "bloom_level": 4, ...}
    """

    def __init__(self, item_pool: list, prior_theta: float = 0.0,
                 se_threshold: float = 0.3, max_items: int = 15):
        """
        Args:
            item_pool: List of item dicts (must have 'id', 'a', 'b')
            prior_theta: Initial θ estimate (default 0 = average)
            se_threshold: Stop when SE < this (default 0.3)
            max_items: Maximum items to administer
        """
        self.item_pool = list(item_pool)
        self.theta = prior_theta
        self.se_threshold = se_threshold
        self.max_items = max_items

        self.administered_items = []   # List of item dicts
        self.responses = []            # List of bools
        self.administered_ids = set()  # Set of item IDs

    def get_next_item(self) -> dict | None:
        """Chọn item tiếp theo tối ưu."""
        return select_next_item(self.theta, self.item_pool,
                                self.administered_ids)

    def record_response(self, item: dict, is_correct: bool):
        """Ghi nhận response và cập nhật θ."""
        self.administered_items.append(item)
        self.responses.append(is_correct)
        self.administered_ids.add(item.get("id"))

        # Re-estimate θ using EAP
        self.theta = estimate_theta_eap(self.administered_items,
                                        self.responses)

    def should_stop(self) -> bool:
        """Kiểm tra điều kiện dừng."""
        if len(self.responses) >= self.max_items:
            return True
        if len(self.responses) >= 3:  # Need at least 3 items for SE
            se = get_standard_error(self.theta, self.administered_items,
                                    self.responses)
            if se < self.se_threshold:
                return True
        return False

    def get_report(self) -> dict:
        """Báo cáo kết quả phiên CAT."""
        se = get_standard_error(self.theta, self.administered_items,
                                self.responses)
        correct_count = sum(1 for r in self.responses if r)
        total = len(self.responses)

        return {
            "theta": round(self.theta, 3),
            "se": round(se, 3),
            "bloom_level": map_theta_to_bloom(self.theta),
            "items_used": total,
            "accuracy": round(correct_count / max(1, total), 3),
            "correct": correct_count,
            "total": total,
        }

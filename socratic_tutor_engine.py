# socratic_tutor_engine.py
"""
Socratic Tutor Engine — AI Tutor với 3 Persona theo Bloom Level
================================================================

Dựa trên PLiF Framework (Fake & Dabbagh, 2023, Ch.7) và GROW Coaching Model.

3 PERSONA:
  examiner        (L1-L2): Hỏi → Chấm → Giải thích ngắn
  socratic_guide  (L3-L4): Case study → Hỏi gợi mở → Tự phát hiện
  devils_advocate (L5-L6): Quan điểm sai → Tranh biện → Phê bình design

GROW COACHING MODEL:
  Goal    → Xác định mục tiêu học tập
  Reality → Đánh giá hiểu biết hiện tại
  Options → Khám phá các cách tiếp cận
  Will    → Cam kết hành động cụ thể

References:
  - Anderson & Krathwohl (2001). Bloom Taxonomy Revised
  - Whitmore (2009). Coaching for Performance (GROW Model)
  - Fake & Dabbagh (2023). PLiF Framework, Ch.7
"""
import re
import os
import json
import time

from persona_engine import select_persona, PERSONAS, get_learning_coach, build_coach_prompt

# ============================================================
# ============================================================
#  STORY 1.1.2 — SYSTEM PROMPT BUILDER
# ============================================================

def build_system_prompt(persona: dict, node_context: dict,
                        bloom_level: int, difficulty_alpha: int = 50,
                        grow_phase: str = None,
                        adaptive_hint: str = None) -> str:
    """
    Tạo system prompt cho AI tutor session.

    Args:
        persona: Persona dict từ select_persona()
        node_context: {"title": str, "content": str, ...}
        bloom_level: Target Bloom level (1-6)
        difficulty_alpha: Difficulty 0-100
        grow_phase: GROW phase hint (optional)
        adaptive_hint: CAT-based difficulty hint (optional)

    Returns:
        System prompt string
    """
    title = node_context.get("title", "Bài học")
    content = node_context.get("content", "")[:10000]
    ref_materials = node_context.get("ref_materials", "")[:50000]

    bloom_verbs = {
        1: "nhận biết, liệt kê, định nghĩa, nhớ lại",
        2: "giải thích, so sánh, tóm tắt, diễn giải",
        3: "áp dụng, thực hiện, giải quyết, minh họa",
        4: "phân tích, so sánh-đối chiếu, suy luận, phân loại",
        5: "đánh giá, phê bình, biện luận, chứng minh",
        6: "thiết kế, sáng tạo, đề xuất, tổng hợp",
    }

    prompt_parts = [
        f"=== PERSONA: {persona['name']} ({persona['icon']}) ===",
        f"Giọng điệu: {persona['tone']}",
        f"Chiến lược: {persona['strategy']}",
        "",
        persona["system_instruction"],
        "",
        f"=== BÀI HỌC: {title} ===",
        f"Nội dung: {content}" if content else "",
        f"\nTài liệu tham khảo:\n{ref_materials}" if ref_materials else "",
        "",
        f"=== MỤC TIÊU BLOOM: L{bloom_level} ===",
        f"Động từ mục tiêu: {bloom_verbs.get(bloom_level, '')}",
        f"Độ khó yêu cầu: {difficulty_alpha}/100",
    ]

    if adaptive_hint:
        prompt_parts.append(f"\n=== GỢI Ý ADAPTIVE (từ CAT) ===\n{adaptive_hint}")

    if grow_phase:
        grow_hint = get_grow_phase_prompt(grow_phase, node_context)
        prompt_parts.append(f"\n=== GROW COACHING PHASE ===\n{grow_hint}")

    prompt_parts.extend([
        "",
        "=== LUẬT BẮT BUỘC ===",
        "1. Câu đầu tiên: Đặt câu hỏi CHUYÊN SÂU dựa CHÍNH XÁC vào 'Tài liệu tham khảo' và 'Nội dung' bên trên. KHÔNG ĐƯỢC tự bịa ra chủ đề chung chung.",
        "2. NẾU 'Tài liệu tham khảo' và 'Nội dung' bên trên bị trống hoặc quá chung chung, HÃY DỪNG LẠI và thông báo: 'Hệ thống không tìm thấy kịch bản hoặc tài liệu cho bài học này. Vui lòng cập nhật tài liệu để tôi có thể đặt câu hỏi chính xác.'",
        "3. Khi sinh viên trả lời: dùng chiến lược persona để phản hồi.",
        "4. Sau 3-5 lượt trao đổi, CHẤM ĐIỂM bằng JSON block:",
        '   {"verdict": "passed"}  — nếu sinh viên thông thạo',
        '   {"verdict": "failed"}  — nếu sinh viên chưa đạt',
        '   {"verdict": "continue"} — nếu cần hỏi thêm',
        "5. Luôn dùng tiếng Việt. Không bọc JSON trong markdown code block.",
    ])

    return "\n".join(p for p in prompt_parts if p is not None)


# ============================================================
#  STORY 1.1.3 — GROW COACHING FRAMEWORK
# ============================================================

GROW_PHASES = [
    {
        "id": "goal",
        "name": "Goal (Mục tiêu)",
        "instruction": (
            "Hỏi sinh viên: Mục tiêu học tập của bạn với chủ đề này là gì? "
            "Bạn muốn đạt được điều gì sau khi học xong?"
        ),
    },
    {
        "id": "reality",
        "name": "Reality (Thực tế)",
        "instruction": (
            "Đánh giá hiểu biết hiện tại: Bạn đã biết gì về chủ đề này? "
            "Hãy cho tôi biết những gì bạn đang gặp khó khăn."
        ),
    },
    {
        "id": "options",
        "name": "Options (Lựa chọn)",
        "instruction": (
            "Khám phá các cách tiếp cận: Có những cách nào để giải quyết vấn đề này? "
            "Hãy liệt kê ít nhất 2-3 phương án và phân tích ưu nhược."
        ),
    },
    {
        "id": "will",
        "name": "Will (Hành động)",
        "instruction": (
            "Cam kết hành động: Bạn sẽ làm gì tiếp theo? "
            "Hãy đề xuất một bước cụ thể để áp dụng kiến thức vừa học."
        ),
    },
]

_GROW_ORDER = [p["id"] for p in GROW_PHASES]


def get_grow_phase_prompt(phase_id: str, node_context: dict) -> str:
    """
    Tạo prompt bổ sung cho GROW coaching phase.

    Args:
        phase_id: "goal", "reality", "options", "will"
        node_context: Node context dict

    Returns:
        GROW phase instruction string
    """
    title = node_context.get("title", "chủ đề")

    for phase in GROW_PHASES:
        if phase["id"] == phase_id:
            return (
                f"Phase hiện tại: {phase['name']}\n"
                f"Hướng dẫn: {phase['instruction']}\n"
                f"Áp dụng cho chủ đề: {title}"
            )

    return ""


def advance_grow_phase(current_phase: str) -> str | None:
    """
    Chuyển sang phase GROW tiếp theo.

    Returns:
        Next phase ID, or None if completed
    """
    if current_phase not in _GROW_ORDER:
        return _GROW_ORDER[0] if _GROW_ORDER else None

    idx = _GROW_ORDER.index(current_phase)
    if idx + 1 < len(_GROW_ORDER):
        return _GROW_ORDER[idx + 1]
    return None


# ============================================================
#  STORY 1.1.4 — VERDICT EXTRACTION & SCORING
# ============================================================

def extract_verdict(ai_response_text: str) -> dict:
    """
    Trích xuất verdict JSON từ AI response.

    Handles:
      - '{"verdict": "passed"}' embedded in text
      - No verdict → "continue"
      - Malformed JSON → "continue"

    Returns:
        {"verdict": str, "clean_text": str}
    """
    clean_text = ai_response_text

    # Try to find verdict JSON
    pattern = r'\{[^{}]*"verdict"\s*:\s*"(\w+)"[^{}]*\}'
    match = re.search(pattern, ai_response_text)

    if match:
        verdict = match.group(1).lower()
        # Normalize
        if verdict in ("passed", "pass"):
            verdict = "passed"
        elif verdict in ("failed", "fail"):
            verdict = "failed"
        else:
            verdict = "continue"
        # Remove JSON from display text
        clean_text = re.sub(pattern, '', ai_response_text).strip()
    else:
        verdict = "continue"

    return {
        "verdict": verdict,
        "clean_text": clean_text,
    }


def calculate_socratic_score(verdicts: list, bloom_level: int) -> float:
    """
    Tính điểm Socratic session từ lịch sử verdicts.

    Scoring:
      - "passed" = +1.0
      - "continue" = +0.3 (vẫn đang trao đổi tốt)
      - "failed" = +0.0

    Final = weighted_sum / max_possible × bloom_weight

    Args:
        verdicts: List of verdict strings ["passed", "continue", "failed"]
        bloom_level: 1-6

    Returns:
        Score (0.0 → 1.0)
    """
    if not verdicts:
        return 0.0

    weights = {
        "passed": 1.0,
        "continue": 0.3,
        "failed": 0.0,
    }

    total = sum(weights.get(v, 0.0) for v in verdicts)
    max_possible = len(verdicts) * 1.0  # All passed

    if max_possible == 0:
        return 0.0

    raw_score = total / max_possible
    return min(1.0, raw_score)


# ============================================================
#  STORY 1.2.1 — SOCRATIC SESSION CLASS
# ============================================================

class SocraticSession:
    """
    Quản lý một phiên Socratic Tutor hoàn chỉnh.

    Usage:
        session = SocraticSession(bloom_level=3)
        system_prompt = session.start({"title": "TMĐT", "content": "..."})
        # Send system_prompt to AI, get response
        result = session.process_ai_response(ai_response)
        # result["should_stop"] → True/False
        report = session.get_report()
    """

    def __init__(self, bloom_level: int = 3, difficulty_alpha: int = 50,
                 use_grow: bool = False, max_turns: int = 8):
        self.bloom_level = bloom_level
        self.difficulty_alpha = difficulty_alpha
        self.use_grow = use_grow
        self.max_turns = max_turns

        self.persona = select_persona(bloom_level)
        self.verdicts = []
        self.turns = 0
        self.grow_phase = "goal" if use_grow else None
        self.started = False
        self.finished = False
        self.node_context = {}

    def start(self, node_context: dict, adaptive_hint: str = None) -> str:
        """Bắt đầu session, trả về system prompt."""
        self.node_context = node_context
        self.started = True

        prompt = build_system_prompt(
            persona=self.persona,
            node_context=node_context,
            bloom_level=self.bloom_level,
            difficulty_alpha=self.difficulty_alpha,
            grow_phase=self.grow_phase,
            adaptive_hint=adaptive_hint,
        )
        return prompt

    def process_ai_response(self, response_text: str) -> dict:
        """
        Xử lý AI response: extract verdict, update state.

        Returns:
            {"verdict": str, "clean_text": str, "should_stop": bool}
        """
        result = extract_verdict(response_text)
        self.verdicts.append(result["verdict"])
        self.turns += 1

        # Advance GROW phase on "continue"
        if self.use_grow and result["verdict"] == "continue" and self.grow_phase:
            self.grow_phase = advance_grow_phase(self.grow_phase)

        # Check stop conditions
        should_stop = (
            result["verdict"] in ("passed", "failed")
            or self.turns >= self.max_turns
        )

        if should_stop:
            self.finished = True

        result["should_stop"] = should_stop
        return result

    def get_report(self) -> dict:
        """Báo cáo kết quả phiên Socratic."""
        score = calculate_socratic_score(self.verdicts, self.bloom_level)

        # Determine final verdict
        if "passed" in self.verdicts:
            final = "passed"
        elif "failed" in self.verdicts:
            final = "failed"
        else:
            final = "incomplete"

        return {
            "score": round(score, 3),
            "bloom_level": self.bloom_level,
            "persona_used": self.persona["id"],
            "turns": self.turns,
            "verdicts": list(self.verdicts),
            "final_verdict": final,
            "grow_phases_completed": (
                _GROW_ORDER.index(self.grow_phase) if self.grow_phase and self.grow_phase in _GROW_ORDER else len(_GROW_ORDER)
            ) if self.use_grow else None,
            "timestamp": time.time(),
        }


# ============================================================
#  STORY 1.2.2 — CAT-ADAPTIVE CONTEXT
# ============================================================

def get_adaptive_context(cat_session, node_context: dict) -> dict:
    """
    Tạo adaptive context dựa trên CAT θ estimate.

    Args:
        cat_session: CATSession instance (from cat_engine.py)
        node_context: Node context dict

    Returns:
        Dict with difficulty_hint for prompt builder
    """
    theta = getattr(cat_session, 'theta', 0.0)

    if theta < -1.0:
        hint = ("Sinh viên đang ở mức CƠ BẢN (θ thấp). "
                "Hãy dùng scaffolding: câu hỏi đơn giản, gợi ý nhiều, "
                "khuyến khích và dìu dắt nhẹ nhàng.")
        level = "scaffolding"
    elif theta < 0.5:
        hint = ("Sinh viên ở mức TRUNG BÌNH. "
                "Hỏi câu hỏi vừa phải, cho phép suy nghĩ nhưng sẵn sàng gợi ý.")
        level = "normal"
    elif theta < 1.5:
        hint = ("Sinh viên ở mức KHÁ (θ cao). "
                "Hỏi câu hỏi nâng cao, đòi hỏi phân tích sâu, ít gợi ý hơn.")
        level = "advanced"
    else:
        hint = ("Sinh viên ở mức XUẤT SẮC (θ rất cao). "
                "Hỏi câu challenge cực khó, tranh biện gay gắt, "
                "đòi hỏi sáng tạo và bảo vệ quan điểm.")
        level = "challenge"

    return {
        "theta": round(theta, 2),
        "difficulty_hint": hint,
        "difficulty_level": level,
    }


# ============================================================
#  STORY 1.2.3 — SESSION PERSISTENCE
# ============================================================

def _get_session_dir(user_id: str, subject_id: str) -> str:
    """Đường dẫn thư mục lưu session history."""
    dir_path = f"user_data/{user_id}/socratic_sessions"
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def save_session_result(user_id: str, subject_id: str,
                        node_id: str, report: dict):
    """Lưu kết quả session vào lịch sử."""
    dir_path = _get_session_dir(user_id, subject_id)
    history_file = os.path.join(dir_path, f"{subject_id}_{node_id}.json")

    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = {"node_id": node_id, "subject_id": subject_id, "sessions": []}

    report_copy = dict(report)
    if "timestamp" not in report_copy:
        report_copy["timestamp"] = time.time()

    history["sessions"].append(report_copy)
    history["total_sessions"] = len(history["sessions"])

    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_session_history(user_id: str, subject_id: str,
                        node_id: str) -> list:
    """Lấy lịch sử sessions cho một node."""
    dir_path = _get_session_dir(user_id, subject_id)
    history_file = os.path.join(dir_path, f"{subject_id}_{node_id}.json")

    if not os.path.exists(history_file):
        return []

    with open(history_file, 'r', encoding='utf-8') as f:
        history = json.load(f)

    return history.get("sessions", [])

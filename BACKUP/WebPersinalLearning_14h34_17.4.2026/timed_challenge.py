# timed_challenge.py
"""
Timed Challenge Mode - Speed Quiz Racing
- Select a chapter → System generates 10 questions
- 60-second countdown timer
- +10 points + 3s bonus for correct
- -5 points + 5s penalty for wrong
- Combo multiplier for consecutive corrects
- Fire combo animation
- Results screen with shareable stats
- Best score saved for leaderboard
"""

from nicegui import ui, run, app
import json
import os
import time
from gemini_helper import get_chat_model


# ============================================================
#  TIMED CHALLENGE CSS
# ============================================================

TIMED_CSS = """
<style>
@keyframes timer-pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}
@keyframes combo-fire {
    0% { transform: scale(0.5) rotate(-10deg); opacity: 0; }
    50% { transform: scale(1.3) rotate(5deg); opacity: 1; }
    100% { transform: scale(1) rotate(0); opacity: 1; }
}
@keyframes score-pop {
    0% { transform: translateY(0) scale(1); opacity: 1; }
    100% { transform: translateY(-40px) scale(1.5); opacity: 0; }
}
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-8px); }
    75% { transform: translateX(8px); }
}
.timer-danger { animation: timer-pulse 0.5s ease-in-out infinite; color: #ef4444 !important; }
.combo-fire-anim { animation: combo-fire 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards; }
.score-float { animation: score-pop 1s ease-out forwards; }
.shake-anim { animation: shake 0.3s ease-in-out; }
</style>
"""


# ============================================================
#  AI QUESTION GENERATION
# ============================================================

async def generate_timed_questions(content: str, chapter_name: str, count: int = 10) -> list:
    """Generate multiple-choice questions for timed challenge"""
    model = get_chat_model()
    if not model:
        return []

    prompt = f"""Bạn là hệ thống sinh câu hỏi trắc nghiệm tốc độ cao. Từ nội dung dưới đây,
hãy tạo CHÍNH XÁC {count} câu hỏi trắc nghiệm 4 đáp án dưới dạng JSON array.

Chương: {chapter_name}
Nội dung: {content}

OUTPUT FORMAT (JSON array, KHÔNG có text khác):
[
  {{
    "question": "Câu hỏi ngắn gọn?",
    "options": {{"A": "Đáp án A", "B": "Đáp án B", "C": "Đáp án C", "D": "Đáp án D"}},
    "correct": "A",
    "explanation": "Giải thích ngắn 1-2 câu"
  }},
  ...
]

QUY TẮC:
- Câu hỏi phải rõ ràng, ngắn gọn (phù hợp tốc độ)
- 4 đáp án, chỉ 1 đúng
- Trộn đều các mức độ: dễ (3), trung bình (5), khó (2)
- Tiếng Việt
"""

    try:
        response = await run.io_bound(model.generate_content, prompt)
        text = response.text
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            questions = json.loads(match.group(0))
            return [q for q in questions if isinstance(q, dict) and 'question' in q and 'correct' in q]
    except Exception as e:
        print(f"[TimedChallenge] AI generation error: {e}")
    return []


# ============================================================
#  BEST SCORE PERSISTENCE
# ============================================================

def _get_best_score_path(username: str) -> str:
    return f"user_data/{username}/timed_best_scores.json"


def _load_best_scores(username: str) -> dict:
    path = _get_best_score_path(username)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_best_score(username: str, subject_id: str, chapter: str, score: int, accuracy: float):
    scores = _load_best_scores(username)
    key = f"{subject_id}_{chapter}"
    current_best = scores.get(key, {}).get("score", 0)
    if score > current_best:
        scores[key] = {
            "score": score,
            "accuracy": accuracy,
            "timestamp": time.time(),
            "subject_id": subject_id,
            "chapter": chapter,
        }
        path = _get_best_score_path(username)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
    return score > current_best


# ============================================================
#  TIMED CHALLENGE PAGE
# ============================================================

def register_timed_challenge_page():
    @ui.page('/timed_challenge/{subject_id}')
    async def timed_challenge_page(subject_id: str):
        username = app.storage.user.get('username')
        user_id = app.storage.user.get('id')
        if not username:
            ui.label('Vui lòng đăng nhập').classes('text-red-500 font-bold p-8')
            return

        ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">')
        ui.add_head_html(TIMED_CSS)
        ui.query('body').classes('bg-[#0d1117] font-[Inter]')

        # Load tree
        tree_file = f"user_data/{username}/trees/{subject_id}.json"
        if not os.path.exists(tree_file):
            ui.label('Không tìm thấy dữ liệu.').classes('text-red-400 p-8')
            return

        with open(tree_file, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)

        nodes = tree_data.get('micro_nodes', []) + tree_data.get('macro_nodes', [])
        course_name = tree_data.get('course_name', 'Môn học')

        # State
        state = {
            "questions": [],
            "current_index": 0,
            "score": 0,
            "combo": 0,
            "max_combo": 0,
            "correct_count": 0,
            "wrong_count": 0,
            "time_left": 60,
            "is_running": False,
            "timer_ref": None,
            "answered_this_q": False,
            "start_time": 0,
            "times_per_question": [],
        }

        with ui.column().classes('w-full max-w-2xl mx-auto p-6 min-h-screen items-center'):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/app')).props('flat round color=grey')
                ui.label('⚡ Đua Tốc Độ').classes('text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-red-500')

            main_area = ui.column().classes('w-full flex-grow items-center justify-center')

            # --- CHAPTER SELECT LOBBY ---
            def render_lobby():
                main_area.clear()
                with main_area:
                    ui.label('Chọn chương để bắt đầu thử thách!').classes('text-xl font-bold text-white mb-6')
                    ui.label('⏱️ 60 giây | 10 câu hỏi | Tốc độ & Chính xác').classes('text-sm text-gray-400 mb-6')

                    # Group by chapter
                    chapters = {}
                    for n in nodes:
                        chap = n.get('chapter', 'Chương chung')
                        if chap not in chapters:
                            chapters[chap] = []
                        chapters[chap].append(n)

                    with ui.column().classes('w-full gap-3 max-w-lg'):
                        # All chapters option
                        with ui.card().classes(
                            'w-full p-4 bg-gradient-to-r from-amber-900/50 to-red-900/50 rounded-xl '
                            'cursor-pointer hover:scale-[1.02] transition-all border border-amber-700'
                        ).on('click', lambda: start_challenge(nodes, 'Tất cả')):
                            with ui.row().classes('items-center gap-3'):
                                ui.icon('local_fire_department', color='amber').classes('text-3xl')
                                with ui.column().classes('gap-0'):
                                    ui.label('🔥 Thử thách toàn bộ').classes('font-bold text-white')
                                    ui.label(f'{len(nodes)} nodes → 10 câu random').classes('text-xs text-amber-300')

                        for chap_name, chap_nodes in chapters.items():
                            best = _load_best_scores(username).get(f"{subject_id}_{chap_name}", {})
                            best_score = best.get("score", 0)

                            with ui.card().classes(
                                'w-full p-3 bg-gray-800/50 rounded-xl cursor-pointer hover:bg-gray-700/50 '
                                'transition-all border border-gray-700'
                            ).on('click', lambda cn=chap_nodes, name=chap_name: start_challenge(cn, name)):
                                with ui.row().classes('items-center gap-3 w-full'):
                                    ui.icon('folder', color='amber-400').classes('text-xl')
                                    ui.label(chap_name).classes('font-medium text-gray-200 text-sm flex-grow')
                                    if best_score > 0:
                                        ui.label(f'🏆 {best_score}').classes('text-xs text-amber-400 font-bold')

            async def start_challenge(chapter_nodes, chapter_name):
                """Generate questions and start the timer"""
                main_area.clear()
                with main_area:
                    with ui.column().classes('items-center gap-4'):
                        ui.spinner('dots', size='xl', color='amber')
                        ui.label('AI đang sinh câu hỏi thử thách...').classes('text-amber-300 text-sm animate-pulse')

                content = "\n".join([
                    f"- {n.get('title', '')}: {n.get('content', '')[:200]}" for n in chapter_nodes[:25]
                ])
                questions = await generate_timed_questions(content, chapter_name, count=10)

                if not questions or len(questions) < 3:
                    main_area.clear()
                    with main_area:
                        ui.label('❌ Không thể tạo câu hỏi.').classes('text-red-400')
                        ui.button('Thử lại', on_click=render_lobby).props('color=amber outline')
                    return

                state["questions"] = questions[:10]
                state["current_index"] = 0
                state["score"] = 0
                state["combo"] = 0
                state["max_combo"] = 0
                state["correct_count"] = 0
                state["wrong_count"] = 0
                state["time_left"] = 60
                state["is_running"] = True
                state["answered_this_q"] = False
                state["start_time"] = time.time()
                state["times_per_question"] = []
                state["_chapter_name"] = chapter_name

                render_question()

            # --- QUESTION RENDER ---
            def render_question():
                if not state["is_running"]:
                    return

                idx = state["current_index"]
                questions = state["questions"]

                if idx >= len(questions):
                    finish_challenge()
                    return

                q = questions[idx]
                state["answered_this_q"] = False
                state["_q_start_time"] = time.time()
                main_area.clear()

                with main_area:
                    # Top bar: Timer + Score + Combo
                    with ui.row().classes('w-full max-w-lg items-center justify-between mb-4'):
                        # Timer  
                        timer_label = ui.label(f'⏱️ {state["time_left"]}s').classes(
                            'text-2xl font-extrabold text-white'
                        )
                        if state["time_left"] <= 10:
                            timer_label.classes(add='timer-danger')

                        # Score
                        ui.label(f'💎 {state["score"]}').classes('text-xl font-extrabold text-amber-400')

                        # Combo
                        if state["combo"] >= 2:
                            ui.label(f'🔥 x{state["combo"]}').classes(
                                'text-lg font-extrabold text-orange-400 combo-fire-anim'
                            )

                    # Progress dots
                    with ui.row().classes('w-full max-w-lg justify-center gap-1 mb-4'):
                        for i in range(len(questions)):
                            if i < idx:
                                color = 'bg-green-500' if i < state["correct_count"] else 'bg-red-500'
                            elif i == idx:
                                color = 'bg-amber-400 ring-2 ring-amber-300'
                            else:
                                color = 'bg-gray-700'
                            ui.element('div').classes(f'w-3 h-3 rounded-full {color} transition-all')

                    # Question
                    with ui.card().classes(
                        'w-full max-w-lg p-6 rounded-2xl bg-gray-800/80 border border-gray-700 mb-4'
                    ):
                        ui.label(f'Câu {idx + 1}/{len(questions)}').classes('text-xs text-gray-500 font-bold mb-2')
                        ui.label(q["question"]).classes('text-lg font-bold text-white leading-relaxed')

                    # Options
                    result_container = ui.column().classes('w-full max-w-lg')
                    options_container = ui.column().classes('w-full max-w-lg gap-2')

                    with options_container:
                        btn_map = {}
                        for key in ['A', 'B', 'C', 'D']:
                            if key in q.get('options', {}):
                                opt_text = q['options'][key]
                                btn = ui.button(
                                    f'{key}. {opt_text}',
                                    on_click=lambda e, k=key: handle_answer(k, q, btn_map, result_container, options_container)
                                ).classes(
                                    'w-full text-left px-4 py-3 bg-gray-700/50 text-gray-200 rounded-xl '
                                    'border border-gray-600 hover:border-amber-500 hover:bg-gray-600/50 transition-all'
                                ).props('no-caps align=left')
                                btn_map[key] = btn

                    # Timer tick
                    def tick():
                        if not state["is_running"]:
                            return
                        state["time_left"] -= 1
                        try:
                            timer_label.text = f'⏱️ {state["time_left"]}s'
                            if state["time_left"] <= 10:
                                timer_label.classes(add='timer-danger')
                        except Exception:
                            pass
                        if state["time_left"] <= 0:
                            finish_challenge()

                    if state.get("_timer"):
                        try:
                            state["_timer"].deactivate()
                        except Exception:
                            pass
                    state["_timer"] = ui.timer(1.0, tick)

            def handle_answer(selected, question, btn_map, result_container, options_container):
                """Handle answer selection"""
                if state["answered_this_q"]:
                    return
                state["answered_this_q"] = True

                correct_key = question["correct"]
                is_correct = (selected == correct_key)

                # Track time per question
                q_time = time.time() - state.get("_q_start_time", time.time())
                state["times_per_question"].append(q_time)

                if is_correct:
                    state["score"] += 10 + (state["combo"] * 2)  # Combo bonus
                    state["combo"] += 1
                    state["max_combo"] = max(state["max_combo"], state["combo"])
                    state["correct_count"] += 1
                    state["time_left"] = min(99, state["time_left"] + 3)  # Time bonus

                    # Visual feedback
                    for key, btn in btn_map.items():
                        if key == correct_key:
                            btn.classes(remove='bg-gray-700/50 border-gray-600', add='bg-green-600/50 border-green-500')
                        else:
                            btn.props('disable')
                            btn.classes(add='opacity-50')
                else:
                    state["score"] = max(0, state["score"] - 5)
                    state["combo"] = 0
                    state["wrong_count"] += 1
                    state["time_left"] = max(0, state["time_left"] - 5)  # Time penalty

                    # Visual feedback
                    for key, btn in btn_map.items():
                        if key == correct_key:
                            btn.classes(remove='bg-gray-700/50 border-gray-600', add='bg-green-600/50 border-green-500')
                        elif key == selected:
                            btn.classes(remove='bg-gray-700/50 border-gray-600', add='bg-red-600/50 border-red-500 shake-anim')
                        else:
                            btn.props('disable')
                            btn.classes(add='opacity-50')

                # Gamification
                if user_id:
                    try:
                        from gamification.gamification_ui import process_gamification_event
                        action = 'quiz_correct' if is_correct else 'quiz_wrong'
                        process_gamification_event(user_id, action)
                    except Exception:
                        pass

                # Show brief explanation & auto-advance
                with result_container:
                    emoji = '✅' if is_correct else '❌'
                    score_delta = f'+{10 + (state["combo"]-1)*2}' if is_correct else '-5'
                    ui.label(f'{emoji} {score_delta} điểm').classes(
                        f'text-sm font-bold {"text-green-400" if is_correct else "text-red-400"} mt-2'
                    )

                # Auto-advance after 1.2s
                def next_q():
                    state["current_index"] += 1
                    render_question()

                ui.timer(1.2, next_q, once=True)

            def finish_challenge():
                """End the challenge and show results"""
                state["is_running"] = False
                if state.get("_timer"):
                    try:
                        state["_timer"].deactivate()
                    except Exception:
                        pass

                score = state["score"]
                correct = state["correct_count"]
                total = len(state["questions"])
                accuracy = (correct / max(1, total)) * 100
                avg_time = sum(state["times_per_question"]) / max(1, len(state["times_per_question"]))
                max_combo = state["max_combo"]

                # Save best score
                chapter_name = state.get("_chapter_name", "unknown")
                is_new_best = _save_best_score(username, subject_id, chapter_name, score, accuracy)

                main_area.clear()
                with main_area:
                    # Confetti for great scores
                    if accuracy >= 70:
                        from gamification.gamification_ui import CONFETTI_JS
                        ui.run_javascript(CONFETTI_JS)

                    with ui.card().classes(
                        'w-full max-w-md p-8 rounded-3xl bg-gradient-to-br from-gray-900 to-gray-800 '
                        'border border-gray-700 shadow-2xl text-center'
                    ):
                        # Header
                        grade = '🏆' if accuracy >= 80 else '⭐' if accuracy >= 60 else '💪' if accuracy >= 40 else '📚'
                        ui.html(f'<div style="font-size:64px;">{grade}</div>').classes('mb-2')

                        if is_new_best:
                            ui.label('🎉 KỶ LỤC MỚI!').classes('text-amber-400 font-extrabold text-lg tracking-widest mb-2')

                        ui.label('Thử thách hoàn tất!').classes('text-2xl font-extrabold text-white mb-4')

                        # Score
                        ui.label(f'{score}').classes('text-6xl font-extrabold text-amber-400')
                        ui.label('ĐIỂM').classes('text-xs text-gray-500 tracking-widest mb-4')

                        # Stats grid
                        with ui.row().classes('justify-center gap-6 my-4'):
                            for val, label in [
                                (f'{correct}/{total}', 'Đúng'),
                                (f'{accuracy:.0f}%', 'Chính xác'),
                                (f'{avg_time:.1f}s', 'TB/câu'),
                                (f'x{max_combo}', 'Max Combo'),
                            ]:
                                with ui.column().classes('items-center'):
                                    ui.label(val).classes('text-lg font-extrabold text-white')
                                    ui.label(label).classes('text-[10px] text-gray-500')

                        ui.button('🔄 Thử lại', on_click=render_lobby).classes(
                            'w-full bg-amber-600 text-white font-bold py-3 rounded-xl mb-2 mt-4'
                        ).props('no-caps')

                        ui.button('🏠 Quay lại', on_click=lambda: ui.navigate.to('/app')).classes(
                            'w-full bg-gray-700 text-gray-300 font-bold py-3 rounded-xl'
                        ).props('no-caps')

            # Start
            render_lobby()

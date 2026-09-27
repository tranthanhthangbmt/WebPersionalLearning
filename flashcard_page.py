# flashcard_page.py
"""
Flashcard Mode - AI-powered Spaced Repetition Flashcards
- AI generates flashcards from knowledge tree nodes
- Beautiful flip animation (CSS 3D transforms)
- Swipe left/right: "Chưa biết" / "Đã biết"
- SRS scheduling: Cards you don't know reappear sooner
- Batch mode: 10/20/50 cards per session
- Integrated with gamification engine
"""

from nicegui import ui, run, app
import json
import os
import time
import math
from gemini_helper import get_chat_model, extract_json_from_text


# ============================================================
#  FLASHCARD DATA LAYER (JSON file-based SRS)
# ============================================================

def _get_deck_path(username: str, subject_id: str) -> str:
    """Get path to user's flashcard deck file"""
    deck_dir = f"user_data/{username}/flashcards"
    os.makedirs(deck_dir, exist_ok=True)
    return os.path.join(deck_dir, f"{subject_id}_deck.json")


def _load_deck(username: str, subject_id: str) -> dict:
    """Load a flashcard deck from disk"""
    path = _get_deck_path(username, subject_id)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"cards": [], "stats": {"total_reviews": 0, "mastered": 0}}


def _save_deck(username: str, subject_id: str, deck: dict):
    """Save a flashcard deck to disk"""
    path = _get_deck_path(username, subject_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)


def _srs_next_review(card: dict, knew_it: bool) -> dict:
    """
    SM-2 inspired Spaced Repetition algorithm.
    Updates interval and next_review timestamp.
    """
    interval = card.get("interval", 1)  # in minutes for demo (days in prod)
    ease = card.get("ease", 2.5)
    reps = card.get("reps", 0)

    if knew_it:
        reps += 1
        if reps == 1:
            interval = 1
        elif reps == 2:
            interval = 6
        else:
            interval = int(interval * ease)
        ease = max(1.3, ease + 0.1)
    else:
        reps = 0
        interval = 1
        ease = max(1.3, ease - 0.2)

    card["interval"] = interval
    card["ease"] = round(ease, 2)
    card["reps"] = reps
    card["last_reviewed"] = time.time()
    card["next_review"] = time.time() + (interval * 60)  # minutes for demo
    return card


# ============================================================
#  AI FLASHCARD GENERATION
# ============================================================

async def generate_flashcards_for_node(node_content: str, node_title: str, count: int = 10) -> list:
    """Use Gemini AI to generate flashcards from node content"""
    model = get_chat_model()
    if not model:
        return []

    prompt = f"""Bạn là hệ thống sinh flashcard giáo dục. Từ nội dung bài học dưới đây, 
hãy tạo CHÍNH XÁC {count} flashcards dưới dạng JSON array.

Nội dung bài học: "{node_title}"
{node_content}

OUTPUT FORMAT (JSON array, KHÔNG có text khác):
[
  {{"front": "Thuật ngữ / Câu hỏi ngắn", "back": "Định nghĩa / Câu trả lời ngắn gọn"}},
  ...
]

QUY TẮC:
- front: Câu hỏi hoặc thuật ngữ ngắn gọn (1-2 câu)
- back: Định nghĩa hoặc giải thích (2-3 câu)
- Đa dạng: thuật ngữ, so sánh, ví dụ, ứng dụng
- Ngôn ngữ: Tiếng Việt
- PHẢI trả về đúng {count} thẻ
"""

    try:
        response = await run.io_bound(model.generate_content, prompt)
        text = response.text

        # Parse JSON array from response
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            cards_raw = json.loads(match.group(0))
            cards = []
            for i, c in enumerate(cards_raw):
                if isinstance(c, dict) and 'front' in c and 'back' in c:
                    cards.append({
                        "id": f"card_{int(time.time())}_{i}",
                        "front": c["front"],
                        "back": c["back"],
                        "interval": 1,
                        "ease": 2.5,
                        "reps": 0,
                        "last_reviewed": 0,
                        "next_review": 0,
                    })
            return cards
    except Exception as e:
        print(f"[Flashcard] AI generation error: {e}")
    return []


# ============================================================
#  FLASHCARD UI CSS
# ============================================================

FLASHCARD_CSS = """
<style>
.flashcard-container {
    perspective: 1200px;
    width: 480px;
    height: 320px;
}
.flashcard-inner {
    position: relative;
    width: 100%;
    height: 100%;
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    transform-style: preserve-3d;
}
.flashcard-inner.flipped {
    transform: rotateY(180deg);
}
.flashcard-front, .flashcard-back {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
    border-radius: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px;
    box-sizing: border-box;
}
.flashcard-front {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%);
    color: white;
    border: 2px solid rgba(99, 102, 241, 0.3);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1);
}
.flashcard-back {
    background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%);
    color: white;
    transform: rotateY(180deg);
    border: 2px solid rgba(16, 185, 129, 0.3);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1);
}
@keyframes swipe-left {
    0% { transform: translateX(0) rotate(0); opacity: 1; }
    100% { transform: translateX(-200px) rotate(-15deg); opacity: 0; }
}
@keyframes swipe-right {
    0% { transform: translateX(0) rotate(0); opacity: 1; }
    100% { transform: translateX(200px) rotate(15deg); opacity: 0; }
}
@keyframes card-enter {
    0% { transform: scale(0.8) translateY(30px); opacity: 0; }
    100% { transform: scale(1) translateY(0); opacity: 1; }
}
.swipe-left { animation: swipe-left 0.4s ease-in forwards; }
.swipe-right { animation: swipe-right 0.4s ease-in forwards; }
.card-enter { animation: card-enter 0.4s ease-out forwards; }
</style>
"""


# ============================================================
#  FLASHCARD PAGE REGISTRATION
# ============================================================

def register_flashcard_page():
    @ui.page('/flashcards/{subject_id}')
    async def flashcard_page(subject_id: str):
        username = app.storage.user.get('username')
        user_id = app.storage.user.get('id')
        if not username:
            ui.label('Vui lòng đăng nhập').classes('text-red-500 font-bold p-8')
            return

        ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">')
        ui.add_head_html(FLASHCARD_CSS)
        ui.query('body').classes('bg-[#0d1117] font-[Inter]')

        # Load tree data
        tree_file = f"user_data/{username}/trees/{subject_id}.json"
        if not os.path.exists(tree_file):
            ui.label('Không tìm thấy dữ liệu môn học.').classes('text-red-400 text-xl p-8')
            return

        with open(tree_file, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)

        nodes = tree_data.get('micro_nodes', []) + tree_data.get('macro_nodes', [])
        course_name = tree_data.get('course_name', 'Môn học')

        # State
        state = {
            "current_index": 0,
            "cards": [],
            "knew_count": 0,
            "didnt_know_count": 0,
            "is_flipped": False,
            "session_active": False,
        }

        with ui.column().classes('w-full max-w-2xl mx-auto p-6 min-h-screen items-center'):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-6'):
                ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/app')).props('flat round color=grey')
                ui.label('📚 Flashcards').classes('text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400')
                ui.label(course_name).classes('text-sm text-gray-500')

            main_area = ui.column().classes('w-full flex-grow items-center justify-center')

            # --- NODE SELECTION LOBBY ---
            def render_lobby():
                state["session_active"] = False
                main_area.clear()
                with main_area:
                    ui.label('Chọn chủ đề để tạo Flashcards').classes('text-xl font-bold text-white mb-6')

                    # Group nodes by chapter
                    chapters = {}
                    for n in nodes:
                        chap = n.get('chapter', 'Khác')
                        if chap not in chapters:
                            chapters[chap] = []
                        chapters[chap].append(n)

                    with ui.column().classes('w-full gap-3 max-w-lg'):
                        # Quick: Generate from ALL nodes
                        with ui.card().classes(
                            'w-full p-4 bg-gradient-to-r from-indigo-900 to-purple-900 rounded-xl '
                            'cursor-pointer hover:scale-[1.02] transition-all border border-indigo-700'
                        ).on('click', lambda: start_session_all()):
                            with ui.row().classes('items-center gap-3'):
                                ui.icon('auto_awesome', color='yellow').classes('text-3xl')
                                with ui.column().classes('gap-0'):
                                    ui.label('⚡ Tạo Flashcards từ toàn bộ').classes('font-bold text-white')
                                    ui.label(f'{len(nodes)} nodes → AI sinh 20 thẻ').classes('text-xs text-indigo-300')

                        # Per chapter
                        for chap_name, chap_nodes in chapters.items():
                            with ui.card().classes(
                                'w-full p-3 bg-gray-800/50 rounded-xl cursor-pointer hover:bg-gray-700/50 '
                                'transition-all border border-gray-700'
                            ).on('click', lambda cn=chap_nodes, name=chap_name: start_session_chapter(cn, name)):
                                with ui.row().classes('items-center gap-3'):
                                    ui.icon('folder', color='blue-400').classes('text-xl')
                                    ui.label(chap_name).classes('font-medium text-gray-200 text-sm')
                                    ui.label(f'{len(chap_nodes)} nodes').classes('text-xs text-gray-500 ml-auto')

            async def start_session_all():
                """Generate flashcards from all nodes"""
                main_area.clear()
                with main_area:
                    with ui.column().classes('items-center gap-4'):
                        ui.spinner('dots', size='xl', color='indigo')
                        ui.label('AI đang sinh Flashcards...').classes('text-indigo-300 text-sm animate-pulse')

                all_content = "\n".join([
                    f"- {n.get('title', '')}: {n.get('content', '')[:200]}" for n in nodes[:30]
                ])
                cards = await generate_flashcards_for_node(all_content, course_name, count=20)
                if cards:
                    state["cards"] = cards
                    state["current_index"] = 0
                    state["knew_count"] = 0
                    state["didnt_know_count"] = 0
                    render_card_session()
                else:
                    main_area.clear()
                    with main_area:
                        ui.label('❌ Không thể tạo flashcards. Thử lại?').classes('text-red-400')
                        ui.button('Thử lại', on_click=render_lobby).props('color=blue outline')

            async def start_session_chapter(chapter_nodes, chapter_name):
                """Generate flashcards for a specific chapter"""
                main_area.clear()
                with main_area:
                    with ui.column().classes('items-center gap-4'):
                        ui.spinner('dots', size='xl', color='indigo')
                        ui.label(f'AI đang sinh Flashcards cho {chapter_name}...').classes('text-indigo-300 text-sm animate-pulse')

                content = "\n".join([
                    f"- {n.get('title', '')}: {n.get('content', '')[:300]}" for n in chapter_nodes[:20]
                ])
                cards = await generate_flashcards_for_node(content, chapter_name, count=min(15, len(chapter_nodes) * 2))
                if cards:
                    state["cards"] = cards
                    state["current_index"] = 0
                    state["knew_count"] = 0
                    state["didnt_know_count"] = 0
                    render_card_session()
                else:
                    main_area.clear()
                    with main_area:
                        ui.label('❌ Không thể tạo flashcards.').classes('text-red-400')
                        ui.button('Quay lại', on_click=render_lobby).props('color=blue outline')

            # --- CARD SESSION ---
            def render_card_session():
                state["session_active"] = True
                state["is_flipped"] = False
                idx = state["current_index"]
                cards = state["cards"]
                total = len(cards)

                if idx >= total:
                    render_results()
                    return

                card = cards[idx]
                main_area.clear()

                with main_area:
                    # Progress
                    with ui.row().classes('w-full max-w-lg items-center justify-between mb-4'):
                        ui.label(f'Thẻ {idx + 1} / {total}').classes('text-sm text-gray-400 font-bold')
                        with ui.row().classes('gap-2'):
                            ui.label(f'✅ {state["knew_count"]}').classes('text-green-400 text-sm font-bold')
                            ui.label(f'❌ {state["didnt_know_count"]}').classes('text-red-400 text-sm font-bold')

                    # Progress bar
                    progress = (idx / total) * 100
                    with ui.element('div').classes('w-full max-w-lg bg-gray-800 rounded-full h-2 mb-6'):
                        ui.element('div').classes(
                            'bg-gradient-to-r from-indigo-500 to-cyan-500 h-2 rounded-full transition-all duration-500'
                        ).style(f'width:{progress}%')

                    # Flashcard
                    card_wrapper = ui.element('div').classes('flashcard-container card-enter cursor-pointer')

                    with card_wrapper:
                        inner = ui.element('div').classes('flashcard-inner')

                        with inner:
                            # Front
                            with ui.element('div').classes('flashcard-front'):
                                ui.label('💡 Thuật ngữ').classes('text-xs text-indigo-300 font-bold tracking-widest mb-4 uppercase')
                                ui.label(card["front"]).classes('text-xl font-bold text-center leading-relaxed')
                                ui.label('Nhấp để lật thẻ →').classes('text-xs text-indigo-400 mt-4 italic')

                            # Back
                            with ui.element('div').classes('flashcard-back'):
                                ui.label('📖 Giải thích').classes('text-xs text-emerald-300 font-bold tracking-widest mb-4 uppercase')
                                ui.label(card["back"]).classes('text-base text-center leading-relaxed')

                    def toggle_flip():
                        state["is_flipped"] = not state["is_flipped"]
                        if state["is_flipped"]:
                            inner.classes(add='flipped')
                        else:
                            inner.classes(remove='flipped')

                    card_wrapper.on('click', toggle_flip)

                    # Action Buttons
                    with ui.row().classes('mt-8 gap-6'):
                        ui.button('❌ Chưa biết', on_click=lambda: handle_response(False)).classes(
                            'bg-red-600/80 text-white px-8 py-3 rounded-xl font-bold text-lg '
                            'hover:bg-red-500 transition-all shadow-lg'
                        ).props('no-caps')

                        ui.button("✅ Đã biết", on_click=lambda: handle_response(True)).classes(
                            'bg-green-600/80 text-white px-8 py-3 rounded-xl font-bold text-lg '
                            'hover:bg-green-500 transition-all shadow-lg'
                        ).props('no-caps')

                    # Keyboard shortcuts hint
                    ui.label('💡 Space = Lật thẻ | ← Chưa biết | → Đã biết').classes('text-xs text-gray-600 mt-6')

                    # Keyboard shortcuts
                    ui.run_javascript('''
                        document.onkeydown = function(e) {
                            if (e.key === ' ' || e.key === 'Enter') {
                                document.querySelector('.flashcard-container').click();
                                e.preventDefault();
                            }
                        };
                    ''')

            def handle_response(knew_it: bool):
                """Handle user's response to a card"""
                idx = state["current_index"]
                card = state["cards"][idx]

                # Update SRS
                _srs_next_review(card, knew_it)

                if knew_it:
                    state["knew_count"] += 1
                else:
                    state["didnt_know_count"] += 1

                state["current_index"] += 1
                render_card_session()

            # --- RESULTS ---
            def render_results():
                main_area.clear()
                total = len(state["cards"])
                knew = state["knew_count"]
                didnt = state["didnt_know_count"]
                pct = (knew / max(1, total)) * 100

                # Gamification XP
                if user_id:
                    try:
                        from gamification.gamification_ui import process_gamification_event
                        # Award XP based on performance
                        for _ in range(knew):
                            process_gamification_event(user_id, 'quiz_correct')
                    except Exception:
                        pass

                with main_area:
                    with ui.card().classes(
                        'w-full max-w-md p-8 rounded-3xl bg-gradient-to-br from-gray-900 to-gray-800 '
                        'border border-gray-700 shadow-2xl text-center'
                    ):
                        # Trophy
                        trophy = '🏆' if pct >= 80 else '⭐' if pct >= 60 else '💪'
                        ui.html(f'<div style="font-size:72px;">{trophy}</div>').classes('mb-4')

                        ui.label('Phiên học hoàn tất!').classes('text-2xl font-extrabold text-white mb-2')

                        with ui.row().classes('justify-center gap-8 my-6'):
                            with ui.column().classes('items-center'):
                                ui.label(f'{knew}').classes('text-4xl font-extrabold text-green-400')
                                ui.label('Đã biết').classes('text-xs text-gray-400')
                            with ui.column().classes('items-center'):
                                ui.label(f'{didnt}').classes('text-4xl font-extrabold text-red-400')
                                ui.label('Chưa biết').classes('text-xs text-gray-400')
                            with ui.column().classes('items-center'):
                                ui.label(f'{pct:.0f}%').classes('text-4xl font-extrabold text-cyan-400')
                                ui.label('Chính xác').classes('text-xs text-gray-400')

                        # Review cards you didn't know
                        didnt_know_cards = [c for c in state["cards"] if c.get("reps", 0) == 0]
                        if didnt_know_cards:
                            ui.label(f'📋 {len(didnt_know_cards)} thẻ cần ôn lại').classes('text-sm text-amber-400 mb-4')
                            ui.button('🔄 Ôn lại thẻ chưa biết', on_click=lambda: restart_weak()).classes(
                                'w-full bg-amber-600 text-white font-bold py-3 rounded-xl mb-3'
                            ).props('no-caps')

                        ui.button('🏠 Quay lại', on_click=lambda: ui.navigate.to('/app')).classes(
                            'w-full bg-indigo-600 text-white font-bold py-3 rounded-xl'
                        ).props('no-caps')

            def restart_weak():
                """Restart session with only cards the user didn't know"""
                weak_cards = [c for c in state["cards"] if c.get("reps", 0) == 0]
                if weak_cards:
                    state["cards"] = weak_cards
                    state["current_index"] = 0
                    state["knew_count"] = 0
                    state["didnt_know_count"] = 0
                    render_card_session()

            # Start
            render_lobby()

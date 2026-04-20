# advanced_practice.py
"""
Advanced Practice Modes
- Marathon: Endless questions from all nodes in a subject until user stops.
- Weak Focus: Only generate questions from nodes with mastery < 50%.
"""

from nicegui import ui, run, app
import json
import os
import time
from gemini_helper import get_chat_model
from knowledge_tracing import update_node_mastery
from database import Session, engine, select, KnowledgeState


async def generate_practice_question(content: str) -> dict:
    model = get_chat_model()
    if not model:
        return None

    prompt = f"""Tạo 1 câu hỏi trắc nghiệm 4 đáp án thật hóc búa để ôn tập nội dung này:
{content}

OUTPUT FORMAT (JSON array):
[{{
    "question": "Câu hỏi?",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct": "A",
    "explanation": "Giải thích chi tiết tại sao đúng/sai"
}}]"""
    try:
        response = await run.io_bound(model.generate_content, prompt)
        text = response.text
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            questions = json.loads(match.group(0))
            if questions and len(questions) > 0:
                return questions[0]
    except Exception as e:
        print(f"[Practice] AI error: {e}")
    return None


def register_advanced_practice_page():
    @ui.page('/practice/{subject_id}/{mode}')
    async def practice_page(subject_id: str, mode: str):
        username = app.storage.user.get('username')
        user_id = app.storage.user.get('id')
        if not username:
            ui.label('Vui lòng đăng nhập').classes('text-red-500 font-bold p-8')
            return

        ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">')
        ui.query('body').classes('bg-[#0d1117] font-[Inter] overflow-hidden')

        # Load tree
        tree_file = f"user_data/{username}/trees/{subject_id}.json"
        if not os.path.exists(tree_file):
            ui.label('Không tìm thấy dữ liệu.').classes('text-red-400 p-8')
            return

        with open(tree_file, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)

        all_nodes = tree_data.get('micro_nodes', []) + tree_data.get('macro_nodes', [])

        # Filter nodes based on mode
        target_nodes = []
        if mode == 'weak_focus':
            with Session(engine) as session:
                for n in all_nodes:
                    stmt = select(KnowledgeState).where(
                        (KnowledgeState.user_id == user_id) & 
                        (KnowledgeState.concept_id == n['id'])
                    )
                    kstate = session.exec(stmt).first()
                    # ELO 1200 is base. Mastery ~50% is around ELO 1600 depending on formula.
                    # We approximate by just picking nodes with ELO < 1500
                    if not kstate or kstate.elo_rating < 1500:
                        target_nodes.append(n)
            if not target_nodes:
                # If no weak nodes, pick random ones to not leave it empty
                target_nodes = all_nodes[:5]
        else:
            # Marathon
            target_nodes = all_nodes

        import random
        random.shuffle(target_nodes)

        state = {
            "node_queue": target_nodes,
            "current_index": 0,
            "correct": 0,
            "wrong": 0,
            "streak": 0,
            "is_loading": False
        }

        with ui.column().classes('w-full h-screen max-w-3xl mx-auto p-6 items-center'):
            mode_name = "🎯 Tập Trung Điểm Yếu" if mode == 'weak_focus' else "🏃 Marathon Không Giới Hạn"
            
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/app')).props('flat round color=grey')
                ui.label(mode_name).classes('text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-cyan-500')
                
                with ui.row().classes('gap-4'):
                    ui.label().bind_text_from(state, 'correct', backward=lambda x: f'✅ {x}').classes('text-green-400 font-bold')
                    ui.label().bind_text_from(state, 'wrong', backward=lambda x: f'❌ {x}').classes('text-red-400 font-bold')
                    ui.label().bind_text_from(state, 'streak', backward=lambda x: f'🔥 {x}').classes('text-orange-400 font-bold')

            main_area = ui.column().classes('w-full flex-grow items-center justify-center')

            async def load_next_question():
                if state["current_index"] >= len(state["node_queue"]):
                    # End of queue
                    main_area.clear()
                    with main_area:
                        from gamification.gamification_ui import CONFETTI_JS
                        ui.run_javascript(CONFETTI_JS)
                        ui.label('🎉 HOÀN THÀNH PHIÊN TẬP!').classes('text-4xl font-extrabold text-white mb-6 animate-bounce')
                        ui.button('Quay lại Home', on_click=lambda: ui.navigate.to('/app')).classes('bg-green-600 text-white font-bold py-3 px-8 rounded-xl')
                    return

                # Load question
                node = state["node_queue"][state["current_index"]]
                state["is_loading"] = True
                main_area.clear()
                with main_area:
                    with ui.column().classes('items-center gap-4'):
                        ui.spinner('dots', size='xl', color='cyan')
                        ui.label(f'Đang phân tích Node: {node.get("title")}...').classes('text-cyan-300 italic')

                content = node.get('content', '')
                base_alpha = node.get('alpha_base', 10)
                q_data = await generate_practice_question(content)
                state["is_loading"] = False

                if not q_data:
                    state["current_index"] += 1
                    await load_next_question()
                    return

                render_question(node, q_data, base_alpha)

            def render_question(node, q, base_alpha):
                main_area.clear()
                with main_area:
                    # Progress relative to queue
                    pct = ((state["current_index"]) / max(1, len(state["node_queue"]))) * 100
                    with ui.element('div').classes('w-full max-w-2xl bg-gray-800 rounded-full h-2 mb-6'):
                        ui.element('div').classes('bg-cyan-500 h-2 rounded-full transition-all').style(f'width:{pct}%')

                    ui.label(f"Node: {node.get('title')}").classes('text-sm text-cyan-500 font-bold tracking-widest uppercase mb-2')
                    
                    with ui.card().classes('w-full max-w-2xl p-6 rounded-2xl bg-gray-800/80 border border-gray-700 mb-6'):
                        ui.label(q["question"]).classes('text-xl font-bold text-white leading-relaxed')

                    options_container = ui.column().classes('w-full max-w-2xl gap-3')
                    result_container = ui.column().classes('w-full max-w-2xl mt-4')

                    with options_container:
                        btn_map = {}
                        for key in ['A', 'B', 'C', 'D']:
                            if key in q.get('options', {}):
                                opt_text = q['options'][key]
                                btn = ui.button(
                                    f'{key}. {opt_text}',
                                    on_click=lambda e, k=key: evaluate_answer(k, q["correct"], q["explanation"], node["id"], base_alpha, btn_map, result_container, options_container)
                                ).classes(
                                    'w-full text-left px-4 py-4 bg-gray-700/50 text-gray-200 rounded-xl '
                                    'border border-gray-600 hover:border-cyan-500 hover:bg-gray-600/50 transition-all font-medium text-lg'
                                ).props('no-caps align=left')
                                btn_map[key] = btn

            async def evaluate_answer(selected, correct_key, explanation, node_id, base_alpha, btn_map, result_container, options_container):
                is_correct = (selected == correct_key)
                if is_correct:
                    state["correct"] += 1
                    state["streak"] += 1
                    from gamification.gamification_ui import CONFETTI_JS
                    ui.run_javascript(CONFETTI_JS)
                else:
                    state["wrong"] += 1
                    state["streak"] = 0

                # Colorize options
                for key, btn in btn_map.items():
                    btn.props('disable')
                    if key == correct_key:
                        btn.classes(remove='bg-gray-700/50 border-gray-600 hover:border-cyan-500', add='bg-green-900/50 border-green-500 text-green-200')
                    elif key == selected:
                        btn.classes(remove='bg-gray-700/50 border-gray-600 hover:border-cyan-500', add='bg-red-900/50 border-red-500 text-red-200')
                    else:
                        btn.classes(add='opacity-30')

                # Update Mastery & XP
                await run.io_bound(update_node_mastery, username, subject_id, node_id, is_correct, base_alpha)
                if user_id:
                    try:
                        from gamification.gamification_ui import process_gamification_event
                        process_gamification_event(user_id, 'quiz_correct' if is_correct else 'quiz_wrong')
                    except Exception:
                        pass

                with result_container:
                    if is_correct:
                         ui.label('🎉 CHÍNH XÁC!').classes('text-2xl font-bold text-green-400 mb-2')
                    else:
                         ui.label('💥 SAI MẤT RỒI!').classes('text-2xl font-bold text-red-400 mb-2')
                         
                    ui.markdown(f"**Giải thích:**\n{explanation}").classes('text-gray-300 bg-cyan-900/20 p-4 rounded-xl border border-cyan-800 w-full mb-4')
                    
                    def go_next():
                        state["current_index"] += 1
                        ui.timer(0, load_next_question, once=True)
                        
                    ui.button('CÂU TIẾP THEO ➡', on_click=go_next).classes('w-full bg-cyan-600 text-white font-bold py-3 rounded-xl shadow-lg').props('icon-right=arrow_forward')

            # Start automatically
            ui.timer(0, load_next_question, once=True)


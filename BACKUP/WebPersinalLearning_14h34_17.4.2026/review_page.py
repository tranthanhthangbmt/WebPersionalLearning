from nicegui import ui, app
import json
import os
from services.spaced_repetition import get_due_reviews_today, update_review_schedule

def register_review_page():
    @ui.page('/review/{subject_id}')
    async def review_page(subject_id: str):
        username = app.storage.user.get('username')
        user_id = app.storage.user.get('id')
        if not username:
            ui.label('Vui lòng đăng nhập').classes('text-red-500 font-bold p-8')
            return

        ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">')
        ui.query('body').classes('bg-[#0d1117] font-[Inter]')

        # Load tree to get node content
        tree_file = f"user_data/{username}/trees/{subject_id}.json"
        if not os.path.exists(tree_file):
             ui.label('Không tìm thấy dữ liệu cây tri thức.').classes('text-red-400 p-8')
             return

        with open(tree_file, 'r', encoding='utf-8') as f:
             tree_data = json.load(f)

        nodes = {n['id']: n for n in tree_data.get('micro_nodes', []) + tree_data.get('macro_nodes', [])}
        course_name = tree_data.get('course_name', 'Môn học')

        # Get pending reviews
        reviews = get_due_reviews_today(user_id, subject_id)
        
        # State
        state = {
             "queue": reviews,
             "current_index": 0,
             "is_flipped": False
        }

        with ui.column().classes('w-full max-w-2xl mx-auto p-6 min-h-screen items-center'):
            with ui.row().classes('w-full items-center justify-between mb-8'):
                ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/app')).props('flat round color=grey')
                ui.label(f'🔄 Ôn Tập: {course_name}').classes('text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500')
                
                # Badge
                ui.badge(f"{len(reviews)} thẻ", color='red').classes('text-sm font-bold px-3 py-1')

            main_area = ui.column().classes('w-full flex-grow items-center justify-center')
            
            def render_flashcard():
                main_area.clear()
                
                if state["current_index"] >= len(state["queue"]):
                     with main_area:
                          from gamification.gamification_ui import CONFETTI_JS
                          ui.run_javascript(CONFETTI_JS)
                          
                          with ui.card().classes('items-center p-10 bg-gray-800 border border-gray-700 rounded-3xl text-center shadow-2xl'):
                               ui.icon('done_all', size='6rem', color='green')
                               ui.label('HOÀN TẤT ÔN TẬP').classes('text-3xl font-extrabold text-white mt-4 tracking-widest')
                               ui.label('Bạn đã dọn sạch danh sách đợi ôn tập của ngày hôm nay. Trí nhớ của bạn đang được củng cố rất tốt! 🧠').classes('mt-2 text-gray-400 max-w-sm')
                               ui.button('Quay về trang chính', on_click=lambda: ui.navigate.to('/app')).classes('mt-8 bg-purple-600 text-white px-8 py-3 rounded-xl font-bold').props('no-caps')
                     return
                
                rev_item = state["queue"][state["current_index"]]
                node_id = rev_item.node_id
                node_data = nodes.get(node_id, {})
                title = node_data.get('title', 'Unknown Node')
                content = node_data.get('content', 'Không có nội dung chi tiết để ôn tập.')
                
                with main_area:
                     # Progress
                     left = len(state["queue"]) - state["current_index"]
                     ui.label(f'Còn lại: {left} thẻ').classes('text-sm text-gray-500 font-bold mb-4')
                     
                     # Flashcard Container
                     card_container = ui.card().classes(
                          'w-full max-w-lg aspect-video flex-col items-center justify-center p-8 cursor-pointer '
                          'bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-3xl '
                          'shadow-xl hover:shadow-2xl transition-all relative group'
                     ).style('perspective: 1000px;')

                     with card_container:
                          # Nội dung mặt trước
                          front_col = ui.column().classes('items-center absolute inset-0 justify-center transition-all duration-500')
                          with front_col:
                               ui.icon('psychology_alt', size='3rem', color='purple').classes('mb-4 opacity-50 group-hover:scale-110 transition-transform')
                               ui.label(title).classes('text-3xl font-extrabold text-white text-center')
                               ui.label('Bấm vào để lật thẻ').classes('text-xs text-gray-500 mt-8 tracking-widest uppercase')
                          
                          # Nội dung mặt sau
                          back_col = ui.column().classes('items-center absolute inset-0 justify-center p-6 bg-gradient-to-tr from-purple-900/40 to-blue-900/40 opacity-0 pointer-events-none transition-all duration-500')
                          with back_col:
                               ui.label(title).classes('text-lg font-bold text-purple-300 mb-4 border-b border-purple-500/30 pb-2')
                               # Hiển thị nội dung
                               # Dùng scroll area để đề phòng content quá dài
                               with ui.scroll_area().classes('w-full flex-grow'):
                                    ui.markdown(content).classes('text-white text-lg leading-relaxed text-left')
                     
                     # Buttons
                     btn_row = ui.row().classes('w-full max-w-lg justify-between mt-8 opacity-0 pointer-events-none transition-opacity duration-500')
                     with btn_row:
                          ui.button('Quên (1)', on_click=lambda: handle_rate(1, node_id)).classes('bg-red-600/80 hover:bg-red-500 text-white rounded-2xl flex-grow font-bold').props('no-caps')
                          ui.button('Khó (3)', on_click=lambda: handle_rate(3, node_id)).classes('bg-orange-600/80 hover:bg-orange-500 text-white rounded-2xl flex-grow font-bold').props('no-caps')
                          ui.button('Tốt (4)', on_click=lambda: handle_rate(4, node_id)).classes('bg-green-600/80 hover:bg-green-500 text-white rounded-2xl flex-grow font-bold').props('no-caps')
                          ui.button('Dễ (5)', on_click=lambda: handle_rate(5, node_id)).classes('bg-blue-600/80 hover:bg-blue-500 text-white rounded-2xl flex-grow font-bold').props('no-caps')

                     # Logic Lật thẻ
                     def flip():
                          state["is_flipped"] = True
                          front_col.classes(add='opacity-0 scale-95 pointer-events-none', remove='opacity-100')
                          back_col.classes(add='opacity-100 pointer-events-auto scale-100', remove='opacity-0 pointer-events-none scale-95')
                          btn_row.classes(add='opacity-100 pointer-events-auto', remove='opacity-0 pointer-events-none')
                          
                     card_container.on('click', flip)
                     
            def handle_rate(quality, node_id):
                 """Rate the card and advance"""
                 if not state["is_flipped"]:
                      return
                      
                 # Cập nhật SM-2
                 update_review_schedule(user_id, subject_id, node_id, quality)
                 
                 # Gamification points?
                 try:
                      from gamification.gamification_ui import process_gamification_event
                      if quality >= 4:
                           process_gamification_event(user_id, 'quiz_correct')
                 except Exception:
                      pass
                      
                 # Next card
                 state["current_index"] += 1
                 state["is_flipped"] = False
                 render_flashcard()

            render_flashcard()

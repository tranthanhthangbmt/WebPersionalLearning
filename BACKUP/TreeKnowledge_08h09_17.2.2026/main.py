from nicegui import ui, app, run
from data_manager import data_manager
from pkt_engine import StudentState
from bio_battery import BioBattery
from gemini_helper import extract_json_from_text, build_system_prompt, get_gemini_api_key
import google.generativeai as genai
from database import create_db_and_tables, create_user, get_user_by_username
import os
import asyncio

from utils import get_video_url


from services.prediction_service import prediction_service
from services.rag_service import advanced_rag
from services.task_broker import task_broker
from visuals.dynamic_graph import render_dynamic_tree
from xai_engine import explain_recommendation

# Create DB
create_db_and_tables()

# Serve local audio files
app.add_static_files('/audio', os.path.join(os.getcwd(), 'DB', 'audio'))

# Cấu hình Gemini
from gemini_helper import get_gemini_api_key, get_chat_model

GOOGLE_API_KEY = get_gemini_api_key()
genai.configure(api_key=GOOGLE_API_KEY)

# Use robust model selector
model = get_chat_model()

# Start Task Broker
app.on_startup(task_broker.start_worker)

# Main Page
@ui.page('/')
async def main_page():
    # User Mock Login
    user = get_user_by_username("sv01")
    if not user:
        user = create_user("sv01", "password", "Sinh Vien 01")
    
    app.storage.user['id'] = user.id
    app.storage.user['username'] = user.username

    # Initialize Student State
    if 'student_state_data' in app.storage.user:
        # Hydrate from dict
        state = StudentState.from_dict(app.storage.user['student_state_data'])
    else:
        # New State
        state = StudentState(user.id)
        app.storage.user['student_state_data'] = state.to_dict()
    
    # Function to persist state
    def save_state():
        app.storage.user['student_state_data'] = state.to_dict()

    # --- UI Components ---
    # --- UI Components ---
    # Flat header design (no border, no shadow)
    with ui.header().classes(replace='row items-center bg-white text-slate-800 p-2 h-[60px] z-20') as header:
        ui.label('PKT Bio-Tutor').classes('text-xl font-bold text-blue-600 mr-4')
        
        # --- TABS IN HEADER ---
        with ui.tabs().classes('w-auto justify-center mr-4') as tabs:
            tab_knowledge = ui.tab('Kiến Thức', icon='hub')
            tab_video = ui.tab('Video', icon='movie')
            tab_quiz = ui.tab('Quiz', icon='quiz')

        # --- DYNAMIC LESSON TITLE IN HEADER ---
        header_lesson_container = ui.row().classes('items-center gap-2 flex-grow overflow-hidden')
        # Will be populated in load_lesson_ui

        # Prediction Label
        prediction_label = ui.label('').classes('text-sm font-bold text-blue-700 mr-4 whitespace-nowrap')

        # Component Pin Sinh học
        ui.label('Bio:').classes('text-xs mr-1 text-gray-500')
        battery = BioBattery(ui.row())
        
        # Avatar & User Info
        with ui.row().classes('items-center ml-4'):
            ui.avatar(icon='person', color='blue-100', text_color='blue-600').props('size=sm')
            ui.label(user.full_name).classes('font-bold text-sm hidden md:block')

    # Hàm cập nhật Dashboard loop
    def update_ui_loop():
        battery.update(state.current_fatigue)
        if graph_container: # Update graph if needed or periodically
             pass 

    ui.timer(1.0, update_ui_loop)

    # UI Elements references
    chat_container = None
    loading_spinner = None
    graph_container = None
    video_container = None
    quiz_container = None
    # tabs, tab_video, etc. are defined in header above, do not reset them here!
    # prediction_label is defined in header above
    # header_lesson_container is defined in header above (replaced video_header_row)

    # Hàm xử lý Chat với Advanced RAG
    async def chat_response():
        user_msg = input_box.value
        if not user_msg: return
        
        with chat_container:
            ui.chat_message(user_msg, sent=True)
        input_box.value = ''
        loading_spinner.visible = True
        
        try:
            if rag_switch.value:
                # Use Advanced RAG
                # Note: student_state is passed but not currently used in the provided rag_service code
                result = await advanced_rag.answer_with_citation(user.id, user_msg, state.to_dict())
                answer = result['answer']
                sources = result['sources']
            else:
                 # Direct Chat
                response = await run.io_bound(model.generate_content, user_msg)
                answer = response.text
                sources = []

            with chat_container:
                msg = ui.chat_message(answer, sent=False, avatar='https://robohash.org/ai')
                with msg:
                    if sources:
                        ui.separator().classes('my-2')
                        ui.label('Nguồn tham khảo:').classes('text-xs font-bold text-gray-500')
                        with ui.row().classes('gap-1'):
                            seen = set()
                            for src in sources:
                                key = f"{src['source']}-p{src['page']}"
                                if key not in seen:
                                    ui.chip(f"{src['source'][:10]}... (Tr.{src['page']})", icon='description').props('dense outline')
                                    seen.add(key)
        except Exception as e:
            with chat_container:
                ui.chat_message(f"Error: {str(e)}", sent=False)
        
        loading_spinner.visible = False

        # --- Old Logic for Interaction Processing (Simplified for RAG context) ---
        # In a real app, you might want Gemini to classify if the chat was a quiz answer or just a question.
        # For now, we assume chat is mostly Q&A. Quiz answers are handled via buttons.

    # Content Loading
    def load_lesson_ui(concept_id):
        state.current_concept_id = concept_id
        save_state()
        lesson_data = data_manager.get_lesson(concept_id)
        
        # Calculate Prediction
        win_prob = prediction_service.predict_next_performance(user.id, concept_id)
        
        # Switch to Video Tab
        if tabs and tab_video:
            tabs.value = tab_video

        # Update Labels
        if lesson_label_quiz: lesson_label_quiz.text = lesson_data['metadata']['concept_name']
        
        # --- UPDATE HEADER PREDICTION ---
        if prediction_label:
            prediction_label.text = f"Dự đoán: {int(win_prob*100)}%"

        # --- UPDATE GLOBAL HEADER (Title + Why) ---
        if header_lesson_container:
            header_lesson_container.clear()
            with header_lesson_container:
                 # Truncate title if too long for header
                 title = lesson_data['metadata']['concept_name']
                 if len(title) > 50: title = title[:47] + "..."
                 
                 ui.label(title).classes('text-lg font-bold text-gray-800 whitespace-nowrap overflow-hidden text-ellipsis')
                 
                 with ui.button(icon='help', color='blue-1').props('flat round dense').tooltip('Tại sao gợi ý này?'):
                      with ui.menu().classes('bg-white p-4 max-w-lg shadow-xl border'):
                          ui.label('Tại sao gợi ý bài này?').classes('font-bold text-lg mb-2 text-blue-600')
                          ui.markdown(explain_recommendation(concept_id, state)).classes('text-sm text-gray-700')

        # --- LOAD VIDEO ---
        if video_container:
            video_container.clear()
            with video_container:
                video_url = get_video_url(lesson_data['metadata']['concept_name'])
                if video_url:
                     # Overlay Button
                     ui.button(icon='open_in_new', on_click=lambda: ui.open(video_url, new_tab=True)) \
                        .classes('absolute top-4 right-4 z-10 bg-white text-blue-600 opacity-80 hover:opacity-100').props('flat round dense').tooltip('Mở trong tab mới')
                     
                     ui.element('iframe').props(f'src="{video_url}" allowfullscreen').classes('w-full h-full border-none bg-black')
                else:
                     ui.label("Video chưa khả dụng cho bài học này.").classes('italic text-gray-500 m-4')

        # --- LOAD QUIZ ---
        if quiz_container:
            quiz_container.clear()
            with quiz_container:
                questions = lesson_data.get('questions', [])
                if not questions:
                    ui.label("Chưa có câu hỏi cho bài này.").classes('italic text-gray-500')
                else:
                    # --- QUIZ STATE MANAGEMENT ---
                    class QuizController:
                        def __init__(self, questions, state_ref):
                            self.questions = questions
                            self.current_index = 0
                            self.state_ref = state_ref
                            
                            # Load history for current concept
                            cid = self.state_ref.current_concept_id
                            if cid not in self.state_ref.quiz_history:
                                self.state_ref.quiz_history[cid] = {}
                            
                            # Convert string keys back to int if needed
                            self.user_answers = {}
                            if cid in self.state_ref.quiz_history:
                                for k, v in self.state_ref.quiz_history[cid].items():
                                    self.user_answers[int(k)] = v

                            self.container = None
                            self.palette_container = None
                            self.q_card = None
                            self.progress_bar = None
                            
                        def render(self):
                            with ui.row().classes('w-full items-start gap-6 no-wrap'):
                                # Left Column: Question Area
                                with ui.column().classes('w-3/4 flex-grow'):
                                    with ui.element('div').classes('w-full bg-gray-200 rounded-full h-2.5 mb-6'):
                                        self.progress_bar = ui.element('div').classes('bg-blue-600 h-2.5 rounded-full transition-all duration-300').style('width: 0%')
                                    self.container = ui.column().classes('w-full')
                                    self.render_current_question()
                                    
                                # Right Column: Question Palette (Sticky)
                                with ui.column().classes('w-1/4 flex-shrink-0 min-w-[280px] sticky top-4'):
                                    with ui.card().classes('w-full p-4 rounded-2xl shadow-lg border-t-4 border-blue-500 bg-white'):
                                        ui.label('Danh sách câu hỏi').classes('font-bold text-gray-800 mb-4 border-b pb-2')
                                        self.palette_container = ui.grid(columns=5).classes('gap-2 justify-center')
                                        self.render_palette()
                                        
                                        with ui.column().classes('mt-6 space-y-2 text-sm text-gray-600'):
                                            with ui.row().classes('items-center'):
                                                ui.element('div').classes('w-3 h-3 rounded-full bg-gray-200 mr-2')
                                                ui.label('Chưa làm')
                                            with ui.row().classes('items-center'):
                                                ui.element('div').classes('w-3 h-3 rounded-full bg-green-500 mr-2')
                                                ui.label('Đúng (có thể làm lại)')
                                            with ui.row().classes('items-center'):
                                                ui.element('div').classes('w-3 h-3 rounded-full bg-red-500 mr-2')
                                                ui.label('Sai (hãy thử lại)')
                                            with ui.row().classes('items-center'):
                                                ui.element('div').classes('w-3 h-3 rounded-full bg-blue-500 mr-2')
                                                ui.label('Đang chọn')

                        def render_palette(self):
                            self.palette_container.clear()
                            with self.palette_container:
                                for idx, _ in enumerate(self.questions):
                                    history = self.user_answers.get(idx, {})
                                    correct_count = history.get('correct', 0)
                                    wrong_count = history.get('wrong', 0)
                                    
                                    # Base Styles
                                    base_class = 'w-10 h-10 rounded-lg flex items-center justify-center font-bold text-sm transition-all duration-200'
                                    color_class = 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    
                                    # Status Color Priority
                                    status = None
                                    if correct_count > 0:
                                        status = 'correct'
                                        color_class = 'bg-green-500 text-white shadow-sm'
                                    elif wrong_count > 0:
                                        status = 'wrong'
                                        color_class = 'bg-red-500 text-white shadow-sm'
                                    
                                    # Override if currently selected (Blue selection)
                                    if idx == self.current_index and not status:
                                         color_class = 'bg-blue-600 text-white shadow-md'

                                    # Current Selection Indicator (Border/Ring)
                                    ring_class = ''
                                    if idx == self.current_index:
                                        if status: 
                                            ring_class = 'ring-4 ring-blue-300 transform scale-110 z-10'
                                        else:
                                            ring_class = 'ring-2 ring-blue-300 transform scale-105'

                                    msg = f"Câu {idx + 1}: Đúng {correct_count} | Sai {wrong_count}"
                                    if not status: msg = f"Câu {idx + 1}: Chưa làm"
                                        
                                    ui.button(str(idx + 1), on_click=lambda i=idx: self.jump_to(i)).classes(f'{base_class} {color_class} {ring_class}').tooltip(msg)

                        def render_current_question(self):
                            self.container.clear()
                            q = self.questions[self.current_index]
                            progress = ((self.current_index + 1) / len(self.questions)) * 100
                            self.progress_bar.style(f'width: {progress}%')
                            
                            history = self.user_answers.get(self.current_index, {})
                            correct_count = history.get('correct', 0)
                            wrong_count = history.get('wrong', 0)
                            
                            with self.container:
                                with ui.card().classes('w-full p-6 sm:p-8 rounded-2xl shadow-lg relative'):
                                    with ui.row().classes('justify-between items-center mb-6 w-full'):
                                        ui.label(f'Câu {self.current_index + 1}').classes('bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded')
                                        
                                        # Smart Status Badge
                                        if correct_count > 0:
                                            ui.label(f'Đã đúng {correct_count} lần').classes('bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded')
                                        elif wrong_count > 0:
                                            ui.label(f'Đã sai {wrong_count} lần - Hãy thử lại').classes('bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded')
                                        else:
                                            ui.label('Chưa hoàn thành').classes('text-sm font-medium text-gray-500')

                                    ui.label(q['content']).classes('text-xl sm:text-2xl font-semibold text-gray-800 mb-8 leading-relaxed')
                                    options_col = ui.column().classes('w-full space-y-4')
                                    
                                    audio_success = ui.audio('/audio/success.mp3').props('hidden')
                                    audio_fail = ui.audio('/audio/error.mp3').props('hidden')
                                    
                                    btn_map = {}
                                    explanation_ui = None
                                    # No longer locking "is_solved" based on correct answer. Always allow attempts.

                                    with options_col:
                                        for opt in q['options']:
                                            key = opt['key']
                                            text = opt['text']
                                            btn_props = 'outline text-left no-caps'
                                            btn_classes = 'w-full justify-start px-4 py-3 text-gray-700 hover:bg-gray-50 border-2 rounded-lg transition-all'
                                            
                                            # Highlight logic: 
                                            # User requested "reset to default" to allow redo.
                                            # So we DO NOT pre-highlight the answer, even if they solved it.
                                            # We only show the "Badge" at the top (implemented above).
                                            
                                            # if correct_count > 0 and key == q['correct_answer']:
                                            #    btn_classes += ' bg-green-50 border-green-500'
                                            #    btn_props = 'icon=check' 
                                            
                                            b = ui.button(f"{key}. {text}").props(btn_props).classes(btn_classes)
                                            # Always enabled for retry
                                            btn_map[key] = b
                                            
                                            if key == q['correct_answer']:
                                                explanation_ui = ui.column().classes('w-full bg-green-50 p-4 border-l-4 border-green-500 rounded-r mt-2 shadow-sm animate-fade')
                                                # Always hide initially for retry
                                                explanation_ui.classes('hidden')
                                                with explanation_ui:
                                                     ui.label('Giải thích:').classes('font-bold text-green-800 text-sm mb-1')
                                                     ui.markdown(q['explanation']).classes('text-sm text-gray-800')
                                    
                                    def make_handler(btn_map, correct_key, feedback_ui, audio_ok, audio_no, feedback_msg_label):
                                        def handler(e):
                                            sender = e.sender
                                            selected_key = sender.text.split('.')[0].strip()
                                            
                                            # Initialize history if empty
                                            cid = self.state_ref.current_concept_id
                                            if cid not in self.state_ref.quiz_history: self.state_ref.quiz_history[cid] = {}
                                            if str(self.current_index) not in self.state_ref.quiz_history[cid]:
                                                self.state_ref.quiz_history[cid][str(self.current_index)] = {'correct': 0, 'wrong': 0}
                                                
                                            # --- LOGIC UPDATE ---
                                            if selected_key == correct_key:
                                                audio_ok.play()
                                                feedback_msg_label.set_text('')
                                                feedback_msg_label.classes('hidden')
                                                
                                                # Update Stats
                                                self.state_ref.quiz_history[cid][str(self.current_index)]['correct'] += 1
                                                self.state_ref.update_elo(cid, True)
                                                
                                                if feedback_ui: feedback_ui.classes(remove='hidden')
                                                
                                                # Visuals for this attempt
                                                for key, btn in btn_map.items():
                                                    # Don't disable, just update styles
                                                    if key == correct_key:
                                                        btn.props('color=green-6 icon=check')
                                                        btn.classes(remove='text-gray-700 hover:bg-gray-50 border-gray-200', add='bg-green-100 border-green-500 text-green-800')
                                                    else:
                                                        # Reset others
                                                        btn.props(remove='color icon') # Properly remove props
                                                        btn.props('outline') # Restore outline
                                                        btn.classes(add='text-gray-700 hover:bg-gray-50 border-gray-200', remove='bg-red-100 border-red-500 text-red-800 bg-green-100 border-green-500 text-green-800')
                                            else:
                                                audio_no.play()
                                                # Update stats
                                                self.state_ref.quiz_history[cid][str(self.current_index)]['wrong'] += 1
                                                self.state_ref.update_elo(cid, False)
                                                
                                                # Visuals
                                                sender.props('color=red-6 icon=close')
                                                sender.classes(remove='text-gray-700 hover:bg-gray-50 border-gray-200', add='bg-red-100 border-red-500 text-red-800')
                                                feedback_msg_label.set_text('Sai rồi, hãy thử lại!')
                                                feedback_msg_label.classes(remove='hidden')

                                            # Save and Refresh
                                            save_state()
                                            # Sync local cache
                                            self.user_answers[self.current_index] = self.state_ref.quiz_history[cid][str(self.current_index)]
                                            
                                            # Re-render Palette to update counts/colors
                                            self.render_palette()
                                            # Don't re-render current question immediately to avoid flicker, just updated buttons
                                            # Unless we want to update the "Attempts" badge immediately? 
                                            # Let's re-render current question badge only? No, simplified: just re-render palette.
                                            # Actually, if we want to show "Correct: X+1", we need to re-render.
                                            # But full re-render resets the button states (animation).
                                            # Ideally, we just update the badge. But for now, re-rendering palette is enough feedback.
                                            
                                            # Re-render Palette to update counts/colors
                                            self.render_palette()
                                            
                                        return handler

                                    feedback_msg_label = ui.label('').classes('hidden text-red-600 font-bold mt-2 ml-1')
                                    
                                    # Always bind handlers to allow retries
                                    for k, b in btn_map.items():
                                        b.on_click(make_handler(btn_map, q['correct_answer'], explanation_ui, audio_success, audio_fail, feedback_msg_label))

                                    with ui.row().classes('w-full justify-between mt-8'):
                                        ui.button('Trước', on_click=self.prev_q).props('outline').classes('px-6').bind_visibility_from(self, 'current_index', lambda i: i > 0)
                                        if self.current_index == 0: ui.element('div') 
                                        ui.button('Tiếp', on_click=self.next_q).classes('bg-blue-600 text-white px-8 shadow-md hover:bg-blue-700').bind_visibility_from(self, 'current_index', lambda i: i < len(self.questions) - 1)

                        def jump_to(self, idx):
                            self.current_index = idx
                            self.render_current_question()
                            self.render_palette()
                        def next_q(self):
                            if self.current_index < len(self.questions) - 1: self.jump_to(self.current_index + 1)
                        def prev_q(self):
                            if self.current_index > 0: self.jump_to(self.current_index - 1)

                    quiz = QuizController(questions, state)
                    quiz.render()


    # --- LAYOUT GIAO DIỆN MỚI (Single Tab) ---
    # Tabs are defined in header now
    # with ui.tabs().classes('w-full') as tabs:
    #    tab_knowledge = ui.tab('Kiến Thức', icon='hub')
    #    tab_video = ui.tab('Video', icon='movie')
    #    tab_quiz = ui.tab('Quiz', icon='quiz')

    with ui.tab_panels(tabs, value=tab_knowledge).classes('w-full h-[calc(100vh-100px)]'):
        
        # TAB 1: KNOWLEDGE TREE + CHAT
        with ui.tab_panel(tab_knowledge).classes('p-0 h-full overflow-hidden'):
             with ui.row().classes('w-full h-full no-wrap relative'):
                 
                 # --- LEFT DRAWER: MENU (Initially Hidden) ---
                 menu_drawer = ui.column().classes('h-full bg-gray-50 border-r transition-all duration-300 ease-in-out w-[300px]').props('visible=False')
                 with menu_drawer:
                     ui.label("Danh sách bài học").classes('text-lg font-bold mb-2 p-2')
                     
                     # 1. Build Tree Structure
                     concepts = data_manager.get_all_concepts()
                     tree_nodes = []
                     chapters = {}
                     
                     import re
                     chapter_pattern = re.compile(r"(ch[uương]+[_ ]?(\d+))", re.IGNORECASE)
                     
                     for c in concepts:
                         c_name = c['name']
                         chap_match = chapter_pattern.search(c_name)
                         chap_num = int(chap_match.group(2)) if chap_match else 999
                         chap_key = f"CHAPTER_{chap_num}"
                         if chap_num == 999: chap_display = "Tài nguyên khác"
                         else: chap_display = f"Chương {chap_num}"

                         if chap_key not in chapters:
                             chapters[chap_key] = {'id': chap_key, 'label': chap_display, 'children': [], 'num': chap_num}
                         
                         chapters[chap_key]['children'].append({'id': c['id'], 'label': c_name})

                     sorted_chapters = sorted(chapters.values(), key=lambda x: x['num'])
                     
                     def on_tree_select(e):
                         if e.value in chapters: return
                         load_lesson_ui(e.value)

                     ui.tree(sorted_chapters, label_key='label', on_select=on_tree_select).props('expand-icon=chevron_right collapse-icon=expand_more').classes('w-full')

                 # --- CENTER: GRAPH ---
                 with ui.column().classes('flex-grow h-full p-0 relative'):
                     # Toolbar Buttons (Absolute Top)
                     with ui.row().classes('absolute top-2 left-2 z-10'):
                         ui.button(icon='menu', on_click=lambda: menu_drawer.set_visibility(not menu_drawer.visible)).props('flat round dense').tooltip('Hiện/Ẩn Menu')
                     
                     with ui.row().classes('absolute top-2 right-2 z-10'):
                         ui.button(icon='chat', on_click=lambda: chat_drawer.set_visibility(not chat_drawer.visible)).props('flat round dense').tooltip('Hiện/Ẩn Chatbot')

                     # Graph Container
                     graph_container = ui.element('div').classes('w-full h-full')
                     render_dynamic_tree(graph_container, state, on_click=load_lesson_ui)

                 # --- RIGHT DRAWER: CHAT (Initially Hidden) ---
                 chat_drawer = ui.column().classes('h-full bg-white border-l transition-all duration-300 ease-in-out w-[400px]').props('visible=False')
                 with chat_drawer:
                     ui.label("Chatbot Gemini").classes('text-lg font-bold p-2 border-b w-full')
                     
                     chat_container = ui.column().classes('w-full flex-grow overflow-y-auto p-2')
                     loading_spinner = ui.spinner(size='lg').classes('self-center').props('visible=False')
                     
                     with ui.row().classes('w-full items-center gap-2 p-2 border-t'):
                        rag_switch = ui.switch('RAG', value=True).props('color=green dense')
                        input_box = ui.input(placeholder='Hỏi Gemini...').classes('flex-grow').on('keydown.enter', chat_response)
                        ui.button(icon='send', on_click=chat_response).props('round flat dense')

        # TAB 2: VIDEO
        # TAB 2: VIDEO
        with ui.tab_panel(tab_video).classes('p-0 h-full'):
             with ui.column().classes('w-full h-full p-0 relative'):
                 # --- VIDEO PLAYER CONTAINER (Full Height) ---
                 video_container = ui.column().classes('w-full h-full bg-black relative justify-center items-center')

        # TAB 3: QUIZ
        with ui.tab_panel(tab_quiz).classes('p-0 h-full'):
             with ui.column().classes('w-full h-full p-6 bg-gray-50 overflow-y-auto'):
                 lesson_label_quiz = ui.label("Vui lòng chọn bài học từ tab 'Kiến Thức'").classes('text-2xl text-gray-400 font-bold mb-6')
                 quiz_container = ui.column().classes('w-full')

ui.run(storage_secret='pkt_secret_key', title='PKT Bio-Tutor', port=8081)

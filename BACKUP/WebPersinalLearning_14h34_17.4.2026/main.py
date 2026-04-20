from nicegui import ui, app, run
from data_manager import data_manager
from pkt_engine import StudentState
from bio_battery import BioBattery
from gemini_helper import extract_json_from_text, build_system_prompt, get_gemini_api_key
import google.generativeai as genai
from database import create_db_and_tables, create_user, get_user_by_username, authenticate_user, get_user_progress
from auth_service import create_login_page, create_register_page, is_logged_in, logout
import os
import json
import uuid
import asyncio

from utils import get_video_url

# Gamification Engine
from gamification.xp_engine import XPEngine
from gamification.streak_service import StreakService
from gamification.achievement_service import AchievementService
from gamification.gamification_ui import (
    inject_gamification_css, process_gamification_event,
    create_xp_header_widget, show_xp_gain, show_level_up,
    show_achievement_unlock, show_correct_streak
)

from services.prediction_service import prediction_service
from services.rag_service import advanced_rag
from services.task_broker import task_broker
from services.task_broker import task_broker
from visuals.dynamic_graph import render_dynamic_tree
from xai_engine import explain_recommendation
from ai_video_player import AIVideoPlayer
from resource_manager import (
    get_all_nodes_summary, get_node_resources, add_resource,
    remove_resource, detect_resource_type, get_resource_stats,
    get_hierarchical_nodes
)
import re

# Create DB
create_db_and_tables()

# Serve local files
app.add_static_files('/audio', os.path.join(os.getcwd(), 'DB', 'audio'))
app.add_static_files('/user_data', os.path.join(os.getcwd(), 'user_data'))

# Cấu hình Gemini
from gemini_helper import get_gemini_api_key, get_chat_model

GOOGLE_API_KEY = get_gemini_api_key()
genai.configure(api_key=GOOGLE_API_KEY, transport='rest')

# Use robust model selector
model = get_chat_model()

# Start Task Broker
app.on_startup(task_broker.start_worker)

# Thêm MathJax để hiển thị công thức Toán
ui.add_head_html("""
<script>
  window.MathJax = {
    tex: { inlineMath: [['$', '$'], ['\\(', '\\)']] },
    startup: { typeset: false }
  };

  let mathjaxResizeTimer;
  const typesetMathJax = () => {
      clearTimeout(mathjaxResizeTimer);
      mathjaxResizeTimer = setTimeout(() => {
          if (window.MathJax && window.MathJax.typesetPromise) {
              window.MathJax.typesetPromise();
          }
      }, 300);
  };
  window.addEventListener('resize', typesetMathJax);
  // Bắt sự kiện nhả chuột/touch khi kéo splitter để render lại
  window.addEventListener('mouseup', typesetMathJax, true);
  window.addEventListener('touchend', typesetMathJax, true);
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
""", shared=True)

# Inject Gamification CSS animations
inject_gamification_css()

# ============================================================
#  AUTH ROUTES
# ============================================================

@ui.page('/')
def root_page():
    """Root route - redirect based on auth status"""
    if is_logged_in():
        ui.navigate.to('/app')
    else:
        ui.navigate.to('/login')

@ui.page('/login')
def login_page():
    """Login page"""
    if is_logged_in():
        ui.navigate.to('/app')
        return
    create_login_page()

@ui.page('/register')
def register_page():
    """Register page"""
    if is_logged_in():
        ui.navigate.to('/app')
        return
    create_register_page()

@ui.page('/logout')
def logout_page():
    """Logout and redirect"""
    logout()

@ui.page('/onboarding')
async def onboarding_page():
    """Onboarding wizard for new users"""
    if not is_logged_in():
        ui.navigate.to('/login')
        return
    from onboarding import create_onboarding_wizard
    await create_onboarding_wizard()

# ============================================================
#  MAIN APP (Protected)
# ============================================================

@ui.page('/app')
async def main_page():
    # --- AUTH CHECK ---
    if not is_logged_in():
        ui.navigate.to('/login')
        return
    
    # Load user from session
    user = get_user_by_username(app.storage.user.get('username', ''))
    if not user:
        ui.navigate.to('/login')
        return
    
    app.storage.user['id'] = user.id
    app.storage.user['username'] = user.username

    # --- GAMIFICATION: Daily check-in ---
    streak_result = StreakService.check_in(user.id)
    if streak_result.get('daily_bonus_awarded'):
        daily_xp = XPEngine.add_xp(user.id, 'daily_login')
        ui.timer(1.0, lambda: show_xp_gain(daily_xp['xp_gained'], daily_xp['multiplier'], 'Bonus đăng nhập hàng ngày'), once=True)
        # Check for streak milestones
        streak = streak_result['streak']
        if streak in (3, 7, 14, 30, 60, 100):
            from gamification.gamification_ui import show_streak_milestone
            ui.timer(2.0, lambda s=streak: show_streak_milestone(s), once=True)
    # Check for any pending achievements
    new_achievements = AchievementService.check_all(user.id)
    for i, ach in enumerate(new_achievements):
        ui.timer(3.0 + i * 1.5, lambda a=ach: show_achievement_unlock(a), once=True)


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
    dark = ui.dark_mode()
    left_drawer = ui.left_drawer(value=True, bordered=True).classes('bg-[#f8fafc] flex flex-col justify-between z-50')
    
    with ui.header().classes(replace='row items-center bg-white text-slate-800 p-2 h-[60px] shadow-sm z-40 justify-between'):
        with ui.row().classes('items-center gap-3 w-1/3'):
            ui.button(icon='menu', on_click=left_drawer.toggle).props('flat round dense color=blue-7')
            ui.label('PKT Bio-Tutor').classes('text-2xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 hidden md:block')

        # --- DYNAMIC LESSON TITLE IN HEADER ---
        header_lesson_container = ui.row().classes('items-center gap-2 flex-grow justify-center overflow-hidden w-1/3')

        # Right side info
        with ui.row().classes('items-center justify-end gap-3 w-1/3 pr-2'):
            prediction_label = ui.label('').classes('text-sm font-bold text-blue-700 whitespace-nowrap hidden lg:block')
            
            gamification_stats = XPEngine.get_user_stats(user.id)
            create_xp_header_widget(gamification_stats)

            ui.button(icon='dark_mode', on_click=dark.toggle).props('flat round dense color=grey-6').tooltip('Giao diện Sáng/Tối')
            with ui.row().classes('items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 py-0.5 rounded-full border border-transparent transition-all'):
                ui.avatar(icon='person', color='blue-100', text_color='blue-600').props('size=sm')
                ui.label(user.full_name).classes('font-bold text-sm hidden sm:block mr-1')
                with ui.menu().classes('min-w-[150px]'):
                    ui.menu_item('Hồ sơ cá nhân', on_click=lambda: ui.notify('Tính năng đang phát triển'))
                    ui.menu_item('Cài đặt', on_click=lambda: ui.notify('Đang phát triển'))
                    ui.separator()
                    ui.menu_item('Đăng xuất', on_click=lambda: ui.navigate.to('/logout')).classes('text-red-500 font-medium')

    with left_drawer:
        with ui.column().classes('w-full mt-4'):
            with ui.tabs().props('vertical active-color="primary" indicator-color="primary"').classes('w-full text-slate-600 font-medium z-10') as tabs:
                tab_dashboard = ui.tab('Tổng quan', icon='dashboard').classes('justify-start px-6')
                tab_journey = ui.tab('Hành trình', icon='insights').classes('justify-start px-6')
                tab_library = ui.tab('Cửa hàng UGC', icon='store').classes('justify-start px-6')
                tab_social = ui.tab('Cộng đồng', icon='public').classes('justify-start px-6')
                tab_nexus = ui.tab('Nexus Space', icon='explore').classes('justify-start px-6')
                ui.separator().classes('my-2 w-[80%] mx-auto bg-gray-200')
                tab_video = ui.tab('Học liệu Video', icon='play_circle').classes('justify-start px-6')
                tab_quiz = ui.tab('Kiểm tra', icon='quiz').classes('justify-start px-6')
                tab_tutor = ui.tab('Gia sư AI', icon='smart_toy').classes('justify-start px-6')
                ui.separator().classes('my-2 w-[80%] mx-auto bg-gray-200')
                tab_studio = ui.tab('Graph Studio', icon='architecture').classes('justify-start px-6')
                tab_leaderboard = ui.tab('Xếp hạng', icon='leaderboard').classes('justify-start px-6')
                tab_profile = ui.tab('Hồ sơ', icon='person').classes('justify-start px-6 hidden')
        
        ui.space()
        with ui.column().classes('w-full mt-auto mb-4 px-4 items-start'):
             ui.button('Nhận Trợ giúp', icon='help_outline', on_click=lambda: ui.notify('Đang xây dựng.')).props('flat text-color="blue-grey-6" no-caps size="sm"').classes('w-full justify-start')
             ui.label('Powered by Antigravity').classes('text-[10px] text-gray-400 font-mono w-full text-center mt-2')

    battery_ref = [None]
    
    # Hàm cập nhật Dashboard loop
    def update_ui_loop():
        if battery_ref[0]:
            battery_ref[0].update(state.current_fatigue)
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
            ui.chat_message(user_msg, sent=True).classes('font-medium')
        input_box.value = ''
        
        # Show loading in chat
        with chat_container:
            spinner_row = ui.row().classes('items-center gap-2')
            with spinner_row:
                 ui.spinner('dots', size='md', color='blue-500')
                 ui.label('AI đang suy nghĩ...').classes('text-gray-400 text-xs italic')
        
        try:
            if rag_switch.value:
                # Freemium Paywall Check
                if user.role == 'student':
                    ui.run_javascript("if(typeof Swal === 'undefined') { let script = document.createElement('script'); script.src = 'https://cdn.jsdelivr.net/npm/sweetalert2@11'; document.head.appendChild(script); setTimeout(() => Swal.fire({title: 'Tính năng Premium', text: 'Chế độ Socratic AI Deep RAG chỉ dành cho tài khoản Chuyên sâu. Xem Bảng giá!', icon: 'warning', confirmButtonText: 'Hiểu rồi', confirmButtonColor: '#8b5cf6'}), 500); } else { Swal.fire({title: 'Tính năng Premium', text: 'Chế độ Socratic AI Deep RAG chỉ dành cho tài khoản Chuyên sâu. Xem Bảng giá!', icon: 'warning', confirmButtonText: 'Hiểu rồi', confirmButtonColor: '#8b5cf6'}); }")
                    if 'spinner_row' in locals(): chat_container.remove(spinner_row)
                    return
                # Use Advanced RAG
                result = await advanced_rag.answer_with_citation(user.id, user_msg, state.to_dict())
                answer = result['answer']
                sources = result['sources']
            else:
                 # Direct Chat
                response = await run.io_bound(model.generate_content, user_msg)
                answer = response.text
                sources = []
            
            # Remove spinner
            chat_container.remove(spinner_row)

            with chat_container:
                msg = ui.chat_message(answer, sent=False, avatar='https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg').classes('bg-blue-50/50 p-2 rounded-lg')
                with msg:
                    if sources:
                        ui.separator().classes('my-2 bg-blue-100')
                        with ui.row().classes('items-center gap-1'):
                            ui.icon('library_books', color='blue-500').classes('text-xs')
                            ui.label('Nguồn tham khảo:').classes('text-xs font-bold text-blue-600')
                        
                        with ui.row().classes('gap-2 mt-1'):
                            seen = set()
                            for src in sources:
                                key = f"{src['source']}-p{src['page']}"
                                if key not in seen:
                                    # Create a "Card" look for citations
                                    with ui.link(target='#').classes('no-underline group'):
                                         with ui.card().classes('flex-row items-center gap-2 px-2 py-1 bg-white border border-blue-100 shadow-sm hover:shadow-md hover:border-blue-300 transition-all cursor-pointer'):
                                             ui.icon('description', color='blue-400').classes('text-xs group-hover:text-blue-600')
                                             with ui.column().classes('gap-0'):
                                                 ui.label(src['source'][:15] + '...').classes('text-[10px] font-bold text-gray-700 leading-none group-hover:text-blue-700')
                                                 ui.label(f"Trang {src['page']}").classes('text-[9px] text-gray-500 leading-none')
                                    seen.add(key)
        except Exception as e:
            if 'spinner_row' in locals(): chat_container.remove(spinner_row)
            with chat_container:
                ui.chat_message(f"Error: {str(e)}", sent=False).classes('text-red-500')
        
        # Scroll to bottom
        # chat_container.scroll_to(percent=1.0) # ui.column doesn't have scroll_to, the scroll_area does. We need to refactor layout to expose scroll_area.

    # ============================================================
    #  CONCEPT ID RESOLVER (Maps 3D Graph IDs to DataManager IDs)
    # ============================================================
    def resolve_concept_id(node_id, node_label=None):
        """Resolve a 3D graph node ID to a data_manager concept_id.
        
        The 3D graph uses IDs like 'c1.1', 'c2.3', 'm1' from the uploaded tree JSON,
        while data_manager uses IDs like 'Chuong_1_Tiet_1' from DB/JSON_Data/.
        This function attempts multiple strategies to map between them.
        """
        # Strategy 1: Direct match (already correct ID)
        if data_manager.get_lesson(node_id):
            print(f"[Resolver] Direct match: {node_id}")
            return node_id
        
        # Strategy 2: Pattern match c{X}.{Y} -> Chuong_{X}_Tiet_{Y}
        id_match = re.match(r'^c(\d+)[._](\d+)$', node_id, re.IGNORECASE)
        if id_match:
            mapped_id = f"Chuong_{id_match.group(1)}_Tiet_{id_match.group(2)}"
            if data_manager.get_lesson(mapped_id):
                print(f"[Resolver] Pattern match: {node_id} -> {mapped_id}")
                return mapped_id
        
        # Strategy 3: Try extracting chapter/lesson from label if provided
        if node_label:
            ch_m = re.search(r'(?:Chương|Chuong|Ch)[_\s.-]*(\d+)', node_label, re.IGNORECASE)
            ls_m = re.search(r'(?:Tiết|Tiet|Bài|Bai)[_\s.-]*(\d+)', node_label, re.IGNORECASE)
            if ch_m and ls_m:
                mapped_id = f"Chuong_{ch_m.group(1)}_Tiet_{ls_m.group(1)}"
                if data_manager.get_lesson(mapped_id):
                    print(f"[Resolver] Label pattern match: {node_id} -> {mapped_id} (from '{node_label}')")
                    return mapped_id
        
        # Strategy 4: Fuzzy search by label across all concepts
        if node_label:
            all_concepts = data_manager.get_all_concepts()
            label_lower = node_label.lower().strip()
            # Try exact substring match
            for c in all_concepts:
                c_name_lower = c['name'].lower()
                if label_lower in c_name_lower or c_name_lower in label_lower:
                    print(f"[Resolver] Fuzzy match: {node_id} -> {c['id']} (label='{node_label}' ~ name='{c['name']}')")
                    return c['id']
            # Try keyword overlap match
            label_words = set(re.findall(r'\w+', label_lower))
            if len(label_words) >= 2:  # Need at least 2 words for meaningful matching
                best_match = None
                best_score = 0
                for c in all_concepts:
                    c_words = set(re.findall(r'\w+', c['name'].lower()))
                    overlap = len(label_words & c_words)
                    if overlap > best_score and overlap >= 2:
                        best_score = overlap
                        best_match = c['id']
                if best_match:
                    print(f"[Resolver] Keyword overlap match: {node_id} -> {best_match} (score={best_score})")
                    return best_match
        
        print(f"[Resolver] No match found for node_id='{node_id}', label='{node_label}'")
        return None

    # Content Loading
    def load_lesson_ui(concept_id, target_tab=None):
        state.current_concept_id = concept_id
        save_state()
        lesson_data = data_manager.get_lesson(concept_id)
        
        if not lesson_data:
            print(f"[Main] WARNING: No lesson data found for concept_id='{concept_id}'")
            ui.notify(f'Không tìm thấy dữ liệu bài học cho: {concept_id}', type='warning')
            # Still switch tab so user sees something
            if tabs and target_tab:
                tabs.value = target_tab
            return
        
        # Calculate Prediction
        win_prob = prediction_service.predict_next_performance(user.id, concept_id)
        
        # Switch to Target Tab
        if tabs:
            if target_tab:
                tabs.value = target_tab
            elif tab_video:
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
            
            # Check for AI Script first
            concept_name = lesson_data['metadata']['concept_name']
            # Robust regex for lesson parsing
            ch_match = re.search(r'(?:Chương|Chuong)[_\s-]*(\d+)', concept_name, re.IGNORECASE)
            ls_match = re.search(r'(?:Tiết|Tiet)[_\s-]*(\d+)', concept_name, re.IGNORECASE)
            
            script_found = False
            if ch_match or ls_match:
                ch_num = ch_match.group(1) if ch_match else "1"
                ls_num = ls_match.group(1) if ls_match else "1"
                folder_name = f"Chuong_{ch_num}_Tiet_{ls_num}"
                script_path = os.path.join(os.getcwd(), 'DB', 'Video', folder_name, 'script.txt')
                
                if os.path.exists(script_path):
                    print(f"[Main] Script found at {script_path}. Loading AI Player.")
                    AIVideoPlayer(video_container, concept_name, script_path)
                    script_found = True
            
            if not script_found:
                 with video_container:
                    video_url = get_video_url(concept_name)
                    if video_url:
                         # Overlay Button
                         ui.button(icon='open_in_new', on_click=lambda url=video_url: ui.open(url, new_tab=True)) \
                            .classes('absolute top-4 right-4 z-10 bg-white text-blue-600 opacity-80 hover:opacity-100 shadow-lg').props('flat round dense').tooltip('Mở trong tab mới')
                         
                         ui.element('iframe').props(f'src="{video_url}" allowfullscreen').classes('w-full h-full border-none bg-black')
                    else:
                         with ui.column().classes('items-center justify-center w-full h-full gap-4'):
                             ui.icon('videocam_off', color='gray-400', size='3rem')
                             ui.label(f"Video chưa khả dụng cho bài học: {concept_name}").classes('italic text-gray-500 text-lg')
                             ui.label("Kiểm tra lại DB/Video/ hoặc DB/videosLinksCourse.txt").classes('text-xs text-gray-400')

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
                                                
                                                # --- GAMIFICATION: Award XP for correct answer ---
                                                try:
                                                    user_db_id = app.storage.user.get('id')
                                                    if user_db_id:
                                                        process_gamification_event(user_db_id, 'quiz_correct')
                                                except Exception as gx:
                                                    print(f"[Gamification] Error: {gx}")
                                                
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
                                                
                                                # --- GAMIFICATION: Track wrong answer ---
                                                try:
                                                    user_db_id = app.storage.user.get('id')
                                                    if user_db_id:
                                                        from gamification.xp_engine import XPEngine
                                                        XPEngine.add_xp(user_db_id, 'quiz_wrong', custom_xp=0)
                                                except Exception as gx:
                                                    print(f"[Gamification] Error: {gx}")
                                                
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

    with ui.tab_panels(tabs, value=tab_dashboard).classes('w-full h-[calc(100vh-60px)] m-0 p-0'):
        
        # TAB 00: DASHBOARD (TỔNG QUAN)
        with ui.tab_panel(tab_dashboard).classes('p-0 h-full bg-slate-50 overflow-y-auto'):
            with ui.column().classes('w-full max-w-7xl mx-auto p-6 md:p-10'):
                # Header Section
                with ui.row().classes('w-full items-center justify-between mb-8'):
                    with ui.column().classes('gap-1'):
                        ui.label(f'Chào mừng trở lại, {user.full_name}! 👋').classes('text-3xl font-extrabold text-blue-900 tracking-tight')
                        ui.label('Tiếp tục hành trình tri thức của bạn hôm nay.').classes('text-slate-500 font-medium text-base')
                    with ui.button('Bắt đầu học ngay', icon='play_arrow', on_click=lambda: setattr(tabs, 'value', tab_journey)).classes('bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold px-6 py-2 shadow-lg hover:shadow-xl hover:scale-105 transition-all w-full md:w-auto').props('rounded'):
                        pass
                
                with ui.row().classes('w-full gap-6 items-stretch flex-nowrap md:flex-wrap lg:flex-nowrap'):
                    # Left Column: Stats & Battery
                    with ui.column().classes('w-full lg:w-1/3 gap-6 flex-grow'):
                        # Stats Card
                        with ui.card().classes('w-full p-6 bg-white rounded-3xl shadow-sm hover:shadow-md transition-all border border-gray-100 relative overflow-hidden'):
                            with ui.element('div').classes('absolute -right-10 -top-10 w-32 h-32 bg-blue-50 rounded-full blur-2xl'): pass
                            ui.label('Tiến trình Khóa học').classes('font-bold text-gray-800 text-lg mb-4')
                            with ui.row().classes('w-full items-center justify-between mb-2'):
                                with ui.column().classes('gap-0'):
                                    ui.label('Cấp độ hiện tại').classes('text-xs text-gray-500')
                                    ui.label(f"Level {gamification_stats.get('level', 1)}").classes('text-2xl font-black text-blue-700 leading-none')
                                with ui.column().classes('gap-0 items-end'):
                                    ui.label('Kinh nghiệm').classes('text-xs text-gray-500')
                                    with ui.row().classes('items-center'):
                                        ui.icon('diamond', size='xs', color='purple-400').classes('mr-1')
                                        ui.label(f"{gamification_stats.get('total_xp', 0)} XP").classes('text-xl font-bold text-purple-700 leading-none')
                            
                            # Streak element
                            with ui.row().classes('w-full items-center justify-center p-3 mt-4 bg-orange-50 rounded-2xl border border-orange-100 gap-2'):
                                ui.icon('local_fire_department', color='orange-500').classes('text-2xl')
                                ui.label(f"{gamification_stats.get('streak', 0)} Ngày học liên tiếp").classes('font-bold text-orange-600')

                        # Bio Battery Card
                        with ui.card().classes('w-full p-6 bg-white rounded-3xl shadow-sm hover:shadow-md transition-all border border-gray-100 items-center justify-center'):
                            with ui.row().classes('w-full justify-between items-start mb-2'):
                                ui.label('Bio Battery').classes('font-bold text-gray-800 text-lg')
                                ui.icon('bolt', color='yellow-500 text-xl')
                            ui.label('Theo dõi mức độ mệt mỏi nhận thức của bạn.').classes('text-xs text-gray-500 mb-4 text-center w-full')
                            
                            with ui.row().classes('w-full justify-center'):
                                battery_ref[0] = BioBattery(ui.row())

                    # Center & Right Column: Next Action & Recommended
                    with ui.column().classes('w-full lg:w-2/3 gap-6'):
                        # Knowledge Tracing Prediction Card
                        with ui.card().classes('w-full p-8 bg-gradient-to-br from-indigo-900 via-blue-900 to-indigo-800 rounded-[2rem] shadow-xl text-white relative overflow-hidden h-[240px] justify-center'):
                             # Pattern overlay
                             with ui.element('div').classes('absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white via-transparent to-transparent bg-[length:20px_20px]'): pass
                             with ui.row().classes('relative z-10 w-full items-center justify-between'):
                                 with ui.column().classes('w-2/3 gap-3'):
                                     ui.label('Khuyến nghị Tiếp theo bởi AI').classes('text-blue-200 font-medium text-sm tracking-widest uppercase')
                                     ui.label('Phân tích Sự tiến hóa & Học máy').classes('text-3xl font-extrabold leading-tight text-white drop-shadow-md')
                                     ui.label('Dựa trên mô hình Knowledge Tracing, bạn đang có tỷ lệ nắm vững cao ở phần trước. Đây là thời điểm Vàng để học bài này.').classes('text-sm text-blue-100 opacity-90 leading-relaxed mt-2')
                                 with ui.button(icon='play_arrow', on_click=lambda: setattr(tabs, 'value', tab_journey)).classes('bg-white text-indigo-900 w-16 h-16 rounded-full shadow-2xl hover:scale-110 transition-transform flex items-center justify-center'):
                                     pass
                             
                        # Tasks / Goals
                        with ui.card().classes('w-full p-6 bg-white rounded-3xl shadow-sm hover:shadow-md transition-all border border-gray-100 flex-grow'):
                             ui.label('Nhiệm vụ trong ngày').classes('font-bold text-gray-800 text-lg mb-4')
                             with ui.column().classes('w-full gap-3'):
                                 # Task 1
                                 with ui.row().classes('w-full p-4 rounded-xl border border-gray-200 items-center justify-between hover:border-gray-300 hover:bg-gray-50 transition-colors cursor-pointer'):
                                     with ui.row().classes('items-center gap-3'):
                                         ui.icon('check_circle', color='gray-300').classes('text-2xl')
                                         with ui.column().classes('gap-0'):
                                             ui.label('Hoàn thành 3 câu hỏi Quiz').classes('font-bold text-sm text-gray-800')
                                             ui.label('Thưởng: 50 XP').classes('text-xs text-purple-600 font-medium')
                                     ui.button('Làm ngay').props('outline rounded size=sm color=blue')
                                 
                                 # Task 2
                                 with ui.row().classes('w-full p-4 rounded-xl border border-gray-200 items-center justify-between hover:border-gray-300 hover:bg-gray-50 transition-colors cursor-pointer'):
                                     with ui.row().classes('items-center gap-3'):
                                         ui.icon('check_circle', color='green-500').classes('text-2xl bg-green-50 rounded-full')
                                         with ui.column().classes('gap-0'):
                                             ui.label('Tương tác với AI Tutor').classes('font-bold text-sm text-gray-800 line-through')
                                             ui.label('Đã hoàn thành').classes('text-xs text-green-600')
                                     ui.button('Đã nhận').props('flat disabled size=sm color=gray')

        # TAB 0: PUBLIC LIBRARY (Thư viện công cộng)
        with ui.tab_panel(tab_library).classes('p-6 h-full bg-gradient-to-br from-slate-50 to-blue-50/30 overflow-y-auto'):
            with ui.column().classes('w-full max-w-6xl mx-auto'):
                # Header
                with ui.row().classes('w-full items-center justify-between mb-6'):
                    with ui.column().classes('gap-1'):
                        ui.label('📚 Thư viện Cây Tri Thức').classes('text-3xl font-extrabold text-slate-800 tracking-tight')
                        ui.label('Khám phá và thêm cây tri thức vào bộ sưu tập cá nhân').classes('text-slate-500')
                    with ui.row().classes('items-center gap-3'):
                        ui.input(placeholder='🔍 Tìm kiếm...').props('rounded outlined dense').classes('w-64')

                # Load public library
                _json = json
                public_lib_path = os.path.join(os.getcwd(), 'DB', 'public_library.json')
                public_trees = []
                if os.path.exists(public_lib_path):
                    with open(public_lib_path, 'r', encoding='utf-8') as _plf:
                        public_trees = _json.load(_plf).get('trees', [])

                # Also load user's current subjects to check what's already added
                user_subj_file = f'user_data/{user.username}/subjects.json'
                user_subject_ids = set()
                if os.path.exists(user_subj_file):
                    with open(user_subj_file, 'r', encoding='utf-8') as _usf:
                        for s in _json.load(_usf).get('subjects', []):
                            user_subject_ids.add(s.get('id', ''))

                lib_cards_container = ui.row().classes('w-full gap-5 flex-wrap')

                def render_public_cards():
                    lib_cards_container.clear()
                    # Reload user subjects
                    _user_ids = set()
                    if os.path.exists(user_subj_file):
                        with open(user_subj_file, 'r', encoding='utf-8') as _rf:
                            for s in _json.load(_rf).get('subjects', []):
                                _user_ids.add(s.get('id', ''))

                    with lib_cards_container:
                        if not public_trees:
                            ui.label('Chưa có cây tri thức công cộng nào.').classes('text-gray-400 italic')
                        else:
                            for tree in public_trees:
                                already_added = tree['id'] in _user_ids
                                # Card colors based on category
                                gradients = [
                                    'from-blue-500 to-indigo-600',
                                    'from-emerald-500 to-teal-600',
                                    'from-purple-500 to-pink-600',
                                    'from-orange-500 to-red-600',
                                ]
                                grad = gradients[hash(tree['id']) % len(gradients)]

                                with ui.card().classes('w-[300px] p-0 rounded-2xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 overflow-hidden border border-gray-100'):
                                    # Gradient header
                                    with ui.element('div').classes(f'w-full h-28 bg-gradient-to-br {grad} relative flex items-end p-4'):
                                        ui.label(tree['title']).classes('text-white font-extrabold text-lg leading-tight drop-shadow-md')
                                        # Node count badge
                                        ui.label(f"{tree['total_nodes']} nodes").classes('absolute top-3 right-3 bg-white/20 backdrop-blur-sm text-white text-xs font-bold px-2 py-0.5 rounded-full')

                                    with ui.column().classes('p-4 gap-3'):
                                        ui.label(tree.get('description', '')).classes('text-sm text-gray-500 line-clamp-2')

                                        with ui.row().classes('items-center justify-between w-full'):
                                            with ui.row().classes('items-center gap-1'):
                                                ui.icon('star', color='yellow-500').classes('text-sm')
                                                ui.label(f"{tree.get('rating', '4.5')}").classes('text-sm font-bold text-gray-700')
                                                ui.label(f"({tree.get('downloads', 0)})").classes('text-xs text-gray-400')
                                            
                                            price = tree.get('price_xp', 0)
                                            if price == 0:
                                                ui.label('Miễn phí').classes('text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold')
                                            else:
                                                with ui.row().classes('items-center gap-1 bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full'):
                                                    ui.icon('diamond', size='xs')
                                                    ui.label(f'{price} XP').classes('text-xs font-bold')

                                        with ui.row().classes('items-center gap-2'):
                                            ui.label(f"🏷️ {tree.get('category', 'Chung')}").classes('text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium')
                                            if tree.get('is_trending'):
                                                ui.label("🔥 Trending").classes('text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-bold')

                                        if already_added:
                                            ui.button('✅ Đã sở hữu', on_click=None).props('disable flat no-caps color=green').classes('w-full')
                                        else:
                                            def add_tree(t=tree):
                                                price_xp = t.get('price_xp', 0)
                                                if price_xp > 0:
                                                    current_xp = XPEngine.get_user_stats(user.id)['total_xp']
                                                    if current_xp < price_xp:
                                                        ui.notify(f'Bạn không đủ {price_xp} XP để tải tài liệu này. Hãy học thêm!', type='negative')
                                                        return
                                                    # Trừ điểm XP
                                                    XPEngine.add_xp(user.id, 'buy_item', custom_xp=-price_xp)
                                                    ui.notify(f'Đã mua thành công với giá {price_xp} XP!', type='info')

                                                import shutil, uuid
                                                # Copy tree file to user's trees directory
                                                user_tree_dir = f'user_data/{user.username}/trees'
                                                os.makedirs(user_tree_dir, exist_ok=True)
                                                src_path = os.path.join(os.getcwd(), t['filename'].replace('\\', '/'))
                                                dst_path = os.path.join(user_tree_dir, f"{t['id']}.json")
                                                shutil.copy2(src_path, dst_path)

                                                # Update user's subjects.json
                                                subj_data = {'subjects': []}
                                                if os.path.exists(user_subj_file):
                                                    with open(user_subj_file, 'r', encoding='utf-8') as rf:
                                                        subj_data = _json.load(rf)

                                                if not any(s['id'] == t['id'] for s in subj_data['subjects']):
                                                    subj_data['subjects'].append({
                                                        'id': t['id'],
                                                        'title': t['title'],
                                                        'filename': dst_path.replace('\\', '/'),
                                                        'total_nodes': t['total_nodes']
                                                    })
                                                    with open(user_subj_file, 'w', encoding='utf-8') as wf:
                                                        _json.dump(subj_data, wf, ensure_ascii=False, indent=2)

                                                ui.notify(f'✅ Đã sở hữu "{t["title"]}"!', type='positive')
                                                render_public_cards()

                                            btn_text = f'Mua ({tree.get("price_xp")} XP)' if tree.get('price_xp', 0) > 0 else 'Thêm vào thư viện'
                                            ui.button(btn_text, on_click=add_tree).props('outline rounded no-caps color=blue').classes('w-full font-bold hover:bg-blue-50')

                render_public_cards()

                # Info section
                with ui.card().classes('w-full mt-6 p-4 rounded-xl bg-blue-50/50 border border-blue-100'):
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('info', color='blue-500').classes('text-xl')
                        ui.label('💡 Dùng XP cày được từ Quiz để thanh toán chi phí tại Chợ Cây Tri Thức (UGC). Cây mới sẽ xuất hiện trong tab Graph Studio.').classes('text-sm text-blue-700')

        # TAB SOCIAL (CỘNG ĐỒNG)
        with ui.tab_panel(tab_social).classes('p-6 h-full bg-slate-50 overflow-y-auto'):
            from social_page import create_social_section
            social_container = ui.column().classes('w-full max-w-5xl mx-auto')
            
            def load_social():
                create_social_section(user, social_container)
            
            tabs.on_value_change(lambda e: load_social() if e.value == tab_social else None)

        # TAB 1: JOURNEY DASHBOARD (2D + AI)
        with ui.tab_panel(tab_journey).classes('p-0 h-full overflow-hidden bg-slate-50'):
             with ui.row().classes('w-full h-full no-wrap gap-0'):
                 
                 # --- LEFT PANEL: CURRICULUM (Sidebar) ---
                 with ui.column().classes('w-[280px] h-full bg-white border-r border-gray-200 flex flex-col shadow-sm z-10'):
                     # Header
                     with ui.row().classes('w-full p-4 items-center border-b border-gray-100'):
                         ui.icon('school', color='blue-600').classes('text-2xl')
                         ui.label('Chương trình học').classes('font-bold text-gray-800 text-lg tracking-tight')
                     
                     # Search
                     with ui.row().classes('w-full px-4 py-2 bg-gray-50 border-b border-gray-100'):
                         ui.input(placeholder='Tìm kiếm bài học...').props('dense outlined rounded color=blue-6 text-color=grey-8').classes('w-full bg-white text-sm')

                     # Curriculum Tree/List
                     with ui.scroll_area().classes('flex-grow w-full p-2'):
                         # 1. Build Data
                         concepts = data_manager.get_all_concepts()
                         chapters = {}
                         import re
                         chapter_pattern = re.compile(r"(ch(?:ương|uong)[_ ]?(\d+))", re.IGNORECASE)
                         
                         for c in concepts:
                             c_name = c['name']
                             chap_match = chapter_pattern.search(c_name)
                             chap_num = int(chap_match.group(2)) if chap_match else 999
                             chap_key = f"CHAPTER_{chap_num}"
                             if chap_num == 999: chap_display = "Tài nguyên bổ trợ"
                             else: chap_display = f"Chương {chap_num}"

                             if chap_key not in chapters:
                                 chapters[chap_key] = {'id': chap_key, 'label': chap_display, 'children': [], 'num': chap_num}
                             
                             chapters[chap_key]['children'].append({'id': c['id'], 'label': c_name})

                         sorted_chapters = sorted(chapters.values(), key=lambda x: x['num'])
                         
                         # 2. Render Custom Tree
                         for chap in sorted_chapters:
                             with ui.expansion(chap['label'], icon='folder_open').classes('w-full mb-1 bg-white rounded-lg border border-transparent hover:border-blue-100 transition-all font-semibold text-gray-700').props('header-class="text-blue-900"'):
                                 for child in chap['children']:
                                     # Lesson Item
                                     with ui.row().classes('w-full cursor-pointer hover:bg-blue-50 p-2 pl-8 rounded-md transition-colors items-center group') \
                                         .on('click', lambda id=child['id']: load_lesson_ui(id)):
                                         ui.icon('article', color='gray-400').classes('text-sm mr-2 group-hover:text-blue-500')
                                         ui.label(child['label']).classes('text-sm text-gray-600 group-hover:text-blue-700 leading-tight w-full truncate')

                 # --- CENTER PANEL: KNOWLEDGE GRAPH ---
                 with ui.column().classes('flex-grow h-full relative bg-slate-50 overflow-hidden'):
                     # Toolbar (Floating)
                     with ui.row().classes('absolute top-4 left-4 z-20 gap-2'):
                         with ui.button(icon='zoom_in', on_click=lambda: ui.notify('Zoom In')).props('flat round dense color=grey-7').classes('bg-white shadow-md border border-gray-200 hover:bg-blue-50'):
                              ui.tooltip('Phóng to')
                         with ui.button(icon='zoom_out', on_click=lambda: ui.notify('Zoom Out')).props('flat round dense color=grey-7').classes('bg-white shadow-md border border-gray-200 hover:bg-blue-50'):
                              ui.tooltip('Thu nhỏ')
                         with ui.button(icon='refresh', on_click=lambda: ui.notify('Reset View')).props('flat round dense color=grey-7').classes('bg-white shadow-md border border-gray-200 hover:bg-blue-50'):
                              ui.tooltip('Đặt lại')

                     # Graph Container
                     graph_container = ui.element('div').classes('w-full h-full bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:20px_20px]')
                     render_dynamic_tree(graph_container, state, on_click=load_lesson_ui)
                     
                     # Bottom Status Bar
                     with ui.row().classes('absolute bottom-0 w-full bg-white/80 backdrop-blur border-t border-gray-200 p-2 justify-between px-4 text-xs text-gray-500'):
                         ui.label('Graph Engine: NetworkX + VisJS')
                         ui.label(f'Nodes: {len(concepts)} | Edges: {len(concepts)*2}') # Dummy stats

                 # --- RIGHT PANEL: AI ASSISTANT (Chat) ---
                 with ui.column().classes('w-[350px] h-full bg-white border-l border-gray-200 flex flex-col shadow-lg z-20'):
                     # Header
                     with ui.row().classes('w-full p-4 items-center justify-between border-b border-gray-100 bg-gradient-to-r from-blue-50 to-white'):
                         with ui.row().classes('items-center gap-2'):
                             ui.avatar(icon='smart_toy', color='blue-600', text_color='white').props('size=sm')
                             with ui.column().classes('gap-0'):
                                 ui.label('AI Tutor').classes('font-bold text-blue-900 leading-none')
                                 ui.label('Powered by Gemini 1.5').classes('text-[10px] text-blue-400 font-medium')
                         
                         rag_switch = ui.switch('Pro', value=True).props('dense color=blue keep-color').tooltip('Chế độ Nâng cao (RAG)')

                     # Chat History
                     with ui.scroll_area().classes('flex-grow w-full p-4 bg-gray-50/50') as chat_scroll_area:
                         chat_container = ui.column().classes('w-full gap-4')
                         
                         # Welcome Message
                         with chat_container:
                             with ui.row().classes('gap-3 items-start animate-fade'):
                                 ui.avatar(icon='smart_toy', color='white', text_color='blue-600').classes('border border-blue-100 shadow-sm')
                                 with ui.column().classes('gap-1'):
                                     ui.label('AI Tutor').classes('text-xs font-bold text-gray-500 ml-1')
                                     ui.label('Chào bạn! Mình là trợ lý học tập AI. Mình đã học toàn bộ giáo trình môn này. Hãy hỏi mình bất cứ điều gì nhé!').classes('bg-white p-3 rounded-2xl rounded-tl-none text-sm text-gray-700 shadow-sm border border-gray-100')

                     # Input Area
                     with ui.column().classes('w-full p-4 border-t border-gray-100 bg-white gap-2'):
                         # Suggestion Chips
                         with ui.row().classes('gap-2 overflow-x-auto w-full no-wrap pb-2'):
                              for q in ["Tóm tắt chương 1?", "Khái niệm TMĐT?", "Mô hình B2B là gì?"]:
                                  ui.button(q, on_click=lambda txt=q: [input_box.set_value(txt), chat_response()]).props('dense outline rounded color=grey-5 size=sm').classes('whitespace-nowrap')

                         with ui.row().classes('w-full items-center gap-2 relative'):
                             input_box = ui.input(placeholder='Nhập câu hỏi...').props('rounded outlined dense borderless').classes('w-full bg-gray-100 pr-10').on('keydown.enter', chat_response)
                             ui.button(icon='send', on_click=chat_response).props('flat round dense color=blue').classes('absolute right-1 top-1/2 transform -translate-y-1/2')

        # TAB 2: NEXUS SPACE (IMMERSIVE 3D)
        with ui.tab_panel(tab_nexus).classes('p-0 h-full bg-[#0d1117]'):
             nexus_container = ui.column().classes('w-full h-full relative justify-center items-center')
             
             async def activate_nexus():
                 subj_file = f"user_data/{user.username}/subjects.json"
                 if os.path.exists(subj_file):
                     with open(subj_file, 'r', encoding='utf-8') as sf:
                         subjects = json.load(sf)["subjects"]
                         if subjects:
                             last_path = subjects[0]['filename']
                             from step2_5_visualize_tree import visualize_knowledge_tree
                             await run.io_bound(visualize_knowledge_tree, user.username, last_path)
                             nexus_container.clear()
                             with nexus_container:
                                 # The "Polling Event" Master Fix (checks both __bridge_payload and postMessage)
                                 async def check_nexus_3d_bridge():
                                     try:
                                         payload = await ui.run_javascript('''
                                             // Check postMessage payload first, then __bridge_payload
                                             if (window.__nexus_postmsg_payload) {
                                                 let p = window.__nexus_postmsg_payload;
                                                 window.__nexus_postmsg_payload = null;
                                                 return p;
                                             }
                                             if (window.__bridge_payload) {
                                                 let p = window.__bridge_payload;
                                                 window.__bridge_payload = null;
                                                 return p;
                                             }
                                             return null;
                                         ''', timeout=1.0)
                                         if payload and isinstance(payload, dict):
                                             raw_node_id = payload.get('id')
                                             action = payload.get('action', 'video')
                                             node_label = payload.get('label', '')
                                             
                                             if raw_node_id:
                                                 # Resolve the 3D graph node ID to a data_manager concept_id
                                                 node_id = resolve_concept_id(raw_node_id, node_label) or raw_node_id
                                                 print(f"[Nexus] Bắt được sự kiện Polling từ 3D Bridge: {raw_node_id} -> {node_id}, Action: {action}")
                                                 try:
                                                     target_tab = None
                                                     if action == 'video': target_tab = tab_video
                                                     elif action == 'quiz': target_tab = tab_quiz
                                                     
                                                     if target_tab:
                                                         load_lesson_ui(node_id, target_tab=target_tab)
                                                     
                                                     if action == 'tutor':
                                                         try:
                                                             subject_id = os.path.basename(last_path).replace('.json', '')
                                                             ui.run_javascript(f"window.open('/quiz_node/{subject_id}/{node_id}', '_blank', 'width=1100,height=800,left=200,top=100')")
                                                         except Exception as tutor_e:
                                                             print(f"[Nexus] Lỗi khi mở Khảo Thí Cấp Cao: {tutor_e}")
                                                 except Exception as err:
                                                     print(f"[Nexus] Lỗi khi xử lý thao tác 3D: {err}")
                                     except Exception:
                                         pass

                                 # Install postMessage listener for Nexus
                                 ui.run_javascript('''
                                     if (!window.__nexus_postmsg_installed) {
                                         window.__nexus_postmsg_installed = true;
                                         window.addEventListener('message', function(event) {
                                             if (event.data && event.data.type === 'graph3d_action') {
                                                 console.log('[Nexus Bridge] postMessage received:', JSON.stringify(event.data.payload));
                                                 window.__nexus_postmsg_payload = event.data.payload;
                                             }
                                         });
                                         console.log('[Nexus Bridge] postMessage listener installed');
                                     }
                                 ''')

                                 # Poll every 500ms
                                 ui.timer(0.5, check_nexus_3d_bridge)

                                 # Hidden bridge element for iframe-to-parent communication
                                 bridge = ui.element('div').props('id="nexus-bridge"').classes('hidden')

                                 import time
                                 v = int(time.time())
                                 ui.element('iframe').props(f'src="/user_data/{user.username}/current_visual_tree.html?v={v}" width="100%" height="100%"').classes('w-full h-full border-none')
                 else:
                     with nexus_container:
                         ui.label('Không gian 3D chưa được thiết lập. Hãy tạo cây trong Graph Studio.').classes('text-gray-400 italic')
              
             tabs.on_value_change(lambda e: [activate_nexus() if e.value == tab_nexus else None])

        # TAB 3: VIDEO bài giảng
        with ui.tab_panel(tab_video).classes('p-0 h-full'):
             with ui.column().classes('w-full h-full p-0 relative'):
                 video_container = ui.column().classes('w-full h-full bg-black relative justify-center items-center')

        # TAB 4: QUIZ
        with ui.tab_panel(tab_quiz).classes('p-0 h-full'):
             with ui.column().classes('w-full h-full p-6 bg-gray-50 overflow-y-auto'):
                 lesson_label_quiz = ui.label("Vui lòng chọn bài học từ tab 'Hành trình'").classes('text-2xl text-gray-400 font-bold mb-6')
                 quiz_container = ui.column().classes('w-full')

        # TAB 5: GRAPH STUDIO (ADVANCED MGMT)
        with ui.tab_panel(tab_studio).classes('p-6 h-full bg-gray-50 overflow-y-auto w-full'):
             ui.label('Graph Studio').classes('text-3xl font-extrabold text-slate-800 mb-1 tracking-tight')
             ui.label('Quản trị Đồ thị Tri thức Đẳng cấp Quốc tế.').classes('text-slate-500 mb-8')
             
             # --- THƯ VIỆN MÔN HỌC ---
             library_container = ui.row().classes('w-full gap-4 mb-8')
             tree_preview_container = ui.column().classes('w-full mt-4')
             
             from step2_5_visualize_tree import visualize_knowledge_tree

             async def render_3d_graph(json_file_path):
                 try:
                     ui.notify('Đang kích hoạt Mạng Lưới Không Gian 3D...', type='info')
                     await run.io_bound(visualize_knowledge_tree, user.username, json_file_path)
                     tree_preview_container.clear()
                     with tree_preview_container:
                         ui.label('Mô hình Mạng lưới Giáo dục 3D (Tương tác):').classes('font-bold text-lg text-blue-800 mb-2 mt-4')
                         
                         # === ROBUST BRIDGE: postMessage listener + polling ===
                         def handle_studio_bridge_action(raw_node_id, action, node_label=''):
                             """Central handler for 3D graph bridge actions"""
                             if not raw_node_id:
                                 return
                             node_id = resolve_concept_id(raw_node_id, node_label) or raw_node_id
                             print(f"[Graph Studio] Bắt được sự kiện 3D Bridge: {raw_node_id} -> {node_id}, Action: {action}")
                             try:
                                 target_tab = None
                                 if action == 'video': target_tab = tab_video
                                 elif action == 'quiz': target_tab = tab_quiz
                                 if target_tab:
                                     load_lesson_ui(node_id, target_tab=target_tab)
                                 
                                 if action == 'tutor':
                                     import os
                                     subject_id = os.path.basename(json_file_path).replace('.json', '')
                                     ui.run_javascript(f"window.open('/quiz_node/{subject_id}/{node_id}', '_blank', 'width=1100,height=800,left=200,top=100')")
                             except Exception as err:
                                 print(f"[Graph Studio] Lỗi khi xử lý thao tác 3D: {err}")

                         # METHOD A: postMessage listener (most reliable for iframe communication)
                         async def check_studio_postmessage():
                             try:
                                 payload = await ui.run_javascript('''
                                     if (window.__studio_postmsg_payload) {
                                         let p = window.__studio_postmsg_payload;
                                         window.__studio_postmsg_payload = null;
                                         return p;
                                     }
                                     return null;
                                 ''', timeout=1.0)
                                 if payload and isinstance(payload, dict):
                                     node_id = payload.get('id')
                                     action = payload.get('action', 'video')
                                     node_label = payload.get('label', '')
                                     if node_id:
                                         handle_studio_bridge_action(node_id, action, node_label)
                             except Exception:
                                 pass

                         # Install postMessage listener on parent window
                         ui.run_javascript('''
                             if (!window.__studio_postmsg_installed) {
                                 window.__studio_postmsg_installed = true;
                                 window.addEventListener('message', function(event) {
                                     if (event.data && event.data.type === 'graph3d_action') {
                                         console.log('[Studio Bridge] postMessage received:', JSON.stringify(event.data.payload));
                                         window.__studio_postmsg_payload = event.data.payload;
                                     }
                                 });
                                 console.log('[Studio Bridge] postMessage listener installed');
                             }
                         ''')

                         # Poll every 500ms for postMessage payloads
                         ui.timer(0.5, check_studio_postmessage)
                         
                         # METHOD B: Also keep input bridge as fallback
                         def handle_3d_click(e):
                             if getattr(e, 'value', None) is None: return
                             import json as _json
                             try:
                                 payload = _json.loads(e.value)
                                 if payload and isinstance(payload, dict):
                                     node_id = payload.get('id')
                                     action = payload.get('action', 'video')
                                     node_label = payload.get('label', '')
                                     if node_id:
                                         handle_studio_bridge_action(node_id, action, node_label)
                             except Exception:
                                 pass
                                     
                         bridge = ui.input(on_change=handle_3d_click).props('id="studio-bridge"').classes('absolute -top-[1000px] left-0 opacity-0 z-[-1]')

                         import time
                         v = int(time.time())
                         ui.element('iframe').props(f'src="/user_data/{user.username}/current_visual_tree.html?v={v}" width="100%" height="100%"').classes('w-full h-[1200px] border-none rounded-xl shadow-lg')
                         
                         with open(json_file_path, 'r', encoding='utf-8') as f:
                             read_json = json.load(f)
                         with ui.expansion('Xem chi tiết cấu trúc JSON thô (Dành cho Dev)', icon='code').classes('w-full mt-4 bg-gray-50 border rounded-lg text-gray-700'):
                             ui.code(json.dumps(read_json, indent=2, ensure_ascii=False), language='json').classes('w-full overflow-y-auto max-h-[500px] border shadow-sm rounded')
                 except Exception as ex:
                     ui.notify(f'❌ Lỗi dựng đồ họa: {str(ex)}', type='negative')

             def render_library():
                 library_container.clear()
                 subj_file = f"user_data/{user.username}/subjects.json"
                 subjects_data = {"subjects": []}
                 if os.path.exists(subj_file):
                     with open(subj_file, 'r', encoding='utf-8') as sf:
                         subjects_data = json.load(sf)
                         
                 # ========== RESOURCE MANAGER DIALOG ==========
                 def open_resource_manager(tree_path, subject_title):
                     """Mở dialog quản lý tài nguyên học tập cho 1 môn học."""
                     with ui.dialog().props('maximized') as res_dialog, \
                          ui.card().classes('w-full h-full p-0 bg-gray-50'):
                         
                         # ===== HEADER =====
                         with ui.row().classes('w-full items-center px-6 py-4 bg-white border-b shadow-sm gap-4'):
                             ui.icon('link', size='md').classes('text-indigo-600')
                             with ui.column().classes('gap-0 flex-1'):
                                 ui.label('Quản lý Tài nguyên Học tập').classes('text-xl font-extrabold text-slate-800 tracking-tight')
                                 ui.label(subject_title).classes('text-sm text-slate-400')
                             # Stats badge
                             stats_badge = ui.label('').classes('text-xs bg-indigo-50 text-indigo-600 font-bold px-3 py-1 rounded-full border border-indigo-100')
                             ui.button(icon='close', on_click=res_dialog.close).props('flat round color=grey')
                         
                         def refresh_stats():
                             try:
                                 st = get_resource_stats(tree_path)
                                 stats_badge.text = f"📎 {st['total_resources']} tài nguyên · {st['nodes_with_resources']}/{st['total_nodes']} node"
                             except:
                                 stats_badge.text = ''
                         refresh_stats()

                         # ===== MAIN CONTENT: SPLITTER =====
                         with ui.splitter(value=35).classes('w-full flex-1').style('height: calc(100vh - 80px)') as splitter:
                             
                             # --- LEFT: NODE LIST ---
                             with splitter.before:
                                 with ui.column().classes('w-full h-full p-0'):
                                     # Search bar
                                     node_search = ui.input(placeholder='Tìm node...').props('outlined dense clearable').classes('w-full px-3 pt-3')
                                     node_search.on('update:model-value', lambda: render_node_list())
                                     
                                     node_list_container = ui.scroll_area().classes('w-full flex-1')

                             # --- RIGHT: RESOURCE DETAIL ---
                             with splitter.after:
                                 detail_container = ui.scroll_area().classes('w-full h-full')
                         
                         # State
                         selected_node_id = {'value': None}

                                                  # ===== RENDER NODE LIST (Hierarchical) =====
                         def render_node_list():
                             node_list_container.clear()
                             try:
                                 # Sử dụng cấu trúc phân cấp mới
                                 tree_structure = get_hierarchical_nodes(tree_path)
                             except Exception as ex:
                                 with node_list_container:
                                     ui.label(f'Lỗi: {ex}').classes('text-red-500 p-4')
                                 return

                             search_q = (node_search.value or '').lower().strip()
                             type_icons = {'macro': '🌐', 'micro': '📚', 'assess': '🧪'}

                             def render_node_item(n, level=0):
                                 """Hàm đệ quy hoặc lồng nhau để vẽ từng node card."""
                                 # Kiểm tra điều kiện mở khóa (Prerequisites)
                                 is_accessible = True
                                 missing_prereqs = []
                                 if n['type'] != 'macro':
                                     # Lấy state hiện tại (đã được fetch ở main hoặc load từ DB)
                                     # Ở đây dùng logic từ StudentState lặp lại hoặc tiêm vào
                                     # Để đơn giản và nhanh, ta dùng function check nội bộ
                                     is_accessible, missing_prereqs = state.is_node_accessible(n['id'], n.get('prerequisites', []))
                                 
                                 is_sel = selected_node_id['value'] == n['id']
                                 base_cls = 'bg-white hover:bg-indigo-50 border-gray-100'
                                 if is_sel: base_cls = 'bg-indigo-100 border-indigo-400 shadow-sm'
                                 if not is_accessible: base_cls = 'bg-slate-50 border-gray-200 opacity-60 grayscale-[0.5]'
                                 
                                 ml_val = level * 4
                                 
                                 with ui.card().classes(f'w-full p-2 mb-1 cursor-pointer border transition-all rounded-lg {base_cls} ml-{ml_val}').on('click', lambda nid=n['id']: select_node(nid)):
                                     with ui.row().classes('w-full items-center gap-2 no-wrap'):
                                         if not is_accessible:
                                             ui.label('🔒').classes('text-xs text-slate-400')
                                         else:
                                             ui.label(type_icons.get(n['type'], '📌')).classes('text-xs opacity-70')
                                             
                                         with ui.column().classes('flex-1 gap-0 overflow-hidden'):
                                             ui.label(n['label']).classes(f'text-[13px] font-semibold {"text-slate-400" if not is_accessible else "text-slate-700"} truncate')
                                             ui.label(n['id']).classes('text-[9px] text-gray-400 font-mono')
                                         
                                         if n.get('resource_count', 0) > 0:
                                             ui.badge(str(n['resource_count']), color='indigo').props('rounded').classes('text-[9px] px-1 min-w-[18px]')

                             with node_list_container:
                                 with ui.column().classes('w-full gap-1 p-3'):
                                     for chap in tree_structure:
                                         lessons = chap.get('children', [])
                                         match_chap = search_q in chap['label'].lower() or search_q in chap['id'].lower()
                                         match_any_child = any(search_q in l['label'].lower() or search_q in l['id'].lower() for l in lessons)
                                         
                                         if search_q and not match_chap and not match_any_child:
                                             continue

                                         is_expanded = bool(search_q) or any(selected_node_id['value'] == l['id'] for l in lessons) or selected_node_id['value'] == chap['id']
                                         
                                         with ui.expansion('', icon=type_icons['macro']).classes('w-full border border-gray-100 rounded-lg mb-1 overflow-hidden').props(f'header-class="text-sm font-bold text-slate-800 p-2 bg-slate-50" {"value" if is_expanded else ""}') as exp:
                                             with exp.add_slot('header'):
                                                 with ui.row().classes('items-center w-full justify-between pr-4'):
                                                     with ui.row().classes('items-center gap-2'):
                                                         ui.label(type_icons['macro']).classes('text-lg')
                                                         ui.label(chap['label']).classes('text-sm font-bold truncate').style('max-width: 180px')
                                                     
                                                     total_res = chap.get('total_resource_count', 0)
                                                     if total_res > 0:
                                                         ui.badge(f"{total_res} 📎", color='blue-6').props('outline rounded').classes('text-[10px]')

                                             with ui.column().classes('w-full pl-2 border-l-2 border-indigo-100 ml-4 py-1 gap-1'):
                                                 if not search_q or match_chap:
                                                     render_node_item(chap, level=0)
                                                 for les in lessons:
                                                     if search_q and search_q not in les['label'].lower() and search_q not in les['id'].lower() and not match_chap:
                                                         continue
                                                     render_node_item(les, level=0)
                                                     for assess in les.get('children', []):
                                                         render_node_item(assess, level=1)
                         
                         # ===== SELECT NODE =====
                         def select_node(node_id):
                             selected_node_id['value'] = node_id
                             render_node_list()
                             render_detail(node_id)
                         
                         # ===== RENDER DETAIL PANEL =====
                         def render_detail(node_id):
                             detail_container.clear()
                             
                             try:
                                 resources = get_node_resources(tree_path, node_id)
                                 all_nodes = get_all_nodes_summary(tree_path)
                                 node_info = next((n for n in all_nodes if n['id'] == node_id), None)
                             except Exception as ex:
                                 with detail_container:
                                     ui.label(f'Lỗi: {ex}').classes('text-red-500 p-6')
                                 return
                             
                             node_label = node_info['label'] if node_info else node_id
                             
                             with detail_container:
                                 with ui.column().classes('w-full p-6 gap-4'):
                                     # Node header
                                     with ui.row().classes('items-center gap-3 mb-2'):
                                         type_icons = {'macro': '🌐', 'micro': '📚', 'assess': '🧪'}
                                         ui.label(type_icons.get(node_info['type'] if node_info else '', '📌')).classes('text-2xl')
                                         with ui.column().classes('gap-0'):
                                             ui.label(node_label).classes('text-xl font-bold text-slate-800')
                                             ui.label(f'ID: {node_id}').classes('text-xs text-gray-400 font-mono')
                                     
                                     ui.separator()
                                     
                                     # ===== ADD RESOURCE FORM =====
                                     ui.label('Thêm tài nguyên mới').classes('text-sm font-bold text-indigo-700 uppercase tracking-wide')
                                     
                                     with ui.card().classes('w-full p-4 bg-indigo-50/50 border border-indigo-100 rounded-xl'):
                                         input_url = ui.input(label='URL tài nguyên', placeholder='https://youtube.com/watch?v=...').props('outlined dense').classes('w-full mb-2')
                                         input_title = ui.input(label='Tiêu đề (tùy chọn)', placeholder='Tự động phát hiện nếu để trống').props('outlined dense').classes('w-full mb-2')
                                         
                                         # URL preview
                                         url_preview = ui.label('').classes('text-xs text-gray-500 italic mb-2')
                                         
                                         def on_url_change():
                                             url_val = input_url.value or ''
                                             if url_val.startswith('http'):
                                                 _, icon, name = detect_resource_type(url_val)
                                                 url_preview.text = f'{icon} Loại phát hiện: {name}'
                                             else:
                                                 url_preview.text = ''
                                         input_url.on('update:model-value', lambda: on_url_change())
                                         
                                         def do_add_resource():
                                             url_val = (input_url.value or '').strip()
                                             title_val = (input_title.value or '').strip()
                                             if not url_val:
                                                 ui.notify('Vui lòng nhập URL', type='warning')
                                                 return
                                             if not url_val.startswith('http'):
                                                 ui.notify('URL phải bắt đầu bằng http:// hoặc https://', type='warning')
                                                 return
                                             try:
                                                 res = add_resource(tree_path, node_id, url_val, title_val)
                                                 ui.notify(f'✅ Đã thêm: {res["title"]}', type='positive')
                                                 input_url.value = ''
                                                 input_title.value = ''
                                                 url_preview.text = ''
                                                 render_detail(node_id)
                                                 render_node_list()
                                                 refresh_stats()
                                             except ValueError as ve:
                                                 ui.notify(f'⚠️ {ve}', type='warning')
                                             except Exception as ex:
                                                 ui.notify(f'❌ Lỗi: {ex}', type='negative')
                                         
                                         ui.button('Thêm tài nguyên', icon='add_link', on_click=do_add_resource).props('color=indigo unelevated rounded').classes('w-full font-bold')
                                     
                                     # ===== EXISTING RESOURCES =====
                                     ui.label(f'Tài nguyên hiện có ({len(resources)})').classes('text-sm font-bold text-slate-600 uppercase tracking-wide mt-2')
                                     
                                     if not resources:
                                         with ui.card().classes('w-full p-6 bg-gray-50 border border-dashed border-gray-200 rounded-xl text-center'):
                                             ui.label('📭').classes('text-4xl mb-2')
                                             ui.label('Chưa có tài nguyên nào').classes('text-gray-400 font-medium')
                                             ui.label('Thêm link YouTube, PDF, Google Docs... ở trên').classes('text-xs text-gray-300')
                                     else:
                                         for res in resources:
                                             res_id = res.get('id', '')
                                             res_icon = res.get('icon', '🌐')
                                             res_type = res.get('type', 'web')
                                             res_title = res.get('title', 'Untitled')
                                             res_url = res.get('url', '')
                                             
                                             type_color_map = {
                                                 'youtube': 'border-l-red-400 bg-red-50/30',
                                                 'pdf': 'border-l-orange-400 bg-orange-50/30',
                                                 'gdoc': 'border-l-blue-400 bg-blue-50/30',
                                                 'gsheet': 'border-l-green-400 bg-green-50/30',
                                                 'gslide': 'border-l-yellow-400 bg-yellow-50/30',
                                                 'colab': 'border-l-purple-400 bg-purple-50/30',
                                                 'gdrive': 'border-l-emerald-400 bg-emerald-50/30',
                                                 'github': 'border-l-gray-700 bg-gray-50/30',
                                                 'kaggle': 'border-l-cyan-400 bg-cyan-50/30',
                                                 'wiki': 'border-l-slate-400 bg-slate-50/30',
                                                 'arxiv': 'border-l-rose-400 bg-rose-50/30',
                                             }
                                             card_cls = type_color_map.get(res_type, 'border-l-indigo-300 bg-white')
                                             
                                             with ui.card().classes(f'w-full p-3 rounded-lg border-l-4 {card_cls} shadow-sm hover:shadow transition-all'):
                                                 with ui.row().classes('w-full items-center gap-3'):
                                                     ui.label(res_icon).classes('text-xl')
                                                     with ui.column().classes('flex-1 gap-0 min-w-0'):
                                                         ui.label(res_title).classes('text-sm font-semibold text-slate-700 truncate')
                                                         ui.link(res_url, res_url, new_tab=True).classes('text-[11px] text-indigo-400 truncate hover:text-indigo-600').style('max-width: 350px; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap')
                                                         with ui.row().classes('gap-2 mt-1'):
                                                             ui.badge(res_type.upper(), color='gray').props('dense rounded').classes('text-[9px]')
                                                             added = res.get('added_at', '')
                                                             if added:
                                                                 ui.label(added[:10]).classes('text-[9px] text-gray-300')
                                                     with ui.row().classes('gap-1'):
                                                         ui.button(icon='open_in_new', on_click=lambda u=res_url: ui.run_javascript(f'window.open("{u}", "_blank")')).props('flat round size=sm color=indigo').tooltip('Mở link')
                                                         ui.button(icon='delete_outline', on_click=lambda rid=res_id: do_remove(node_id, rid)).props('flat round size=sm color=red').tooltip('Xóa')
                                     
                                     def do_remove(nid, rid):
                                         try:
                                             if remove_resource(tree_path, nid, rid):
                                                 ui.notify('🗑️ Đã xóa tài nguyên', type='info')
                                                 render_detail(nid)
                                                 render_node_list()
                                                 refresh_stats()
                                             else:
                                                 ui.notify('Không tìm thấy tài nguyên', type='warning')
                                         except Exception as ex:
                                             ui.notify(f'❌ Lỗi: {ex}', type='negative')
                         
                         # Initial render
                         render_node_list()
                         with detail_container:
                             with ui.column().classes('w-full h-full items-center justify-center p-12'):
                                 ui.label('📎').classes('text-6xl mb-4')
                                 ui.label('Chọn một node bên trái').classes('text-xl font-bold text-gray-300')
                                 ui.label('để quản lý tài nguyên học tập').classes('text-sm text-gray-300')
                     
                     res_dialog.open()

                 with library_container:
                     if subjects_data["subjects"]:
                         ui.label('Thư viện Tri thức của bạn').classes('text-xl font-bold text-gray-800 w-full mb-2 border-b pb-2')
                         for subj in subjects_data["subjects"]:
                             subj_id = os.path.basename(subj.get('filename', '')).replace('.json', '')
                             with ui.card().classes('w-[280px] p-4 bg-white shadow border-t-4 border-blue-500 hover:shadow-lg transition-all'):
                                 ui.label(subj.get('title', 'Môn học')).classes('font-bold text-lg text-blue-900 mb-1 truncate').tooltip(subj.get('title'))
                                 ui.label(f"Nodes: {subj.get('total_nodes', 0)}").classes('text-sm text-gray-500 mb-3')
                                 # Bắt async function trong lambda bằng wrapper
                                 async_handler = lambda p=subj.get('filename'): getattr(ui, 'timer')(0, lambda: render_3d_graph(p), once=True)
                                 ui.button('Phân giải 3D', on_click=async_handler).props('outline color=blue size=sm').classes('w-full font-bold shadow-sm mb-2')
                                 ui.button('📎 Quản lý Tài nguyên', on_click=lambda p=subj.get('filename'), t=subj.get('title', 'Môn học'): open_resource_manager(p, t)).props('outline color=indigo size=sm').classes('w-full font-bold shadow-sm mb-2')
                                 with ui.row().classes('w-full gap-1 mb-1'):
                                     ui.button('📚 Flashcards', on_click=lambda sid=subj_id: ui.navigate.to(f'/flashcards/{sid}')).props('outline color=cyan size=sm dense').classes('flex-1 text-xs')
                                     ui.button('⚡ Đua tốc độ', on_click=lambda sid=subj_id: ui.navigate.to(f'/timed_challenge/{sid}')).props('outline color=amber size=sm dense').classes('flex-1 text-xs')
                                 with ui.row().classes('w-full gap-1'):
                                     ui.button('🏃 Marathon', on_click=lambda sid=subj_id: ui.navigate.to(f'/practice/{sid}/marathon')).props('outline color=green size=sm dense').classes('flex-1 text-xs')
                                     ui.button('🎯 Điểm yếu', on_click=lambda sid=subj_id: ui.navigate.to(f'/practice/{sid}/weak_focus')).props('outline color=red size=sm dense').classes('flex-1 text-xs')

             # Khởi tạo thư viện lần đầu
             render_library()

             with ui.row().classes('w-full gap-6 items-start flex-nowrap'):
                 # --- CARD 1: XÂY DỰNG CÂY (.txt) ---
                 with ui.card().classes('w-full md:w-[48%] flex-1 p-4 shadow-sm bg-white border border-gray-100'):
                     ui.label('Bước 1: Khởi tạo Cây Tri Thức').classes('text-lg font-bold text-blue-700')
                     ui.label('1. Tải lên file văn bản (.txt) tài liệu môn học.').classes('text-sm text-gray-600 mb-1')
                     ui.label('2. Trí tuệ Nhân tạo sẽ tự động phân tích thành cấu trúc JSON.').classes('text-sm text-gray-600 mb-4')
                     
                     upload_status_txt = ui.label('').classes('italic text-gray-400 mb-2')
                     actions_txt = ui.row().classes('w-full mt-2')

                     async def handle_upload_txt(e):
                         filename = getattr(e, 'name', 'tài liệu')
                         upload_status_txt.text = f'⏳ Đang xử lý {filename}... (quá trình này mất khoảng 20s)'
                         actions_txt.clear()
                         
                         if hasattr(e, 'content'): content_bytes = e.content.read()
                         elif hasattr(e, 'file'): content_bytes = await e.file.read()
                         else: raise Exception("Lỗi đọc file upload")
                             
                         content = content_bytes.decode('utf-8') if hasattr(content_bytes, 'decode') else content_bytes
                         content = content[:15000] # Bảo vệ API giới hạn độ dài
                         
                         from step1_build_tree import build_tree_for_user
                         from step2_build_edges import build_edges_for_user
                         try:
                             ui.notify(f'AI đang đọc hiểu nội dung {filename}...', type='info')
                             path, data = await run.io_bound(build_tree_for_user, user.username, content)
                             if data:
                                 upload_status_txt.text = f'⏳ Đang suy luận các mối quan hệ logic (Edges)...'
                                 await run.io_bound(build_edges_for_user, user.username)
                                 
                                 upload_status_txt.text = f'✅ Hoàn tất Khởi tạo!'
                                 ui.notify('Đã sinh cấu trúc Cây Tri Thức', type='positive')
                                 
                                 with actions_txt:
                                     ui.label(f'Thành quả phân tích đã được lưu trữ dưới dạng JSON.').classes('text-green-600 font-bold w-full mb-1')
                                     ui.button('Tải xuống JSON', on_click=lambda: ui.download(path, f"{user.username}_knowledge_tree.json")).props('color=blue icon=download outline rounded')
                             else:
                                 upload_status_txt.text = '❌ Tạo cây thất bại (lỗi AI).'
                         except Exception as ex:
                             upload_status_txt.text = f'❌ Lỗi: {str(ex)}'

                     ui.upload(on_upload=handle_upload_txt, auto_upload=True, multiple=False, label='Chọn file Đầu Vào (.txt)').props('bordered accept=".txt"').classes('w-full bg-blue-50 hover:bg-blue-100 rounded border-dashed border-2 border-blue-300')

                 # --- CARD 2: NHẬP VÀO THƯ VIỆN (.json) ---
                 with ui.card().classes('w-full md:w-[48%] flex-1 p-4 shadow-sm bg-white border border-gray-100'):
                     ui.label('Bước 2: Nhập vào Thư Viện').classes('text-lg font-bold text-green-700')
                     ui.label('Tải lên JSON Cây Tri Thức để lưu vào Thư Viện và tạo liên kết 3D.').classes('text-sm text-gray-600 mb-4')
                     upload_status_json = ui.label('').classes('italic text-gray-400 mb-2')

                     async def handle_upload_json(e):
                         filename = getattr(e, 'name', 'dữ liệu JSON')
                         upload_status_json.text = f'⏳ Đang lưu trữ...'
                         
                         if hasattr(e, 'content'): content_bytes = e.content.read()
                         elif hasattr(e, 'file'): content_bytes = await e.file.read()
                         else: raise Exception("Lỗi đọc file upload")
                             
                         out_dir = f"user_data/{user.username}/trees"
                         os.makedirs(out_dir, exist_ok=True)
                         
                         uid = uuid.uuid4().hex[:8]
                         out_path = f"{out_dir}/{uid}.json"
                         
                         with open(out_path, "wb") as f:
                             f.write(content_bytes)

                         # Bóc tách metadata
                         tree_data = json.loads(content_bytes.decode('utf-8'))
                         course_title = tree_data.get('course_name') or tree_data.get('title') or f"Môn học tải lên ({uid})"
                         total_nodes = len(tree_data.get('macro_nodes', [])) + len(tree_data.get('micro_nodes', [])) + len(tree_data.get('assess_nodes', []))
                         
                         subj_file = f"user_data/{user.username}/subjects.json"
                         subjects_data = {"subjects": []}
                         if os.path.exists(subj_file):
                             with open(subj_file, 'r', encoding='utf-8') as sf:
                                 subjects_data = json.load(sf)
                                 
                         # Check duplicate
                         if not any(s['title'] == course_title for s in subjects_data["subjects"]):
                             subjects_data["subjects"].append({
                                 "id": uid,
                                 "title": course_title,
                                 "filename": out_path,
                                 "total_nodes": total_nodes
                             })
                             with open(subj_file, 'w', encoding='utf-8') as sf:
                                 json.dump(subjects_data, sf, ensure_ascii=False, indent=2)

                         try:
                             upload_status_json.text = f'⏳ Đang biên dịch Đồ họa (Flat Graph)...'
                             await render_3d_graph(out_path)
                             upload_status_json.text = f'✅ Lưu vào Thư viện thành công!'
                             render_library() # Render lại hàng thư viện ở trên
                         except Exception as ex:
                             upload_status_json.text = f'❌ Lỗi dựng đồ họa: {str(ex)}'

                     ui.upload(on_upload=handle_upload_json, auto_upload=True, multiple=False, label='Nhập thẻ file (.json)').props('bordered accept=".json"').classes('w-full bg-green-50 hover:bg-green-100 rounded border-dashed border-2 border-green-300')

             # Chuyển container đồ họa xuống bên dưới
             tree_preview_container = ui.column().classes('w-full mt-8')

        # TAB 5: TUTOR AI
        with ui.tab_panel(tab_tutor).classes('p-0 h-full bg-slate-50'):
             with ui.splitter(value=65).classes('w-full h-full').props('separator-class="bg-blue-100"') as main_splitter:
                 with main_splitter.before:
                     with ui.splitter(horizontal=True, value=25).classes('w-full h-full').props('separator-class="bg-blue-100"') as left_splitter:
                         
                         def toggle_problem_panel():
                             if left_splitter.value > 8:
                                 left_splitter.value = 6
                             else:
                                 left_splitter.value = 25

                         with left_splitter.before:
                             with ui.column().classes('w-full h-full bg-slate-50 relative no-wrap') as problem_panel:
                                 with ui.row().classes('w-full h-full p-4 no-wrap gap-4 items-stretch') as problem_content_container:
                                     with ui.column().classes('flex-grow h-full no-wrap bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden'):
                                         with ui.row().classes('w-full bg-blue-50/50 p-2 items-center border-b border-blue-100 justify-between'):
                                             with ui.row().classes('items-center gap-2'):
                                                 ui.icon('assignment', color='blue-600').classes('text-lg ml-2')
                                                 ui.label('Đề bài & Yêu cầu').classes('font-bold text-blue-900')
                                             ui.button(icon='expand_less', on_click=toggle_problem_panel).props('flat round size=sm color=gray')
                                         with ui.scroll_area().classes('w-full flex-grow p-4'):
                                             tutor_problem = ui.textarea(placeholder='Nhập nội dung đề bài vào đây...').classes('w-full text-base').props('borderless autogrow autofocus')
                                     
                                     with ui.column().classes('justify-start w-[180px] shrink-0 pt-2'):
                                         ui.button('Bắt đầu làm bài', on_click=lambda: getattr(ui, 'timer')(0.1, tutor_start_exercise, once=True)).classes('w-full bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-md hover:shadow-lg font-bold py-3 transition-all').props('rounded text-color="white" icon="play_arrow"')
                         
                         with left_splitter.separator:
                             with ui.row().classes('w-full h-full items-center justify-center bg-gray-200/50 transition hover:bg-blue-200 cursor-row-resize'):
                                 ui.icon('drag_handle', color='gray').classes('text-lg')

                         with left_splitter.after:
                             with ui.column().classes('flex-grow h-full bg-gray-50 flex flex-col w-full no-wrap relative'):
                                 with ui.row().classes('w-full p-4 items-center border-b border-gray-200 bg-white shadow-sm z-10'):
                                     ui.icon('code', color='green-600').classes('text-2xl')
                                     ui.label('Không gian làm bài').classes('font-bold text-gray-800 text-lg')
                                 with ui.scroll_area().classes('w-full flex-grow p-4 bg-white shadow-inner'):
                                     tutor_workspace = ui.textarea(placeholder='Hãy trình bày lời giải của bạn...').classes('w-full text-base font-mono').props('borderless autogrow')
                                 
                                 def send_predefined_prompt(action):
                                     if action == 'run':
                                         tutor_input.value = "Đóng vai trình biên dịch, hãy thử chạy hoặc phân tích đoạn code/lời giải trong Không gian làm bài của tôi."
                                     elif action == 'eval':
                                         tutor_input.value = "Đây là phần làm bài của tôi, hãy chấm điểm và đánh giá sửa lỗi chi tiết nhé."
                                     elif action == 'help':
                                         tutor_input.value = "Tôi chưa rõ cách giải quyết. Hãy giảng lại giúp tôi phần kiến thức lý thuyết cơ bản (công thức, khái niệm trọng tâm) cần để giải quyết bước tiếp theo nhé."
                                     getattr(ui, 'timer')(0.1, tutor_send_message, once=True)

                                 with ui.row().classes('w-full p-3 border-t border-gray-200 bg-gray-50 gap-4 justify-center items-center shadow-[0_-2px_4px_rgba(0,0,0,0.02)]'):
                                     ui.button('▶ Chạy code', on_click=lambda: send_predefined_prompt('run')).classes('bg-green-600 text-white hover:bg-green-700 transition').props('unelevated rounded')
                                     ui.button('💬 Chấm bài & Đánh giá', on_click=lambda: send_predefined_prompt('eval')).classes('bg-blue-600 text-white hover:bg-blue-700 transition').props('unelevated rounded')
                                     ui.button('💡 AI Giúp đỡ', on_click=lambda: send_predefined_prompt('help')).classes('bg-yellow-600 text-white hover:bg-yellow-700 transition').props('unelevated rounded')

                 with main_splitter.separator:
                     with ui.column().classes('w-full h-full items-center justify-center bg-gray-200/50 transition hover:bg-blue-200 cursor-col-resize'):
                         ui.icon('drag_indicator', color='gray').classes('text-lg')

                 with main_splitter.after:
                     with ui.column().classes('w-full h-full bg-white flex flex-col shadow-[0_0_15px_rgba(0,0,0,0.05)] z-20 no-wrap'):
                         with ui.row().classes('w-full p-4 items-center border-b border-gray-100 bg-gradient-to-r from-blue-50 to-white shadow-sm'):
                             ui.avatar(icon='smart_toy', color='blue-600', text_color='white').props('size=sm')
                             ui.label('Gia sư AI').classes('font-bold text-blue-900 ml-2')
                         
                         with ui.scroll_area().classes('flex-grow w-full p-4 bg-gray-50/50') as tutor_chat_scroll:
                             # KHU VỰC ĐIỀU KHIỂN HỌC TẬP AIEDU QUỐC TẾ
                             with ui.row().classes('w-full justify-center gap-6 mb-6 pb-4 border-b border-gray-200'):
                                 ui.button('Khám Sức Khỏe Học Tập (Context-Aware)', on_click=lambda: tutor_diagnose_state()).classes('bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:scale-105 transition shadow-lg').props('rounded icon="health_and_safety"')
                                 ui.button('Lập Thiết Kế GANTT (7 Ngày)', on_click=lambda: tutor_gantt_planner()).classes('bg-gradient-to-r from-rose-500 to-red-600 text-white hover:scale-105 transition shadow-lg').props('rounded icon="calendar_month"')
                             
                             tutor_chat_container = ui.column().classes('w-full gap-4')
                             with tutor_chat_container:
                                 with ui.row().classes('w-full no-wrap items-start gap-3'):
                                     ui.icon('auto_awesome', color='blue-600').classes('text-xl mt-1')
                                     with ui.column().classes('bg-blue-50/60 p-3 rounded-2xl rounded-tl-sm shadow-sm w-full'):
                                          ui.markdown('Chào bạn, mình là Gia sư AI Toàn tri (Omnipresent Tutor) phiên bản Đại học Quốc tế. Mình có khả năng đọc được quá trình học của bạn. Bấm thử nút chức năng bên trên hoặc tự nhập câu hỏi bên dưới nhé!')
                         
                         async def send_hidden_system_prompt(sys_prompt):
                             with tutor_chat_container:
                                 spinner = ui.row().classes('items-center gap-2')
                                 with spinner:
                                     ui.spinner('dots', size='md', color='purple-500')
                                     ui.label('Trợ lý Thông minh đang phân tích màng lưới tri thức sinh viên...').classes('text-purple-600 text-xs italic font-bold tracking-widest')
                             try:
                                 response = await run.io_bound(model.generate_content, sys_prompt)
                                 tutor_chat_container.remove(spinner)
                                 with tutor_chat_container:
                                     with ui.row().classes('w-full no-wrap items-start gap-3'):
                                         ui.icon('psychology', color='purple-600').classes('text-3xl mt-1 drop-shadow-md')
                                         with ui.column().classes('bg-purple-50/80 p-5 rounded-2xl rounded-tl-sm shadow-md border border-purple-200 w-full overflow-hidden'):
                                             ui.markdown(response.text)
                                 ui.run_javascript('setTimeout(() => { document.querySelector(".q-scrollarea__container").scrollTo(0, 9999); }, 300);')
                             except Exception as e:
                                 tutor_chat_container.remove(spinner)
                                 ui.notify(f"Lỗi Lõi Nhận Thức AI: {e}", type="negative")

                         def tutor_diagnose_state():
                             from aiedu_tutor_extensions import build_context_diagnosis_prompt
                             username = app.storage.user.get('username')
                             p = build_context_diagnosis_prompt(username)
                             if "Xin lỗi" in p: ui.notify(p, type='warning')
                             else: getattr(ui, 'timer')(0.1, lambda: send_hidden_system_prompt(p), once=True)

                         def tutor_gantt_planner():
                             from aiedu_tutor_extensions import build_gantt_planner_prompt
                             username = app.storage.user.get('username')
                             p = build_gantt_planner_prompt(username)
                             if "Xin lỗi" in p: ui.notify(p, type='warning')
                             else: getattr(ui, 'timer')(0.1, lambda: send_hidden_system_prompt(p), once=True)

                         async def tutor_start_exercise():
                             prob = tutor_problem.value
                             if not prob or not prob.strip():
                                 ui.notify('Vui lòng nhập đề bài trước khi bắt đầu!', type='warning')
                                 return
                             
                             if left_splitter.value > 8:
                                 toggle_problem_panel()
                             
                             with tutor_chat_container:
                                 spinner = ui.row().classes('items-center gap-2')
                                 with spinner:
                                     ui.spinner('dots', size='md', color='blue-500')
                                     ui.label('Đang phân tích đề bài...').classes('text-gray-400 text-xs italic')
                             
                             prompt = f"""Bạn là gia sư AI. Người học vừa nhập một đề bài mới để bắt đầu làm.
Đề bài: {prob}

Nhiệm vụ:
1. Gửi một lời chào thân thiện.
2. Xác nhận đã nhận đề bài và tóm tắt ngắn gọn yêu cầu (1-2 câu).
3. Khuyến khích người học bắt đầu suy nghĩ và viết lời giải vào "Không gian làm bài", sau đó nhấn "Gửi" ở khung chat để bạn hướng dẫn bước đầu tiên.
4. Trình bày bằng Markdown. KHÔNG giải bài toán lúc này.
5. BẮT BUỘC sử dụng cú pháp LaTeX: dùng `$$...$$` cho công thức tách dòng, và dùng `$ ... $` cho công thức trong dòng. Tuyệt đối KHÔNG dùng `\\(...\\)`.
6. Khi viết phép nhân trong công thức, dùng `\\cdot` hoặc viết liền (vd `2x^2`). TUYỆT ĐỐI KHÔNG dùng dấu `*` (asterisk) vì Markdown sẽ hiểu nhầm là in nghiêng. Nếu copy đề bài của học sinh, hãy tự động thay dấu `*` thành viết liền hoặc `\\cdot`.
7. Đảm bảo Xuống Dòng trước và sau mỗi gạch đầu dòng (`-` hoặc `*`) để danh sách hiển thị rõ ràng, không bị dính chùm.
"""
                             try:
                                 response = await run.io_bound(model.generate_content, prompt)
                                 tutor_chat_container.remove(spinner)
                                 with tutor_chat_container:
                                     with ui.row().classes('w-full no-wrap items-start gap-3'):
                                         ui.icon('auto_awesome', color='blue-600').classes('text-xl mt-1')
                                         with ui.column().classes('bg-blue-50/60 p-3 rounded-2xl rounded-tl-sm shadow-sm w-full overflow-hidden'):
                                             ui.markdown(response.text)
                                 ui.run_javascript('setTimeout(() => { if (window.MathJax) MathJax.typesetPromise(); }, 300);')
                             except Exception as e:
                                 tutor_chat_container.remove(spinner)
                                 with tutor_chat_container:
                                     with ui.row().classes('w-full no-wrap items-start gap-3'):
                                         ui.icon('error', color='red-500').classes('text-xl mt-1')
                                         with ui.column().classes('bg-red-50 p-3 rounded-2xl rounded-tl-sm shadow-sm w-full'):
                                             ui.markdown(f"**Lỗi:** {str(e)}").classes('text-red-600')
                         
                         async def tutor_send_message():
                             msg = tutor_input.value
                             if not msg: return
                             
                             with tutor_chat_container:
                                 with ui.row().classes('w-full no-wrap justify-end'):
                                     with ui.column().classes('bg-gray-100 p-3 rounded-2xl rounded-tr-sm max-w-[85%] shadow-sm'):
                                         ui.markdown(msg).classes('text-gray-800 font-medium')
                             tutor_input.value = ''
                             
                             with tutor_chat_container:
                                 spinner = ui.row().classes('items-center gap-2')
                                 with spinner:
                                     ui.spinner('dots', size='md', color='blue-500')
                                     ui.label('Đang suy nghĩ...').classes('text-gray-400 text-xs italic')
                             
                             try:
                                 problem_text = tutor_problem.value or "Chưa có đề bài"
                                 workspace_text = tutor_workspace.value or "Chưa có bài làm"
                                 
                                 prompt = f"""Bạn là gia sư AI. Người học đang hỏi bạn: "{msg}".
Đề bài của người học:
{problem_text}

Bài làm hiện tại của người học:
{workspace_text}

Nhiệm vụ:
1. Trả lời câu hỏi và hướng dẫn người học từng bước.
2. Tuyệt đối không đưa ra đáp án trực tiếp.
3. Chỉ hướng dẫn tiếp theo từ bài làm hiện tại.
4. Trình bày dưới dạng Markdown dễ đọc.
5. BẮT BUỘC sử dụng cú pháp LaTeX: dùng `$$...$$` cho công thức tách dòng, và dùng `$ ... $` cho công thức trong dòng. Tuyệt đối KHÔNG dùng `\\(...\\)`.
6. Khi viết phép nhân trong công thức, dùng `\\cdot` hoặc viết liền (vd `2x^2`). TUYỆT ĐỐI KHÔNG dùng dấu `*` (asterisk) vì Markdown sẽ hiểu nhầm là in nghiêng. Nếu copy đề bài của học sinh, hãy tự động thay dấu `*` thành viết liền hoặc `\\cdot`.
7. Đảm bảo Xuống Dòng trước và sau mỗi gạch đầu dòng (`-` hoặc `*`) để danh sách hiển thị rõ ràng, không bị dính chùm.
"""
                                 response = await run.io_bound(model.generate_content, prompt)
                                 tutor_chat_container.remove(spinner)
                                 with tutor_chat_container:
                                     with ui.row().classes('w-full no-wrap items-start gap-3'):
                                         ui.icon('auto_awesome', color='blue-600').classes('text-xl mt-1')
                                         with ui.column().classes('bg-blue-50/60 p-3 rounded-2xl rounded-tl-sm shadow-sm w-full overflow-hidden'):
                                             ui.markdown(response.text)
                                 ui.run_javascript('setTimeout(() => { if (window.MathJax) MathJax.typesetPromise(); }, 300);')
                             except Exception as e:
                                 tutor_chat_container.remove(spinner)
                                 with tutor_chat_container:
                                     with ui.row().classes('w-full no-wrap items-start gap-3'):
                                         ui.icon('error', color='red-500').classes('text-xl mt-1')
                                         with ui.column().classes('bg-red-50 p-3 rounded-2xl rounded-tl-sm shadow-sm w-full'):
                                             ui.markdown(f"**Lỗi:** {str(e)}").classes('text-red-600')
                                 
                         with ui.column().classes('w-full p-4 border-t border-gray-100 bg-white gap-2 z-10 no-wrap'):
                             with ui.row().classes('w-full items-center gap-2 relative'):
                                 tutor_input = ui.input(placeholder='Hỏi gia sư...').props('rounded outlined dense borderless').classes('w-full bg-gray-100 pr-10').on('keydown.enter', tutor_send_message)
                                 ui.button(icon='send', on_click=tutor_send_message).props('flat round dense color=blue').classes('absolute right-1 top-1/2 transform -translate-y-1/2')

        # TAB: LEADERBOARD (BẢNG XẾP HẠNG)
        with ui.tab_panel(tab_leaderboard).classes('p-6 h-full bg-gray-50 overflow-y-auto'):
            from leaderboard_page import create_leaderboard_section
            leaderboard_container = ui.column().classes('w-full')
            
            def load_leaderboard():
                create_leaderboard_section(user, leaderboard_container)
            
            # Load on tab switch
            tabs.on_value_change(lambda e: load_leaderboard() if e.value == tab_leaderboard else None)

        # TAB: HỒ SƠ (PROFILE)
        with ui.tab_panel(tab_profile).classes('p-6 h-full bg-gray-50 overflow-y-auto'):
            from profile_page import create_profile_section
            profile_container = ui.column().classes('w-full')
            
            def load_profile():
                create_profile_section(user, profile_container)
            
            # Load on tab switch
            tabs.on_value_change(lambda e: load_profile() if e.value == tab_profile else None)
            # Initial load
            load_profile()

# Đăng ký Giao diện Đánh giá Năng lực (Khảo Thí)
from quiz_page import register_quiz_page
register_quiz_page()

# Đăng ký Flashcard Mode
from flashcard_page import register_flashcard_page
register_flashcard_page()

# Đăng ký Timed Challenge Mode
from timed_challenge import register_timed_challenge_page
register_timed_challenge_page()

# Đăng ký Advanced Practice Mode
from advanced_practice import register_advanced_practice_page
register_advanced_practice_page()

# Đăng ký Spaced Repetition Review Page
from review_page import register_review_page
register_review_page()

# Đăng ký Parent Dashboard
from parent_dashboard import register_parent_dashboard
register_parent_dashboard()

# Đăng ký Teacher Dashboard
from teacher_dashboard import register_teacher_dashboard
register_teacher_dashboard()

# Đăng ký Health Check (API Monitor)
@app.get("/api/health")
def api_health_check():
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"status": "healthy", "version": "1.0.0", "app": "PKT Bio-Tutor"})

ui.run(storage_secret='pkt_secret_key', title='PKT Bio-Tutor', port=8081)

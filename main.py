from nicegui import ui, app, run
from data_manager import data_manager
from pkt_engine import StudentState
from bio_battery import BioBattery
from gemini_helper import extract_json_from_text, build_system_prompt, get_gemini_api_key
import google.generativeai as genai
from database import create_db_and_tables, create_user, get_user_by_username, authenticate_user, get_user_progress, get_or_create_google_user, update_user_drive_ids
from auth_service import create_login_page, create_register_page, is_logged_in, logout
from services.google_drive_service import GoogleDriveService
from config.google_oauth_config import GoogleOAuthConfig
import os
import json
import uuid
import asyncio
import shutil
import time
from resource_sync import sync_resources_to_tree

from utils import get_video_url
from profile_page import create_profile_section


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
from services.rag_service import RAGService
from services.task_broker import task_broker
from visuals.dynamic_graph import render_dynamic_tree
from xai_engine import explain_recommendation
from tour_guide import setup_tour_dependencies, trigger_tour
from ai_video_player import AIVideoPlayer
from resource_manager import (
    get_all_nodes_summary, get_node_resources, add_resource,
    remove_resource, detect_resource_type, get_resource_stats,
    get_hierarchical_nodes, get_node_detail, update_node_description
)
from omni_tutor_ui import build_omni_drawer
import re
from dashboard_admin import build_dashboard_admin_ui

# Create DB
create_db_and_tables()

# Serve local files
app.add_static_files('/Video', os.path.join(os.getcwd(), 'DB', 'Video'))
app.add_static_files('/audio', os.path.join(os.getcwd(), 'DB', 'audio'))
app.add_static_files('/user_data', os.path.join(os.getcwd(), 'user_data'))

# Cấu hình Gemini
from gemini_helper import get_gemini_api_key, get_chat_model

GOOGLE_API_KEY = get_gemini_api_key()
genai.configure(api_key=GOOGLE_API_KEY, transport='rest')

# Use robust model selector
model = get_chat_model()

# Start Task Broker
async def cleanup_guest_data():
    """Xóa dữ liệu khách đã quá 24 giờ để tiết kiệm dung lượng."""
    user_data_root = os.path.join(os.getcwd(), 'user_data')
    if not os.path.exists(user_data_root):
        return
    import time
    now = time.time()
    for item in os.listdir(user_data_root):
        if item.startswith('guest_'):
            path = os.path.join(user_data_root, item)
            if os.path.isdir(path):
                mtime = os.path.getmtime(path)
                if now - mtime > 86400: # 24h
                    try:
                        shutil.rmtree(path)
                        print(f"[Cleanup] Đã xóa thư mục khách cũ: {item}")
                    except Exception as e:
                        print(f"[Cleanup] Lỗi khi xóa {item}: {e}")

app.on_startup(task_broker.start_worker)
app.on_startup(cleanup_guest_data)

# Thêm MathJax để hiển thị công thức Toán
ui.add_head_html("""
<script>
  window.MathJax = {
    tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] },
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
<style>
  :fullscreen {
    background-color: #060714 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100vw !important;
    height: 100vh !important;
  }
  :fullscreen > * { 
    width: 100% !important; 
    height: 100% !important; 
  }
</style>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
""", shared=True)

setup_tour_dependencies()

# ============================================================
#  AUTH ROUTES
# ============================================================

@ui.page('/')
def root_page():
    """Root route - redirect based on auth status or show landing page"""
    if is_logged_in() or app.storage.user.get('role') == 'guest':
        ui.navigate.to('/app')
    else:
        from pages.landing_page import enter_guest_mode
        enter_guest_mode('Khám phá Tự do')

@ui.page('/welcome')
def welcome_page():
    """Landing page"""
    from pages.landing_page import create_landing_page
    create_landing_page()

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

# ============================================================
#  SPRINT 01: GOOGLE OAUTH ROUTES
# ============================================================

@ui.page('/auth/google/mock')
async def google_mock_login():
    """Simulate a successful Google Login for development/testing."""
    if not GoogleOAuthConfig.MOCK_MODE:
        ui.navigate.to('/login')
        return
    
    with ui.column().classes('w-full min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950'):
        ui.spinner('orbit', size='xl', color='blue-400')
        ui.label('Developer Mode: Đang giả lập Google Login...').classes('text-blue-300 text-lg mt-4 animate-pulse')
    
    await asyncio.sleep(1.5)
    
    # Giả lập dữ liệu callback
    mock_code = 'mock_auth_code_123'
    ui.navigate.to(f'/auth/google/callback?code={mock_code}')

@ui.page('/auth/google/login')
def google_login_redirect():
    """Redirect user to Google OAuth consent screen."""
    if not GoogleOAuthConfig.is_configured():
        ui.label('Google OAuth chưa được cấu hình. Vui lòng thiết lập CLIENT_ID và CLIENT_SECRET trong file .env').classes('text-red-500 text-center p-8')
        return
    
    # Tạo CSRF state token
    import secrets
    state = secrets.token_urlsafe(32)
    app.storage.user['oauth_state'] = state
    
    auth_url = GoogleDriveService.get_auth_url(state=state)
    ui.navigate.to(auth_url, new_tab=False)

@ui.page('/auth/google/callback')
async def google_callback(code: str = '', state: str = '', error: str = ''):
    """Handle Google OAuth callback after user consents."""
    from nicegui import ui
    
    with ui.column().classes('w-full min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950'):
        # Kiểm tra lỗi từ Google (VD: user bấm Cancel) ngay lập tức
        if error:
            ui.icon('error_outline', size='4rem', color='red-400')
            ui.label(f'Đăng nhập bị hủy: {error}').classes('text-red-400 text-lg')
            ui.button('Quay lại Đăng nhập', on_click=lambda: ui.navigate.to('/login')).classes('mt-4')
            return

        if not code:
            ui.navigate.to('/login')
            return

        # Hiển thị UI chờ
        ui.spinner('orbit', size='xl', color='blue-400')
        status_label = ui.label('Đang xác thực với Google...').classes('text-blue-300 text-lg mt-4 animate-pulse')

        async def do_work():
            try:
                # Bước 1: Đổi code lấy tokens
                status_label.text = '🔑 Đang lấy token xác thực...'
                tokens = await run.io_bound(GoogleDriveService.exchange_code, code)
                access_token = tokens.get('access_token')
                
                if not access_token:
                    raise Exception('Không nhận được access_token từ Google')
                
                # Bước 2: Lấy thông tin người dùng
                status_label.text = '👤 Đang lấy thông tin tài khoản...'
                user_info = await run.io_bound(GoogleDriveService.get_user_info, access_token)
                
                if not user_info:
                    raise Exception('Không thể lấy thông tin từ Google API')

                google_id = user_info.get('id', '')
                email = user_info.get('email', '')
                full_name = user_info.get('name', email.split('@')[0])
                avatar_url = user_info.get('picture', '')
                
                # Bước 3: Tìm hoặc tạo user trong database
                status_label.text = '📦 Đang thiết lập tài khoản...'
                user = await run.io_bound(
                    get_or_create_google_user,
                    google_id, email, full_name, avatar_url, tokens.get('refresh_token', '')
                )
                
                # Bước 4: Đăng nhập vào hệ thống
                app.storage.user['authenticated'] = True
                app.storage.user['id'] = user.id
                app.storage.user['username'] = user.username
                app.storage.user['full_name'] = user.full_name
                app.storage.user['role'] = user.role
                app.storage.user['is_onboarded'] = user.is_onboarded
                app.storage.user['google_access_token'] = access_token
                app.storage.user['login_method'] = 'google'
                
                # Bước 5: Khởi tạo Google Drive (chạy ngầm)
                status_label.text = '☁️ Đang kết nối Google Drive...'
                try:
                    drive_env = await run.io_bound(GoogleDriveService.init_drive_environment, access_token)
                    if drive_env:
                        profile_id = drive_env.get('profile_file_id', '')
                        app.storage.user['drive_profile_file_id'] = profile_id
                        
                        await run.io_bound(
                            update_user_drive_ids,
                            user.id,
                            drive_env.get('root_folder_id', ''),
                            drive_env.get('subjects_folder_id', ''),
                            profile_id
                        )
                        
                        # --- Task 2.4: Tải dữ liệu Profile vào StateManager ---
                        status_label.text = '📥 Đang đồng bộ dữ liệu cá nhân...'
                        service = GoogleDriveService._build_drive_service(access_token)
                        profile_json = await run.io_bound(GoogleDriveService.download_json_file, service, profile_id)
                        
                        if profile_json:
                            from services.state_manager import state_manager
                            state_manager.load_profile(profile_json, user.id, profile_id)
                except Exception as drive_err:
                    print(f'[OAuth] ⚠️ Lỗi khởi tạo/đồng bộ Drive: {drive_err}')
                
                status_label.text = '✨ Thành công! Đang vào hệ thống...'
                await asyncio.sleep(0.5)
                
                if user.is_onboarded:
                    ui.navigate.to('/app')
                else:
                    ui.navigate.to('/onboarding')
                    
            except Exception as e:
                print(f'[OAuth] ❌ Lỗi callback: {e}')
                status_label.text = f'❌ Đăng nhập thất bại: {str(e)}'
                status_label.classes(remove='animate-pulse', add='text-red-400')
                ui.button('Thử lại', on_click=lambda: ui.navigate.to('/login')).classes('mt-4 bg-blue-600 text-white px-6 py-2 rounded-xl')

        # Sử dụng timer để xử lý logic sau khi UI đã render
        ui.timer(0.1, do_work, once=True)

@ui.page('/onboarding')
async def onboarding_page():
    """Onboarding wizard for new users"""
    if not is_logged_in():
        ui.navigate.to('/login')
        return
    from onboarding import create_onboarding_wizard
    await create_onboarding_wizard()

@ui.page('/test_sync')
async def test_sync_page():
    """Trang kiểm tra tính năng Auto-Sync XP lên Drive."""
    if not is_logged_in():
        ui.navigate.to('/login')
        return
    
    from services.state_manager import state_manager
    
    # Đảm bảo dữ liệu được nạp vào RAM
    await state_manager.auto_rehydrate()
    
    with ui.column().classes('w-full items-center justify-center mt-10'):
        ui.label('Sprint 2: Auto-Sync Test').classes('text-3xl font-bold')
        
        # Hiển thị XP hiện tại từ StateManager (Cấu trúc phẳng)
        current_xp = state_manager.profile_data.get("total_xp", 0)
        xp_label = ui.label(f"XP hiện tại: {current_xp}").classes('text-xl')
        
        def add_xp():
            state_manager.add_xp(10)
            new_xp = state_manager.profile_data.get("total_xp", 0)
            xp_label.text = f"XP hiện tại: {new_xp}"
            ui.notify(f"Đã cộng 10 XP! Hệ thống sẽ tự đồng bộ sau 5 giây.", type='positive')

        ui.button('Cộng 10 XP', on_click=add_xp).classes('bg-green-500 text-white px-6 py-2 rounded-lg')
        ui.label('Mở terminal để xem log quá trình Sync ngầm.').classes('text-gray-500 mt-4')
        ui.button('Về trang chủ', on_click=lambda: ui.navigate.to('/app')).classes('mt-10')

@ui.page('/library/{subject_id}')
async def library_page(subject_id: str):
    """Trang quản lý tài liệu và RAG cho môn học."""
    if not is_logged_in():
        ui.navigate.to('/login')
        return

    from services.rag_service import RAGService
    
    with ui.column().classes('w-full max-w-4xl mx-auto p-6'):
        ui.label(f'Thư viện môn học: {subject_id}').classes('text-3xl font-bold mb-6')
        
        # --- Section 1: Upload PDF ---
        with ui.card().classes('w-full p-4 mb-6'):
            ui.label('📚 Tải lên tài liệu PDF để AI học').classes('text-xl font-semibold mb-2')
            
            progress_container = ui.column().classes('w-full hidden')
            with progress_container:
                status_msg = ui.label('Đang chuẩn bị...')
                progress_bar = ui.linear_progress(value=0, show_value=False).classes('w-full')
            
            async def handle_upload(e):
                progress_container.set_visibility(True)
                
                # --- CHẨN ĐOÁN (In ra terminal để debug) ---
                print(f"[DEBUG] Upload Event: {type(e)}")
                
                # 1. Lấy tên file (Thử mọi cách)
                file_name = None
                for attr in ['name', 'filename']:
                    if hasattr(e, attr):
                        file_name = getattr(e, attr)
                        break
                if not file_name and hasattr(e, 'args') and isinstance(e.args, dict):
                    file_name = e.args.get('name') or e.args.get('filename')
                
                if not file_name:
                    file_name = f"doc_{int(time.time())}.pdf"

                # 2. Lấy nội dung file (Thử mọi cách)
                content = None
                if hasattr(e, 'file'):
                    content = e.file
                    if not file_name:
                        file_name = getattr(e.file, 'name', f"doc_{int(time.time())}.pdf")
                elif hasattr(e, 'content'):
                    content = e.content
                elif hasattr(e, 'args') and isinstance(e.args, dict):
                    content = e.args.get('content')
                
                # Trường hợp e chính là một dictionary (một số bản cũ)
                if content is None and isinstance(e, dict):
                    content = e.get('content')
                    if not file_name: file_name = e.get('name')

                if content is None:
                    print(f"[DEBUG] Không tìm thấy content. Các thuộc tính hiện có: {dir(e)}")
                    ui.notify("❌ Không tìm thấy nội dung file. Hãy kiểm tra Terminal.", type='negative')
                    progress_container.set_visibility(False)
                    return

                temp_path = f"temp_rag/{subject_id}_{file_name}"
                os.makedirs("temp_rag", exist_ok=True)

                try:
                    with open(temp_path, 'wb') as f:
                        # Đọc dữ liệu (Xử lý cả trường hợp async read cho file lớn)
                        if hasattr(content, 'read'):
                            data = content.read()
                            if asyncio.iscoroutine(data):
                                data = await data
                        else:
                            data = content
                        f.write(data)
                except Exception as err:
                    ui.notify(f"❌ Lỗi ghi file: {err}", type='negative')
                    progress_container.set_visibility(False)
                    return
                
                def update_progress(val, msg):
                    try:
                        progress_bar.set_value(val)
                        status_msg.set_text(msg)
                    except Exception:
                        pass # Bỏ qua nếu element đã bị xóa (do F5)
                
                # Bắt đầu Ingestion
                progress_container.set_visibility(True)
                status_msg.set_text("🚀 Khởi động luồng RAG...")
                print(f"[RAG] 🚀 Bắt đầu Ingestion cho subject: {subject_id}")
                
                success, res = await RAGService.ingest_pdf(temp_path, subject_id, update_progress)
                if success:
                    # Đồng bộ lên Drive
                    print(f"[RAG] ☁️ Đang đồng bộ lên Drive...")
                    await RAGService.sync_to_drive(subject_id, app.storage.user['id'], temp_path, update_progress)
                    ui.notify('✅ Đã nạp tài liệu và đồng bộ Drive thành công!', type='positive')
                    status_msg.set_text("✅ Hoàn thành!")
                else:
                    print(f"[RAG] ❌ Lỗi: {res}")
                    ui.notify(f'❌ Lỗi RAG: {res}', type='negative')
                    status_msg.set_text(f"❌ Lỗi: {res}")
                    progress_bar.props('color=red')
                
                # Để thanh tiến trình hiện thêm 3 giây cho người dùng thấy kết quả
                await asyncio.sleep(3)
                progress_container.set_visibility(False)

            ui.upload(on_upload=handle_upload, label='Chọn file PDF (Sách, giáo trình...)', auto_upload=True).classes('w-full')

        # --- Section 2: Chat với tài liệu ---
        with ui.card().classes('w-full p-4'):
            ui.label('💬 Hỏi đáp với tài liệu (RAG)').classes('text-xl font-semibold mb-4')
            
            chat_container = ui.column().classes('w-full h-64 overflow-y-auto border p-2 mb-4 bg-gray-50')
            query_input = ui.input(placeholder='Hỏi gì đó về nội dung sách...').classes('w-full')
            
            async def ask_rag():
                q = query_input.value
                if not q: return
                query_input.value = ''
                
                with chat_container:
                    ui.label(f"User: {q}").classes('font-bold text-blue-600')
                    loading = ui.label("AI đang đọc sách...").classes('italic text-gray-500')
                
                response = await RAGService.query(subject_id, q)
                loading.delete()
                
                with chat_container:
                    ui.markdown(f"**AI:** {response}").classes('bg-white p-2 rounded shadow-sm')
                
                chat_container.scroll_to(1.0) # Scroll to bottom

            ui.button('Gửi câu hỏi', on_click=ask_rag).classes('w-full bg-blue-600 text-white')

        ui.button('Quay lại Dashboard', on_click=lambda: ui.navigate.to('/app')).classes('mt-6')

# ============================================================
#  MAIN APP (Protected)
# ============================================================

@ui.page('/pricing')
def pricing_route():
    from pricing_page import create_pricing_page
    create_pricing_page()

@ui.page('/app')
async def main_page():
    # --- AUTH CHECK ---
    is_guest = app.storage.user.get('role') == 'guest'
    if not is_guest and not is_logged_in():
        ui.navigate.to('/')
        return
    
    if is_guest:
        from datetime import datetime
        class MockGuestUser:
            id = 0
            username = app.storage.user.get('username', 'guest')
            full_name = app.storage.user.get('full_name', 'Khách viếng thăm')
            role = 'guest'
            email = "guest@example.com"
            avatar_url = ""
            bio = ""
            group = 'guest_exp'

            is_onboarded = True
            password = ""
            created_at = datetime.now()
            # Missing fields for profile page
            google_id = ""
            google_avatar_url = ""
            google_refresh_token = ""
            drive_root_folder_id = ""
            drive_subjects_folder_id = ""
            drive_profile_file_id = ""

        user = MockGuestUser()
    else:
        # Load user from session
        user = get_user_by_username(app.storage.user.get('username', ''))
        if not user:
            ui.navigate.to('/login')
            return
    
    app.storage.user['id'] = user.id
    app.storage.user['username'] = user.username

    # --- GAMIFICATION: Daily check-in ---
    try:
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
    except Exception as e:
        print(f"[Main] Gamification check-in error: {e}")

    # Initialize Student State
    try:
        if 'student_state_data' in app.storage.user:
            # Hydrate from dict
            state = StudentState.from_dict(app.storage.user['student_state_data'])
        else:
            # New State
            state = StudentState(user.id)
            app.storage.user['student_state_data'] = state.to_dict()
    except Exception as e:
        print(f"[Main] StudentState initialization error: {e}")
        state = StudentState(user.id) # Fallback to fresh state
    
    # Function to persist state
    def save_state():
        try:
            app.storage.user['student_state_data'] = state.to_dict()
        except: pass

    # --- CROSS-TAB SYNC REGISTRY ---
    # To allow tabs (UGC Store <-> Graph Studio) to refresh each other without F5
    view_refreshers = {
        'library': lambda: None, # Graph Studio (Personal Library)
        'public': lambda: None   # UGC Store
    }
    
    # Shared state for internal navigation (e.g. Graph Studio Library vs 3D)
    nav_state = {'is_in_studio_graph': False, 'back_to_library': None}

    # --- UI Components ---
    # --- UI Components ---
    dark = ui.dark_mode()
    left_drawer = ui.left_drawer(value=True, bordered=True).classes('bg-[#f8fafc] flex flex-col justify-between z-50').props('breakpoint=768')
    
    async def toggle_menu():
        left_drawer.toggle()

    with left_drawer:
        with ui.column().classes('w-full mt-4'):
            with ui.tabs().props('vertical active-color="primary" indicator-color="primary"').classes('w-full text-slate-600 font-medium z-10') as main_tabs:
                # ── TIER 0: HOME ──
                tab_dashboard = ui.tab('Tổng quan', icon='dashboard').classes('justify-start px-6 font-bold')
                
                # Tab Action Registry
                tab_actions = {}
                
                ui.separator().classes('my-2 w-[80%] mx-auto bg-gray-200')
                
                # ── TIER 1: PRIMARY LEARNING (Most Used) ──
                tab_nexus = ui.tab('Vũ trụ Tri thức 3D', icon='explore').classes('justify-start px-6 hidden')
                tab_library = ui.tab('Thư viện Bài học', icon='store').classes('justify-start px-6').props('id="tab-library"')
                
                ui.separator().classes('my-2 w-[80%] mx-auto bg-gray-200')
                
                # ── TIER 2-3: CREATION & MANAGEMENT ──
                tab_studio = ui.tab('Graph Studio', icon='architecture').classes('justify-start px-6').props('id="tab-studio"')
                tab_creator = ui.tab('Creator Hub (AI)', icon='add_circle').classes('justify-start px-6')
                
                ui.separator().classes('my-2 w-[80%] mx-auto bg-gray-200')
                
                # ── TIER 4-5: AI & ASSESSMENT ──
                tab_tutor = ui.tab('Gia sư AI (Omni)', icon='smart_toy').classes('justify-start px-6').props('id="tab-tutor"')
                tab_quiz = ui.tab('Kiểm tra & Đánh giá', icon='quiz').classes('justify-start px-6').props('id="tab-quiz"')
                tab_video = ui.tab('Học liệu & Bài giảng', icon='play_circle').classes('justify-start px-6').props('id="tab-video"')
                
                ui.separator().classes('my-2 w-[80%] mx-auto bg-gray-200')
                
                # ── GAMIFICATION ──
                tab_leaderboard = ui.tab('Xếp hạng', icon='leaderboard').classes('justify-start px-6')
                
                ui.separator().classes('my-2 w-[80%] mx-auto bg-gray-200')
                
                # ── BÁO CÁO (ADMIN) ──
                tab_admin = ui.tab('Báo cáo (Thử nghiệm)', icon='analytics').classes('justify-start px-6 font-bold text-indigo-700 bg-indigo-50')
                
                # Hidden/Experimental
                tab_journey = ui.tab('Hành trình', icon='insights').classes('justify-start px-6 hidden')
                tab_profile = ui.tab('profile', icon='person').props('label="Hồ sơ"').classes('justify-start px-6')

                tab_bloom = ui.tab('Bloom Hub', icon='psychology').classes('justify-start px-6 hidden')
                tab_social = ui.tab('Cộng đồng', icon='public').classes('justify-start px-6 hidden')
                tab_pricing = ui.tab('Gói thuê bao', icon='workspace_premium').classes('hidden')
        
        with ui.column().classes('w-full mt-auto mb-4 px-4 items-start'):
             def handle_tour_click():
                 v = main_tabs.value
                 if v == 'Thư viện Bài học':
                     trigger_tour('library')
                 elif v == 'Graph Studio':
                     trigger_tour('studio')
                 elif v in ['Học liệu & Bài giảng', 'Kiểm tra & Đánh giá', 'Gia sư AI (Omni)']:
                     trigger_tour('study')
                 else:
                     trigger_tour('dashboard')

             ui.button('Hướng dẫn sử dụng', icon='help_outline', on_click=handle_tour_click).props('flat text-color="blue-grey-6" no-caps size="sm"').classes('w-full justify-start')
             ui.label('Powered by Antigravity').classes('text-[10px] text-gray-400 font-mono w-full text-center mt-2')

    def handle_back_navigation():
        if main_tabs.value == 'Vũ trụ Tri thức 3D':
            main_tabs.value = tab_studio
        elif main_tabs.value == 'Graph Studio' and nav_state['is_in_studio_graph'] and nav_state['back_to_library']:
            nav_state['back_to_library']()
        else:
            main_tabs.value = tab_dashboard

    with ui.header().classes(replace='row items-center bg-white text-slate-800 p-2 h-[64px] shadow-sm z-40 justify-between flex-nowrap'):
        with ui.row().classes('items-center gap-1 md:gap-3 w-auto'):
            ui.button(icon='menu', on_click=toggle_menu).props('flat round dense color=blue-7')
            back_button = ui.button(icon='arrow_back', on_click=handle_back_navigation) \
                .props('flat round dense color=blue-7').classes('hidden')
            ui.label('PKT Bio-Tutor').classes('text-2xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 hidden md:block')

        # --- DYNAMIC LESSON TITLE IN HEADER ---
        header_lesson_container = ui.row().classes('items-center gap-2 flex-grow justify-center overflow-hidden hidden md:flex')

        # Right side info
        with ui.row().classes('items-center justify-end gap-1.5 sm:gap-3 flex-nowrap pr-1 md:pr-2'):
            prediction_label = ui.label('').classes('text-xs font-bold text-blue-700 whitespace-nowrap hidden xl:block')
            if is_guest:
                with ui.row().classes('items-center mr-2 hidden lg:flex bg-amber-50 border border-amber-200 px-3 py-1 rounded-full'):
                    ui.icon('info', color='amber-500', size='xs')
                    ui.label('Tài khoản Khách (Dữ liệu bị xóa sau 24h)').classes('text-[10px] font-bold text-amber-700 ml-1')
                with ui.button(on_click=lambda: ui.navigate.to('/login')).props('unelevated rounded no-caps').classes('bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-bold px-2 sm:px-3 py-1 shadow-sm hover:scale-105 transition-all flex items-center'):
                    ui.icon('save', size='16px')
                    ui.label('Đăng nhập để lưu').classes('text-[11px] whitespace-nowrap hidden sm:block ml-1.5')

            gamification_stats = XPEngine.get_user_stats(user.id)
            create_xp_header_widget(gamification_stats)

            with ui.button(on_click=lambda: setattr(main_tabs, 'value', tab_pricing)).props('outline rounded size=sm no-caps color="amber-8"').classes('border-amber-400 text-amber-700 bg-amber-50 hover:bg-amber-100 font-bold px-2 py-1 shadow-sm transition-all inline-flex items-center'):
                ui.icon('workspace_premium', size='16px')
                ui.label('Gói thuê bao').classes('whitespace-nowrap hidden sm:block ml-1')

            ui.button(icon='dark_mode', on_click=dark.toggle).props('flat round dense color=grey-6').tooltip('Giao diện Sáng/Tối')
            with ui.row().classes('items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 py-0.5 rounded-full border border-transparent transition-all'):
                ui.avatar(icon='person', color='blue-100', text_color='blue-600').props('size=sm')
                ui.label(user.full_name).classes('font-bold text-sm hidden sm:block mr-1')
                with ui.menu().classes('min-w-[150px]'):
                    if not is_guest:
                        ui.menu_item('Hồ sơ cá nhân', on_click=lambda: setattr(main_tabs, 'value', 'profile'))
                        ui.menu_item('Cài đặt', on_click=lambda: setattr(main_tabs, 'value', 'profile'))
                        ui.menu_item('Nâng cấp tài khoản', on_click=lambda: setattr(main_tabs, 'value', tab_pricing)).classes('text-amber-600 font-bold')

                        ui.separator()
                        ui.menu_item('Đăng xuất', on_click=lambda: ui.navigate.to('/logout')).classes('text-red-500 font-medium')
                    else:
                        ui.menu_item('Đăng nhập', on_click=lambda: ui.navigate.to('/login')).classes('text-blue-600 font-bold')
                        ui.menu_item('Đăng ký', on_click=lambda: ui.navigate.to('/register')).classes('text-purple-600 font-bold')
        

    # ── MIT STANDARD: Auto-close drawer on mobile after tab selection ──
    # Register centralized tab switch handler
    async def handle_global_tab_change(e):
        # 1. Close drawer ONLY on mobile (<= 768px)
        try:
            width = await ui.run_javascript('window.innerWidth', timeout=1.0)
            if width and int(width) <= 768:
                left_drawer.hide()
        except Exception:
            pass
        
        # 1.5 Update Back Button Visibility
        show_back = e.value in ['Vũ trụ Tri thức 3D', 'Graph Studio', 'Bloom Hub', 'Học liệu & Bài giảng', 'Gói thuê bao']
        if show_back:
            back_button.classes(remove='hidden')
        else:
            back_button.classes(add='hidden')
        
        # 2. Update Omni Context
        update_omni_tab_context(e)
        
        # 3. Dynamic loading from registry
        action = tab_actions.get(e.value)
        if action:
            try:
                action()
            except Exception as ex:
                print(f"[Tabs] Error executing action for {e.value}: {ex}")

    main_tabs.on_value_change(handle_global_tab_change)
    
    # ── TAB SWITCH POLLER ──
    def check_force_tab_switch():
        try:
            if 'force_tab_switch' in app.storage.user:
                target = app.storage.user.pop('force_tab_switch')
                main_tabs.value = target
        except RuntimeError:
            pass
    ui.timer(0.5, check_force_tab_switch)

    # ── BLOOM HUB POLLER (handles pending bloom_hub requests from 3D Bridge) ──
    async def check_pending_bloom_hub():
        try:
            pending = app.storage.user.get('pending_bloom_nav')
            if pending and isinstance(pending, dict):
                app.storage.user.pop('pending_bloom_nav', None)
                subject_id = pending.get('subject_id', '')
                node_id = pending.get('node_id', '')
                node_label = pending.get('node_label', '')
                source = pending.get('source', 'graph_studio')
                json_file_path = pending.get('json_file_path', '')
                
                print(f"[Bloom Poller] Đang xử lý pending bloom_hub: node={node_id}, subject={subject_id}, source={source}")
                
                from bloom_hub_page import build_bloom_hub_ui
                
                async def switch_back_to_studio():
                    main_tabs.value = tab_studio
                    if json_file_path:
                        await render_3d_graph(json_file_path)
                
                async def switch_back_to_nexus():
                    main_tabs.value = tab_nexus
                
                switch_back = switch_back_to_nexus if source == 'nexus' else switch_back_to_studio
                
                try:
                    main_tabs.value = tab_bloom
                    import asyncio
                    await asyncio.sleep(0.2)
                    await build_bloom_hub_ui(bloom_container, subject_id, node_id, user.username, switch_back, node_label=node_label)
                    print(f"[Bloom Poller] ✅ Bloom Hub đã được tải thành công cho node: {node_id}")
                except Exception as e:
                    import traceback
                    print(f"[Bloom Poller] ❌ Lỗi khi tải Bloom Hub: {e}")
                    traceback.print_exc()
                    with open("bloom_error.log", "w", encoding="utf-8") as f:
                        f.write(traceback.format_exc())
                    ui.notify(f"Lỗi Bloom Hub: {e}", type="negative")
        except RuntimeError:
            pass
    ui.timer(0.5, check_pending_bloom_hub)
    
    # --- OMNI-TUTOR INTEGRATION ---
    omni_ui = None
    try:
        omni_ui = build_omni_drawer()
    except Exception as e:
        print(f"[Main] Error building Omni-Drawer: {e}")
        ui.notify('Gia sư AI tạm thời không khả dụng.', type='warning')
    
    def update_omni_tab_context(e):
        tab_name = e.value
        tab_map = {
            'Tổng quan': 'dashboard',
            'Thư viện Bài học': 'library',
            'Graph Studio': 'graph_studio',
            'Creator Hub (AI)': 'creator_hub',
            'Gia sư AI (Omni)': 'tutor_chat',
            'Kiểm tra & Đánh giá': 'assessment',
            'Học liệu & Bài giảng': 'video_lessons',
            'Xếp hạng': 'leaderboard'
        }
        ctx_tab = tab_map.get(tab_name, tab_name.lower())
        app.storage.user['omni_context']['current_tab'] = ctx_tab
        
        # Reset node context if moving away from content areas
        if ctx_tab not in ('video_lessons', 'bloom_hub', 'assessment'):
            app.storage.user['omni_context']['node_id'] = None
            # node_content will be updated by the specific page renderer (e.g. Dashboard)
            app.storage.user['omni_context']['node_content'] = f"Đang ở trang {tab_name}"
        
        # Thêm thông tin môn học vào label nếu đang ở các tab quan trọng
        subj_id = app.storage.user['omni_context'].get('subject_id', '')
        if omni_ui:
            if ctx_tab in ('graph_studio', 'video_lessons', 'bloom_hub') and subj_id:
                omni_ui['context_label'].text = f'Đang theo dõi: {tab_name} ({subj_id})'
            else:
                omni_ui['context_label'].text = f'Đang theo dõi: {tab_name}'
        
    # tabs.on_value_change(update_omni_tab_context) # Moved to global handler

    # Set drawer to overlay mode on mobile (not push content)
    ui.add_css('''
        @media (max-width: 768px) {
            .q-drawer--left { position: fixed !important; z-index: 9999 !important; }
        }
        .q-drawer--mini .q-tab__label { display: none !important; }
        .q-drawer--mini .q-tab { padding-left: 0 !important; padding-right: 0 !important; justify-content: center !important; }
        .q-drawer--mini .q-separator { display: none !important; }
    ''')

    battery_ref = [None]
    
    # Hàm cập nhật Dashboard loop
    def update_ui_loop():
        if battery_ref[0]:
            battery_ref[0].update(state.current_fatigue)
        if graph_container: # Update graph if needed or periodically
             pass 

    def update_ui_loop():
        try:
            # Logic cập nhật UI định kỳ
            pass 
        except Exception:
            pass
    
    # Sử dụng try-except khi khởi tạo timer
    try:
        ui.timer(1.0, update_ui_loop)
    except Exception:
        pass

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
    def load_lesson_ui(concept_id, target_tab=None, is_meso=False, meso_label='', meso_children=None):
        state.current_concept_id = concept_id
        save_state()
        
        lesson_data = data_manager.get_lesson(concept_id) if not is_meso else None
        
        # --- UPDATE OMNI-CONTEXT ---
        if 'omni_context' in app.storage.user:
            app.storage.user['omni_context']['node_id'] = concept_id
            app.storage.user['omni_context']['subject_id'] = data_manager.current_subject_id if hasattr(data_manager, 'current_subject_id') else 'Bio-Tree'
            if lesson_data:
                # Tóm tắt nội dung bài học để AI không bị quá tải token
                summary = lesson_data.get('metadata', {}).get('summary', '') or lesson_data.get('script_content', '')[:500]
                app.storage.user['omni_context']['node_content'] = summary
            else:
                app.storage.user['omni_context']['node_content'] = f"Nhóm bài học: {meso_label}"
            
            # Cập nhật nhãn ngữ cảnh ngay lập tức
            if omni_ui:
                omni_ui['context_label'].text = f'Đang đồng hành: Bài giảng ({app.storage.user["omni_context"]["subject_id"]})'
        
        if not is_meso and not lesson_data:
            # Thu thập resources từ tree JSON
            tree_res = _get_tree_node_resources(concept_id)
            if tree_res or app.storage.user.get('target_video_url'):
                # Tạo dummy lesson_data từ resources để chạy tiếp fallback video/quiz
                lesson_data = {
                    'metadata': {'concept_name': meso_label or concept_id},
                    'resources': tree_res or [],
                    'script_content': '',
                    'is_custom': True
                }
            else:
                print(f"[Main] WARNING: No lesson data found for concept_id='{concept_id}'")
                ui.notify(f'Không tìm thấy dữ liệu bài học cho: {concept_id}', type='warning')
                if main_tabs and target_tab:
                    main_tabs.value = target_tab
                return
        
        win_prob = prediction_service.predict_next_performance(user.id, concept_id) if not is_meso else 0.5
        
        if main_tabs:
            if target_tab:
                main_tabs.value = target_tab
            elif tab_video:
                main_tabs.value = tab_video

        # Update Labels
        title = lesson_data['metadata']['concept_name'] if lesson_data else meso_label
        if lesson_label_quiz: lesson_label_quiz.text = title
        
        if prediction_label:
            prediction_label.text = f"Dự đoán: {int(win_prob*100)}%" if not is_meso else "Dự đoán: Đang đánh giá..."

        if header_lesson_container:
            header_lesson_container.clear()
            with header_lesson_container:
                 title_trunc = title
                 if len(title_trunc) > 50: title_trunc = title_trunc[:47] + "..."
                 ui.label(title_trunc).classes('text-lg font-bold text-gray-800 whitespace-nowrap overflow-hidden text-ellipsis')
                 
                 with ui.button(icon='help', color='blue-1').props('flat round dense').tooltip('Tại sao gợi ý này?'):
                      with ui.menu().classes('bg-white p-4 max-w-lg shadow-xl border'):
                          ui.label('Tại sao gợi ý bài này?').classes('font-bold text-lg mb-2 text-blue-600')
                          ui.markdown(explain_recommendation(concept_id, state) if not is_meso else "Đây là nhóm bài học được gom theo chuẩn.").classes('text-sm text-gray-700')

        # --- LOAD VIDEO ---
        def _get_tree_node_resources(node_id):
            """Tìm resources cho node từ tree JSON của user.
            1. Kiểm tra resources trực tiếp trên node đó
            2. Fallback: tìm resources từ macro node cha (mX)
            Dùng cache để tránh đọc lại JSON nhiều lần."""
            if not hasattr(_get_tree_node_resources, '_cache'):
                _get_tree_node_resources._cache = {}
            
            def _search_in_nodes(nodes):
                if node_id not in nodes:
                    return None
                # === Ưu tiên 1: Resources trực tiếp trên node ===
                node_data = nodes.get(node_id, {})
                if node_data.get('resources'):
                    return node_data['resources']
                # === Ưu tiên 2: Kế thừa từ macro cha ===
                # Strategy A: Chuong_X_Tiet_Y → mX
                m = re.match(r'^Chuong_(\d+)_', node_id)
                if m:
                    macro_node = nodes.get(f"m{m.group(1)}", {})
                    if macro_node.get('resources'):
                        return macro_node['resources']
                # Strategy B: cX.Y → mX
                m2 = re.match(r'^c(\d+)\.', node_id)
                if m2:
                    macro_node = nodes.get(f"m{m2.group(1)}", {})
                    if macro_node.get('resources'):
                        return macro_node['resources']
                # Strategy C: Scan macros for matching chapter
                ch = re.search(r'(\d+)', node_id)
                if ch:
                    for nid, ninfo in nodes.items():
                        if ninfo.get('type') == 'macro' and ninfo.get('resources'):
                            nm = re.search(r'(\d+)', nid)
                            if nm and nm.group(1) == ch.group(1):
                                return ninfo['resources']
                return None

            try:
                tree_dir = f"user_data/{user.username}/trees"
                if os.path.exists(tree_dir):
                    for fname in os.listdir(tree_dir):
                        if not fname.endswith('.json'):
                            continue
                        fpath = os.path.join(tree_dir, fname)
                        if fpath not in _get_tree_node_resources._cache:
                            with open(fpath, 'r', encoding='utf-8') as tf:
                                _get_tree_node_resources._cache[fpath] = json.load(tf).get('nodes', {})
                        result = _search_in_nodes(_get_tree_node_resources._cache[fpath])
                        if result:
                            return result
            except Exception as e:
                print(f"[Video Fallback] Error finding tree resources: {e}")
            return []

        def render_video_block(ld, cid):
            concept_name = ld.get('metadata', {}).get('concept_name', ld.get('title', 'Bài học'))
            folder_name = cid
            script_path = os.path.join(os.getcwd(), 'DB', 'Video', folder_name, 'script.txt')
            
            script_found = False
            is_valid_format = re.match(r'^c\d+\.\d+$', folder_name) or folder_name.startswith('Chuong_')
            
            target_url = app.storage.user.pop('target_video_url', None)
            
            # Đảm bảo nếu user click vào một resource có target_url, ta ưu tiên target_url thay vì tự động load video local trùng ID
            # Đặc biệt nếu target_url là link youtube, ta bỏ qua AIVideoPlayer
            skip_local_player = ld.get('is_custom', False)
            if target_url and ('youtube.com' in target_url or 'youtu.be' in target_url):
                skip_local_player = True
            
            if not skip_local_player and (os.path.exists(script_path) or is_valid_format):
                pc = ui.column().classes('w-full min-h-[10px]')
                script_content = ld.get('script_content')
                
                # NẾU chưa có script_content, thử tìm trong resources (ưu tiên file txt)
                if not script_content:
                    for r in ld.get('resources', []):
                        url = r.get('url', '')
                        if url.endswith('.txt') or 'kịch bản' in r.get('title', '').lower():
                            if url.startswith('/'): url = url.lstrip('/')
                            file_path = os.path.join(os.getcwd(), url)
                            if os.path.exists(file_path):
                                try:
                                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                                        script_content = f.read()
                                        script_path = file_path # Cập nhật đường dẫn để map với script mới
                                        break
                                except: pass

                def _go_back_to_tree():
                    if main_tabs and tab_studio:
                        main_tabs.value = tab_studio
                        ui.notify('Quay lại Graph Studio', type='info', icon='hub')

                player = AIVideoPlayer(pc, concept_name, script_path, folder_name, script_content=script_content, on_back=_go_back_to_tree)
                if player.slides:
                    script_found = True
                else:
                    pc.delete()
            
            if not script_found:
                resources = ld.get('resources', [])
                # Allow youtube type, mp4, lesson.html (interactive AI lectures)
                # Exclude quiz.html and session.html which are not video content
                def _is_video_resource(r):
                    url = r.get('url', '')
                    if not url: return False
                    if 'quiz' in url.lower() or 'session' in url.lower(): return False
                    if url.endswith('.json'): return False
                    return True
                video_resources = [r for r in resources if _is_video_resource(r)]
                
                # FALLBACK: Nếu data_manager không có video, tìm trong tree JSON (cả node và macro cha)
                if not video_resources:
                    tree_resources = _get_tree_node_resources(cid)
                    video_resources = [r for r in tree_resources if _is_video_resource(r)]
                
                # Nếu có target_url từ bridge, đảm bảo nó nằm đầu danh sách
                if target_url:
                    existing_urls = [r.get('url', '') for r in video_resources]
                    if target_url not in existing_urls:
                        # Inject tài nguyên tổng hợp cho URL được chọn
                        video_resources.insert(0, {'url': target_url, 'title': 'Tài nguyên đã chọn', 'type': 'link'})
                    print(f"[Video] target_url={target_url}, total resources={len(video_resources)}")
                
                if not video_resources:
                    with ui.column().classes('items-center justify-center w-full min-h-[300px] gap-4 bg-gray-50 rounded-lg'):
                        ui.icon('videocam_off', color='gray-400', size='3rem')
                        ui.label(f"Video chưa khả dụng cho bài học: {concept_name}").classes('italic text-gray-400')
                else:
                    display_area = ui.column().classes('w-full h-full p-0')
                    def show_video(idx):
                        display_area.clear()
                        res = video_resources[idx]
                        vurl = res.get('url')
                        with display_area:
                            if 'youtube.com' in vurl or 'youtu.be' in vurl:
                                import urllib.parse
                                yt_id = ""
                                if 'v=' in vurl: yt_id = urllib.parse.parse_qs(urllib.parse.urlparse(vurl).query).get('v', [''])[0]
                                else: yt_id = vurl.split('/')[-1]
                                ui.element('iframe').props(f'src="https://www.youtube.com/embed/{yt_id}" width="100%" height="500px" allowfullscreen').classes('w-full border-none bg-black rounded-lg')
                            elif '.html' in vurl:
                                # Interactive HTML Player from github.io
                                ui.element('iframe').props(f'src="{vurl}" width="100%" height="650px" allow="autoplay; fullscreen"').classes('w-full border-none bg-black rounded-xl shadow-lg')
                                with ui.row().classes('w-full p-2 justify-center'):
                                    ui.button('Mở toàn màn hình (Tab Mới)', icon='open_in_new').props(f'href="{vurl}" target="_blank" flat dense color=blue font-bold')
                            elif '.pdf' in vurl.lower() or ('drive.google.com' in vurl and '/view' in vurl) or res.get('type') == 'pdf':
                                if 'drive.google.com' in vurl:
                                    embed_url = vurl.replace('/view', '/preview')
                                    ui.element('iframe').props(f'src="{embed_url}" width="100%" height="700px" allowfullscreen').classes('w-full border-none rounded-xl shadow-lg')
                                else:
                                    ui.element('iframe').props(f'src="{vurl}" width="100%" height="700px"').classes('w-full border-none rounded-xl shadow-lg')
                                with ui.row().classes('w-full p-2 justify-center'):
                                    ui.button('Mở toàn màn hình (Tab Mới)', icon='open_in_new').props(f'href="{vurl}" target="_blank" flat dense color=blue font-bold')
                            elif vurl.startswith('http') and not any(vurl.lower().endswith(ext) for ext in ['.mp4', '.webm', '.ogg', '.mp3', '.wav']):
                                if 'khanacademy.org' in vurl and '/v/' in vurl:
                                    title = res.get('title', '')
                                    spinner_label = ui.label('Đang lấy link video gốc từ YouTube...').classes('text-gray-500 italic mt-4 text-center w-full')
                                    container = ui.column().classes('w-full items-center p-0 m-0')
                                    
                                    async def load_khan_youtube():
                                        import urllib.request, urllib.parse, re, asyncio
                                        def fetch_yt():
                                            try:
                                                query = f"Khan Academy {title} youtube"
                                                data = urllib.parse.urlencode({'q': query}).encode('utf-8')
                                                req = urllib.request.Request('https://lite.duckduckgo.com/lite/', data=data, headers={'User-Agent': 'Mozilla/5.0'})
                                                html = urllib.request.urlopen(req, timeout=3).read().decode('utf-8')
                                                matches = re.findall(r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})', html)
                                                if not matches:
                                                    matches = re.findall(r'youtu\.be/([a-zA-Z0-9_-]{11})', html)
                                                return matches[0] if matches else None
                                            except:
                                                return None
                                        
                                        yt_id = await asyncio.to_thread(fetch_yt)
                                        spinner_label.delete()
                                        with container:
                                            if yt_id:
                                                ui.element('iframe').props(f'src="https://www.youtube.com/embed/{yt_id}" width="100%" height="500px" allowfullscreen').classes('w-full border-none bg-black rounded-lg')
                                            else:
                                                ui.label('⚠️ Trình duyệt chặn cookie bên thứ 3 nên không thể nhúng video này.').classes('text-sm text-red-500 font-bold mb-2')
                                                ui.element('iframe').props(f'src="{vurl}" width="100%" height="500px" allow="autoplay; fullscreen"').classes('w-full border-none bg-white rounded-xl shadow-lg')
                                                with ui.row().classes('w-full p-2 justify-center items-center gap-4'):
                                                    ui.button('Mở trực tiếp trên tab mới', icon='open_in_new').props(f'href="{vurl}" target="_blank" flat dense color=blue font-bold')
                                    ui.timer(0.1, load_khan_youtube, once=True)
                                else:
                                    # General web page (e.g. Khan Academy articles, external links)
                                    if 'khanacademy.org' in vurl:
                                        with ui.card().classes('w-full items-center p-12 bg-gray-50 shadow-inner rounded-xl border border-gray-200 mt-4'):
                                            ui.icon('article', size='4rem', color='gray-400').classes('mb-4')
                                            ui.label('Tài liệu từ Khan Academy').classes('text-xl font-bold text-gray-700 mb-6')
                                            ui.button('Mở tài liệu trong tab mới', icon='open_in_new').props(f'href="{vurl}" target="_blank" color=primary unelevated rounded padding="8px 24px"')
                                    else:
                                        ui.element('iframe').props(f'src="{vurl}" width="100%" height="750px" allow="autoplay; fullscreen"').classes('w-full border-none bg-white rounded-xl shadow-lg')
                                        with ui.row().classes('w-full p-2 justify-center items-center gap-4'):
                                            ui.label('Nếu trang web không hiển thị hoặc bị chặn, click nút bên cạnh:').classes('text-xs text-gray-500')
                                            ui.button('Mở trong tab mới', icon='open_in_new').props(f'href="{vurl}" target="_blank" flat dense color=blue font-bold')
                            else:
                                ui.video(vurl).classes('w-full h-auto max-h-[80vh] rounded-lg shadow-inner bg-black')
                                with ui.row().classes('w-full p-2 justify-center'):
                                    ui.button('Mở link gốc', icon='open_in_new').props(f'href="{vurl}" target="_blank" flat dense color=blue')

                    if len(video_resources) > 1:
                        with ui.row().classes('w-full p-2 bg-slate-100 items-center justify-between rounded-t-lg mt-4'):
                            ui.label(f"Chọn bài giảng ({len(video_resources)})").classes('text-xs font-bold text-slate-500 uppercase tracking-wider')
                            selector = ui.select({i: r.get('title', f'Phần {i+1}') for i, r in enumerate(video_resources)}, value=0).props('dense outlined bg-white').classes('w-48')
                            selector.on_value_change(lambda e: show_video(e.value))
                    
                    start_idx = 0
                    if target_url:
                        for i, r in enumerate(video_resources):
                            if r.get('url') == target_url:
                                start_idx = i
                                break
                    if len(video_resources) > 1 and start_idx != 0:
                        selector.value = start_idx
                    else:
                        show_video(start_idx)

        # --- LOAD VIDEO ---
        if video_container:
            video_container.clear()
            with video_container:
                if is_meso and meso_children:
                    with ui.column().classes('w-full h-full p-0 gap-0'):
                        with ui.row().classes('w-full p-2 bg-slate-800 items-center justify-between rounded-none z-10'):
                            ui.label(f"Chương trình đào tạo: {meso_label}").classes('text-lg font-bold text-white')
                            selector = ui.select({child.get('id'): f"Tiết: {child.get('title')}" for child in meso_children}, value=meso_children[0].get('id')).props('dense outlined dark').classes('w-64')
                            
                        display_area = ui.column().classes('w-full flex-grow p-0 m-0 relative')
                        
                        def show_meso_video(e):
                            display_area.clear()
                            sel_id = e.value
                            sel_child = next((c for c in meso_children if c.get('id') == sel_id), meso_children[0])
                            child_lesson = data_manager.get_lesson(sel_id)
                            if not child_lesson:
                                child_lesson = dict(sel_child)
                                child_lesson['is_custom'] = True
                            with display_area:
                                if child_lesson: render_video_block(child_lesson, sel_id)
                                else: ui.label("Dữ liệu không khả dụng.").classes('p-4 italic text-gray-400 text-center w-full mt-10')

                        selector.on_value_change(show_meso_video)
                        # trigger first render
                        class DummyEvent:
                            def __init__(self, val):
                                self.value = val
                        show_meso_video(DummyEvent(meso_children[0].get('id')))
                else:
                    render_video_block(lesson_data, concept_id)

        # --- LOAD QUIZ ---
        if quiz_container:
            quiz_container.clear()
            with quiz_container:
                questions = []
                if lesson_data:
                    questions = lesson_data.get('questions', [])
                elif is_meso and meso_children:
                    for child in meso_children:
                        child_lesson = data_manager.get_lesson(child.get('id'))
                        if child_lesson and child_lesson.get('questions'):
                            questions.extend(child_lesson.get('questions', []))
                            
                if not questions:
                    if is_meso:
                        ui.label("Chưa có câu hỏi tổng hợp cho phần này. Vui lòng chọn từng bài học nhỏ.").classes('italic text-gray-500 p-4')
                    else:
                        ui.label("Chưa có câu hỏi cho bài này.").classes('italic text-gray-500 p-4')
                else:
                    # --- QUIZ STATE MANAGEMENT ---
                    class QuizController:
                        def __init__(self, questions, state_ref, cid=None):
                            self.questions = questions
                            self.current_index = 0
                            self.state_ref = state_ref
                            
                            # Use explicit cid if provided, else fallback to current state
                            self.cid = cid or self.state_ref.current_concept_id
                            
                            if self.cid not in self.state_ref.quiz_history:
                                self.state_ref.quiz_history[self.cid] = {}
                            
                            # Convert string keys back to int if needed
                            self.user_answers = {}
                            if self.cid in self.state_ref.quiz_history:
                                for k, v in self.state_ref.quiz_history[self.cid].items():
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
                                                ui.element('div').classes('w-3 h-3 rounded-full bg-yellow-500 mr-2')
                                                ui.label('Làm lại đúng')
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
                                    # Status Color Priority
                                    status = None
                                    color_prop = ''
                                    text_color = 'white'
                                    
                                    if correct_count > 0 and wrong_count > 0:
                                        status = 'correct_after_wrong'
                                        color_prop = 'warning'
                                    elif correct_count > 0:
                                        status = 'correct'
                                        color_prop = 'positive'
                                    elif wrong_count > 0:
                                        status = 'wrong'
                                        color_prop = 'negative'
                                    
                                    # Override if currently selected (Blue selection)
                                    if idx == self.current_index and not status:
                                         color_prop = 'primary'
                                         
                                    if not color_prop:
                                         color_prop = 'grey-4'
                                         text_color = 'grey-8'

                                    # Current Selection Indicator (Border/Ring)
                                    ring_class = ''
                                    if idx == self.current_index:
                                        if status: 
                                            ring_class = 'ring-4 ring-blue-300 transform scale-110 z-10'
                                        else:
                                            ring_class = 'ring-2 ring-blue-300 transform scale-105'

                                    msg = f"Câu {idx + 1}: Đúng {correct_count} | Sai {wrong_count}"
                                    if not status: msg = f"Câu {idx + 1}: Chưa làm"
                                        
                                    btn = ui.button(str(idx + 1), on_click=lambda i=idx: self.jump_to(i))
                                    btn.classes(f'{base_class} {ring_class}').tooltip(msg)
                                    btn.props(f'color={color_prop} text-color={text_color} unelevated')

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
                                            cid = self.cid
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
                                                
                                                # Update Omni-Context Error Streak
                                                if 'omni_context' in app.storage.user:
                                                    app.storage.user['omni_context']['error_streak'] = 0
                                                
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
                                                
                                                # Update Omni-Context Error Streak
                                                if 'omni_context' in app.storage.user:
                                                    app.storage.user['omni_context']['error_streak'] = app.storage.user['omni_context'].get('error_streak', 0) + 1
                                                
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
                                    
                                    # Trigger MathJax to render any math in the new question
                                    ui.run_javascript('typesetMathJax()')

                        def jump_to(self, idx):
                            self.current_index = idx
                            self.render_current_question()
                            self.render_palette()
                        def next_q(self):
                            if self.current_index < len(self.questions) - 1: self.jump_to(self.current_index + 1)
                        def prev_q(self):
                            if self.current_index > 0: self.jump_to(self.current_index - 1)

                    # RENDER QUIZ BLOCK Helper
                    def render_quiz_block(q_list, c_id, resources=None):
                        resources = resources or []
                        link_quizzes = [r for r in resources if 'quiz' in r.get('url', '').lower() or r.get('title', '').startswith('📝')]
                        
                        if not q_list and not link_quizzes:
                            ui.label("Chưa có câu hỏi cho bài này.").classes('italic text-gray-500 p-4')
                        elif link_quizzes:
                            with ui.column().classes('w-full bg-slate-50 p-6 rounded-xl border border-slate-200 items-center justify-center'):
                                ui.icon('assignment_turned_in', size='4rem', color='blue-500').classes('mb-2 shadow-sm rounded-full bg-blue-50 p-2')
                                ui.label('Hệ thống Đánh giá Trực tuyến').classes('font-bold text-xl text-slate-800 tracking-tight')
                                ui.label('Vui lòng hoàn thành bài tập trên hệ thống để ghi nhận kết quả.').classes('text-sm text-slate-500 mb-6 text-center')
                                for rq in link_quizzes:
                                    ui.button(rq.get('title', 'Làm bài Trắc nghiệm'), icon='open_in_new', on_click=lambda _, u=rq.get('url'): ui.open(u, new_tab=True)).classes('mt-2 bg-gradient-to-r from-blue-600 to-indigo-700 text-white font-bold text-base px-8 py-2 shadow-lg hover:scale-105 transition-transform').props('rounded')
                        else:
                            with ui.column().classes('w-full bg-white p-4 rounded-xl'):
                                quiz = QuizController(q_list, state, cid=c_id)
                                quiz.render()

                    if is_meso and meso_children:
                        with ui.column().classes('w-full max-w-5xl mx-auto gap-4 relative'):
                            for child in meso_children:
                                child_id = child.get('id')
                                child_lesson = data_manager.get_lesson(child_id) or child
                                child_questions = child_lesson.get('questions', [])
                                
                                with ui.expansion(f"Đánh giá: {child.get('title')}", icon='quiz').classes('w-full border-2 border-slate-200 rounded-xl bg-white shadow-sm overflow-hidden').props('header-class="font-bold text-slate-800 bg-slate-50 text-lg p-4"'):
                                    render_quiz_block(child_questions, child_id, resources=child_lesson.get('resources', []))
                    else:
                        render_quiz_block(questions, concept_id, resources=lesson_data.get('resources', []))


    # --- LAYOUT GIAO DIỆN MỚI (Single Tab) ---
    # Tabs are defined in header now
    # with ui.tabs().classes('w-full') as tabs:
    #    tab_knowledge = ui.tab('Kiến Thức', icon='hub')
    #    tab_video = ui.tab('Video', icon='movie')
#    tab_quiz = ui.tab('Quiz', icon='quiz')

    with ui.tab_panels(main_tabs, value=tab_dashboard).classes('w-full h-[calc(100vh-60px)] m-0 p-0'):
        
        # TAB PRICING
        with ui.tab_panel(tab_pricing).classes('p-0 h-full bg-slate-50 overflow-y-auto'):
            from pricing_page import create_pricing_page
            create_pricing_page(is_standalone=False)

        # TAB 00: DASHBOARD (TỔNG QUAN)
        with ui.tab_panel(tab_dashboard).classes('p-0 h-full bg-slate-50 overflow-y-auto'):
            
            @ui.refreshable
            def render_dashboard():
                from multi_subject_dashboard import (
                    load_all_subjects, get_subject_card_data, get_cross_subject_summary,
                    save_access_policy, load_access_policy, get_daily_tasks, get_unified_review_queue
                )
                
                username = user.username
                summary = get_cross_subject_summary(username)
                subjects = load_all_subjects(username)
                tasks = get_daily_tasks(username, max_tasks=4)
                current_policy = load_access_policy(username)
                
                # Update Omni-Context for Dashboard
                if 'omni_context' in app.storage.user:
                    app.storage.user['omni_context'].update({
                        'current_tab': 'dashboard',
                        'subject_id': 'GLOBAL_DASHBOARD',
                        'subject_title': 'Trang Tổng Quan',
                        'node_content': f"Trang Tổng Quan. Môn học: {len(subjects or [])}. Nhiệm vụ: {len(tasks or [])}. Cảnh báo: {summary.get('critical_review_count', 0)} bài."
                    })

                def on_policy_change(e):
                    save_access_policy(username, e.value)
                    ui.notify(f"Đã cập nhật Access Policy: {e.value}", type='positive')
                
                with ui.column().classes('w-full max-w-7xl mx-auto p-6 md:p-10'):
                    # Header Section
                    with ui.row().classes('w-full items-center justify-between mb-8'):
                        with ui.column().classes('gap-1'):
                            ui.label(f'Chào mừng trở lại, {user.full_name}! 👋').classes('text-3xl font-extrabold text-blue-900 tracking-tight')
                            ui.label('Tiếp tục hành trình tri thức của bạn hôm nay.').classes('text-slate-500 font-medium text-base')
                        
                        with ui.row().classes('items-center gap-4'):
                            with ui.column().classes('gap-0'):
                                ui.label('Chế độ học (Access Policy)').classes('text-xs font-bold text-gray-500 uppercase tracking-wider')
                                ui.select(
                                    options={'k12_strict': 'K-12', 'university_flexible': 'Đại học', 'professional_open': 'Chuyên nghiệp'},
                                    value=current_policy,
                                    on_change=on_policy_change
                                ).props('dense outlined borderless bg-white rounded').classes('w-48 shadow-sm')
                            
                            ui.button('Bắt đầu học ngay', icon='play_arrow', on_click=lambda: setattr(main_tabs, 'value', tab_studio)).classes('bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold px-6 py-2 shadow-lg hover:shadow-xl hover:scale-105 transition-all').props('rounded')
                    
                    # --- SMART REVIEW QUEUE (Filtered for valid lessons) ---
                    critical_queue = get_unified_review_queue(username, max_items=10)
                    valid_criticals = [item for item in critical_queue if data_manager.get_lesson(item['node_id'])]
                    
                    # Critical Alert (Only show if there are actionable valid lessons)
                    if len(valid_criticals) > 0:
                        with ui.row().classes('w-full p-4 mb-6 bg-red-50 border-l-4 border-red-500 rounded-r-xl items-center justify-between shadow-sm'):
                            with ui.row().classes('items-center gap-3'):
                                ui.icon('warning', color='red-500').classes('text-2xl animate-pulse')
                                with ui.column().classes('gap-0'):
                                    ui.label('Cảnh báo Suy giảm Trí nhớ!').classes('font-bold text-red-800')
                                    ui.label(f'Có {len(valid_criticals)} khái niệm quan trọng cần ôn tập ngay.').classes('text-sm text-red-600')
                            
                            # --- REVIEW SELECTOR DIALOG ---
                            with ui.dialog() as review_dialog, ui.card().classes('w-full max-w-lg bg-white rounded-3xl p-0 overflow-hidden shadow-2xl border border-gray-100'):
                                # Header
                                with ui.row().classes('w-full bg-gradient-to-r from-red-600 to-rose-500 p-6 items-center justify-between'):
                                    with ui.row().classes('items-center gap-3'):
                                        ui.icon('emergency', color='white').classes('text-2xl animate-pulse')
                                        ui.label('Chọn bài cần ôn tập').classes('text-xl font-bold text-white tracking-tight')
                                    ui.button(icon='close', on_click=review_dialog.close).props('flat round color=white size=sm')
                                
                                # List of nodes
                                with ui.column().classes('w-full p-6 gap-4'):
                                    ui.label('Dưới đây là các khái niệm bạn đang có dấu hiệu suy giảm trí nhớ:').classes('text-gray-500 text-sm italic mb-2')
                                    
                                    for item in valid_criticals:
                                        with ui.row().classes('w-full p-4 rounded-2xl border border-red-100 bg-red-50/30 items-center justify-between hover:bg-red-100/50 hover:border-red-300 transition-all cursor-pointer group').on('click', lambda i=item: [
                                            load_lesson_ui(i['node_id'], target_tab=tab_video),
                                            review_dialog.close(),
                                            ui.notify(f"Đang mở bài ôn tập: {i['node_id']}", type='positive')
                                        ]):
                                            with ui.column().classes('gap-0'):
                                                ui.label(item['node_id']).classes('font-bold text-red-800 text-base group-hover:text-red-600 transition-colors')
                                                ui.label(f"Môn học: {item.get('subject_title', 'Chưa rõ')}").classes('text-xs text-red-500/70 font-medium')
                                            
                                            ui.button(icon='arrow_forward', on_click=lambda i=item: [
                                                load_lesson_ui(i['node_id'], target_tab=tab_video),
                                                review_dialog.close()
                                            ]).props('flat round color=red size=sm')

                            def open_review_selector():
                                if len(valid_criticals) == 1:
                                    load_lesson_ui(valid_criticals[0]['node_id'], target_tab=tab_video)
                                    ui.notify(f"Đang mở bài ôn tập: {valid_criticals[0]['node_id']}", type='positive')
                                else:
                                    review_dialog.open()
                                    
                            ui.button('Ôn tập ngay', on_click=open_review_selector).props('outline color=red rounded size=sm shadow-sm')

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

                            # Bio Battery Card — Premium
                            with ui.card().classes('w-full p-0 rounded-3xl shadow-lg hover:shadow-xl transition-all border border-gray-100 overflow-hidden'):
                                # Header gradient
                                with ui.row().classes('w-full items-center justify-between px-5 py-3').style('background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);'):
                                    with ui.row().classes('items-center gap-2'):
                                        ui.html('<span style="font-size:18px;">🔋</span>')
                                        ui.label('Bio Battery').classes('font-black text-white text-sm tracking-wide')
                                    ui.html('''<div style="display:flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;background:rgba(52,211,153,0.15);border:1px solid rgba(52,211,153,0.2);">
                                        <div style="width:6px;height:6px;border-radius:50%;background:#34d399;animation:bb-pulse 1.5s infinite;"></div>
                                        <span style="color:#6ee7b7;font-size:10px;font-weight:700;">LIVE</span>
                                    </div>''')
                                # Widget area
                                with ui.column().classes('w-full items-center justify-center px-4 py-2').style('background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); min-height: 220px;'):
                                    battery_ref[0] = BioBattery(ui.column().classes('items-center'))

                        # Center & Right Column: Course Cards & Tasks
                        with ui.column().classes('w-full lg:w-2/3 gap-6'):
                            
                            # Course Cards Grid
                            with ui.card().classes('w-full p-6 bg-white rounded-3xl shadow-sm border border-gray-100').props('id="resume-learning-section"'):
                                ui.label('Môn học của bạn').classes('font-bold text-gray-800 text-lg mb-4')
                                if not subjects:
                                    ui.label('Chưa có môn học nào. Hãy đến Thư viện để thêm.').classes('text-gray-500 italic')
                                else:
                                    # Use a grid layout instead of a flex row to avoid squeezing cards
                                    with ui.element('div').classes('w-full grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-5'):
                                        for subj in subjects:
                                            card_data = get_subject_card_data(username, subj)
                                            pct = card_data['completion_pct']
                                            
                                            if pct >= 70:
                                                bg_color = 'bg-emerald-50 border-emerald-100'
                                                bar_color = 'bg-emerald-500'
                                                icon_color = 'text-emerald-500'
                                                bg_icon_color = 'bg-emerald-100'
                                            elif pct >= 30:
                                                bg_color = 'bg-blue-50 border-blue-100'
                                                bar_color = 'bg-blue-500'
                                                icon_color = 'text-blue-500'
                                                bg_icon_color = 'bg-blue-100'
                                            else:
                                                bg_color = 'bg-amber-50 border-amber-100'
                                                bar_color = 'bg-amber-500'
                                                icon_color = 'text-amber-500'
                                                bg_icon_color = 'bg-amber-100'
                                                
                                            with ui.column().classes(f'w-full p-3 md:p-4 rounded-xl border {bg_color} hover:-translate-y-0.5 hover:shadow-md transition-all duration-300 cursor-pointer relative overflow-hidden group').on('click', lambda s=subj: setattr(main_tabs, 'value', tab_studio)):
                                                # Decorative background circle
                                                with ui.element('div').classes(f'absolute -right-2 -top-2 w-16 h-16 rounded-full opacity-20 group-hover:scale-110 transition-transform duration-500 {bar_color} blur-xl'): pass
                                                
                                                # Top section with Title and Icon
                                                with ui.row().classes('w-full items-start justify-between no-wrap mb-1 gap-2'):
                                                    ui.label(card_data['title']).classes('font-bold text-slate-800 text-sm leading-tight line-clamp-2 flex-grow')
                                                    with ui.element('div').classes(f'p-1.5 rounded-lg {bg_icon_color} flex-shrink-0'):
                                                        ui.icon('school').classes(f'text-base {icon_color}')
                                                
                                                # Spacer
                                                ui.element('div').classes('flex-grow')
                                                
                                                # Middle section with Stats
                                                with ui.row().classes('w-full justify-between items-end mt-2 mb-1'):
                                                    with ui.row().classes('items-center gap-2'):
                                                        ui.label(f"{card_data['nodes_learned']}/{card_data['total_nodes']}").classes('text-xs font-medium text-slate-500')
                                                        with ui.row().classes('items-center gap-0.5 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100/50'):
                                                            ui.icon('psychology', size='10px', color='indigo-500')
                                                            ui.label(f"{card_data['avg_bloom']}/6.0").classes('text-[10px] font-bold text-indigo-600')
                                                    
                                                    ui.label(f"{int(pct)}%").classes(f'text-sm font-black {icon_color}')

                                                # Progress bar with shadow
                                                with ui.element('div').classes('w-full h-1.5 bg-slate-200/80 rounded-full mt-1 overflow-hidden shadow-inner'):
                                                    ui.element('div').classes(f'h-full {bar_color} rounded-full transition-all duration-1000').style(f'width: {pct}%')
                                                    
                                                # Review Badge
                                                if card_data['review_urgency'] > 0:
                                                    with ui.element('div').classes('absolute top-0 right-0 bg-gradient-to-r from-red-500 to-rose-600 text-white text-[9px] font-bold px-2 py-0.5 rounded-bl-lg shadow-sm z-10'):
                                                        ui.label(f"{card_data['review_urgency']} Ôn")

                            # Tasks / Goals (Dynamic)
                            with ui.card().classes('w-full p-6 bg-white rounded-3xl shadow-sm hover:shadow-md transition-all border border-gray-100 flex-grow').props('id="recommendation-section"'):
                                with ui.row().classes('w-full items-center justify-between mb-4'):
                                    with ui.row().classes('items-center gap-2'):
                                        ui.icon('auto_awesome', color='amber-500', size='sm')
                                        ui.label('Nhiệm vụ Thông minh').classes('font-bold text-gray-800 text-lg')
                                    ui.label('Gợi ý từ AI').classes('text-[10px] font-bold text-blue-500 bg-blue-50 px-2 py-1 rounded-full uppercase tracking-wider')

                                with ui.column().classes('w-full gap-4'):
                                    if not tasks:
                                        with ui.column().classes('w-full items-center justify-center p-6 bg-slate-50 rounded-2xl border border-slate-100 dashed'):
                                            ui.icon('celebration', size='md', color='emerald-400').classes('mb-2')
                                            ui.label('Tuyệt vời! Bạn đã hoàn thành các mục tiêu.').classes('text-emerald-600 font-medium')
                                            ui.label('Hãy tiếp tục khám phá bài học mới.').classes('text-slate-400 text-sm')
                                    else:
                                        for task in tasks:
                                            is_review = task['type'] == 'review_node'
                                            is_learn = task['type'] == 'learn_next'
                                            
                                            icon_name = 'replay' if is_review else ('lightbulb_outline' if is_learn else 'psychology')
                                            bg_color = 'bg-rose-50 border-rose-100' if is_review else ('bg-sky-50 border-sky-100' if is_learn else 'bg-fuchsia-50 border-fuchsia-100')
                                            hover_bg = 'hover:bg-rose-100' if is_review else ('hover:bg-sky-100' if is_learn else 'hover:bg-fuchsia-100')
                                            icon_color = 'text-rose-500' if is_review else ('text-sky-500' if is_learn else 'text-fuchsia-500')
                                            btn_color = 'red' if is_review else ('blue' if is_learn else 'purple')
                                            
                                            def on_task_click(t=task):
                                                if t.get('node_id'):
                                                    # Kiểm tra xem có dữ liệu bài học thật không
                                                    if data_manager.get_lesson(t['node_id']):
                                                        load_lesson_ui(t['node_id'], target_tab=tab_video)
                                                        ui.notify(f"Bắt đầu nhiệm vụ: {t['title']}", type='positive')
                                                    else:
                                                        ui.notify(f"Đang chuẩn bị dữ liệu cho bài: {t['title']}. Hãy quay lại sau.", type='info')
                                                        setattr(main_tabs, 'value', tab_studio)
                                                elif t['type'] == 'socratic_practice':
                                                    setattr(main_tabs, 'value', tab_tutor)
                                                else:
                                                    setattr(main_tabs, 'value', tab_studio)

                                            with ui.row().classes(f'w-full p-4 rounded-2xl border {bg_color} {hover_bg} transition-all duration-300 cursor-pointer items-stretch justify-between group').on('click', on_task_click):
                                                with ui.row().classes('items-center gap-4 flex-grow no-wrap'):
                                                    with ui.element('div').classes('p-3 rounded-xl bg-white shadow-sm'):
                                                        ui.icon(icon_name).classes(f'text-2xl {icon_color}')
                                                    with ui.column().classes('gap-0 flex-grow justify-center'):
                                                        ui.label(task['title']).classes('font-bold text-[15px] text-slate-800 line-clamp-1')
                                                        ui.label(task['description']).classes('text-[13px] text-slate-500 line-clamp-1 mt-0.5')
                                                
                                                with ui.column().classes('items-end justify-center gap-2 pl-4 border-l border-white/50 min-w-[100px]'):
                                                    with ui.row().classes('items-center gap-1'):
                                                        ui.icon('bolt', size='xs', color='amber-500')
                                                        ui.label(f"+{task['xp_reward']} XP").classes('text-xs font-bold text-amber-600')
                                                    ui.button('Thực hiện', on_click=on_task_click).props(f'unelevated rounded size=sm color={btn_color}').classes('px-3 font-bold shadow-sm group-hover:-translate-y-0.5 transition-transform')

            render_dashboard()

        # TAB 0: PUBLIC LIBRARY (Thư viện công cộng)
        with ui.tab_panel(tab_library).classes('p-6 h-full bg-gradient-to-br from-slate-50 to-blue-50/30 overflow-y-auto'):
            with ui.column().classes('w-full max-w-6xl mx-auto'):
                # Header
                with ui.row().classes('w-full items-center justify-between mb-6'):
                    with ui.column().classes('gap-1'):
                        ui.label('📚 Thư viện Cây Tri Thức').classes('text-3xl font-extrabold text-slate-800 tracking-tight')
                        ui.label('Khám phá và thêm cây tri thức vào bộ sưu tập cá nhân').classes('text-slate-500')
                    with ui.row().classes('items-center gap-3'):
                        ui.input(placeholder='🔍 Tìm kiếm...').props('id="library-search-bar" rounded outlined dense').classes('w-64')

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

                lib_cards_container = ui.row().classes('w-full gap-5 flex-wrap').props('id="library-category-filter"')

                def render_public_cards():
                    view_refreshers['public'] = render_public_cards # Register
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
                                # MIT Dynamic Palette: Sync with Graph Studio
                                palettes = [
                                    ('from-indigo-500 to-blue-600', 'indigo-700', 'shadow-indigo-100'),
                                    ('from-emerald-500 to-teal-600', 'emerald-700', 'shadow-emerald-100'),
                                    ('from-amber-500 to-orange-600', 'amber-700', 'shadow-amber-100'),
                                    ('from-purple-500 to-violet-600', 'purple-700', 'shadow-purple-100'),
                                    ('from-rose-500 to-pink-600', 'rose-700', 'shadow-rose-100'),
                                    ('from-cyan-500 to-sky-600', 'cyan-700', 'shadow-cyan-100'),
                                ]
                                accent_grad, btn_color, shadow_color = palettes[hash(tree['id']) % len(palettes)]
                                cat_name = tree.get('category', 'Khác')

                                with ui.card().classes('w-[320px] p-0 overflow-hidden rounded-2xl border border-slate-200 shadow-sm hover:shadow-xl transition-all duration-300 group').props('id="btn-preview-tree"'):
                                    # Top Accent Bar
                                    ui.element('div').classes(f'w-full h-1.5 bg-gradient-to-r {accent_grad}')
                                    
                                    with ui.column().classes('w-full p-6'):
                                        # Title & Nodes
                                        with ui.row().classes('w-full items-start justify-between no-wrap mb-2'):
                                            ui.label(tree['title']).classes('font-black text-xl text-slate-800 leading-tight truncate flex-1').tooltip(tree['title'])
                                            with ui.row().classes('items-center gap-1'):
                                                ui.badge(f"{tree['total_nodes']} N", color='slate-100').classes('text-slate-500 text-[10px] font-bold px-2 py-0.5 mt-1')
                                                
                                                def show_delete_prompt(t=tree):
                                                    with ui.dialog() as dlg, ui.card().classes('p-6 rounded-2xl w-80'):
                                                        ui.label('Xác nhận xóa').classes('text-xl font-bold text-red-600 mb-2')
                                                        ui.label(f'Bạn đang xóa "{t["title"]}" khỏi hệ thống.').classes('text-sm text-gray-600 mb-4')
                                                        pwd = ui.input('Mật khẩu quản trị', password=True).classes('w-full mb-4')
                                                        with ui.row().classes('w-full justify-end gap-2'):
                                                            ui.button('Hủy', on_click=dlg.close).props('flat text-color=gray')
                                                            def do_del():
                                                                if pwd.value == '-Abcd1234':
                                                                    try:
                                                                        with open(public_lib_path, 'r', encoding='utf-8') as f:
                                                                            data = _json.load(f)
                                                                        data['trees'] = [x for x in data['trees'] if x['id'] != t['id']]
                                                                        with open(public_lib_path, 'w', encoding='utf-8') as f:
                                                                            _json.dump(data, f, ensure_ascii=False, indent=2)
                                                                        public_trees[:] = data['trees']
                                                                        ui.notify('Đã xóa môn học thành công!', type='positive')
                                                                        dlg.close()
                                                                        render_public_cards()
                                                                    except Exception as e:
                                                                        ui.notify(f'Lỗi xóa file: {e}', type='negative')
                                                                else:
                                                                    ui.notify('Mật khẩu không đúng!', type='negative')
                                                            ui.button('Xóa', color='red', on_click=do_del).props('unelevated')
                                                    dlg.open()
                                                
                                                ui.button(icon='delete', on_click=show_delete_prompt).props('flat round size=xs color=red').classes('mt-1 hover:bg-red-50')
                                        
                                        # Description
                                        ui.label(tree.get('description', 'Không có mô tả.')).classes('text-sm text-slate-500 line-clamp-2 h-10 mb-4')
                                        
                                        # Stats Row
                                        with ui.row().classes('w-full items-center justify-between mb-4 bg-slate-50 p-3 rounded-xl border border-slate-100'):
                                            # Rating
                                            with ui.row().classes('items-center gap-1'):
                                                ui.icon('star', color='amber-500', size='xs')
                                                ui.label(f"{tree.get('rating', '4.5')}").classes('text-xs font-black text-slate-700')
                                                ui.label(f"({tree.get('downloads', 0)})").classes('text-[10px] text-slate-400')
                                            
                                            # Price
                                            price = tree.get('price_xp', 0)
                                            if price == 0:
                                                ui.label('MIỄN PHÍ').classes('text-[10px] font-black text-emerald-600 tracking-wider')
                                            else:
                                                with ui.row().classes('items-center gap-1 text-purple-700'):
                                                    ui.icon('diamond', size='xs')
                                                    ui.label(f'{price} XP').classes('text-xs font-black')

                                        # Category & Trending
                                        with ui.row().classes('w-full items-center gap-2 mb-6'):
                                            ui.label(cat_name).classes('text-[10px] uppercase font-bold tracking-widest text-slate-400')
                                            if tree.get('is_trending'):
                                                with ui.row().classes('items-center gap-1 bg-red-50 text-red-600 px-2 py-0.5 rounded-full'):
                                                    ui.icon('bolt', size='xs')
                                                    ui.label('TRENDING').classes('text-[10px] font-black')

                                        # Action Button
                                        if already_added:
                                            with ui.button().props('unelevated color=slate-100 text-color=slate-400 disable').classes('w-full rounded-xl py-3'):
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.icon('check_circle', size='sm')
                                                    ui.label('ĐÃ SỞ HỮU').classes('font-black tracking-tight')
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
                                                
                                                try:
                                                    from resource_sync import sync_resources_to_tree
                                                    sync_resources_to_tree(dst_path)
                                                except: pass

                                                try:
                                                    from resource_sync import sync_bloom_content_to_tree
                                                    sync_bloom_content_to_tree(dst_path, user.username)
                                                except: pass

                                                # Update user's subjects.json
                                                subj_data = {'subjects': []}
                                                if os.path.exists(user_subj_file):
                                                    with open(user_subj_file, 'r', encoding='utf-8') as rf:
                                                        subj_data = _json.load(rf)

                                                if not any(s['id'] == t['id'] for s in subj_data['subjects']):
                                                    subj_data['subjects'].append({
                                                        'id': t['id'], 'title': t['title'],
                                                        'filename': dst_path.replace('\\', '/'),
                                                        'total_nodes': t['total_nodes']
                                                    })
                                                    with open(user_subj_file, 'w', encoding='utf-8') as wf:
                                                        _json.dump(subj_data, wf, ensure_ascii=False, indent=2)

                                                ui.notify(f'✅ Đã sở hữu "{t["title"]}"!', type='positive')
                                                render_public_cards()
                                                # SYNC: Refresh Personal Library too
                                                view_refreshers['library']()

                                            btn_label = f'MUA {price} XP' if price > 0 else 'THÊM VÀO THƯ VIỆN'
                                            with ui.button(on_click=add_tree).props(f'id="btn-start-learning" unelevated color={btn_color} size=lg').classes(f'w-full rounded-xl py-3 hover:scale-[1.02] transition-transform {shadow_color} shadow-lg'):
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.icon('shopping_bag' if price > 0 else 'add_task', size='sm')
                                                    ui.label(btn_label).classes('font-black tracking-tight')

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
            
            tab_actions['Cộng đồng'] = load_social

        # TAB 6: BLOOM HUB (Học tập sâu)
        with ui.tab_panel(tab_bloom).classes('p-0 m-0 h-full w-full bg-[#0d1117] overflow-hidden'):
            bloom_container = ui.element('div').classes('w-full h-full p-0 m-0')
            
            # Register tab action for Bloom Hub - picks up pending navigation
            async def load_bloom_from_pending():
                pending = app.storage.user.get('pending_bloom_nav')
                if pending and isinstance(pending, dict):
                    # Will be handled by check_pending_bloom_hub poller
                    pass
            tab_actions['Bloom Hub'] = lambda: None  # Placeholder to prevent errors

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
                             if hasattr(nexus_container, 'nexus_timer') and nexus_container.nexus_timer:
                                 try:
                                     nexus_container.nexus_timer.delete()
                                 except:
                                     pass
                             nexus_container.clear()
                             with nexus_container:
                                 # The "Polling Event" Master Fix (checks both __bridge_payload and postMessage)
                                 async def check_nexus_3d_bridge():
                                     try:
                                         payload = await ui.run_javascript('''
                                             if (window.__graph_action_payload) {
                                                 let p = window.__graph_action_payload;
                                                 window.__graph_action_payload = null;
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
                                             children = payload.get('children', [])
                                             target_url = payload.get('target_url')
                                             selected_child = payload.get('selected_child')
                                             
                                             if raw_node_id:
                                                 print(f"[Nexus] Bắt được sự kiện 3D Bridge: {raw_node_id}, Action: {action}, URL: {target_url}, Child: {selected_child}")
                                                 
                                                 if target_url:
                                                     app.storage.user['target_video_url'] = target_url
                                                     
                                                 if action == 'bloom_hub':
                                                     subject_id = os.path.basename(last_path).replace('.json', '')
                                                     app.storage.user['pending_bloom_nav'] = {
                                                         'subject_id': subject_id,
                                                         'node_id': raw_node_id,
                                                         'node_label': node_label,
                                                         'source': 'nexus',
                                                         'json_file_path': last_path,
                                                     }
                                                     main_tabs.value = tab_bloom
                                                     return
                                                 
                                                 if children and len(children) > 0:
                                                     if selected_child:
                                                         child_idx = next((i for i, c in enumerate(children) if c.get('id') == selected_child), -1)
                                                         if child_idx > 0:
                                                             children.insert(0, children.pop(child_idx))
                                                     target_tab = tab_video if action == 'video' else tab_quiz
                                                     if target_tab:
                                                         load_lesson_ui(raw_node_id, target_tab=target_tab, is_meso=True, meso_label=node_label, meso_children=children)
                                                     return
                                                 
                                                 node_id = resolve_concept_id(raw_node_id, node_label) or raw_node_id
                                                 try:
                                                     target_tab = None
                                                     if action == 'video': target_tab = tab_video
                                                     elif action == 'quiz': target_tab = tab_quiz
                                                     
                                                     if target_tab:
                                                         load_lesson_ui(node_id, target_tab=target_tab)
                                                     
                                                     subject_id = os.path.basename(last_path).replace('.json', '')
                                                     if action in ['tutor', 'ai_tutor']:
                                                         try:
                                                             target_url = f'/quiz_node/{subject_id}/{node_id}'
                                                             ui.run_javascript(f"window.open('{target_url}', '_blank', 'width=1200,height=900,left=150,top=50')")
                                                         except Exception as tutor_e:
                                                             print(f"[Nexus] Lỗi khi mở Khảo Thí Cấp Cao: {tutor_e}")
                                                 except Exception as err:
                                                     print(f"[Nexus] Lỗi khi xử lý thao tác 3D: {err}")
                                     except RuntimeError: pass
                                     except Exception: pass

                                 # Install postMessage listener for Nexus
                                 ui.run_javascript('''
                                     if (!window.__graph_action_postmsg_installed) {
                                         window.__graph_action_postmsg_installed = true;
                                         window.addEventListener('message', function(event) {
                                             if (event.data && event.data.type === 'graph3d_action') {
                                                 console.log('[Global Bridge] postMessage received:', JSON.stringify(event.data.payload));
                                                 window.__graph_action_payload = event.data.payload;
                                             }
                                         });
                                         console.log('[Global Bridge] postMessage listener installed');
                                     }
                                 ''')

                                 # Poll every 500ms
                                 nexus_container.nexus_timer = ui.timer(0.5, check_nexus_3d_bridge)

                                 # Hidden bridge element for iframe-to-parent communication
                                 bridge = ui.element('div').props('id="nexus-bridge"').classes('hidden')

                                 import time
                                 v = int(time.time())
                                 ui.element('iframe').props(f'src="/user_data/{user.username}/current_visual_tree.html?v={v}" width="100%" height="100%"').classes('w-full h-full border-none')
                 else:
                     with nexus_container:
                         ui.label('Không gian 3D chưa được thiết lập. Hãy tạo cây trong Graph Studio.').classes('text-gray-400 italic')
              
             tab_actions['Vũ trụ Tri thức 3D'] = activate_nexus

        # TAB 3: VIDEO bài giảng
        with ui.tab_panel(tab_video).classes('p-0 h-full'):
             with ui.column().classes('w-full h-full p-0 relative'):
                 video_container = ui.column().classes('w-full h-full bg-black relative justify-center items-center')

        # TAB 4: QUIZ
        with ui.tab_panel(tab_quiz).classes('p-0 h-full'):
             with ui.column().classes('w-full h-full p-6 bg-gray-50 overflow-y-auto'):
                 lesson_label_quiz = ui.label("Vui lòng chọn bài học từ tab 'Hành trình'").classes('text-2xl text-gray-400 font-bold mb-6')
                 quiz_container = ui.column().classes('w-full')

        # TAB 7: PROFILE (Hồ sơ cá nhân)
        with ui.tab_panel('profile').classes('p-0 h-full bg-slate-50 overflow-y-auto'):
             ui.label('>>> PROFILE TAB ACTIVE <<<').classes('text-red-500 font-bold p-2 text-xs')
             profile_container = ui.column().classes('w-full min-h-screen p-4')
             
             def load_profile():
                 try:
                     print(f"[Profile] Loading profile for user: {user.username} (ID: {user.id})")
                     create_profile_section(user, profile_container)
                 except Exception as e:
                     import traceback
                     error_msg = f"Lỗi tải hồ sơ: {str(e)}"
                     ui.notify(error_msg, type='negative')
                     print(f"[Profile] Error: {traceback.format_exc()}")
             
             tab_actions['profile'] = load_profile
             # Manually trigger if already on profile tab (e.g. after refresh)
             if main_tabs.value == 'profile':
                 load_profile()

        # TAB 8: XẾP HẠNG (LEADERBOARD)
        with ui.tab_panel(tab_leaderboard).classes('p-0 h-full bg-slate-50 overflow-y-auto'):
             from leaderboard_page import create_leaderboard_section
             leaderboard_container = ui.column().classes('w-full')
             
             def load_leaderboard():
                 create_leaderboard_section(user, leaderboard_container)
             
             tab_actions['Xếp hạng'] = load_leaderboard
             if main_tabs.value == 'Xếp hạng':
                 load_leaderboard()

        # TAB: ADMIN DASHBOARD
        with ui.tab_panel(tab_admin).classes('p-0 h-full bg-slate-50 overflow-y-auto w-full'):
             build_dashboard_admin_ui()



        # TAB 5: GRAPH STUDIO (ADVANCED MGMT)
        with ui.tab_panel(tab_studio).classes('p-0 h-full bg-gray-50 overflow-y-auto w-full'):
             # === VIEW SWITCHING: Library vs 3D Graph ===
             studio_library_view = ui.column().classes('w-full p-6')
             studio_graph_view = ui.column().classes('w-full h-full p-0 hidden')
             
             with studio_library_view:
                 ui.label('Graph Studio').classes('text-3xl font-extrabold text-slate-800 mb-1 tracking-tight')
                 ui.label('Quản trị Đồ thị Tri thức Đẳng cấp Quốc tế.').classes('text-slate-500 mb-8')
                 # --- THƯ VIỆN MÔN HỌC ---
                 library_container = ui.row().classes('w-full gap-4 flex-wrap')
             
             tree_preview_container = studio_graph_view
             
             def show_graph_view():
                 nav_state['is_in_studio_graph'] = True
                 studio_library_view.classes('hidden', remove='w-full')
                 studio_graph_view.classes(remove='hidden')
                 studio_graph_view.classes('w-full')
             
             def show_library_view():
                 nav_state['is_in_studio_graph'] = False
                 studio_graph_view.classes('hidden', remove='w-full')
                 studio_library_view.classes(remove='hidden')
                 studio_library_view.classes('w-full')
             
             nav_state['back_to_library'] = show_library_view
             
             from step2_5_visualize_tree import visualize_knowledge_tree

             async def render_3d_graph(json_file_path):
                 try:
                     ui.notify('🔄 Đang đồng bộ & tối ưu hóa Mạng Lưới 3D...', type='info')
                     # 1. Tự động quét và đồng bộ tài nguyên từ thư mục local
                     from resource_sync import sync_resources_to_tree, sync_bloom_content_to_tree
                     await run.io_bound(sync_resources_to_tree, json_file_path)
                     
                     # 1b. Đồng bộ nội dung Bloom từ thư viện chung
                     bloom_sync = await run.io_bound(sync_bloom_content_to_tree, json_file_path, user.username)
                     if bloom_sync.get('synced', 0) > 0:
                         ui.notify(f'📥 Đã tải {bloom_sync["synced"]} gói nội dung từ thư viện!', type='positive')
                     
                     # 2. Tái tạo HTML 3D
                     from step2_5_visualize_tree import visualize_knowledge_tree
                     await run.io_bound(visualize_knowledge_tree, user.username, json_file_path)
                     
                     # --- UPDATE OMNI-CONTEXT ---
                     if 'omni_context' in app.storage.user:
                         subj_id = os.path.basename(json_file_path).replace('.json', '')
                         subj_title = app.storage.user['omni_context'].get('subject_title', subj_id)
                         app.storage.user['omni_context']['subject_id'] = subj_id
                         app.storage.user['omni_context']['current_tab'] = 'graph_studio'
                         omni_ui['context_label'].text = f'Đang theo dõi: Graph Studio ({subj_title})'

                     if hasattr(tree_preview_container, 'studio_timer') and tree_preview_container.studio_timer:
                         try:
                             tree_preview_container.studio_timer.delete()
                         except:
                             pass
                     tree_preview_container.clear()
                     show_graph_view()
                     with tree_preview_container:
                         
                         # === ROBUST BRIDGE: postMessage listener + polling ===
                         async def handle_studio_bridge_action(raw_node_id, action, node_label='', children=None, target_url=None, selected_child=None):
                             """Central handler for 3D graph bridge actions"""
                             if not raw_node_id:
                                 return
                                 
                             print(f"[Graph Studio] Bắt được sự kiện 3D Bridge: {raw_node_id}, Action: {action}, URL: {target_url}, Child: {selected_child}")
                                 
                             if target_url:
                                 app.storage.user['target_video_url'] = target_url
                                 
                             if action == 'bloom_hub':
                                 import os
                                 subject_id = os.path.basename(json_file_path).replace('.json', '')
                                 # Use pending_bloom_nav mechanism to avoid context issues
                                 app.storage.user['pending_bloom_nav'] = {
                                     'subject_id': subject_id,
                                     'node_id': raw_node_id,
                                     'node_label': node_label,
                                     'source': 'graph_studio',
                                     'json_file_path': json_file_path,
                                 }
                                 print(f"[Graph Studio] Đã đặt pending_bloom_nav cho node: {raw_node_id}")
                                 return

                             if children and len(children) > 0:
                                 # Meso Node action
                                 if selected_child:
                                     # Reorder children so selected_child is first
                                     child_idx = next((i for i, c in enumerate(children) if c.get('id') == selected_child), -1)
                                     if child_idx > 0:
                                         children.insert(0, children.pop(child_idx))
                                 target_tab = tab_video if action == 'video' else tab_quiz
                                 if target_tab:
                                     # if we have a selected child we could reorder, but relying on target_url is enough
                                     load_lesson_ui(raw_node_id, target_tab=target_tab, is_meso=True, meso_label=node_label, meso_children=children)
                                 return

                             is_custom_tree = 'user_data' in json_file_path or 'public_trees' in json_file_path
                             if is_custom_tree:
                                 node_id = raw_node_id
                             else:
                                 node_id = resolve_concept_id(raw_node_id, node_label) or raw_node_id
                             try:
                                 target_tab = None
                                 if action == 'video': target_tab = tab_video
                                 elif action == 'quiz': target_tab = tab_quiz
                                 if target_tab:
                                     load_lesson_ui(node_id, target_tab=target_tab)
                                 
                                 if action in ['tutor', 'ai_tutor']:
                                     import os
                                     subject_id = os.path.basename(json_file_path).replace('.json', '')
                                     target_url = f'/quiz_node/{subject_id}/{node_id}'
                                     ui.run_javascript(f"window.open('{target_url}', '_blank', 'width=1200,height=900,left=150,top=50')")
                             except Exception as err:
                                 print(f"[Graph Studio] Lỗi khi xử lý thao tác 3D: {err}")

                         # METHOD A: postMessage listener (most reliable for iframe communication)
                         async def check_studio_postmessage():
                             try:
                                 payload = await ui.run_javascript('''
                                     if (window.__graph_action_payload) {
                                         let p = window.__graph_action_payload;
                                         window.__graph_action_payload = null;
                                         return p;
                                     }
                                     return null;
                                 ''', timeout=1.0)
                                 if payload and isinstance(payload, dict):
                                     node_id = payload.get('id')
                                     action = payload.get('action', 'video')
                                     node_label = payload.get('label', '')
                                     children = payload.get('children', [])
                                     target_url = payload.get('target_url')
                                     selected_child = payload.get('selected_child')
                                     if node_id:
                                         await handle_studio_bridge_action(node_id, action, node_label, children, target_url, selected_child)
                             except Exception:
                                 pass

                         # Install postMessage listener on parent window
                         ui.run_javascript('''
                             if (!window.__graph_action_postmsg_installed) {
                                 window.__graph_action_postmsg_installed = true;
                                 window.addEventListener('message', function(event) {
                                     if (event.data && event.data.type === 'graph3d_action') {
                                         console.log('[Global Bridge] postMessage received:', JSON.stringify(event.data.payload));
                                         window.__graph_action_payload = event.data.payload;
                                     }
                                 });
                                 console.log('[Global Bridge] postMessage listener installed');
                             }
                         ''')

                         # Poll every 500ms for postMessage payloads
                         tree_preview_container.studio_timer = ui.timer(0.5, check_studio_postmessage)
                         
                         # METHOD B: Also keep input bridge as fallback
                         async def handle_3d_click(e):
                             if getattr(e, 'value', None) is None: return
                             import json as _json
                             try:
                                 payload = _json.loads(e.value)
                                 if payload and isinstance(payload, dict):
                                     node_id = payload.get('id')
                                     action = payload.get('action', 'video')
                                     node_label = payload.get('label', '')
                                     if node_id:
                                         await handle_studio_bridge_action(node_id, action, node_label)
                             except Exception:
                                 pass
                                     
                         bridge = ui.input(on_change=handle_3d_click).props('id="studio-bridge"').classes('absolute -top-[1000px] left-0 opacity-0 z-[-1]')

                         import time
                         v = int(time.time())
                         ui.element('iframe').props(f'src="/user_data/{user.username}/current_visual_tree.html?v={v}" width="100%" height="100%"').classes('w-full border-none shadow-lg').style('height: calc(100vh - 150px); min-height: 600px;')
                         
                         with open(json_file_path, 'r', encoding='utf-8') as f:
                             read_json = json.load(f)
                         with ui.expansion('Xem chi tiết cấu trúc JSON thô (Dành cho Dev)', icon='code').classes('w-full mt-4 bg-gray-50 border rounded-lg text-gray-700'):
                             ui.code(json.dumps(read_json, indent=2, ensure_ascii=False), language='json').classes('w-full overflow-y-auto max-h-[500px] border shadow-sm rounded')
                 except Exception as ex:
                     ui.notify(f'❌ Lỗi dựng đồ họa: {str(ex)}', type='negative')

             def render_library():
                 view_refreshers['library'] = render_library # Register
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
                         expanded_chaps = set()

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
                                     for chap_idx, chap in enumerate(tree_structure):
                                         lessons = chap.get('children', [])
                                         match_chap = search_q in chap['label'].lower() or search_q in chap['id'].lower()
                                         match_any_child = any(search_q in l['label'].lower() or search_q in l['id'].lower() for l in lessons)
                                         
                                         if search_q and not match_chap and not match_any_child:
                                             continue

                                         is_expanded = chap_idx in expanded_chaps or bool(search_q) or any(selected_node_id['value'] == l['id'] for l in lessons) or selected_node_id['value'] == chap['id']
                                         
                                         exp = ui.expansion('', icon=type_icons['macro']).classes('w-full border border-gray-100 rounded-lg mb-1 overflow-hidden').props(f'header-class="text-sm font-bold text-slate-800 p-2 bg-slate-50"')
                                         exp.value = is_expanded
                                         exp.on('update:value', lambda v, idx=chap_idx: expanded_chaps.add(idx) if v else expanded_chaps.discard(idx))
                                         
                                         with exp:
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
                                 node_detail = get_node_detail(tree_path, node_id)
                             except Exception as ex:
                                 with detail_container:
                                     ui.label(f'Lỗi: {ex}').classes('text-red-500 p-6')
                                 return
                             
                             node_label = node_info['label'] if node_info else node_id
                             description_md = node_detail.get('description_md', '') if node_detail else ''
                             content_fallback = node_detail.get('content', '') if node_detail else ''
                             
                             # Local state for edit mode
                             desc_state = {'editing': False}
                             
                             with detail_container:
                                 with ui.column().classes('w-full p-6 gap-4'):
                                     # Node header
                                     with ui.row().classes('items-center gap-3 mb-2'):
                                         type_icons = {'macro': '🌐', 'micro': '📚', 'assess': '🧪'}
                                         ui.label(type_icons.get(node_info['type'] if node_info else '', '📌')).classes('text-2xl')
                                         with ui.column().classes('gap-0'):
                                             with ui.row().classes('items-center gap-2'):
                                                 ui.label(node_label).classes('text-xl font-bold text-slate-800')
                                                 if node_id.startswith('Chuong_'):
                                                     ui.button(icon='play_circle', on_click=lambda nid=node_id: [res_dialog.close(), load_lesson_ui(nid)]) \
                                                         .props('flat round color=green size=md').tooltip('Học ngay bài này (Mở Trình phát)')
                                             ui.label(f'ID: {node_id}').classes('text-xs text-gray-400 font-mono')
                                     
                                     ui.separator()
                                     
                                     # ===== DESCRIPTION SECTION (MỚI) =====
                                     with ui.row().classes('w-full items-center justify-between'):
                                         ui.label('📝 Mô tả chi tiết').classes('text-sm font-bold text-emerald-700 uppercase tracking-wide')
                                         with ui.row().classes('gap-1'):
                                             desc_edit_btn = ui.button(icon='edit', on_click=lambda: _toggle_desc_edit(node_id)).props('flat round size=sm color=blue').tooltip('Chỉnh sửa mô tả')
                                             desc_ai_btn = ui.button('AI ✨', icon='auto_awesome', on_click=lambda nid=node_id: _ai_generate_desc(nid)).props('flat dense size=sm color=purple').classes('text-xs font-bold').tooltip('AI tự động sinh mô tả')
                                     
                                     # Description card
                                     desc_card = ui.card().classes('w-full p-0 border border-emerald-100 rounded-xl overflow-hidden')
                                     with desc_card:
                                         # Preview container
                                         desc_preview = ui.column().classes('w-full p-4 bg-emerald-50/30')
                                         with desc_preview:
                                             if description_md:
                                                 ui.markdown(description_md).classes('w-full prose prose-sm max-w-none text-slate-700')
                                                 ui.run_javascript('setTimeout(() => { if (window.MathJax) MathJax.typesetPromise(); }, 300);')
                                             elif content_fallback:
                                                 ui.label('Nội dung tóm tắt (chưa có mô tả chi tiết):').classes('text-xs text-gray-400 italic mb-1')
                                                 ui.label(content_fallback).classes('text-sm text-slate-500 leading-relaxed')
                                                 ui.html('<div class="mt-3 text-center"><span class="text-xs text-emerald-400 italic">💡 Nhấn "AI ✨" để tạo mô tả chi tiết tự động</span></div>')
                                             else:
                                                 with ui.column().classes('items-center py-6'):
                                                     ui.icon('description', color='gray').classes('text-3xl mb-2 opacity-40')
                                                     ui.label('Chưa có mô tả').classes('text-gray-400 text-sm')
                                                     ui.label('Nhấn "AI ✨" để tạo tự động hoặc ✏️ để viết tay').classes('text-[11px] text-gray-300')
                                         
                                         # Edit container (hidden by default)
                                         desc_edit_area = ui.column().classes('w-full p-4 bg-white')
                                         desc_edit_area.set_visibility(False)
                                         with desc_edit_area:
                                             ui.label('Chỉnh sửa Markdown (hỗ trợ LaTeX: $...$ hoặc $$...$$)').classes('text-[10px] text-gray-400 mb-1')
                                             desc_textarea = ui.textarea(
                                                 value=description_md or content_fallback or '',
                                                 placeholder='Viết mô tả bằng Markdown...\n\n## Mục tiêu bài học\n- ...\n\n## Công thức\n$$E = mc^2$$'
                                             ).props('outlined autogrow').classes('w-full font-mono text-sm').style('min-height: 200px')
                                             
                                             with ui.row().classes('w-full justify-end gap-2 mt-2'):
                                                 ui.button('Hủy', icon='close', on_click=lambda: _toggle_desc_edit(node_id)).props('flat size=sm color=grey')
                                                 ui.button('💾 Lưu', icon='save', on_click=lambda nid=node_id: _save_desc(nid)).props('unelevated size=sm color=green rounded').classes('font-bold')
                                         
                                         # AI loading spinner
                                         desc_spinner = ui.row().classes('w-full p-4 items-center gap-3 bg-purple-50')
                                         desc_spinner.set_visibility(False)
                                         with desc_spinner:
                                             ui.spinner('dots', size='md', color='purple')
                                             desc_spinner_label = ui.label('AI đang phân tích ngữ cảnh bài học...').classes('text-purple-600 text-sm font-bold italic')
                                     
                                     def _toggle_desc_edit(nid):
                                         is_edit = not desc_state['editing']
                                         desc_state['editing'] = is_edit
                                         desc_preview.set_visibility(not is_edit)
                                         desc_edit_area.set_visibility(is_edit)
                                         if is_edit:
                                             # Load current content into textarea
                                             current = description_md or content_fallback or ''
                                             desc_textarea.value = current
                                     
                                     def _save_desc(nid):
                                         new_md = (desc_textarea.value or '').strip()
                                         try:
                                             success = update_node_description(tree_path, nid, new_md)
                                             if success:
                                                 ui.notify('✅ Đã lưu mô tả chi tiết!', type='positive')
                                                 render_detail(nid)  # Re-render to show preview
                                             else:
                                                 ui.notify('⚠️ Không tìm thấy node', type='warning')
                                         except Exception as ex:
                                             ui.notify(f'❌ Lỗi: {ex}', type='negative')
                                     
                                     async def _ai_generate_desc(nid):
                                         desc_spinner.set_visibility(True)
                                         desc_spinner_label.text = 'AI đang phân tích ngữ cảnh bài học...'
                                         desc_preview.set_visibility(False)
                                         desc_edit_area.set_visibility(False)
                                         try:
                                             from ai_description_generator import generate_node_description
                                             result = await run.io_bound(generate_node_description, tree_path, nid)
                                             desc_spinner.set_visibility(False)
                                             
                                             # Show in edit mode so user can review/edit before saving
                                             desc_state['editing'] = True
                                             desc_textarea.value = result
                                             desc_edit_area.set_visibility(True)
                                             ui.notify('✨ AI đã tạo mô tả! Hãy xem lại và nhấn Lưu.', type='info')
                                         except Exception as ex:
                                             desc_spinner.set_visibility(False)
                                             desc_preview.set_visibility(True)
                                             ui.notify(f'❌ Lỗi AI: {ex}', type='negative')
                                     
                                     ui.separator().classes('my-1')
                                     
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
                                                 # Tự động cập nhật đồ thị 3D bên dưới
                                                 ui.timer(0, lambda: render_3d_graph(tree_path), once=True)
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
                                                         # --- QUICK PLAY BUTTON ---
                                                         if node_id.startswith('Chuong_'):
                                                             ui.button(icon='play_arrow', on_click=lambda nid=node_id: [res_dialog.close(), load_lesson_ui(nid)]).props('flat round size=sm color=green').tooltip('Bắt đầu học ngay (Mở Player)')
                                                         
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

                 def open_publish_dialog(subj):
                     with ui.dialog() as dlg, ui.card().classes('w-96 p-6 rounded-xl'):
                         ui.label('Đăng bán Cây Tri Thức').classes('text-xl font-extrabold text-slate-800 mb-1')
                         ui.label(f'{subj.get("title", "Môn học")}').classes('text-md font-bold text-indigo-600 mb-2 truncate')
                         ui.label('Bạn có thể đóng góp cây tri thức này vào Cửa hàng UGC và đặt mức phí (XP) để chia sẻ với cộng đồng.').classes('text-sm text-slate-500 mb-6')
                         
                         xp_input = ui.number('Giá cho thuê (XP)', value=0, min=0, format='%d').props('outlined dense').classes('w-full mb-4')
                         desc_input = ui.textarea('Mô tả ngắn gọn', value=subj.get('description', '')).props('outlined dense rows=3').classes('w-full mb-6')
                         
                         def do_publish():
                             try:
                                 xp = int(xp_input.value or 0)
                                 desc = desc_input.value.strip() or f'Cây tri thức {subj.get("title")} do cộng đồng đóng góp.'
                                 
                                 subj_filename = subj.get('filename')
                                 subj_id = os.path.basename(subj_filename).replace('.json', '')
                                 target_dir = os.path.join(os.getcwd(), 'DB', 'public_trees')
                                 os.makedirs(target_dir, exist_ok=True)
                                 target_path = os.path.join(target_dir, f'{subj_id}.json')
                                 
                                 import shutil
                                 shutil.copy2(subj_filename, target_path)
                                 
                                 pub_lib_path = os.path.join(os.getcwd(), 'DB', 'public_library.json')
                                 pub_data = {"trees": []}
                                 if os.path.exists(pub_lib_path):
                                     with open(pub_lib_path, 'r', encoding='utf-8') as f:
                                         pub_data = json.load(f)
                                 
                                 existing = next((t for t in pub_data.get('trees', []) if t['id'] == subj_id), None)
                                 if existing:
                                     existing['price_xp'] = xp
                                     existing['description'] = desc
                                     existing['premium_only'] = (xp > 0)
                                 else:
                                     pub_data['trees'].append({
                                         "id": subj_id,
                                         "title": subj.get('title'),
                                         "filename": f"DB/public_trees/{subj_id}.json",
                                         "total_nodes": subj.get('total_nodes', 0),
                                         "description": desc,
                                         "category": "Cộng đồng (UGC)",
                                         "is_trending": False,
                                         "premium_only": (xp > 0)
                                     })
                                     
                                 with open(pub_lib_path, 'w', encoding='utf-8') as f:
                                     json.dump(pub_data, f, ensure_ascii=False, indent=2)
                                     
                                 ui.notify('✅ Đăng cây thành công lên Cửa hàng UGC!', type='positive')
                                 dlg.close()
                             except Exception as e:
                                 ui.notify(f'❌ Lỗi: {e}', type='negative')
                                 
                         with ui.row().classes('w-full justify-end gap-3'):
                             ui.button('Hủy', on_click=dlg.close).props('flat text-color=gray-500')
                             ui.button('Đăng lên', icon='publish', on_click=do_publish).props('color=indigo px-6 rounded-lg')
                     dlg.open()

                 with library_container:
                     if subjects_data["subjects"]:
                         ui.label('Thư viện Tri thức của bạn').classes('text-xl font-bold text-gray-800 w-full mb-2 border-b pb-2')
                         for subj in subjects_data["subjects"]:
                             subj_id = os.path.basename(subj.get('filename', '')).replace('.json', '')
                             # MIT Dynamic Palette: Variety with Professionalism
                             palettes = [
                                 ('from-indigo-500 to-blue-600', 'indigo-700', 'shadow-indigo-100'),
                                 ('from-emerald-500 to-teal-600', 'emerald-700', 'shadow-emerald-100'),
                                 ('from-amber-500 to-orange-600', 'amber-700', 'shadow-amber-100'),
                                 ('from-purple-500 to-violet-600', 'purple-700', 'shadow-purple-100'),
                                 ('from-rose-500 to-pink-600', 'rose-700', 'shadow-rose-100'),
                                 ('from-cyan-500 to-sky-600', 'cyan-700', 'shadow-cyan-100'),
                             ]
                             accent_grad, btn_color, shadow_color = palettes[hash(subj_id) % len(palettes)]

                             # MIT Standard Card: Clean, Professional, Hierarchical
                             with ui.card().classes('w-[320px] p-0 overflow-hidden rounded-2xl border border-slate-200 shadow-sm hover:shadow-xl transition-all duration-300 group'):
                                 # Top Accent Bar
                                 ui.element('div').classes(f'w-full h-1.5 bg-gradient-to-r {accent_grad}')
                                 
                                 with ui.column().classes('w-full p-6'):
                                     # Header: Title & Meta
                                     with ui.row().classes('w-full items-start justify-between no-wrap mb-1'):
                                         ui.label(subj.get('title', 'Môn học')).classes('font-black text-xl text-slate-800 leading-tight truncate flex-1').tooltip(subj.get('title'))
                                         ui.badge(f"{subj.get('total_nodes', 0)} Nodes", color='slate-100').classes('text-slate-500 text-[10px] font-bold px-2 py-0.5 mt-1')
                                     
                                     ui.label('Knowledge Galaxy Interface').classes('text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-6')
                                     
                                     # --- PRIMARY ACTION: HERO BUTTON ---
                                     def _activate_3d_wrapper(p=subj.get('filename'), t=subj.get('title')):
                                         if 'omni_context' in app.storage.user:
                                             app.storage.user['omni_context']['subject_title'] = t
                                         ui.timer(0, lambda: render_3d_graph(p), once=True)
                                         
                                     with ui.button(on_click=_activate_3d_wrapper).props(f'unelevated color={btn_color} size=lg').classes(f'w-full rounded-xl py-3 group-hover:scale-[1.02] transition-transform {shadow_color} shadow-lg'):
                                         with ui.row().classes('items-center gap-3'):
                                             ui.icon('auto_awesome').classes('text-xl')
                                             ui.label('KÍCH HOẠT VŨ TRỤ 3D').classes('font-black tracking-tight')

                                     # --- SECONDARY ACTIONS BAR ---
                                     with ui.row().classes('w-full mt-6 pt-4 border-t border-slate-100 items-center justify-between'):
                                         # Practice Hub (Menu)
                                         with ui.button(icon='psychology').props('flat round color=blue-6 size=md').classes('hover:bg-blue-50') as practice_btn:
                                             ui.tooltip('Trung tâm Luyện tập (Flashcards, Marathon...)')
                                             with ui.menu().classes('p-2 rounded-xl border border-slate-100 shadow-2xl'):
                                                 ui.label('LUYỆN TẬP BLOOM').classes('text-[10px] font-black text-slate-400 px-4 py-2')
                                                 ui.menu_item('📚 Flashcards (Ghi nhớ)', on_click=lambda sid=subj_id: ui.navigate.to(f'/flashcards/{sid}')).classes('rounded-lg hover:bg-cyan-50 text-cyan-700')
                                                 ui.menu_item('⚡ Đua tốc độ (Phản xạ)', on_click=lambda sid=subj_id: ui.navigate.to(f'/timed_challenge/{sid}')).classes('rounded-lg hover:bg-amber-50 text-amber-700')
                                                 ui.menu_item('🏃 Marathon (Bền bỉ)', on_click=lambda sid=subj_id: ui.navigate.to(f'/practice/{sid}/marathon')).classes('rounded-lg hover:bg-green-50 text-green-700')
                                                 ui.menu_item('🎯 Điểm yếu (Tối ưu)', on_click=lambda sid=subj_id: ui.navigate.to(f'/practice/{sid}/weak_focus')).classes('rounded-lg hover:bg-red-50 text-red-700')
                                         
                                         # Resource Manager
                                         ui.button(icon='folder_open', on_click=lambda p=subj.get('filename'), t=subj.get('title', 'Môn học'): open_resource_manager(p, t)) \
                                             .props('flat round color=slate-5 size=md').classes('hover:bg-slate-50').tooltip('Quản lý Tài nguyên')
                                         
                                         # UGC Publishing
                                         ui.button(icon='publish', on_click=lambda s=subj: open_publish_dialog(s)) \
                                             .props('flat round color=purple-5 size=md').classes('hover:bg-purple-50').tooltip('Đưa lên Cửa hàng UGC')
                                         
                                         # More Options (Delete/Info)
                                         with ui.button(icon='more_horiz').props('flat round color=slate-3 size=md').classes('hover:bg-slate-50'):
                                             with ui.menu().classes('p-2 rounded-xl shadow-2xl border'):
                                                 def open_delete_confirm(s=subj):
                                                     with ui.dialog() as d, ui.card().classes('p-8 rounded-2xl w-96'):
                                                         ui.icon('warning', color='red', size='lg').classes('mb-4')
                                                         ui.label('Loại bỏ môn học?').classes('text-2xl font-black text-slate-800 mb-2')
                                                         ui.label(f'Bạn có chắc chắn muốn xóa "{s.get("title")}" khỏi thư viện cá nhân?').classes('text-slate-500 mb-8 leading-relaxed')
                                                         with ui.row().classes('w-full justify-end gap-3'):
                                                             ui.button('Hủy', on_click=d.close).props('flat text-color=gray-500')
                                                             def do_delete():
                                                                 try:
                                                                     # 1. Update subjects.json
                                                                     subj_f = f"user_data/{user.username}/subjects.json"
                                                                     if os.path.exists(subj_f):
                                                                         with open(subj_f, 'r', encoding='utf-8') as f:
                                                                             data = json.load(f)
                                                                         data['subjects'] = [sub for sub in data['subjects'] if sub.get('filename') != s.get('filename')]
                                                                         with open(subj_f, 'w', encoding='utf-8') as f:
                                                                             json.dump(data, f, ensure_ascii=False, indent=2)
                                                                     
                                                                     # 2. Delete the actual tree file
                                                                     if s.get('filename') and os.path.exists(s.get('filename')):
                                                                         os.remove(s.get('filename'))
                                                                         
                                                                     ui.notify(f'✅ Đã loại bỏ: {s.get("title")}', type='positive')
                                                                     d.close()
                                                                     render_library() 
                                                                     # SYNC: Refresh UGC Store too
                                                                     view_refreshers['public']()
                                                                 except Exception as ex:
                                                                     ui.notify(f'❌ Lỗi khi xóa: {ex}', type='negative')
                                                             ui.button('Xác nhận xóa', on_click=do_delete, icon='delete_forever').props('color=red unelevated px-6 rounded-lg')
                                                     d.open()
                                                 
                                                 ui.menu_item('🗑️ Loại bỏ môn học', on_click=open_delete_confirm).classes('text-red-600 font-bold hover:bg-red-50 rounded-lg')
                                                 ui.menu_item('ℹ️ Xem thông tin chi tiết').classes('text-slate-600 rounded-lg')

             # Khởi tạo thư viện lần đầu
             render_library()


        # TAB 6: CREATOR HUB — FULLY AUTOMATED 3-STEP WIZARD
        with ui.tab_panel(tab_creator).classes('p-0 h-full bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 overflow-y-auto'):
            # ══════════════════════════════════════════════════════════════════
            # CREATOR HUB — AUTO-PIPELINE WIZARD (MIT-Level UX)
            # ══════════════════════════════════════════════════════════════════
            creator_state = {
                'step': 1,
                'json_path': None,
                'tree_data': None,
                'course_title': '',
            }

            # ── HEADER BAR ──────────────────────────────────────────────────
            with ui.column().classes('w-full px-8 pt-8 pb-4'):
                with ui.row().classes('w-full items-center justify-between flex-wrap gap-4'):
                    with ui.column().classes('gap-1'):
                        with ui.row().classes('items-center gap-3'):
                            ui.icon('hub', color='indigo-300').classes('text-4xl')
                            ui.label('Creator Hub').classes('text-4xl font-black text-white tracking-tight')
                        ui.label('Biến tài liệu bài giảng thành vũ trụ tri thức 3D tự động — chuẩn MIT / Harvard.').classes('text-slate-400 text-sm font-medium')

                    # Stepper Indicator
                    step_labels_list = [('auto_awesome', '1. AI Phân Tích'), ('schema', '2. Biên Dịch 3D'), ('attach_file', '3. Nhúng Tài Nguyên')]
                    step_colors_a = ['bg-blue-500', 'bg-green-500', 'bg-indigo-500']
                    step_dots = []
                    with ui.row().classes('items-center gap-0 bg-white/5 rounded-2xl px-4 py-3 border border-white/10 flex-wrap'):
                        for idx, (ic, lbl) in enumerate(step_labels_list):
                            with ui.column().classes('items-center gap-1 w-28'):
                                dot = ui.row().classes(f'w-10 h-10 rounded-full items-center justify-center {"bg-blue-500 ring-2 ring-white/30" if idx == 0 else "bg-white/10"} transition-all duration-500')
                                with dot:
                                    ui.icon(ic, color='white').classes('text-xl')
                                step_dots.append(dot)
                                ui.label(lbl).classes('text-[10px] font-bold text-slate-400 text-center leading-tight')
                            if idx < 2:
                                ui.icon('chevron_right', color='gray').classes('text-slate-600 self-center')

            def update_stepper(active_step):
                done_colors = ['bg-blue-300/40', 'bg-green-300/40', 'bg-indigo-300/40']
                active_colors = ['bg-blue-500', 'bg-green-500', 'bg-indigo-500']
                for i, dot in enumerate(step_dots):
                    all_bg = ' '.join(done_colors) + ' ' + ' '.join(active_colors) + ' bg-white/10 opacity-70 ring-2 ring-white/30'
                    dot.classes(remove=all_bg)
                    if i < active_step - 1:
                        dot.classes(add=done_colors[i] + ' opacity-70')
                    elif i == active_step - 1:
                        dot.classes(add=active_colors[i] + ' ring-2 ring-white/30')
                    else:
                        dot.classes(add='bg-white/10')

            creator_step1 = ui.column().classes('w-full px-8 pb-10')
            creator_step2 = ui.column().classes('w-full px-8 pb-10')
            creator_step3 = ui.column().classes('w-full px-8 pb-10')

            def show_creator_step(n):
                creator_state['step'] = n
                creator_step1.set_visibility(n == 1)
                creator_step2.set_visibility(n == 2)
                creator_step3.set_visibility(n == 3)
                update_stepper(n)
            show_creator_step(1)

            # ════════════ STEP 1 ══════════════════════════════════════════════
            with creator_step1:
                with ui.row().classes('w-full gap-6 items-stretch'):
                    # Upload Card
                    with ui.card().classes('flex-1 min-w-[300px] p-8 bg-white/5 border border-white/10 rounded-3xl backdrop-blur-sm'):
                        with ui.row().classes('items-center gap-3 mb-2'):
                            ui.element('div').classes('w-1 h-8 bg-blue-400 rounded-full')
                            ui.label('Bước 1: AI Phân Tích Tài Liệu').classes('text-2xl font-bold text-white')
                        ui.label('Tải lên tài liệu (.txt, .pdf, .docx) — AI sẽ tự động trích xuất Chương → Bài → Câu hỏi, suy luận quan hệ logic và lưu thẳng vào thư viện.').classes('text-slate-400 text-sm mb-6 leading-relaxed')

                        s1_status_row = ui.row().classes('w-full items-center gap-3 mb-3')
                        s1_status_row.set_visibility(False)
                        with s1_status_row:
                            s1_icon = ui.icon('hourglass_empty', color='blue-300').classes('text-2xl')
                            s1_label = ui.label('').classes('text-blue-200 font-bold text-sm')

                        s1_progress = ui.linear_progress(value=0).props('color=blue-4 track-color=white/10 stripe size=8px rounded').classes('w-full mb-6')
                        s1_progress.set_visibility(False)

                        async def handle_upload_txt(e):
                            # Robust filename extraction
                            if isinstance(e, dict):
                                filename = e.get('name') or e.get('filename') or getattr(e.get('file'), 'filename', None) or getattr(e.get('file'), 'name', None) or 'tài liệu.pdf'
                            else:
                                filename = getattr(e, 'name', None) or getattr(e, 'filename', None) or getattr(getattr(e, 'file', None), 'filename', None) or getattr(getattr(e, 'file', None), 'name', None) or 'tài liệu.pdf'
                            
                            s1_status_row.set_visibility(True)
                            s1_progress.set_visibility(True)
                            s1_label.text = f'Đọc {filename}...'
                            s1_progress.value = 0.05

                            try:
                                if isinstance(e, dict):
                                    content_bytes = e.get('content') or await e.get('file').read()
                                else:
                                    if hasattr(e, 'content'): content_bytes = e.content.read()
                                    elif hasattr(e, 'file'): content_bytes = await e.file.read()
                                    else: raise ValueError("Không tìm thấy nội dung file trong sự kiện upload.")
                            except Exception as read_ex:
                                s1_icon.name = 'error'; s1_label.text = f'❌ Lỗi đọc file: {str(read_ex)}'; return

                            async def process_document_bg(course_name, file_bytes):
                                from document_parser import parse_document
                                from step1_build_tree import build_tree_for_user
                                from step2_build_edges import build_edges_for_user

                                try:
                                    try:
                                        parsed_content = await run.io_bound(parse_document, course_name, file_bytes)
                                    except ValueError as ve:
                                        s1_icon.name = 'error'; s1_icon.props('color=red-400')
                                        s1_label.text = f'❌ {str(ve)}'
                                        return

                                    s1_label.text = '🧠 AI trích xuất Chương, Bài, Câu hỏi...'
                                    s1_progress.value = 0.2
                                    path, data = await run.io_bound(build_tree_for_user, user.username, parsed_content)
                                    if not data:
                                        s1_icon.name = 'error'; s1_label.text = 'AI không trả về kết quả.'; return

                                    s1_label.text = '🔗 Suy luận quan hệ tiên quyết (Prerequisite Edges)...'
                                    s1_progress.value = 0.5
                                    await run.io_bound(build_edges_for_user, user.username)
                                    s1_progress.value = 0.7

                                    s1_label.text = '📚 Lưu vào Thư viện...'
                                    import uuid as _uuid
                                    out_dir = f'user_data/{user.username}/trees'
                                    os.makedirs(out_dir, exist_ok=True)
                                    uid = _uuid.uuid4().hex[:8]
                                    out_path = f'{out_dir}/{uid}.json'
                                    with open(path, 'r', encoding='utf-8') as _f:
                                        final_tree = json.load(_f)
                                    with open(out_path, 'w', encoding='utf-8') as _f:
                                        json.dump(final_tree, _f, ensure_ascii=False, indent=2)

                                    course_title = final_tree.get('course_name', f'Môn học - {course_name}')
                                    n_macro = len(final_tree.get('macro_nodes', []))
                                    n_micro = len(final_tree.get('micro_nodes', []))
                                    n_assess = len(final_tree.get('assess_nodes', []))

                                    subj_file = f'user_data/{user.username}/subjects.json'
                                    subj_data = {'subjects': []}
                                    if os.path.exists(subj_file):
                                        with open(subj_file, 'r', encoding='utf-8') as sf: subj_data = json.load(sf)
                                    
                                    # Update existing or add new
                                    found_idx = next((i for i, s in enumerate(subj_data['subjects']) if s['title'] == course_title), None)
                                    subj_entry = {'id': uid, 'title': course_title, 'filename': out_path, 'total_nodes': n_macro + n_micro + n_assess}
                                    if found_idx is not None:
                                        subj_data['subjects'][found_idx] = subj_entry
                                    else:
                                        subj_data['subjects'].append(subj_entry)
                                        
                                    with open(subj_file, 'w', encoding='utf-8') as sf: json.dump(subj_data, sf, ensure_ascii=False, indent=2)

                                    creator_state.update({'json_path': out_path, 'tree_data': final_tree, 'course_title': course_title})
                                    # Guard against client being deleted during long async operations
                                    try:
                                        render_library()
                                        s1_progress.value = 1.0
                                        s1_icon.name = 'check_circle'
                                        s1_icon.props('color=green-400')
                                        s1_label.text = f'✅ {n_macro} Chương · {n_micro} Bài · {n_assess} Kiểm tra'
                                        _prepare_step2(course_title, n_macro, n_micro, n_assess, out_path)
                                        import asyncio
                                        await asyncio.sleep(1.5)
                                        show_creator_step(2)
                                    except Exception as ui_ex:
                                        print(f'⚠️ UI update skipped (client may have disconnected): {ui_ex}')
                                except Exception as ex:
                                    try:
                                        s1_icon.name = 'error'; s1_icon.props('color=red-400')
                                        s1_label.text = f'Lỗi: {str(ex)}'
                                    except Exception:
                                        print(f'❌ Tree build error (client disconnected): {ex}')

                            async def run_bg():
                                await process_document_bg(filename, content_bytes)
                            from nicegui import background_tasks
                            background_tasks.create(run_bg())

                        ui.upload(on_upload=handle_upload_txt, auto_upload=True, multiple=False, label='Kéo thả hoặc Click chọn file (.txt, .pdf, .docx)').props('bordered accept=".txt,.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" flat color=blue').classes('w-full bg-blue-500/10 rounded-2xl border-2 border-dashed border-blue-400/40 hover:border-blue-400 transition-all')

                        ui.separator().classes('my-4 bg-white/10')
                        ui.label('Hoặc import JSON có sẵn:').classes('text-slate-500 text-xs mb-2')

                        async def handle_json_import(e):
                            if hasattr(e, 'content'): cb = e.content.read()
                            elif hasattr(e, 'file'): cb = await e.file.read()
                            else: return
                            try:
                                ft = json.loads(cb.decode('utf-8'))
                                import uuid as _uuid2
                                uid2 = _uuid2.uuid4().hex[:8]
                                od = f'user_data/{user.username}/trees'; os.makedirs(od, exist_ok=True)
                                op = f'{od}/{uid2}.json'
                                with open(op, 'w', encoding='utf-8') as f2: json.dump(ft, f2, ensure_ascii=False, indent=2)
                                ct = ft.get('course_name', f'JSON ({uid2})')
                                nm, nmi, na = len(ft.get('macro_nodes', [])), len(ft.get('micro_nodes', [])), len(ft.get('assess_nodes', []))
                                sf2 = f'user_data/{user.username}/subjects.json'
                                sd2 = {'subjects': []}
                                if os.path.exists(sf2):
                                    with open(sf2) as f3: sd2 = json.load(f3)
                                
                                # Update existing or add new
                                found_idx2 = next((i for i, s in enumerate(sd2['subjects']) if s['title'] == ct), None)
                                subj_entry2 = {'id': uid2, 'title': ct, 'filename': op, 'total_nodes': nm+nmi+na}
                                if found_idx2 is not None:
                                    sd2['subjects'][found_idx2] = subj_entry2
                                else:
                                    sd2['subjects'].append(subj_entry2)
                                    
                                with open(sf2, 'w', encoding='utf-8') as f4: json.dump(sd2, f4, ensure_ascii=False, indent=2)
                                creator_state.update({'json_path': op, 'tree_data': ft, 'course_title': ct})
                                render_library()
                                _prepare_step2(ct, nm, nmi, na, op)
                                ui.notify(f'Đã import: {ct}', type='positive')
                                import asyncio
                                await asyncio.sleep(0.3)
                                show_creator_step(2)
                            except Exception as ex: ui.notify(f'Lỗi: {ex}', type='negative')

                        ui.upload(on_upload=handle_json_import, auto_upload=True, multiple=False, label='Import JSON').props('bordered accept=".json" flat color=gray dense').classes('w-full')

                    # Info Card
                    with ui.card().classes('w-72 flex-shrink-0 p-6 bg-white/3 border border-white/8 rounded-3xl'):
                        ui.label('Supported Formats').classes('text-white font-bold mb-4 text-sm tracking-wide')
                        tips = [
                            ('📄', '.TXT — Plain Text (UTF-8)', 'Bài giảng, slide text, ghi chú'),
                            ('📕', '.PDF — Portable Document', 'Sách, giáo trình, đề cương (có text layer)'),
                            ('📘', '.DOCX — Microsoft Word', 'Báo cáo, luận văn, tài liệu Word'),
                            ('✅', 'Có cấu trúc Chương/Bài', '"Chương 1:", "Bài 1.1:" giúp AI chuẩn xác hơn'),
                            ('⚡', 'Tối ưu < 15,000 ký tự', 'Upload ~1 chương/lần để đảm bảo chất lượng'),
                        ]
                        for em, t, d in tips:
                            with ui.row().classes('items-start gap-2 mb-3'):
                                ui.label(em).classes('text-lg flex-shrink-0')
                                with ui.column().classes('gap-0'):
                                    ui.label(t).classes('text-white text-xs font-bold leading-tight')
                                    ui.label(d).classes('text-slate-500 text-[10px] leading-tight mt-0.5')

            # ════════════ STEP 2 ══════════════════════════════════════════════
            with creator_step2:
                s2_title = ui.label('').classes('text-3xl font-black text-white mb-2')
                s2_stats = ui.row().classes('gap-4 mb-5 flex-wrap')
                s2_status = ui.label('').classes('text-slate-400 text-sm italic mb-3')
                s2_graph = ui.column().classes('w-full rounded-2xl overflow-hidden bg-black/20 border border-white/10 min-h-[520px]')
                s2_actions = ui.row().classes('gap-4 mt-5')
                s2_actions.set_visibility(False)

                def _prepare_step2(course_title, n_macro, n_micro, n_assess, json_path):
                    s2_title.text = course_title
                    s2_stats.clear()
                    with s2_stats:
                        for icon_n, val, lbl, col in [
                            ('auto_awesome', str(n_macro), 'Chương', 'blue-300'),
                            ('library_books', str(n_micro), 'Bài học', 'green-300'),
                            ('quiz', str(n_assess), 'Kiểm tra', 'yellow-300'),
                        ]:
                            with ui.card().classes('px-5 py-3 bg-white/5 border border-white/10 rounded-2xl'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon(icon_n, color=col.replace('-', '_')).classes('text-2xl')
                                    with ui.column().classes('gap-0'):
                                        ui.label(val).classes(f'text-2xl font-black text-{col}')
                                        ui.label(lbl).classes('text-slate-500 text-xs')
                    s2_status.text = '⏳ Đang biên dịch đồ họa 3D...'
                    s2_actions.set_visibility(False)

                    async def _do_render():
                        try:
                            from resource_sync import sync_resources_to_tree
                            await run.io_bound(sync_resources_to_tree, json_path)
                            from step2_5_visualize_tree import visualize_knowledge_tree
                            await run.io_bound(visualize_knowledge_tree, user.username, json_path)
                            s2_status.text = '✅ Đồ họa 3D đã sẵn sàng — kéo để khám phá!'
                            s2_graph.clear()
                            with s2_graph:
                                import time as _t
                                v = int(_t.time())
                                ui.element('iframe').props(f'src="/user_data/{user.username}/current_visual_tree.html?v={v}" width="100%" height="520"').classes('w-full border-none')
                            s2_actions.set_visibility(True)
                            s2_actions.clear()
                            with s2_actions:
                                ui.button('Tiếp: Nhúng Tài Nguyên →', icon='arrow_forward',
                                          on_click=lambda: [_build_step3(json_path, course_title), show_creator_step(3)]).classes('bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-bold px-8 shadow-xl hover:scale-105 transition-all').props('rounded')

                                def _open_editor():
                                    from tree_editor_ui import open_tree_editor
                                    def _on_editor_save(updated_tree):
                                        # Refresh 3D iframe
                                        s2_graph.clear()
                                        with s2_graph:
                                            import time as _t2
                                            v2 = int(_t2.time())
                                            ui.element('iframe').props(f'src="/user_data/{user.username}/current_visual_tree.html?v={v2}" width="100%" height="520"').classes('w-full border-none')
                                        # Update stats
                                        ct = updated_tree.get('course_name', course_title)
                                        nm = len(updated_tree.get('macro_nodes', []))
                                        nmi = len(updated_tree.get('micro_nodes', []))
                                        na = len(updated_tree.get('assess_nodes', []))
                                        s2_title.text = ct
                                        s2_status.text = f'✅ Đã cập nhật: {nm} Chương · {nmi} Bài · {na} Kiểm tra'
                                        ui.notify('🎉 Cây tri thức đã được cập nhật!', type='positive')
                                    open_tree_editor(json_path, user.username, on_save_callback=_on_editor_save)

                                ui.button('✏️ Chỉnh sửa cây', icon='edit', on_click=_open_editor).classes('bg-gradient-to-r from-amber-500 to-orange-600 text-white font-bold px-6 shadow-xl hover:scale-105 transition-all').props('rounded')
                                ui.button('Tải JSON', icon='download', on_click=lambda: ui.download(json_path, f'{course_title}.json')).props('flat color=white rounded')
                        except Exception as ex:
                            s2_status.text = f'❌ Lỗi render 3D: {ex}'

                    with creator_step2:
                        ui.timer(0.5, _do_render, once=True)

            # ════════════ STEP 3 ══════════════════════════════════════════════
            with creator_step3:
                s3_content = ui.column().classes('w-full')
                expanded_chaps_dict = {}
                sel3 = {'id': None}

                def _build_step3(json_path, course_title):
                    s3_content.clear()
                    expanded_chaps_dict.clear() # Clear state for new course
                    sel3['id'] = None
                    
                    with s3_content:
                        with ui.row().classes('w-full items-center justify-between mb-6 flex-wrap gap-4'):
                            with ui.column().classes('gap-1'):
                                ui.label(f'Nhúng Tài Nguyên').classes('text-3xl font-black text-white')
                                ui.label(course_title).classes('text-indigo-300 font-bold text-lg')
                                ui.label('Gắn video YouTube, PDF, tài liệu và kịch bản AI vào từng bài học.').classes('text-slate-400 text-sm')
                            with ui.row().classes('gap-3'):
                                ui.button('◀ Xem lại 3D', icon='view_in_ar', on_click=lambda: show_creator_step(2)).props('flat color=white rounded')
                                ui.button('Vào Graph Studio 🚀', icon='architecture', on_click=lambda: setattr(main_tabs, 'value', tab_studio)).classes('bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold').props('rounded')

                        try:
                            from resource_sync import sync_resources_to_tree
                            # Sync resources to ensure they are correct (removes old auto-sync links if course type changed)
                            sync_resources_to_tree(json_path)
                            
                            from resource_manager import get_hierarchical_nodes, get_node_resources, add_resource, get_all_nodes_summary
                            
                            with ui.splitter(value=28).classes('w-full rounded-2xl overflow-hidden border border-white/10').style('height:620px') as spl3:
                                with spl3.before:
                                    with ui.column().classes('w-full h-full bg-white/3 p-3'):
                                        ui.label('Danh sách Bài học').classes('text-white font-bold text-sm mb-2')
                                        ns3 = ui.input(placeholder='Tìm bài học...').props('dense outlined dark clearable').classes('w-full mb-2')
                                        nl3 = ui.scroll_area().classes('w-full flex-1')

                                with spl3.after:
                                    with ui.column().classes('w-full h-full p-4 bg-white/3'):
                                        det3 = ui.scroll_area().classes('w-full h-full')
                                        with det3:
                                            with ui.column().classes('items-center justify-center h-full'):
                                                ui.icon('touch_app', color='gray').classes('text-5xl mb-3')
                                                ui.label('Chọn bài học để thêm tài nguyên').classes('text-slate-400 text-sm')

                            def _render_nl3():
                                nl3.clear()
                                try: tree = get_hierarchical_nodes(json_path)
                                except: return
                                q = (ns3.value or '').lower()
                                with nl3:
                                    with ui.column().classes('w-full gap-1 p-1'):
                                        for chap_idx, chap in enumerate(tree):
                                            chap_match = q in chap['label'].lower()
                                            children = chap.get('children', [])
                                            child_match = any(q in c['label'].lower() for c in children)
                                            if q and not chap_match and not child_match: continue
                                            
                                            # Persistent expansion state
                                            chap_id = chap.get('id', str(chap_idx))
                                            if chap_id not in expanded_chaps_dict:
                                                expanded_chaps_dict[chap_id] = False
                                            
                                            is_selected_parent = any(sel3['id'] == c['id'] for c in children) if sel3['id'] else False
                                            if is_selected_parent:
                                                expanded_chaps_dict[chap_id] = True
                                            
                                            exp = ui.expansion(chap['label'], icon='book').classes('w-full rounded-lg overflow-hidden border border-white/10').props('header-class="text-white text-xs font-bold bg-white/5 px-2 py-1"')
                                            exp.bind_value(expanded_chaps_dict, chap_id)
                                            if q != '' and (chap_match or child_match):
                                                exp.value = True
                                            
                                            with exp:
                                                for les in children:
                                                    if q and not q in les['label'].lower() and not chap_match: continue
                                                    is_sel = sel3['id'] == les['id']
                                                    cls = 'bg-indigo-500/30 border-indigo-400' if is_sel else 'hover:bg-white/5 border-transparent'
                                                    with ui.card().classes(f'w-full p-2 mb-1 cursor-pointer border rounded-lg text-xs text-slate-300 transition-all {cls}').on('click', lambda lid=les['id']: [sel3.__setitem__('id', lid), _render_det3(lid), ui.timer(0, _render_nl3, once=True)]):
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.icon('play_lesson', size='xs', color='indigo' if is_sel else 'gray')
                                                            ui.label(les['label']).classes('truncate flex-1')
                                                            rc = les.get('resource_count', 0)
                                                            if rc: ui.badge(str(rc), color='indigo').props('rounded dense')

                            def _render_det3(node_id):
                                det3.clear()
                                with det3:
                                    with ui.column().classes('w-full gap-4 p-2'):
                                        try:
                                            resources = get_node_resources(json_path, node_id)
                                            all_nodes = get_all_nodes_summary(json_path)
                                            node_info = next((n for n in all_nodes if n['id'] == node_id), None)
                                            node_detail = get_node_detail(json_path, node_id)
                                        except Exception as ex:
                                            ui.label(f'Lỗi: {ex}').classes('text-red-400'); return

                                        ui.label(node_info['label'] if node_info else node_id).classes('text-white font-bold text-lg')
                                        
                                        # ===== DESCRIPTION SECTION (Dark Theme) =====
                                        s3_desc_md = node_detail.get('description_md', '') if node_detail else ''
                                        s3_content_fb = node_detail.get('content', '') if node_detail else ''
                                        s3_desc_state = {'editing': False}
                                        
                                        with ui.row().classes('w-full items-center justify-between'):
                                            ui.label('📝 Mô tả chi tiết').classes('text-emerald-300 font-bold text-xs uppercase tracking-wide')
                                            with ui.row().classes('gap-1'):
                                                s3_edit_btn = ui.button(icon='edit', on_click=lambda: _s3_toggle_edit(node_id)).props('flat round size=sm color=blue').tooltip('Chỉnh sửa')
                                                s3_ai_btn = ui.button('AI ✨', icon='auto_awesome', on_click=lambda nid=node_id: _s3_ai_gen(nid)).props('flat dense size=sm color=purple').classes('text-xs font-bold').tooltip('AI sinh mô tả')
                                        
                                        with ui.card().classes('w-full p-0 bg-white/5 border border-white/10 rounded-xl overflow-hidden'):
                                            # Preview
                                            s3_preview = ui.column().classes('w-full p-4')
                                            with s3_preview:
                                                if s3_desc_md:
                                                    ui.markdown(s3_desc_md).classes('w-full prose prose-sm prose-invert max-w-none text-slate-300')
                                                    ui.run_javascript('setTimeout(() => { if (window.MathJax) MathJax.typesetPromise(); }, 300);')
                                                elif s3_content_fb:
                                                    ui.label(s3_content_fb).classes('text-sm text-slate-400 leading-relaxed')
                                                    ui.html('<div class="mt-2 text-center"><span class="text-xs text-emerald-400/70 italic">💡 Nhấn "AI ✨" để tạo mô tả chi tiết</span></div>')
                                                else:
                                                    with ui.column().classes('items-center py-4'):
                                                        ui.icon('description', color='gray').classes('text-2xl mb-1 opacity-30')
                                                        ui.label('Nhấn "AI ✨" để tạo mô tả hoặc ✏️ để viết').classes('text-slate-500 text-xs')
                                            
                                            # Edit area
                                            s3_edit_area = ui.column().classes('w-full p-4')
                                            s3_edit_area.set_visibility(False)
                                            with s3_edit_area:
                                                ui.label('Markdown (hỗ trợ LaTeX: $...$)').classes('text-[10px] text-slate-500 mb-1')
                                                s3_textarea = ui.textarea(
                                                    value=s3_desc_md or s3_content_fb or '',
                                                    placeholder='## Mục tiêu\n- ...\n\n## Công thức\n$$E = mc^2$$'
                                                ).props('outlined dark autogrow').classes('w-full font-mono text-sm').style('min-height: 160px')
                                                with ui.row().classes('w-full justify-end gap-2 mt-2'):
                                                    ui.button('Hủy', on_click=lambda: _s3_toggle_edit(node_id)).props('flat size=sm color=grey')
                                                    ui.button('💾 Lưu', on_click=lambda nid=node_id: _s3_save(nid)).props('unelevated size=sm color=green rounded').classes('font-bold')
                                            
                                            # Spinner
                                            s3_spinner = ui.row().classes('w-full p-3 items-center gap-2 bg-purple-500/10')
                                            s3_spinner.set_visibility(False)
                                            with s3_spinner:
                                                ui.spinner('dots', size='md', color='purple')
                                                s3_spin_lbl = ui.label('AI đang phân tích...').classes('text-purple-300 text-xs font-bold italic')
                                        
                                        def _s3_toggle_edit(nid):
                                            is_e = not s3_desc_state['editing']
                                            s3_desc_state['editing'] = is_e
                                            s3_preview.set_visibility(not is_e)
                                            s3_edit_area.set_visibility(is_e)
                                            if is_e:
                                                s3_textarea.value = s3_desc_md or s3_content_fb or ''
                                        
                                        def _s3_save(nid):
                                            new_md = (s3_textarea.value or '').strip()
                                            try:
                                                if update_node_description(json_path, nid, new_md):
                                                    ui.notify('✅ Đã lưu mô tả!', type='positive')
                                                    _render_det3(nid)
                                                else:
                                                    ui.notify('⚠️ Node không tìm thấy', type='warning')
                                            except Exception as ex:
                                                ui.notify(f'❌ Lỗi: {ex}', type='negative')
                                        
                                        async def _s3_ai_gen(nid):
                                            s3_spinner.set_visibility(True)
                                            s3_preview.set_visibility(False)
                                            s3_edit_area.set_visibility(False)
                                            try:
                                                from ai_description_generator import generate_node_description
                                                result = await run.io_bound(generate_node_description, json_path, nid)
                                                s3_spinner.set_visibility(False)
                                                s3_desc_state['editing'] = True
                                                s3_textarea.value = result
                                                s3_edit_area.set_visibility(True)
                                                ui.notify('✨ AI đã tạo mô tả! Xem lại và nhấn Lưu.', type='info')
                                            except Exception as ex:
                                                s3_spinner.set_visibility(False)
                                                s3_preview.set_visibility(True)
                                                ui.notify(f'❌ Lỗi AI: {ex}', type='negative')
                                        
                                        ui.separator().classes('bg-white/10 my-1')

                                        with ui.card().classes('w-full p-5 bg-white/5 border border-white/10 rounded-2xl'):
                                            ui.label('➕ Thêm tài nguyên mới').classes('text-white font-bold text-sm mb-3')
                                            new_url = ui.input('URL (YouTube, Drive, PDF, GitHub...)').props('outlined dark dense').classes('w-full mb-2')
                                            new_title = ui.input('Tiêu đề (tùy chọn)').props('outlined dark dense').classes('w-full mb-2')
                                            new_type = ui.select({'youtube': '📺 YouTube Video', 'pdf': '📄 PDF / Tài liệu', 'doc': '📝 Ghi chú / Slides', 'script': '🎙️ Kịch bản AI', 'lab': '🔬 Lab / Colab'}, value='youtube', label='Loại tài nguyên').props('outlined dark dense').classes('w-full mb-3')
                                            def _do_add_res():
                                                if not new_url.value.strip(): ui.notify('Nhập URL trước!', type='warning'); return
                                                try:
                                                    add_resource(json_path, node_id, new_url.value.strip(), new_title.value or new_url.value.strip()[:60], new_type.value)
                                                    new_url.value = ''; new_title.value = ''
                                                    _render_det3(node_id); ui.timer(0, _render_nl3, once=True)
                                                    ui.notify('✅ Đã thêm tài nguyên!', type='positive')
                                                except Exception as ex: ui.notify(f'Lỗi: {ex}', type='negative')
                                            ui.button('Thêm', icon='add', on_click=_do_add_res).classes('bg-indigo-500 text-white font-bold').props('rounded')

                                        if resources:
                                            with ui.column().classes('w-full gap-2 mt-2'):
                                                ui.label(f'{len(resources)} tài nguyên').classes('text-slate-400 text-xs font-bold')
                                                type_icons = {'youtube': '📺', 'pdf': '📄', 'doc': '📝', 'script': '🎙️', 'lab': '🔬'}
                                                for res in resources:
                                                    with ui.card().classes('w-full p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all'):
                                                        with ui.row().classes('items-center gap-3'):
                                                            ui.label(type_icons.get(res.get('type', ''), '📎')).classes('text-xl flex-shrink-0')
                                                            with ui.column().classes('flex-1 min-w-0 gap-0'):
                                                                ui.label(res.get('title', 'Tài nguyên')).classes('text-white text-sm font-semibold truncate')
                                                                ui.label(res.get('url', '')[:55]).classes('text-indigo-300 text-[10px] truncate')
                                                            ui.button(icon='open_in_new', on_click=lambda u=res.get('url',''): ui.run_javascript(f'window.open("{u}","_blank")')).props('flat round size=sm color=indigo').tooltip('Mở')
                                        else:
                                            with ui.column().classes('items-center py-8'):
                                                ui.icon('add_circle_outline', color='gray').classes('text-4xl mb-2')
                                                ui.label('Chưa có tài nguyên. Thêm URL video/PDF bên trên.').classes('text-slate-500 text-xs text-center')

                            ns3.on('update:model-value', lambda: _render_nl3())
                            _render_nl3()
                        except ImportError as ie:
                            ui.label(f'Resource Manager module chưa khả dụng: {ie}').classes('text-red-400')

                        with ui.card().classes('w-full mt-6 p-6 bg-gradient-to-r from-green-500/20 to-emerald-500/10 border border-green-400/30 rounded-2xl'):
                            with ui.row().classes('w-full items-center justify-between flex-wrap gap-4'):
                                with ui.column().classes('gap-1'):
                                    ui.label('🎉 Cây Tri Thức đã sẵn sàng khai thác!').classes('text-white font-black text-xl')
                                    ui.label('Vũ trụ tri thức đã được biên dịch đầy đủ. Hãy vào Graph Studio để bắt đầu hành trình học tập.').classes('text-green-200 text-sm')
                                with ui.row().classes('gap-3'):
                                    ui.button('🚀 Vào Graph Studio', icon='architecture', on_click=lambda: setattr(main_tabs, 'value', tab_studio)).classes('bg-gradient-to-r from-green-500 to-emerald-600 text-white font-black px-6 shadow-xl hover:scale-105 transition-all').props('rounded')
                                    ui.button('+ Tạo cây mới', icon='add', on_click=lambda: show_creator_step(1)).props('flat color=white rounded')


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
                                             with ui.row().classes('items-center gap-1'):
                                                 ui.button(icon='edit', on_click=lambda: toggle_problem_edit_mode()).props('flat round size=sm color=blue').tooltip('Sửa/Xem đề bài')
                                                 ui.button(icon='play_arrow', on_click=lambda: getattr(ui, 'timer')(0.1, tutor_start_exercise, once=True)).props('flat round size=md color=blue').tooltip('Bắt đầu làm bài')
                                                 ui.button(icon='expand_less', on_click=toggle_problem_panel).props('flat round size=sm color=gray')
                                         
                                         def toggle_problem_edit_mode():
                                             is_editing = 'hidden' not in tutor_problem.classes
                                             if is_editing:
                                                 tutor_problem.classes('hidden')
                                                 tutor_problem_display.classes(remove='hidden')
                                                 tutor_problem_display.content = tutor_problem.value or "Chưa có nội dung đề bài."
                                                 ui.run_javascript('setTimeout(() => { if (window.MathJax) MathJax.typesetPromise(); }, 200);')
                                             else:
                                                 tutor_problem_display.classes('hidden')
                                                 tutor_problem.classes(remove='hidden')

                                         with ui.scroll_area().classes('w-full flex-grow px-4 pt-1 pb-4'):
                                             tutor_problem = ui.textarea(placeholder='Nhập nội dung đề bài vào đây...').classes('w-full text-base').props('borderless autogrow autofocus')
                                             tutor_problem_display = ui.markdown('').classes('w-full text-base hidden')
                         
                         with left_splitter.separator:
                             with ui.row().classes('w-full h-full items-center justify-center bg-gray-200/50 transition hover:bg-blue-200 cursor-row-resize'):
                                 ui.icon('drag_handle', color='gray').classes('text-lg')

                         with left_splitter.after:
                             with ui.column().classes('flex-grow h-full bg-gray-50 flex flex-col w-full no-wrap relative'):
                                 with ui.row().classes('w-full p-4 items-center border-b border-gray-200 bg-white shadow-sm z-10'):
                                     ui.icon('code', color='green-600').classes('text-2xl')
                                     ui.label('Không gian làm bài').classes('font-bold text-gray-800 text-lg')
                                 with ui.scroll_area().classes('w-full flex-grow px-4 pt-1 pb-4 bg-white shadow-inner'):
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

                         # === PENDING EXERCISE FROM BLOOM HUB ===
                         def _check_pending_exercise():
                             """Auto-fill problem from Bloom Hub exercise."""
                             pe = app.storage.user.get('pending_exercise')
                             if not pe:
                                 return
                             exercise = pe.get('exercise', {})
                             phase = pe.get('phase', 'guided')
                             bloom_level = pe.get('bloom_level', 2)
                             bloom_vi = pe.get('bloom_vi', '')
                             bloom_icon = pe.get('bloom_icon', '')
                             node_title_ex = pe.get('node_title', '')
                             course_name = pe.get('course_name', '')

                             # Build formatted problem text
                             title = exercise.get('title', 'Bài tập')
                             problem = exercise.get('problem', '')
                             hints = exercise.get('hints', [])

                             # Format: include metadata header + problem + hints
                             header = f"[{bloom_icon} L{bloom_level} {bloom_vi}] {course_name} — {node_title_ex}"
                             hint_text = ''
                             if hints and phase == 'guided':
                                 hint_text = '\n\n💡 GỢI Ý:\n' + '\n'.join(f'{i+1}. {h}' for i, h in enumerate(hints))

                             full_problem = f"{header}\n\n📋 {title}\n\n{problem}{hint_text}"
                             tutor_problem.value = full_problem
                             tutor_problem_display.content = full_problem
                             tutor_problem.classes('hidden')
                             tutor_problem_display.classes(remove='hidden')
                             ui.run_javascript('setTimeout(() => { if (window.MathJax) MathJax.typesetPromise(); }, 300);')

                             # Show phase notification
                             if phase == 'guided':
                                 ui.notify(f'📝 Bài tập hướng dẫn L{bloom_level} đã sẵn sàng! Gia sư AI sẽ hỗ trợ bạn.', type='positive', timeout=5000)
                             else:
                                 ui.notify(f'🎯 Bài tập đánh giá L{bloom_level} — Hãy tự làm bài!', type='warning', timeout=5000)

                             # Clear pending to prevent re-triggering
                             del app.storage.user['pending_exercise']

                             # Auto-trigger start exercise after a short delay
                             ui.timer(0.5, tutor_start_exercise, once=True)

                         # Check for pending exercises continuously
                         def _safe_check_pending_exercise():
                             try:
                                 _check_pending_exercise()
                             except RuntimeError:
                                 pass
                         ui.timer(0.5, _safe_check_pending_exercise)

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

ui.run(storage_secret='pkt_secret_key', title='PKT Bio-Tutor', port=8081, host='0.0.0.0', reload=False)

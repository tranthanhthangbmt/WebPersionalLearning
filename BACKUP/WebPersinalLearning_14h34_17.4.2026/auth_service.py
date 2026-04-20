# auth_service.py - Authentication & Authorization Service
from nicegui import ui, app
from database import (
    create_db_and_tables, create_user, get_user_by_username, 
    get_user_by_email, authenticate_user, get_user_progress
)
import re


def is_valid_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_logged_in() -> bool:
    """Check if current user is logged in"""
    return app.storage.user.get('authenticated', False)


def get_current_user_id() -> int:
    """Get current logged-in user ID"""
    return app.storage.user.get('id', None)


def get_current_username() -> str:
    """Get current logged-in username"""
    return app.storage.user.get('username', '')


def logout():
    """Clear user session and redirect to login"""
    app.storage.user.clear()
    ui.navigate.to('/login')


# ============================================================
#  LOGIN PAGE
# ============================================================
def create_login_page():
    """Build the Login page UI"""

    # Inject Google Font
    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">')

    # --- FULL PAGE BACKGROUND ---
    with ui.column().classes('w-full min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 relative overflow-hidden'):
        
        # Animated blobs background
        ui.html('''
            <div style="position:absolute;top:-20%;left:-10%;width:500px;height:500px;background:radial-gradient(circle,rgba(59,130,246,0.15),transparent 70%);border-radius:50%;animation:float1 8s ease-in-out infinite;"></div>
            <div style="position:absolute;bottom:-15%;right:-5%;width:600px;height:600px;background:radial-gradient(circle,rgba(139,92,246,0.12),transparent 70%);border-radius:50%;animation:float2 10s ease-in-out infinite;"></div>
            <div style="position:absolute;top:40%;left:60%;width:300px;height:300px;background:radial-gradient(circle,rgba(6,182,212,0.1),transparent 70%);border-radius:50%;animation:float3 12s ease-in-out infinite;"></div>
            <style>
                @keyframes float1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(30px,-40px)} }
                @keyframes float2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-20px,30px)} }
                @keyframes float3 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-40px,-20px)} }
            </style>
        ''')

        # --- LOGIN CARD ---
        with ui.card().classes('w-[420px] p-8 rounded-3xl shadow-2xl bg-white/[0.03] backdrop-blur-xl border border-white/10 z-10'):
            
            # Logo & Title
            with ui.column().classes('items-center mb-8 gap-2'):
                ui.html('''
                    <div style="width:60px;height:60px;border-radius:16px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);display:flex;align-items:center;justify-content:center;box-shadow:0 8px 32px rgba(59,130,246,0.3);">
                        <span style="font-size:28px;">🌳</span>
                    </div>
                ''')
                ui.label('PKT Bio-Tutor').classes('text-2xl font-extrabold text-white tracking-tight')
                ui.label('Cây Tri Thức Cá Nhân Hóa').classes('text-sm text-blue-300/70 font-medium')

            # Error message container
            error_label = ui.label('').classes('text-red-400 text-sm text-center w-full hidden')

            # Form
            username_input = ui.input(
                label='Tên đăng nhập',
            ).props('rounded outlined dark color=blue-4 label-color=blue-200').classes('w-full mb-2')

            password_input = ui.input(
                label='Mật khẩu',
                password=True, password_toggle_button=True
            ).props('rounded outlined dark color=blue-4 label-color=blue-200').classes('w-full mb-1')

            # Remember me & Forgot password
            with ui.row().classes('w-full justify-between items-center mb-6'):
                ui.checkbox('Ghi nhớ đăng nhập').props('dark color=blue-4 dense').classes('text-blue-200/60 text-xs')
                ui.link('Quên mật khẩu?', '/forgot-password').classes('text-xs text-blue-400 hover:text-blue-300 no-underline hover:underline')

            def do_login():
                username = username_input.value.strip()
                password = password_input.value

                if not username or not password:
                    error_label.text = '⚠️ Vui lòng nhập đầy đủ thông tin'
                    error_label.classes(remove='hidden')
                    return

                user = authenticate_user(username, password)
                if user:
                    # Save to session
                    app.storage.user['authenticated'] = True
                    app.storage.user['id'] = user.id
                    app.storage.user['username'] = user.username
                    app.storage.user['full_name'] = user.full_name
                    app.storage.user['role'] = user.role
                    app.storage.user['is_onboarded'] = user.is_onboarded
                    
                    ui.notify(f'Chào mừng {user.full_name}! 🎉', type='positive')
                    
                    # Redirect based on onboarding status
                    if user.is_onboarded:
                        ui.navigate.to('/app')
                    else:
                        ui.navigate.to('/onboarding')
                else:
                    error_label.text = '❌ Sai tên đăng nhập hoặc mật khẩu'
                    error_label.classes(remove='hidden')

            # Login button
            ui.button(
                'Đăng nhập', on_click=do_login
            ).classes('w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-base shadow-lg shadow-blue-600/25 hover:shadow-blue-600/40 hover:scale-[1.02] transition-all duration-200').props('no-caps')

            # Divider
            with ui.row().classes('w-full items-center gap-3 my-6'):
                ui.element('div').classes('flex-grow h-px bg-white/10')
                ui.label('hoặc').classes('text-xs text-blue-300/50 font-medium')
                ui.element('div').classes('flex-grow h-px bg-white/10')

            # Register link
            with ui.row().classes('w-full justify-center'):
                ui.label('Chưa có tài khoản?').classes('text-sm text-blue-200/50')
                ui.link('Đăng ký ngay', '/register').classes('text-sm text-blue-400 font-bold no-underline hover:text-blue-300 ml-1')

            # Bind Enter key
            password_input.on('keydown.enter', do_login)
            username_input.on('keydown.enter', lambda: password_input.run_method('focus'))


# ============================================================
#  REGISTER PAGE
# ============================================================
def create_register_page():
    """Build the Register page UI"""

    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">')

    with ui.column().classes('w-full min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 relative overflow-hidden'):
        
        # Background blobs
        ui.html('''
            <div style="position:absolute;top:-15%;right:-10%;width:500px;height:500px;background:radial-gradient(circle,rgba(139,92,246,0.15),transparent 70%);border-radius:50%;animation:float1 8s ease-in-out infinite;"></div>
            <div style="position:absolute;bottom:-10%;left:-8%;width:400px;height:400px;background:radial-gradient(circle,rgba(59,130,246,0.12),transparent 70%);border-radius:50%;animation:float2 10s ease-in-out infinite;"></div>
            <style>
                @keyframes float1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(30px,-40px)} }
                @keyframes float2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-20px,30px)} }
            </style>
        ''')

        # --- REGISTER CARD ---
        with ui.card().classes('w-[460px] p-8 rounded-3xl shadow-2xl bg-white/[0.03] backdrop-blur-xl border border-white/10 z-10'):
            
            # Header
            with ui.column().classes('items-center mb-6 gap-2'):
                ui.html('''
                    <div style="width:60px;height:60px;border-radius:16px;background:linear-gradient(135deg,#8b5cf6,#3b82f6);display:flex;align-items:center;justify-content:center;box-shadow:0 8px 32px rgba(139,92,246,0.3);">
                        <span style="font-size:28px;">🚀</span>
                    </div>
                ''')
                ui.label('Tạo tài khoản mới').classes('text-2xl font-extrabold text-white tracking-tight')
                ui.label('Bắt đầu hành trình học tập cá nhân hóa').classes('text-sm text-purple-300/70 font-medium')

            error_label = ui.label('').classes('text-red-400 text-sm text-center w-full hidden')
            success_label = ui.label('').classes('text-green-400 text-sm text-center w-full hidden')

            # Form fields
            fullname_input = ui.input(
                label='Họ và tên'
            ).props('rounded outlined dark color=purple-4 label-color=purple-200').classes('w-full mb-2')
            
            email_input = ui.input(
                label='Email'
            ).props('rounded outlined dark color=purple-4 label-color=purple-200').classes('w-full mb-2')

            username_input = ui.input(
                label='Tên đăng nhập'
            ).props('rounded outlined dark color=purple-4 label-color=purple-200').classes('w-full mb-2')

            password_input = ui.input(
                label='Mật khẩu', 
                password=True, password_toggle_button=True
            ).props('rounded outlined dark color=purple-4 label-color=purple-200').classes('w-full mb-2')

            confirm_input = ui.input(
                label='Xác nhận mật khẩu',
                password=True, password_toggle_button=True
            ).props('rounded outlined dark color=purple-4 label-color=purple-200').classes('w-full mb-2')

            # Role selection
            role_select = ui.select(
                label='Bạn là...',
                options={
                    'student': '🎓 Học sinh / Sinh viên',
                    'teacher': '👨‍🏫 Giáo viên',
                    'parent': '👨‍👩‍👧 Phụ huynh'
                },
                value='student'
            ).props('rounded outlined dark color=purple-4 label-color=purple-200 emit-value map-options').classes('w-full mb-4')

            def do_register():
                fullname = fullname_input.value.strip()
                email = email_input.value.strip()
                username = username_input.value.strip()
                password = password_input.value
                confirm = confirm_input.value
                role = role_select.value

                # Reset messages
                error_label.classes(add='hidden')
                success_label.classes(add='hidden')

                # Validation
                if not all([fullname, email, username, password, confirm]):
                    error_label.text = '⚠️ Vui lòng điền đầy đủ tất cả các trường'
                    error_label.classes(remove='hidden')
                    return

                if not is_valid_email(email):
                    error_label.text = '⚠️ Email không hợp lệ'
                    error_label.classes(remove='hidden')
                    return

                if len(username) < 3:
                    error_label.text = '⚠️ Tên đăng nhập phải có ít nhất 3 ký tự'
                    error_label.classes(remove='hidden')
                    return

                if len(password) < 6:
                    error_label.text = '⚠️ Mật khẩu phải có ít nhất 6 ký tự'
                    error_label.classes(remove='hidden')
                    return

                if password != confirm:
                    error_label.text = '❌ Mật khẩu xác nhận không khớp'
                    error_label.classes(remove='hidden')
                    return

                # Check duplicates
                if get_user_by_username(username):
                    error_label.text = '❌ Tên đăng nhập đã tồn tại'
                    error_label.classes(remove='hidden')
                    return

                if email and get_user_by_email(email):
                    error_label.text = '❌ Email đã được sử dụng'
                    error_label.classes(remove='hidden')
                    return

                # Create user
                try:
                    user = create_user(
                        username=username,
                        password=password,
                        full_name=fullname,
                        email=email,
                        role=role
                    )
                    
                    success_label.text = '✅ Đăng ký thành công! Đang chuyển hướng...'
                    success_label.classes(remove='hidden')
                    
                    # Auto-login
                    app.storage.user['authenticated'] = True
                    app.storage.user['id'] = user.id
                    app.storage.user['username'] = user.username
                    app.storage.user['full_name'] = user.full_name
                    app.storage.user['role'] = user.role
                    app.storage.user['is_onboarded'] = False

                    ui.notify(f'Chào mừng {fullname}! 🎉', type='positive')
                    ui.timer(1.5, lambda: ui.navigate.to('/onboarding'), once=True)
                    
                except Exception as e:
                    error_label.text = f'❌ Lỗi: {str(e)}'
                    error_label.classes(remove='hidden')

            # Register button
            ui.button(
                'Tạo tài khoản', on_click=do_register
            ).classes('w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold text-base shadow-lg shadow-purple-600/25 hover:shadow-purple-600/40 hover:scale-[1.02] transition-all duration-200').props('no-caps')

            # Login link
            with ui.row().classes('w-full justify-center mt-6'):
                ui.label('Đã có tài khoản?').classes('text-sm text-purple-200/50')
                ui.link('Đăng nhập', '/login').classes('text-sm text-purple-400 font-bold no-underline hover:text-purple-300 ml-1')

from nicegui import ui, app, run
import json
import re
from persona_engine import build_omni_tutor_prompt
from gemini_helper import get_chat_model

# Import confetti from gamification if available, otherwise define a simple one
try:
    from gamification.gamification_ui import CONFETTI_JS
except ImportError:
    CONFETTI_JS = "console.log('Confetti not found')"

def build_omni_drawer():
    """
    Xây dựng giao diện Omni-Drawer (Right Drawer) và Floating Action Button (FAB).
    Hàm này phải được gọi bên trong một hàm có @ui.page.
    """
    # MIT Standard Typography & Markdown Overrides
    ui.add_css('''
        .prose-invert { color: #d1d5db !important; }
        .prose-invert strong { color: #f3f4f6 !important; font-weight: 800 !important; }
        .prose-invert h1, .prose-invert h2, .prose-invert h3 { color: #60a5fa !important; margin-top: 0.5em !important; margin-bottom: 0.2em !important; }
        .prose-invert code { background: #374151 !important; color: #fbbf24 !important; padding: 2px 5px !important; rounded: 4px !important; }
        .prose-invert pre { background: #111827 !important; border: 1px solid #374151 !important; border-radius: 8px !important; padding: 12px !important; }
        .prose-invert ul { list-style-type: disc !important; padding-left: 1.5em !important; }
        .prose-invert ol { list-style-type: decimal !important; padding-left: 1.5em !important; }
    ''')

    # 1. Khởi tạo Trạm gác Ngữ cảnh (Context State Manager) nếu chưa có
    if 'omni_context' not in app.storage.user:
        app.storage.user['omni_context'] = {
            'current_tab': 'dashboard',
            'subject_id': None,
            'node_id': None,
            'node_content': None,
            'error_streak': 0,
            'learner_age_group': 'university',  # Cấu hình mặc định
            'subject_type': 'soft_humanities',   # Cấu hình mặc định
            'context_mode': 'new_learning'
        }

    # 2. Khởi tạo Gemini Model (Sử dụng list để pass by reference trong closure)
    model_container = [None]
    chat_session = [None]

    # 3. Khởi tạo Right Drawer (Bị ẩn mặc định)
    right_drawer = ui.right_drawer(value=False, fixed=True, bordered=True).classes(
        'bg-[#0d1117] text-gray-200 w-[450px] z-[100] shadow-[auto_0px_50px_rgba(0,0,0,0.5)] p-0 flex flex-col border-l border-gray-800'
    )
    
    with right_drawer:
        # --- HEADER ---
        with ui.row().classes('w-full p-4 bg-[#161b22] items-center justify-between border-b border-gray-800'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('auto_awesome', size='sm', color='blue-400').classes('animate-pulse')
                ui.label('Gemini Omni-Core').classes('font-extrabold text-lg bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400')
            ui.button(icon='close', on_click=right_drawer.hide).props('flat round dense color="grey-5"').classes('hover:rotate-90 transition-transform')
        
        # Hidden context label to maintain code compatibility
        context_label = ui.label('').classes('hidden')
        
        # --- CHAT AREA ---
        chat_area = ui.scroll_area().classes('flex-grow w-full p-4 flex flex-col gap-3')
        with chat_area:
            chat_container = ui.column().classes('w-full gap-4')
            with chat_container:
                # Welcome message
                with ui.row().classes('w-full justify-start'):
                    with ui.column().classes('bg-[#1f2937] text-gray-200 p-4 rounded-2xl rounded-tl-sm max-w-[90%] border border-gray-700 shadow-xl'):
                        ui.markdown('**Xin chào!** Gem đã sẵn sàng **Đồng hành cùng bạn** (Omnipresent Companion).').classes('text-sm prose-invert')
                        ui.markdown('Tôi sẽ luôn ở đây để thấu hiểu ngữ cảnh và hỗ trợ bạn tốt nhất. Hãy cùng nhau chinh phục kiến thức nhé!').classes('text-xs mt-1 text-gray-400 prose-invert')
        
        # --- INPUT AREA ---
        with ui.row().classes('w-full p-4 bg-[#161b22] items-center border-t border-gray-800 gap-2'):
            chat_input = ui.input(placeholder='Hỏi Gem bất cứ điều gì...').classes('flex-grow').props('rounded outlined dense dark color="blue-500" bg-color="black"')
            send_btn = ui.button(icon='send').props('flat round dense color="blue-400"').classes('hover:scale-110 transition-transform')

    # --- LOGIC XỬ LÝ CHAT ---
    async def handle_send():
        user_msg = chat_input.value.strip()
        if not user_msg:
            return
        
        chat_input.value = ''
        with chat_container:
            # Custom User Message Bubble
            with ui.row().classes('w-full justify-end mb-1'):
                with ui.column().classes('bg-gradient-to-tr from-blue-700 to-indigo-600 text-white p-3 px-4 rounded-2xl rounded-tr-sm max-w-[85%] shadow-md border border-blue-500/30'):
                    ui.markdown(user_msg).classes('text-sm prose-invert leading-snug font-medium')
            
            chat_area.scroll_to(percent=1.0)
            
            # Loading spinner
            spinner_row = ui.row().classes('items-center gap-2')
            with spinner_row:
                ui.spinner('dots', size='sm', color='blue-400')
                ui.label('Omni-Core đang xử lý...').classes('text-xs text-gray-500 italic')
        
        try:
            # Lấy context hiện tại
            context = app.storage.user.get('omni_context', {})
            
            # 1. Build System Prompt (Persona v2.0)
            context = app.storage.user.get('omni_context', {})
            system_prompt = build_omni_tutor_prompt(context)
            
            # 2. Get/Initialize Model with System Instruction
            if model_container[0] is None:
                model_container[0] = get_chat_model(system_instruction=system_prompt)
            else:
                # Update system instruction in the model if it changed significantly
                model_container[0].update_system_instruction(system_prompt)
            
            model = model_container[0]
            if not model:
                ui.notify('Lỗi: Không tìm thấy API Key nào hoạt động.', type='negative')
                return

            if chat_session[0] is None:
                chat_session[0] = model.start_chat(history=[])
                chat_session[0]._last_ctx_tab = context.get('current_tab')
            else:
                # Nếu đổi Tab lớn, reset session để AI không bị "lag" ngữ cảnh cũ
                if getattr(chat_session[0], '_last_ctx_tab', None) != context.get('current_tab'):
                    chat_session[0] = model.start_chat(history=[])
                    chat_session[0]._last_ctx_tab = context.get('current_tab')

            # 3. Prepare Professional Context Injection
            # We inject the current context as a hidden prefix to the user message 
            # to ensure the AI always sees the LATEST state (including slide transcripts).
            live_ctx = f"""
[LIVE CONTEXT]
Tab: {context.get('current_tab')}
Subject: {context.get('subject_title', context.get('subject_id'))}
Node: {context.get('node_id')}
Content Snapshot:
{context.get('node_content', 'No content available')}
[/LIVE CONTEXT]
"""
            full_user_msg = f"{live_ctx}\n{user_msg}"

            # 4. Send Message
            try:
                response = await run.io_bound(chat_session[0].send_message, full_user_msg)
                if not response or not hasattr(response, 'text'):
                    raise Exception("AI không phản hồi (Response is empty)")
                full_text = response.text
            except Exception as e:
                chat_container.remove(spinner_row)
                ui.notify(f"Lỗi kết nối AI: {str(e)}", type='warning')
                with chat_container:
                    ui.label("Xin lỗi, tôi đang gặp khó khăn khi kết nối với máy chủ. Vui lòng thử lại sau giây lát.").classes('text-xs text-red-400 italic p-2')
                return

            # Tách JSON payload
            clean_text = full_text
            json_payload = None
            
            json_match = re.search(r'---SYSTEM_JSON_START---\n(.*?)\n---SYSTEM_JSON_END---', full_text, re.DOTALL)
            if json_match:
                try:
                    json_payload = json.loads(json_match.group(1))
                    clean_text = full_text.replace(json_match.group(0), "").strip()
                except:
                    pass
            
            # Xóa spinner
            chat_container.remove(spinner_row)
            
            # Hiển thị phản hồi
            with chat_container:
                # Custom AI Message Bubble with Markdown
                with ui.row().classes('w-full justify-start mb-2'):
                    with ui.row().classes('items-start gap-2 max-w-[95%]'):
                        ui.avatar('https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg').classes('mt-1 w-6 h-6 bg-transparent')
                        with ui.column().classes('bg-[#1f2937] text-gray-100 p-4 rounded-2xl rounded-tl-sm border border-gray-700 shadow-2xl'):
                            ui.markdown(clean_text).classes('text-[13px] leading-relaxed prose prose-invert max-w-full')
                
                chat_area.scroll_to(percent=1.0)
            
            # Xử lý Trigger từ JSON
            if json_payload:
                # 1. Pháo hoa
                if json_payload.get('trigger_fireworks'):
                    ui.run_javascript(CONFETTI_JS)
                    ui.notify('Thành tựu mới được ghi nhận!', type='positive', icon='stars')
                
                # 2. Cảnh báo mệt mỏi
                if json_payload.get('fatigue_level') == 'high_critical':
                    chat_input.disable()
                    chat_input.placeholder = 'Hệ thống đã khóa để bạn nghỉ ngơi...'
                    ui.notify('CẢNH BÁO: Pin nhận thức cạn kiệt. Hãy nghỉ ngơi 15 phút.', type='warning', persistent=True)
                
                # 3. Cập nhật context
                if json_payload.get('sentiment'):
                    app.storage.user['omni_context']['current_sentiment'] = json_payload['sentiment']

        except Exception as e:
            if 'spinner_row' in locals(): chat_container.remove(spinner_row)
            ui.notify(f'Omni-Core Error: {str(e)}', type='negative')
            print(f"Omni-Chat Error: {e}")

    send_btn.on_click(handle_send)
    chat_input.on('keydown.enter', handle_send)

    # 3. Khởi tạo Floating Action Button (FAB)
    fab = ui.button(icon='smart_toy', on_click=right_drawer.toggle).classes(
        'fixed bottom-8 right-8 rounded-full w-14 h-14 shadow-[0_0_20px_rgba(59,130,246,0.6)] bg-gradient-to-tr from-blue-600 to-purple-600 text-white hover:scale-110 transition-transform z-[90]'
    ).tooltip('Gọi Gia sư Omni-Core')
    
    # Thêm hiệu ứng pulse cho FAB nếu có streak lỗi
    ui.timer(2.0, lambda: fab.classes('animate-bounce' if app.storage.user.get('omni_context', {}).get('error_streak', 0) >= 2 else '', remove='animate-bounce'))

    # 4. Trả về các tham chiếu để cập nhật UI sau này
    return {
        'drawer': right_drawer,
        'context_label': context_label,
        'chat_area': chat_area,
        'chat_container': chat_container,
        'chat_input': chat_input,
        'fab': fab
    }

# onboarding.py - Onboarding Wizard for New Users
"""
3-Step Onboarding Flow:
  Step 1: "Bạn muốn học gì?" - Chọn hoặc upload tài liệu
  Step 2: "Cây Tri Thức Sống" - AI tự động dệt cây (loading animation)  
  Step 3: "Rà quét lỗ hổng" - Mini diagnostic quiz
"""
from nicegui import ui, app, run
from database import update_user_onboarded
import os
import json


async def create_onboarding_wizard():
    """Build the full 3-step onboarding wizard"""

    username = app.storage.user.get('username', '')
    user_id = app.storage.user.get('id')
    full_name = app.storage.user.get('full_name', 'Bạn')

    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">')

    # State tracking
    wizard_state = {
        'current_step': 1,
        'uploaded_content': None,
        'tree_path': None,
        'tree_data': None,
        'quiz_results': []
    }

    with ui.column().classes('w-full min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 items-center relative overflow-hidden'):

        # Animated background
        ui.html('''
            <div style="position:absolute;top:-10%;left:20%;width:400px;height:400px;background:radial-gradient(circle,rgba(59,130,246,0.1),transparent 70%);border-radius:50%;animation:float1 8s ease-in-out infinite;"></div>
            <div style="position:absolute;bottom:10%;right:10%;width:350px;height:350px;background:radial-gradient(circle,rgba(139,92,246,0.08),transparent 70%);border-radius:50%;animation:float2 10s ease-in-out infinite;"></div>
            <style>
                @keyframes float1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(20px,-30px)} }
                @keyframes float2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-15px,20px)} }
                @keyframes slideUp { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} }
                @keyframes pulse-glow { 0%,100%{box-shadow:0 0 20px rgba(59,130,246,0.3)} 50%{box-shadow:0 0 40px rgba(59,130,246,0.6)} }
                .animate-slideUp { animation: slideUp 0.5s ease-out forwards; }
            </style>
        ''')

        # --- PROGRESS BAR (top) ---
        with ui.row().classes('w-full max-w-3xl mt-8 mb-4 px-8 items-center gap-4 z-10'):
            for step_num in range(1, 4):
                is_active = step_num <= wizard_state['current_step']
                is_current = step_num == wizard_state['current_step']

                step_icons = {1: '📚', 2: '🌳', 3: '🧠'}
                step_labels = {1: 'Chọn tài liệu', 2: 'Dệt cây tri thức', 3: 'Rà quét lỗ hổng'}

                with ui.column().classes('items-center flex-1'):
                    circle_bg = 'bg-blue-500 shadow-lg shadow-blue-500/30' if is_active else 'bg-white/10'
                    ring = 'ring-4 ring-blue-400/50 scale-110' if is_current else ''
                    ui.html(f'''
                        <div style="width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:20px;transition:all 0.3s;" 
                             class="{circle_bg} {ring}">{step_icons[step_num]}</div>
                    ''')
                    text_color = 'text-white font-bold' if is_active else 'text-white/30'
                    ui.label(step_labels[step_num]).classes(f'text-xs mt-1 {text_color}')

                if step_num < 3:
                    line_color = 'bg-blue-500' if step_num < wizard_state['current_step'] else 'bg-white/10'
                    ui.element('div').classes(f'h-0.5 flex-1 {line_color} rounded transition-all duration-500 mt-[-20px]')

        # --- MAIN CONTENT AREA ---
        main_container = ui.column().classes('w-full max-w-3xl flex-grow items-center justify-center px-8 z-10')

        # ============================
        #  STEP 1: CHỌN TÀI LIỆU
        # ============================
        async def render_step1():
            main_container.clear()
            with main_container:
                with ui.card().classes('w-full max-w-[600px] p-8 rounded-3xl bg-white/[0.04] backdrop-blur-xl border border-white/10 shadow-2xl animate-slideUp'):

                    with ui.column().classes('items-center mb-6'):
                        ui.html('<div style="font-size:48px;">📚</div>')
                        ui.label(f'Chào {full_name}!').classes('text-2xl font-extrabold text-white mt-2')
                        ui.label('Bạn muốn học gì hôm nay?').classes('text-blue-300/70 text-base')

                    # Option 1: Upload file
                    with ui.card().classes('w-full p-5 rounded-2xl bg-white/[0.04] border border-blue-400/20 hover:border-blue-400/50 transition-all cursor-pointer mb-4'):
                        with ui.row().classes('items-center gap-4'):
                            ui.html('<div style="width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#3b82f6,#6366f1);display:flex;align-items:center;justify-content:center;font-size:22px;">📄</div>')
                            with ui.column().classes('gap-0 flex-grow'):
                                ui.label('Tải lên tài liệu').classes('text-white font-bold text-base')
                                ui.label('Hỗ trợ file .txt, .pdf, .docx — AI sẽ tự động phân tích').classes('text-blue-200/50 text-xs')

                        upload_status = ui.label('').classes('text-blue-300/70 text-sm mt-3 italic hidden')

                        async def handle_upload(e):
                            # Robust filename extraction
                            if isinstance(e, dict):
                                filename = e.get('name') or e.get('filename') or 'document.txt'
                            else:
                                filename = getattr(e, 'name', None) or getattr(e, 'filename', None) or 'document.txt'

                            upload_status.classes(remove='hidden')
                            upload_status.text = f'⏳ Đang đọc {filename}...'
                            try:
                                if isinstance(e, dict):
                                    content_bytes = e.get('content') or await e.get('file').read()
                                else:
                                    if hasattr(e, 'content'): content_bytes = e.content.read()
                                    elif hasattr(e, 'file'): content_bytes = await e.file.read()
                                    else: raise ValueError("Không tìm thấy nội dung file.")

                                from document_parser import parse_document
                                content = parse_document(filename, content_bytes)
                                wizard_state['uploaded_content'] = content
                                upload_status.text = f'✅ Đã đọc {filename} thành công ({len(content)} ký tự)'
                                upload_status.classes(remove='text-blue-300/70', add='text-green-400')

                                # Show next button
                                next_btn.classes(remove='hidden')
                            except Exception as ex:
                                upload_status.text = f'❌ Lỗi: {str(ex)}'
                                upload_status.classes(remove='text-blue-300/70', add='text-red-400')

                        ui.upload(
                            on_upload=handle_upload, auto_upload=True, multiple=False,
                            label='Kéo thả hoặc chọn file (.txt, .pdf, .docx)'
                        ).props('bordered accept=".txt,.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" dark color=blue-8').classes('w-full mt-3 bg-white/5 rounded-xl')

                    # Option 2: Use sample data
                    with ui.card().classes('w-full p-5 rounded-2xl bg-white/[0.04] border border-purple-400/20 hover:border-purple-400/50 transition-all cursor-pointer'):
                        with ui.row().classes('items-center gap-4'):
                            ui.html('<div style="width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#8b5cf6,#a855f7);display:flex;align-items:center;justify-content:center;font-size:22px;">🎓</div>')
                            with ui.column().classes('gap-0 flex-grow'):
                                ui.label('Dùng dữ liệu mẫu').classes('text-white font-bold text-base')
                                ui.label('Thử nghiệm nhanh với môn Thương Mại Điện Tử').classes('text-purple-200/50 text-xs')

                        def use_sample():
                            # Check if sample tree exists
                            sample_dir = f'user_data/{username}/trees'
                            if os.path.exists(sample_dir):
                                files = [f for f in os.listdir(sample_dir) if f.endswith('.json')]
                                if files:
                                    wizard_state['tree_path'] = os.path.join(sample_dir, files[0])
                                    with open(wizard_state['tree_path'], 'r', encoding='utf-8') as f:
                                        wizard_state['tree_data'] = json.load(f)
                                    # Skip to step 3
                                    ui.timer(0.3, lambda: render_step3(), once=True)
                                    return

                            # Otherwise upload sample content
                            wizard_state['uploaded_content'] = "SAMPLE_MODE"
                            next_btn.classes(remove='hidden')
                            ui.notify('Đã chọn dữ liệu mẫu! Nhấn "Tiếp tục" để AI dệt cây.', type='info')

                        ui.button('Chọn dữ liệu mẫu', on_click=use_sample).props('outline rounded color=purple-4 no-caps').classes('w-full mt-3')

                    # Next button
                    next_btn = ui.button(
                        'Tiếp tục →', on_click=lambda: ui.timer(0.1, render_step2, once=True)
                    ).classes('w-full mt-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-base shadow-lg hidden').props('no-caps')

        # ============================
        #  STEP 2: AI DỆT CÂY
        # ============================
        async def render_step2():
            wizard_state['current_step'] = 2
            main_container.clear()
            with main_container:
                with ui.card().classes('w-full max-w-[600px] p-8 rounded-3xl bg-white/[0.04] backdrop-blur-xl border border-white/10 shadow-2xl animate-slideUp'):

                    with ui.column().classes('items-center'):
                        # Animated tree icon
                        ui.html('''
                            <div style="font-size:64px;animation:pulse-glow 2s ease-in-out infinite;border-radius:50%;padding:16px;">🌳</div>
                        ''')
                        ui.label('AI đang dệt Cây Tri Thức...').classes('text-xl font-extrabold text-white mt-4')
                        ui.label('Trí tuệ nhân tạo đang phân tích cấu trúc kiến thức').classes('text-blue-300/60 text-sm mb-6')

                        # Progress animation
                        progress_container = ui.column().classes('w-full gap-3')
                        with progress_container:
                            steps_msgs = [
                                ('🔍', 'Đọc hiểu nội dung tài liệu...'),
                                ('🧩', 'Phân loại khái niệm macro/micro...'),
                                ('🔗', 'Suy luận mối quan hệ logic...'),
                                ('🎨', 'Tạo đồ thị 3D tương tác...'),
                            ]
                            step_labels = []
                            for icon, msg in steps_msgs:
                                with ui.row().classes('items-center gap-3 opacity-30 transition-all duration-500') as step_row:
                                    ui.label(icon).classes('text-lg')
                                    ui.label(msg).classes('text-sm text-blue-200/70')
                                step_labels.append(step_row)

                        result_container = ui.column().classes('w-full mt-4')

            # Execute tree building
            try:
                content = wizard_state['uploaded_content']

                if content and content != "SAMPLE_MODE":
                    # Animate progress steps
                    for i, label_row in enumerate(step_labels):
                        label_row.classes(remove='opacity-30', add='opacity-100')
                        await asyncio.sleep(0.8)

                    from step1_build_tree import build_tree_for_user
                    from step2_build_edges import build_edges_for_user

                    step_labels[0].classes(remove='opacity-30', add='opacity-100')
                    path, data = await run.io_bound(build_tree_for_user, username, content)

                    step_labels[1].classes(remove='opacity-30', add='opacity-100')
                    step_labels[2].classes(remove='opacity-30', add='opacity-100')

                    if data:
                        await run.io_bound(build_edges_for_user, username)
                        wizard_state['tree_path'] = path
                        wizard_state['tree_data'] = data

                        step_labels[3].classes(remove='opacity-30', add='opacity-100')

                        with result_container:
                            ui.label('✅ Cây tri thức đã được tạo thành công!').classes('text-green-400 font-bold text-center')
                            total_nodes = len(data.get('macro_nodes', [])) + len(data.get('micro_nodes', [])) + len(data.get('assess_nodes', []))
                            ui.label(f'📊 Tổng cộng {total_nodes} khái niệm').classes('text-blue-200/60 text-sm text-center')

                            ui.button(
                                'Xem cây tri thức & Kiểm tra lỗ hổng →',
                                on_click=lambda: ui.timer(0.1, render_step3, once=True)
                            ).classes('w-full mt-4 py-3 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 text-white font-bold shadow-lg').props('no-caps')
                    else:
                        with result_container:
                            ui.label('❌ Không thể tạo cây. Vui lòng thử lại.').classes('text-red-400 text-center')
                            ui.button('Quay lại', on_click=lambda: ui.timer(0.1, render_step1, once=True)).props('outline color=red-4').classes('mt-4')

                else:
                    # Sample mode - skip building
                    for label_row in step_labels:
                        label_row.classes(remove='opacity-30', add='opacity-100')

                    with result_container:
                        ui.label('✅ Đã sử dụng dữ liệu mẫu!').classes('text-green-400 font-bold text-center')
                        ui.button(
                            'Tiếp tục →',
                            on_click=lambda: ui.timer(0.1, render_step3, once=True)
                        ).classes('w-full mt-4 py-3 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 text-white font-bold shadow-lg').props('no-caps')

            except Exception as ex:
                with result_container:
                    ui.label(f'❌ Lỗi: {str(ex)}').classes('text-red-400 text-center')
                    ui.button('Quay lại', on_click=lambda: ui.timer(0.1, render_step1, once=True)).props('outline color=red-4').classes('mt-4')

        # ============================
        #  STEP 3: DIAGNOSTIC QUIZ
        # ============================
        async def render_step3():
            wizard_state['current_step'] = 3
            main_container.clear()
            with main_container:
                with ui.card().classes('w-full max-w-[600px] p-8 rounded-3xl bg-white/[0.04] backdrop-blur-xl border border-white/10 shadow-2xl animate-slideUp'):

                    with ui.column().classes('items-center mb-6'):
                        ui.html('<div style="font-size:48px;">🧠</div>')
                        ui.label('Rà quét lỗ hổng kiến thức').classes('text-xl font-extrabold text-white mt-2')
                        ui.label('Trả lời nhanh 3 câu để AI đánh giá trình độ').classes('text-blue-300/60 text-sm')

                    # Simple diagnostic quiz
                    quiz_questions = [
                        {
                            'q': 'Bạn đã từng tự học với các công cụ trực tuyến chưa?',
                            'options': ['Chưa bao giờ', 'Thỉnh thoảng', 'Thường xuyên', 'Hàng ngày'],
                            'scores': [0, 1, 2, 3]
                        },
                        {
                            'q': 'Bạn tự đánh giá trình độ hiện tại của mình?',
                            'options': ['Mới bắt đầu', 'Cơ bản', 'Trung bình', 'Nâng cao'],
                            'scores': [0, 1, 2, 3]
                        },
                        {
                            'q': 'Mục tiêu học tập của bạn là gì?',
                            'options': ['Hiểu kiến thức cơ bản', 'Chuẩn bị thi', 'Nâng cao kỹ năng', 'Nghiên cứu chuyên sâu'],
                            'scores': [0, 1, 2, 3]
                        }
                    ]

                    quiz_state = {'current': 0, 'answers': []}
                    quiz_container = ui.column().classes('w-full')

                    def render_quiz_question():
                        quiz_container.clear()
                        idx = quiz_state['current']

                        if idx >= len(quiz_questions):
                            # All done - show results
                            render_results()
                            return

                        q = quiz_questions[idx]
                        with quiz_container:
                            # Progress
                            ui.label(f'Câu {idx + 1}/{len(quiz_questions)}').classes('text-blue-400 text-xs font-bold mb-3')
                            with ui.element('div').classes('w-full bg-white/10 rounded-full h-1.5 mb-4'):
                                pct = ((idx + 1) / len(quiz_questions)) * 100
                                ui.element('div').classes('bg-blue-500 h-1.5 rounded-full transition-all duration-300').style(f'width:{pct}%')

                            ui.label(q['q']).classes('text-white font-bold text-lg mb-4')

                            for i, opt in enumerate(q['options']):
                                def select_answer(score=q['scores'][i], option=opt):
                                    quiz_state['answers'].append(score)
                                    quiz_state['current'] += 1
                                    render_quiz_question()

                                ui.button(
                                    opt, on_click=select_answer
                                ).props('outline no-caps rounded').classes(
                                    'w-full mb-2 py-3 text-left justify-start text-white/80 border-white/10 hover:bg-blue-500/20 hover:border-blue-400/50 transition-all'
                                )

                    def render_results():
                        quiz_container.clear()
                        total_score = sum(quiz_state['answers'])
                        max_score = len(quiz_questions) * 3

                        if total_score <= 3:
                            level = "Tân binh"
                            level_icon = "🌱"
                            level_color = "text-green-400"
                            advice = "Hệ thống sẽ bắt đầu từ cơ bản nhất, hướng dẫn từng bước."
                        elif total_score <= 6:
                            level = "Thám hiểm"
                            level_icon = "🧭"
                            level_color = "text-blue-400"
                            advice = "Bạn đã có nền tảng tốt. Hệ thống sẽ bỏ qua phần cơ bản."
                        else:
                            level = "Chiến binh"
                            level_icon = "⚔️"
                            level_color = "text-purple-400"
                            advice = "Bạn đã giỏi! Hệ thống sẽ tập trung vào các thử thách nâng cao."

                        with quiz_container:
                            with ui.column().classes('items-center gap-3'):
                                ui.html(f'<div style="font-size:64px;">{level_icon}</div>')
                                ui.label(f'Cấp độ: {level}').classes(f'text-2xl font-extrabold {level_color}')
                                ui.label(advice).classes('text-blue-200/60 text-sm text-center max-w-md')

                                ui.label(f'Điểm đánh giá: {total_score}/{max_score}').classes('text-white/30 text-xs mt-2')

                                ui.button(
                                    'Bắt đầu hành trình học tập! 🚀',
                                    on_click=complete_onboarding
                                ).classes('w-full mt-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-lg shadow-lg shadow-blue-600/25 hover:scale-[1.02] transition-all').props('no-caps')

                    render_quiz_question()

        def complete_onboarding():
            """Finish onboarding and enter the app"""
            if user_id:
                update_user_onboarded(user_id)
                app.storage.user['is_onboarded'] = True
            ui.navigate.to('/app')

        # Start with Step 1
        import asyncio
        await render_step1()

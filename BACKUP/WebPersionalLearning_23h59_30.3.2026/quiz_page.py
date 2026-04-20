from nicegui import ui, run, app
import json
import re
from gemini_helper import get_chat_model, extract_json_from_text
from knowledge_tracing import update_node_mastery, get_dynamic_difficulty

def register_quiz_page():
    @ui.page('/quiz_node/{subject_id}/{node_id}')
    async def quiz_page(subject_id: str, node_id: str):
        from nicegui import app
        username = app.storage.user.get('username')
        if not username:
            ui.label('Vui lòng đăng nhập lại').classes('text-red-500 font-bold p-8 text-xl')
            return

        ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">')
        ui.query('body').classes('bg-[#0d1117] font-[Inter] overflow-hidden')

        with ui.column().classes('w-full max-w-4xl mx-auto p-4 h-screen no-wrap items-center relative flex flex-col'):
            ui.label(f'Khảo Thí Cấp Cao Socrates').classes('text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-500 mt-2')
            ui.label(f'Chuyên đề: {node_id}').classes('text-gray-400 text-sm mb-4 tracking-widest uppercase')
            # --- Tải dữ liệu cơ bản ---
            tree_file = f"user_data/{username}/trees/{subject_id}.json"
            with open(tree_file, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
                
            node_content = "Nội dung chung"
            base_alpha = 10
            for c in tree_data.get('micro_nodes', []) + tree_data.get('macro_nodes', []) + tree_data.get('assess_nodes', []):
                if c.get('id') == node_id:
                    node_content = c.get('content', '') or c.get('title', '')
                    base_alpha = c.get('alpha_base', 10)
                    break
                    
            alpha, mode = get_dynamic_difficulty(username, subject_id, node_id, base_alpha)
            
            main_container = ui.column().classes('w-full flex-grow flex flex-col items-center justify-center relative')
            
            def render_lobby():
                main_container.clear()
                with main_container:
                    ui.label('Chọn Phương Thức Kiểm Tra').classes('text-2xl font-bold text-white mb-8')
                    with ui.row().classes('w-full justify-center gap-6 max-w-4xl'):
                        # Card 1: Trắc nghiệm
                        with ui.card().classes('w-[200px] h-[220px] bg-gradient-to-br from-indigo-900 to-blue-900 border border-indigo-700 cursor-pointer hover:scale-105 transition-transform flex flex-col items-center justify-center p-4').on('click', render_mcq):
                            ui.icon('fact_check', color='white').classes('text-5xl mb-4')
                            ui.label('Trắc nghiệm').classes('font-bold text-lg text-white text-center')
                            ui.label('Nhận biết nhanh. Cộng x1.0 Điểm Thông thạo.').classes('text-xs text-indigo-200 text-center mt-2')
                            
                        # Card 2: Điền từ
                        with ui.card().classes('w-[200px] h-[220px] bg-gradient-to-br from-teal-900 to-emerald-900 border border-teal-700 cursor-pointer hover:scale-105 transition-transform flex flex-col items-center justify-center p-4').on('click', render_fill_blank):
                            ui.icon('draw', color='white').classes('text-5xl mb-4')
                            ui.label('Điền Từ').classes('font-bold text-lg text-white text-center')
                            ui.label('Tái hiện khái niệm. Cộng x1.2 Điểm Thông thạo.').classes('text-xs text-teal-200 text-center mt-2')

                        # Card 3: Nối từ
                        with ui.card().classes('w-[200px] h-[220px] bg-gradient-to-br from-orange-900 to-amber-900 border border-orange-700 cursor-pointer hover:scale-105 transition-transform flex flex-col items-center justify-center p-4').on('click', render_matching):
                            ui.icon('join_inner', color='white').classes('text-5xl mb-4')
                            ui.label('Nối Từ').classes('font-bold text-lg text-white text-center')
                            ui.label('Hiểu quan hệ. Cộng x1.2 Điểm Thông thạo.').classes('text-xs text-orange-200 text-center mt-2')

                        # Card 4: Socratic
                        with ui.card().classes('w-[200px] h-[220px] bg-gradient-to-br from-purple-900 to-fuchsia-900 border border-purple-700 cursor-pointer hover:scale-105 transition-transform flex flex-col items-center justify-center p-4').on('click', render_socratic):
                            ui.icon('smart_toy', color='white').classes('text-5xl mb-4')
                            ui.label('Hỏi Đáp Socratic').classes('font-bold text-lg text-white text-center')
                            ui.label('Phân tích chuyên sâu. Cộng x1.5 Điểm Thông thạo.').classes('text-xs text-purple-200 text-center mt-2')

            def render_mcq():
                main_container.clear()
                with main_container:
                    ui.button(icon='arrow_back', on_click=render_lobby).props('flat color=white').classes('absolute top-0 left-0 z-10')
                    loading_spinner = ui.row().classes('w-full items-center justify-center gap-3 mt-10')
                    with loading_spinner:
                        ui.spinner('dots', size='3em', color='cyan')
                        ui.label('Giáo sư đang soạn câu hỏi trắc nghiệm...').classes('text-cyan-400 text-xl italic font-bold')

                async def generate_and_render_mcq():
                    try:
                        model = get_chat_model()
                        if not model: raise Exception("Không tải được Model AI")
                        
                        sys_prompt = f"""Dựa vào nội dung bài học sau, hãy tạo MỘT câu hỏi trắc nghiệm (Tập trung vào sự hiểu bản chất, độ khó {alpha}/100):
                        "{node_content}"
                        
                        TRẢ VỀ DUY NHẤT 1 BLOCK JSON theo định dạng sau (Không bọc bằng Markdown code block ```json):
                        {{
                            "question": "Nội dung câu hỏi...",
                            "options": ["Tùy chọn A", "Tùy chọn B", "Tùy chọn C", "Tùy chọn D"],
                            "correct_index": 0,
                            "explanation": "Giải thích chi tiết tại sao đúng/sai..."
                        }}
                        """
                        
                        chat = model.start_chat()
                        response = await run.io_bound(chat.send_message, sys_prompt)
                        json_str = extract_json_from_text(response.text)
                        
                        loading_spinner.delete()
                        
                        mcq_data = json_str
                        if not mcq_data or "question" not in mcq_data or "options" not in mcq_data:
                            raise Exception("AI không trả về đúng định dạng chuẩn API của hệ thống.")
                            
                        # Build UI
                        with main_container:
                            ui.label('📝 CÂU HỎI TRẮC NGHIỆM').classes('text-2xl font-bold text-cyan-400 mb-2 tracking-widest')
                            ui.markdown(f"**{mcq_data['question']}**").classes('text-xl text-white mb-6 bg-gray-800/50 p-6 rounded-xl border border-gray-700 shadow-lg w-full max-w-3xl')
                            
                            options_container = ui.column().classes('w-full max-w-3xl gap-4')
                            result_container = ui.column().classes('w-full max-w-3xl mt-6 hidden')
                            
                            async def check_answer(selected_idx):
                                options_container.clear()
                                result_container.classes(remove='hidden')
                                
                                is_correct = (selected_idx == mcq_data['correct_index'])
                                
                                # Render lại UI Options với màu đúng sai
                                with options_container:
                                    for i, opt in enumerate(mcq_data['options']):
                                        if i == mcq_data['correct_index']:
                                            bg = 'bg-green-900/40 border-green-500 text-green-100'
                                            icon = 'check_circle'
                                        elif i == selected_idx and not is_correct:
                                            bg = 'bg-red-900/40 border-red-500 text-red-100'
                                            icon = 'cancel'
                                        else:
                                            bg = 'bg-[#161b22] border-gray-800 text-gray-500 opacity-50'
                                            icon = 'radio_button_unchecked'
                                            
                                        with ui.row().classes(f'w-full p-4 border rounded-xl items-center gap-4 {bg}'):
                                            ui.icon(icon).classes('text-2xl')
                                            ui.label(opt).classes('text-lg font-medium')
                                
                                # Cập nhật điểm đồng bộ (Chờ hoàn thành)
                                virtual_alpha = min(100, int(base_alpha * 1.0)) # X1.0 cho Trắc nghiệm
                                new_level = await run.io_bound(update_node_mastery, username, subject_id, node_id, is_correct, virtual_alpha)
                                
                                # Hiển thị kết quả & Lời giải
                                with result_container:
                                    if is_correct:
                                        ui.label(f'🎉 CHÍNH XÁC! Điểm thông thạo lên {round(new_level*100)}/100').classes('text-2xl font-bold text-green-400 mb-2')
                                    else:
                                        ui.label(f'💥 RẤT TIẾC! Điểm thông thạo tụt mốc {round(new_level*100)}/100').classes('text-2xl font-bold text-red-400 mb-2')
                                        
                                    ui.markdown(f"**Khuyến nghị học thuật:**\n{mcq_data['explanation']}").classes('text-gray-300 bg-blue-900/20 p-4 rounded-xl border border-blue-800 w-full mb-4')
                                    ui.button('ĐÓNG VÀ TRỞ LẠI CÂY 3D', on_click=lambda: ui.run_javascript('window.close()')).classes('w-full bg-gradient-to-r from-green-600 to-cyan-600 font-bold shadow-lg')
                            
                            with options_container:
                                for i, opt in enumerate(mcq_data['options']):
                                    def make_btn(idx=i, text=opt):
                                        card = ui.card().classes('w-full p-4 border border-gray-700 bg-[#161b22] hover:bg-gray-700 cursor-pointer transition-colors flex flex-row items-center gap-4 group')
                                        async def on_click():
                                            await check_answer(idx)
                                        card.on('click', on_click)
                                        with card:
                                            ui.icon('radio_button_unchecked').classes('text-2xl text-gray-400 group-hover:text-cyan-400')
                                            ui.label(text).classes('text-lg text-gray-300 group-hover:text-cyan-300 font-semibold')
                                    make_btn()
                                    
                    except Exception as e:
                        loading_spinner.delete()
                        with main_container:
                            ui.label(f'LỖI: {e}').classes('text-red-500 p-4 border border-red-500 bg-red-900/20 rounded-xl max-w-2xl font-bold')
                            ui.button('Thử tạo lại đề', on_click=render_mcq).classes('mt-4 text-white')

                with main_container:
                    ui.timer(0.2, generate_and_render_mcq, once=True)
            
            def render_fill_blank():
                main_container.clear()
                with main_container:
                    ui.button(icon='arrow_back', on_click=render_lobby).props('flat color=white').classes('absolute top-0 left-0 z-10')
                    loading_spinner = ui.row().classes('w-full items-center justify-center gap-3 mt-10')
                    with loading_spinner:
                        ui.spinner('dots', size='3em', color='teal')
                        ui.label('Giáo sư đang đục lỗ văn bản...').classes('text-teal-400 text-xl italic font-bold')

                async def generate_and_render_fillblk():
                    try:
                        model = get_chat_model()
                        if not model: raise Exception("Không tải được Model AI")
                        
                        sys_prompt = f"""Dựa vào nội dung bài học sau, hãy tạo MỘT bài tập điền từ bằng cách giấu đi các từ khóa quan trọng nhất. (Độ khó {alpha}/100):
                        "{node_content}"
                        
                        TRẢ VỀ DUY NHẤT 1 BLOCK JSON theo định dạng (Không bọc bằng Markdown code block ```json):
                        {{
                            "content": "Đoạn văn hoàn chỉnh nhưng thay thế các từ khóa bằng [BLANK]",
                            "answers": ["Từ khóa bị giấu thứ 1", "Từ khóa bị giấu thứ 2"],
                            "explanation": "Giải thích ngắn về vai trò của các từ khóa này."
                        }}
                        """
                        
                        chat = model.start_chat()
                        response = await run.io_bound(chat.send_message, sys_prompt)
                        json_str = extract_json_from_text(response.text)
                        
                        loading_spinner.delete()
                        
                        fill_data = json_str
                        if not fill_data or "content" not in fill_data or "answers" not in fill_data:
                            raise Exception("AI không trả về đúng định dạng chuẩn API của hệ thống.")
                            
                        # Build UI
                        with main_container:
                            ui.label('✍️ ĐIỀN TỪ KHÓA').classes('text-2xl font-bold text-teal-400 mb-6 tracking-widest')
                            
                            segments = fill_data['content'].split("[BLANK]")
                            inputs = []
                            
                            text_container = ui.row().classes('w-full max-w-3xl items-center gap-2 mb-6 bg-gray-800/50 p-6 rounded-xl border border-gray-700 shadow-lg text-lg text-white leading-loose')
                            with text_container:
                                for i, seg in enumerate(segments):
                                    ui.label(seg)
                                    if i < len(segments) - 1:
                                        # Có khoảng trống ở đây
                                        inp = ui.input().props('dense outlined dark').classes('w-32 inline-block mx-1')
                                        inputs.append(inp)
                                        
                            result_container = ui.column().classes('w-full max-w-3xl hidden mt-4')
                            
                            async def check_fill_answer():
                                btn_submit.disable()
                                result_container.classes(remove='hidden')
                                
                                user_answers = [inp.value.strip().lower() for inp in inputs]
                                correct_answers = [ans.strip().lower() for ans in fill_data['answers']]
                                
                                is_correct = True
                                for i in range(len(inputs)):
                                    u_a = user_answers[i]
                                    c_a = correct_answers[i]
                                    if not u_a or (u_a not in c_a and c_a not in u_a):
                                        is_correct = False
                                        inputs[i].props('bg-color=red-9 text-white')
                                    else:
                                        inputs[i].props('bg-color=green-9 text-white')
                                
                                virtual_alpha = min(100, int(base_alpha * 1.2)) # X1.2 cho Điền từ
                                new_level = await run.io_bound(update_node_mastery, username, subject_id, node_id, is_correct, virtual_alpha)
                                
                                with result_container:
                                    if is_correct:
                                        ui.label(f'🎉 CHÍNH XÁC KÝ ỨC! Thông thạo lên {round(new_level*100)}/100').classes('text-2xl font-bold text-green-400 mb-2')
                                    else:
                                        ui.label(f'💥 SAI SÓT! Ký ức chưa trọn vẹn. Thông thạo xuống {round(new_level*100)}/100').classes('text-2xl font-bold text-red-400 mb-2')
                                        
                                    ui.markdown(f"**Đáp án đúng:** `{', '.join(fill_data['answers'])}`\n\n**Học thuật:**\n{fill_data['explanation']}").classes('text-gray-300 bg-blue-900/20 p-4 rounded-xl border border-blue-800 w-full mb-4')
                                    ui.button('ĐÓNG VÀ TRỞ LẠI CÂY 3D', on_click=lambda: ui.run_javascript('window.close()')).classes('w-full bg-gradient-to-r from-green-600 to-cyan-600 font-bold shadow-lg')
                                    
                            btn_submit = ui.button('NỘP BÀI CAO KHẢO', on_click=check_fill_answer).classes('w-full max-w-3xl font-bold bg-teal-700 text-white mt-4')

                    except Exception as e:
                        loading_spinner.delete()
                        with main_container:
                            ui.label(f'LỖI: {e}').classes('text-red-500 p-4 border border-red-500 bg-red-900/20 rounded-xl max-w-2xl font-bold')
                            ui.button('Thử tạo lại đề', on_click=render_fill_blank).classes('mt-4 text-white')

                with main_container:
                    ui.timer(0.2, generate_and_render_fillblk, once=True)


            def render_matching():
                main_container.clear()
                with main_container:
                    ui.button(icon='arrow_back', on_click=render_lobby).props('flat color=white').classes('absolute top-0 left-0 z-10')
                    loading_spinner = ui.row().classes('w-full items-center justify-center gap-3 mt-10')
                    with loading_spinner:
                        ui.spinner('dots', size='3em', color='orange')
                        ui.label('Giáo sư đang xáo trộn định nghĩa...').classes('text-orange-400 text-xl italic font-bold')

                async def generate_and_render_matching():
                    try:
                        model = get_chat_model()
                        if not model: raise Exception("Không tải được Model AI")
                        
                        sys_prompt = f"""Dựa vào nội dung bài học sau, hãy tạo MỘT bài tập NỐI TỪ. Tìm 3-4 cặp (Thuật ngữ - Định nghĩa khái niệm) quan trọng nhất. (Độ khó {alpha}/100):
                        "{node_content}"
                        
                        TRẢ VỀ DUY NHẤT 1 BLOCK JSON theo định dạng (Không bọc bằng Markdown code block ```json):
                        {{
                            "matches": [
                                {{"term": "Thuật ngữ 1", "definition": "Định nghĩa cực kỳ ngắn gọn 1"}},
                                {{"term": "Thuật ngữ 2", "definition": "Định nghĩa cực kỳ ngắn gọn 2"}}
                            ],
                            "explanation": "Giải thích tổng quan."
                        }}
                        """
                        
                        chat = model.start_chat()
                        response = await run.io_bound(chat.send_message, sys_prompt)
                        json_str = extract_json_from_text(response.text)
                        
                        loading_spinner.delete()
                        
                        match_data = json_str
                        if not match_data or "matches" not in match_data:
                            raise Exception("AI không trả về đúng định dạng chuẩn API của hệ thống.")
                            
                        import random
                        pairs = match_data['matches']
                        definitions = [p['definition'] for p in pairs]
                        random.shuffle(definitions)
                        # Create dict for ui.select options
                        def_options = {d: d for d in definitions}
                        
                        # Build UI
                        with main_container:
                            ui.label('🔗 NỐI THUẬT NGỮ VÀ KHÁI NIỆM').classes('text-2xl font-bold text-orange-400 mb-6 tracking-widest')
                            
                            select_widgets = []
                            ui_container = ui.column().classes('w-full max-w-4xl gap-4 mb-6')
                            with ui_container:
                                for pair in pairs:
                                    with ui.row().classes('w-full items-center no-wrap gap-4 bg-gray-800/50 p-4 border border-gray-700 rounded-xl shadow-lg'):
                                        ui.label(pair['term']).classes('text-lg font-bold text-orange-300 w-1/3')
                                        ui.icon('arrow_right_alt').classes('text-3xl text-gray-500')
                                        sel = ui.select(options=def_options, label='Chọn định nghĩa đúng...').props('outlined dark dense').classes('flex-grow')
                                        # Workaround: NiceGUI ui.select might truncate long text in dropdowns, but it's okay for short definitions.
                                        select_widgets.append((sel, pair['definition']))
                                        
                            result_container = ui.column().classes('w-full max-w-4xl hidden mt-4')
                            
                            async def check_matching_answer():
                                btn_submit.disable()
                                result_container.classes(remove='hidden')
                                
                                is_correct = True
                                for sel, correct_def in select_widgets:
                                    if sel.value != correct_def:
                                        is_correct = False
                                        sel.props('bg-color=red-9')
                                    else:
                                        sel.props('bg-color=green-9')
                                
                                virtual_alpha = min(100, int(base_alpha * 1.2)) # X1.2 cho Nối từ
                                new_level = await run.io_bound(update_node_mastery, username, subject_id, node_id, is_correct, virtual_alpha)
                                
                                with result_container:
                                    if is_correct:
                                        ui.label(f'🎉 KẾT NỐI HOÀN HẢO! Thông thạo đạt {round(new_level*100)}/100').classes('text-2xl font-bold text-green-400 mb-2')
                                    else:
                                        ui.label(f'💥 RÂU ÔNG NỌ CẮM CẰM BÀ KIA! Thông thạo tụt mốc {round(new_level*100)}/100').classes('text-2xl font-bold text-red-400 mb-2')
                                        
                                    ui.markdown(f"**Học thuật:**\n{match_data.get('explanation', '')}").classes('text-gray-300 bg-blue-900/20 p-4 rounded-xl border border-blue-800 w-full mb-4')
                                    ui.button('ĐÓNG VÀ TRỞ LẠI CÂY 3D', on_click=lambda: ui.run_javascript('window.close()')).classes('w-full bg-gradient-to-r from-green-600 to-cyan-600 font-bold shadow-lg')
                                    
                            btn_submit = ui.button('CHỐT ĐÁP ÁN NỐI TỪ', on_click=check_matching_answer).classes('w-full max-w-4xl font-bold bg-orange-700 text-white mt-4 p-3 rounded-lg shadow-lg')

                    except Exception as e:
                        loading_spinner.delete()
                        with main_container:
                            ui.label(f'LỖI: {e}').classes('text-red-500 p-4 border border-red-500 bg-red-900/20 rounded-xl max-w-2xl font-bold')
                            ui.button('Thử tạo lại đề', on_click=render_matching).classes('mt-4 text-white')

                with main_container:
                    ui.timer(0.2, generate_and_render_matching, once=True)


            def render_socratic():
                main_container.clear()
                with main_container:
                    ui.button(icon='arrow_back', on_click=render_lobby).props('flat color=white').classes('absolute top-0 left-0 z-10')
                    main_card = ui.card().classes('w-full flex-grow bg-[#161b22] border border-gray-800 shadow-2xl rounded-2xl flex flex-col p-4 gap-4 mt-8')
                    
                    with main_card:
                        chat_area = ui.scroll_area().classes('w-full flex-grow p-4 border border-gray-800 rounded-xl bg-[#0d1117]')
                        
                        with ui.row().classes('w-full no-wrap items-center gap-2 mt-auto p-2 border-t border-gray-800'):
                            user_input = ui.input(placeholder='Hồi đáp lý luận của Giáo sư...').props('rounded outlined dark dense').classes('w-full')
                            btn_send = ui.button(icon='send').props('round flat color=cyan')

                    # State variables
                    chat_session = {'session': None}
                    
                    async def render_loading(msg):
                        with chat_area:
                            loading_row = ui.row().classes('w-full items-center gap-3 mb-4')
                            ui.spinner('dots', size='2em', color='gray').classes('text-gray-500')
                            ui.label(msg).classes('text-gray-500 italic')
                        return loading_row

                    async def append_message(sender_is_ai, content):
                        with chat_area:
                            alignment_class = "" if sender_is_ai else "flex-row-reverse"
                            bg_color = 'bg-cyan-900/30 border-cyan-800 text-cyan-50' if sender_is_ai else 'bg-purple-900/30 border-purple-800 text-purple-50'
                            
                            with ui.row().classes(f'w-full no-wrap items-start gap-4 mb-6 {alignment_class}'):
                                if sender_is_ai:
                                    ui.icon('smart_toy', color='cyan').classes('text-3xl mt-1')
                                else:
                                    ui.icon('person', color='purple').classes('text-3xl mt-1')
                                    
                                with ui.column().classes(f'{bg_color} p-4 rounded-2xl max-w-[85%] border shadow-lg'):
                                    ui.markdown(content)
                                    
                        ui.run_javascript("document.querySelector('.q-scrollarea__container').scrollTo(0, 99999);")

                    async def start_socratic_session():
                        loading = await render_loading('Giáo sư đang phân tích nội dung kiến thức...')
                        try:
                            model = get_chat_model()
                            if not model: raise Exception("Không tải được Model AI")
                            
                            sys_prompt = f"""Ngươi là Giáo sư triết học Socrates nghiêm khắc và thông tuệ. Nhiệm vụ của ngươi là kiểm tra sinh viên xem họ CÓ THỰC SỰ HIỂU BẢN CHẤT kiến thức sau không:
                            "{node_content}"
                            (Mục tiêu độ khó yêu cầu: {alpha}/100 | Chiến thuật sư phạm hiện tại: {mode}).
                            
                            LUẬT CHƠI DÀNH CHO GIÁO SƯ (IMPORTANT):
                            1. Câu đầu tiên: Đặt 1 câu hỏi mở, đưa ra tình huống ngược đời, hoặc yêu cầu giải thích thực tiễn để sinh viên bộc lộ lập luận. KHÔNG HỎI TRẮC NGHIỆM ABCD.
                            2. Nếu sinh viên trả lời: KHÔNG BÁO đúng/sai ngay. Hãy dùng Socratic Method (hỏi vặn lại, chất vấn kẽ hở, ép sinh viên tự sửa sai).
                            3. KHI VÀ CHỈ KHI sinh viên thực sự nắm chắc chân lý (hoặc đã vặn vẹo 3-4 lượt và sinh viên rất giỏi), hoặc nếu họ quá tự ti và muốn bỏ cuộc, bạn CÓ QUYỀN CHỐT CHẤM ĐIỂM.
                            
                            FORMAT CHẤM ĐIỂM BẮT BUỘC:
                            Luôn kết thúc câu cuối cùng bằng khối block JSON sau đây (Không bọc Markdown code, ghi plain text):
                            {{"verdict": "passed"}} (nếu thông thạo)
                            HOẶC {{"verdict": "failed"}} (nếu hỏng kiến thức)
                            HOẶC {{"verdict": "continue"}} (nếu muốn hỏi tiếp)
                            """
                            
                            chat = model.start_chat()
                            chat_session['session'] = chat
                            
                            response = await run.io_bound(chat.send_message, sys_prompt)
                            loading.delete()
                            
                            display_text = re.sub(r'\{[^{}]*"verdict"[^{}]*\}', '', response.text).strip()
                            await append_message(True, display_text)
                            
                        except Exception as ex:
                            loading.delete()
                            await append_message(True, f"**LỖI KHỞI TẠO:** {ex}")

                    async def handle_chat():
                        if not user_input.value.strip() or not chat_session['session']: return
                        
                        msg = user_input.value
                        user_input.value = ''
                        
                        await append_message(False, msg)
                        loading = await render_loading('Giáo sư đang săm soi lập luận...')
                        
                        try:
                            response = await run.io_bound(chat_session['session'].send_message, msg)
                            loading.delete()
                            
                            display_text = re.sub(r'\{[^{}]*"verdict"[^{}]*\}', '', response.text).strip()
                            await append_message(True, display_text)
                            
                            json_block = extract_json_from_text(response.text)
                            verdict = json_block.get('verdict', 'continue')
                            
                            if verdict in ['passed', 'failed']:
                                btn_send.disable()
                                user_input.disable()
                                
                                is_correct = (verdict == 'passed')
                                # Hệ số Socratic x1.5 vào Base Alpha
                                virtual_alpha = min(100, int(base_alpha * 1.5))
                                new_level = await run.io_bound(update_node_mastery, username, subject_id, node_id, is_correct, virtual_alpha)
                                
                                with chat_area:
                                    if is_correct:
                                        ui.markdown(f"**🎉 CHÚC MỪNG!** Giáo sư Socrates đã bị khuất phục. Điểm thông thạo leo lên {round(new_level*100)}/100.").classes('text-green-400 mt-4 p-4 border border-green-500 bg-green-900/20 rounded-xl font-bold')
                                    else:
                                        ui.markdown(f"**💥 RẤT TIẾC!** Lỗ hổng kiến thức quá lớn. Điểm thông thạo tụt mốc {round(new_level*100)}/100. Hãy ôn bài và phục thù!").classes('text-red-400 mt-4 p-4 border border-red-500 bg-red-900/20 rounded-xl font-bold')
                                        
                                    ui.button('ĐÓNG KHAI ÂN VÀ CHUYỂN PHÉP 3D', on_click=lambda: ui.run_javascript('window.close()')).classes('w-full mt-4 bg-gradient-to-r from-green-600 to-cyan-600 font-bold text-white shadow-lg')
                                    ui.run_javascript("document.querySelector('.q-scrollarea__container').scrollTo(0, 99999);")
                                    
                        except Exception as ex:
                            loading.delete()
                            await append_message(True, f"**LỖI TRUYỀN TẢI:** {ex}")

                    user_input.on('keydown.enter', handle_chat)
                    btn_send.on_click(handle_chat)
                    
                    ui.timer(0.2, start_socratic_session, once=True)

            # --- KHỞI ĐỘNG LOBBY ---
            render_lobby()

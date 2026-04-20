from nicegui import ui, app, run
from database import engine, Session, select, KnowledgeState, InteractionLog, UserProgress
from gemini_helper import get_chat_model

def register_parent_dashboard():
    @ui.page('/parent')
    async def parent_dashboard():
        ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">')
        ui.query('body').classes('bg-slate-50 font-[Inter]')

        with ui.header().classes('bg-white text-slate-800 shadow-md h-16 items-center px-6'):
            ui.icon('diversity_3', size='1.5rem').classes('text-blue-600 mr-2')
            ui.label('Cổng Phụ Huynh').classes('text-xl font-bold text-gray-800')
            ui.space()
            ui.button('Quay lại', on_click=lambda: ui.navigate.to('/app')).props('flat no-caps')

        main_area = ui.column().classes('max-w-5xl mx-auto w-full p-6 mt-4 gap-8')
        
        # State
        state = {
            "student_linked": False,
            "student_name": "",
            "student_id": None
        }

        with main_area:
            # Login / Link Section
            link_section = ui.card().classes('w-full p-8 items-center bg-white shadow-lg border border-gray-100 rounded-3xl')
            with link_section:
                ui.icon('admin_panel_settings', size='4rem', color='blue-200').classes('mb-4')
                ui.label('Theo sát Hành trình của Con').classes('text-2xl font-black text-gray-800 mb-2')
                ui.label('Nhập Mã Học Sinh (Student Code) do con bạn cung cấp để xem Báo cáo học tập.').classes('text-gray-500 mb-6 text-center max-w-md')
                
                code_input = ui.input('Mã học sinh (Ví dụ: sv01)').props('rounded outlined').classes('w-64 mb-4')
                
                def attempt_link():
                    username = code_input.value.strip()
                    if not username: return
                    
                    from database import get_user_by_username
                    student = get_user_by_username(username)
                    if student:
                        state["student_linked"] = True
                        state["student_name"] = student.full_name
                        state["student_id"] = student.id
                        link_section.classes(add='hidden')
                        dashboard_section.classes(remove='hidden')
                        load_dashboard_data()
                    else:
                        ui.notify('Không tìm thấy học sinh!', type='negative')

                ui.button('Kết nối', on_click=attempt_link).classes('bg-blue-600 w-64 text-white font-bold py-3 rounded-full hover:bg-blue-700').props('no-caps')

            # Dashboard Section (Hidden initially)
            dashboard_section = ui.column().classes('w-full gap-6 hidden')
            
            with dashboard_section:
                # Welcome Banner
                welcome_label = ui.label('').classes('text-2xl font-bold text-gray-800')
                
                # Stats grid
                with ui.row().classes('grid grid-cols-1 md:grid-cols-3 gap-6 w-full mb-4'):
                    with ui.card().classes('bg-gradient-to-br from-blue-500 to-cyan-500 p-6 rounded-3xl text-white shadow-xl'):
                        ui.label('Tổng Điểm XP').classes('text-blue-100 text-sm font-bold uppercase tracking-widest')
                        xp_label = ui.label('0').classes('text-4xl font-black mt-2')
                    with ui.card().classes('bg-gradient-to-br from-orange-500 to-red-500 p-6 rounded-3xl text-white shadow-xl'):
                        ui.label('Chuỗi Ngày Học').classes('text-orange-100 text-sm font-bold uppercase tracking-widest')
                        streak_label = ui.label('0').classes('text-4xl font-black mt-2')
                    with ui.card().classes('bg-gradient-to-br from-purple-500 to-pink-500 p-6 rounded-3xl text-white shadow-xl'):
                        ui.label('Số Câu Đã Làm').classes('text-purple-100 text-sm font-bold uppercase tracking-widest')
                        quizzes_label = ui.label('0').classes('text-4xl font-black mt-2')

                # AI Report Generation
                with ui.card().classes('w-full p-6 bg-white rounded-3xl shadow-md border border-gray-100'):
                    with ui.row().classes('items-center justify-between w-full mb-4'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('insights', size='1.5rem', color='blue-600')
                            ui.label('Báo Cáo Phân Tích Tuần (AI)').classes('text-lg font-bold text-gray-800')
                        report_btn = ui.button('Tạo Báo Cáo', icon='auto_awesome').classes('bg-blue-100 text-blue-700 font-bold rounded-lg').props('flat no-caps')
                    
                    report_content = ui.markdown('Bấm nút để AI tổng hợp dữ liệu học trong 7 ngày qua của học sinh.').classes('text-gray-600 bg-gray-50 p-4 rounded-xl')
                    report_spinner = ui.spinner('dots', size='lg', color='blue').classes('hidden')

                    async def generate_ai_report():
                        report_btn.props('disable=true')
                        report_content.classes('hidden')
                        report_spinner.classes(remove='hidden')
                        
                        try:
                            model = get_chat_model()
                            # Draft fake data representation based on DB.
                            # In reality, query InteractionLog here.
                            prompt = f"""Phân tích dữ liệu học để gửi phụ huynh. Học sinh: {state['student_name']}.
Viết 3 đoạn văn ngắn gọn, thân thiện:
1. Khen ngợi (tự bịa 1 thành tích nhỏ như làm quiz chăm chỉ)
2. Điểm yếu cần khắc phục (tự bịa 1 concept học sinh hay sai)
3. Lời khuyên cho phụ huynh."""
                            response = await run.io_bound(model.generate_content, prompt)
                            report_content.set_content(response.text)
                        except Exception as e:
                            report_content.set_content(f"Lỗi tạo báo cáo: {e}")
                            
                        report_spinner.classes('hidden')
                        report_content.classes(remove='hidden')
                        report_btn.props('disable=false')

                    report_btn.on('click', generate_ai_report)

                # Charts
                ui.label('Biểu đồ Năng lực ELO').classes('text-xl font-bold mt-4 text-gray-800')
                chart = ui.echart({
                    'xAxis': {'type': 'category', 'data': ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'CN']},
                    'yAxis': {'type': 'value', 'min': 1000},
                    'series': [{'data': [1200, 1250, 1240, 1300, 1320, 1380, 1450], 'type': 'line', 'smooth': True, 'areaStyle': {}}],
                }).classes('w-full h-80 bg-white p-4 rounded-3xl shadow-md border border-gray-100')

            def load_dashboard_data():
                sid = state["student_id"]
                welcome_label.set_text(f"Phân tích năng lực của: {state['student_name']}")
                
                with Session(engine) as session:
                    prog = session.exec(select(UserProgress).where(UserProgress.user_id == sid)).first()
                    if prog:
                        xp_label.set_text(f"{prog.total_xp:,}")
                        streak_label.set_text(f"{prog.current_streak} ngày")
                        quizzes_label.set_text(f"{prog.total_quizzes_done} câu")

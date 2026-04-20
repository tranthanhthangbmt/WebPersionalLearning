import sys

def patch_file():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_header = """    # --- UI Components ---
    # Flat header design (no border, no shadow)
    with ui.header().classes(replace='row items-center bg-white text-slate-800 p-2 h-[60px] z-20') as header:
        ui.label('PKT Bio-Tutor').classes('text-xl font-bold text-blue-600 mr-4')
        
        # --- PROFESSIONAL TABS IN HEADER ---
        with ui.tabs().classes('w-auto justify-center mr-4') as tabs:
            tab_journey = ui.tab('Hành trình', icon='insights')
            tab_library = ui.tab('Cửa hàng UGC', icon='store')
            tab_social = ui.tab('Cộng đồng', icon='public')
            tab_nexus = ui.tab('Nexus Space', icon='explore')
            tab_video = ui.tab('Học liệu Video', icon='play_circle')
            tab_quiz = ui.tab('Kiểm tra', icon='quiz')
            tab_studio = ui.tab('Graph Studio', icon='architecture')
            tab_tutor = ui.tab('Gia sư AI', icon='smart_toy')
            tab_leaderboard = ui.tab('Xếp hạng', icon='leaderboard')
            tab_profile = ui.tab('Hồ sơ', icon='person')

        # --- DYNAMIC LESSON TITLE IN HEADER ---
        header_lesson_container = ui.row().classes('items-center gap-2 flex-grow overflow-hidden')
        # Will be populated in load_lesson_ui

        # Prediction Label
        prediction_label = ui.label('').classes('text-sm font-bold text-blue-700 mr-4 whitespace-nowrap')

        # Component Pin Sinh học
        ui.label('Bio:').classes('text-xs mr-1 text-gray-500')
        battery = BioBattery(ui.row())
        
        # --- GAMIFICATION XP WIDGET IN HEADER ---
        gamification_stats = XPEngine.get_user_stats(user.id)
        create_xp_header_widget(gamification_stats)

        # Màn hình Darkmode
        dark = ui.dark_mode()

        # Avatar & User Info
        with ui.row().classes('items-center ml-4 gap-2'):
            ui.button(icon='dark_mode', on_click=dark.toggle).props('flat round dense color=grey-6').tooltip('Giao diện Sáng/Tối')
            ui.avatar(icon='person', color='blue-100', text_color='blue-600').props('size=sm')
            ui.label(user.full_name).classes('font-bold text-sm hidden md:block')
            ui.button(icon='logout', on_click=lambda: ui.navigate.to('/logout')).props('flat round dense color=grey-6').tooltip('Đăng xuất')

    # Hàm cập nhật Dashboard loop
    def update_ui_loop():
        battery.update(state.current_fatigue)
        if graph_container: # Update graph if needed or periodically
             pass 

    ui.timer(1.0, update_ui_loop)"""

    new_header = """    # --- UI Components ---
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

    ui.timer(1.0, update_ui_loop)"""


    old_tab_panel = """    with ui.tab_panels(tabs, value=tab_journey).classes('w-full h-[calc(100vh-100px)]'):
        
        # TAB 0: PUBLIC LIBRARY (Thư viện công cộng)"""

    new_tab_panel = """    with ui.tab_panels(tabs, value=tab_dashboard).classes('w-full h-[calc(100vh-60px)] m-0 p-0'):
        
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

        # TAB 0: PUBLIC LIBRARY (Thư viện công cộng)"""
        
    def find_and_slice(text, old_t, new_t):
        if old_t in text:
            print("Found exact match.")
            return text.replace(old_t, new_t)
        
        # fallback ignoring exact spaces
        import re
        old_pattern = re.sub(r'\s+', '\\\\s+', re.escape(old_t))
        if re.search(old_pattern, text):
            print("Found regex match.")
            return re.sub(old_pattern, new_t.replace('\\', '\\\\'), text)
            
        print("Not found at all!")
        return text

    new_content = find_and_slice(content, old_header, new_header)
    new_content = find_and_slice(new_content, old_tab_panel, new_tab_panel)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == '__main__':
    patch_file()

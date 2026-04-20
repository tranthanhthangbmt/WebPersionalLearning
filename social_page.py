from nicegui import ui
import random

def create_social_section(user, container):
    """Render the Social Network / Feed section inside the given container"""
    container.clear()
    with container:
        with ui.row().classes('w-full gap-6 items-start'):
            
            # LEFT: Activity Feed (Bảng Tin)
            with ui.column().classes('w-full md:w-2/3 gap-4'):
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('🌐 Bảng Tin Chuyên Cần').classes('text-2xl font-black text-gray-800')
                    ui.button(icon='refresh', on_click=lambda: ui.notify('Đã làm mới bảng tin')).props('flat round color=grey')

                # Mock feed items
                feed_events = [
                    {"name": "Trần Tuấn", "action": "Vừa đạt chuỗi học 7 ngày liên tiếp! 🔥", "time": "2 phút trước", "icon": "local_fire_department", "color": "orange"},
                    {"name": "Lê Mai A.", "action": "Vừa hoàn thành Quiz: Thị giác máy tính 🎯", "time": "15 phút trước", "icon": "check_circle", "color": "green"},
                    {"name": "Phạm Cường", "action": "Vừa mua Cây tri thức 'Thương mại điện tử' bằng 500 XP 💎", "time": "1 giờ trước", "icon": "shopping_cart", "color": "purple"},
                    {"name": "Vũ Đăng", "action": "Lên cấp Bậc thầy (Level 4) 🌟", "time": "3 giờ trước", "icon": "military_tech", "color": "yellow"},
                ]
                
                for event in feed_events:
                    with ui.card().classes('w-full p-4 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition'):
                        with ui.row().classes('items-center gap-4'):
                            ui.avatar(icon='person', color='grey-200', text_color='grey-600')
                            with ui.column().classes('gap-0 flex-grow'):
                                ui.label(event['name']).classes('font-bold text-gray-800')
                                ui.label(event['action']).classes(f'text-sm text-gray-600')
                            with ui.column().classes('items-end'):
                                ui.icon(event['icon']).classes(f'text-{event["color"]}-500 text-xl')
                                ui.label(event['time']).classes('text-xs text-gray-400 mt-1')

            # RIGHT: Khoe Điểm & Thách Đấu
            with ui.column().classes('w-full md:w-1/3 gap-6'):
                # 1. Chia sẻ thẻ điểm
                with ui.card().classes('w-full p-6 rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-xl'):
                    ui.icon('share', size='2rem').classes('mb-2 opacity-80')
                    ui.label('Khoe Thành Tích').classes('text-xl font-bold mb-2')
                    ui.label('Chia sẻ bảng điểm ELO và cấp độ của bạn lên Facebook hoăc Zalo để bạn bè cùng trầm trồ.').classes('text-sm text-indigo-100 mb-6')
                    
                    def mock_share():
                        from gamification.gamification_ui import CONFETTI_JS
                        ui.run_javascript(CONFETTI_JS)
                        ui.notify('Đã tạo thẻ stat-card và copy link chia sẻ!', type='positive', position='top-right')

                    ui.button('Tạo Thẻ Tóm Tắt (Stat Card)', on_click=mock_share).classes('w-full bg-white text-indigo-600 font-bold rounded-xl py-2').props('no-caps')

                # 2. Thách Đấu
                with ui.card().classes('w-full p-6 rounded-3xl bg-white border border-rose-100 shadow-sm'):
                    with ui.row().classes('items-center gap-2 mb-4'):
                        ui.icon('swords', color='rose-500') # fallback if sword icon missing: 'sports_mma' or 'flash_on'
                        ui.label('Thách Đấu Bạn Bè').classes('text-lg font-bold text-gray-800')
                    ui.label('Gửi lời mời thách đấu 10 câu Quiz ngẫu nhiên với bạn bè trong danh sách.').classes('text-sm text-gray-500 mb-4')
                    ui.button('Tìm đối thủ', icon='search').classes('w-full bg-rose-500 text-white font-bold rounded-xl').props('no-caps')

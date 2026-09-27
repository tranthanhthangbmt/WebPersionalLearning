from nicegui import ui
from auth_service import is_logged_in

def create_pricing_page(is_standalone=True):
    ui.add_head_html('''
        <style>
            .pricing-card:hover { transform: translateY(-5px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); }
            .pricing-pro-glow { box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); }
        </style>
    ''')
    
    with ui.column().classes('w-full min-h-screen bg-slate-50 items-center py-12 px-4'):
        # Header
        ui.label('Gói thuê bao').classes('text-4xl md:text-5xl font-extrabold text-slate-800 mb-4 text-center')
        ui.label('Khám phá những việc mà PKT Bio-Tutor có thể làm để nâng cao hiệu suất học tập của bạn.').classes('text-slate-500 text-lg md:text-xl text-center max-w-2xl mb-12')
        
        # Cards Container
        with ui.row().classes('w-full max-w-[1300px] justify-center items-stretch gap-6 flex-wrap'):
            
            # --- TIER 1: FREE ---
            with ui.card().classes('w-full md:w-[280px] p-6 flex flex-col justify-between pricing-card transition-all duration-300 rounded-3xl border border-slate-200 shadow-sm'):
                with ui.column().classes('w-full'):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('eco', color='emerald-500').classes('text-2xl')
                        ui.label('Miễn phí').classes('text-2xl font-bold text-slate-800')
                    ui.label('Trải nghiệm cơ bản với hệ thống học tập thông minh.').classes('text-slate-500 text-sm mb-6 min-h-[40px]')
                    
                    with ui.row().classes('items-baseline gap-1 mb-2'):
                        ui.label('0').classes('text-5xl font-extrabold text-slate-800')
                        ui.label('VNĐ/tháng').classes('text-slate-500 font-medium')
                    ui.label('(Cần có Tài khoản)').classes('text-slate-400 text-xs mb-6')
                    
                    ui.button('Bắt đầu', on_click=lambda: handle_upgrade('free')).props('outline rounded no-caps').classes('w-full text-slate-700 border-slate-300 py-3 font-semibold mb-6 hover:bg-slate-100')
                    
                    ui.separator().classes('mb-6')
                    
                    # Features
                    create_feature_list([
                        'Truy cập các khóa học công khai (giá 0đ)',
                        '500 XP mặc định khi đăng ký mới',
                        'Truy cập cơ bản vào Cây tri thức',
                        'Hỗ trợ AI Socratic (tối đa 10 tin/ngày)',
                        'Dữ liệu lưu trữ cơ bản'
                    ])

            # --- TIER 2: PLUS ---
            with ui.card().classes('w-full md:w-[280px] p-6 flex flex-col justify-between pricing-card transition-all duration-300 rounded-3xl border border-slate-200 shadow-sm relative overflow-hidden'):
                with ui.column().classes('w-full'):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('local_library', color='blue-500').classes('text-2xl')
                        ui.label('Học giả (Plus)').classes('text-2xl font-bold text-slate-800')
                    ui.label('Truy cập nhiều tính năng mạnh mẽ để tăng hiệu suất học.').classes('text-slate-500 text-sm mb-6 min-h-[40px]')
                    
                    with ui.row().classes('items-baseline gap-1 mb-2'):
                        ui.label('49.000').classes('text-4xl lg:text-5xl font-extrabold text-blue-600')
                        ui.label('VNĐ/tháng').classes('text-slate-500 font-medium')
                    ui.label('').classes('text-slate-400 text-xs mb-6 h-4') # padding
                    
                    ui.button('Nâng cấp ngay', on_click=lambda: handle_upgrade('plus')).props('unelevated rounded no-caps').classes('w-full bg-blue-100 text-blue-700 border border-blue-200 py-3 font-semibold mb-6 hover:bg-blue-200')
                    
                    ui.separator().classes('mb-6')
                    
                    ui.label('Mọi lợi ích trong bản Miễn phí, kèm theo:').classes('text-sm font-semibold text-slate-700 mb-4')
                    # Features
                    create_feature_list([
                        'Tặng 5.000 XP thưởng mỗi tháng',
                        'Tạo Cây tri thức và PDF cá nhân không giới hạn',
                        'Mở khóa tính năng Gamification (Streak, Huy hiệu)',
                        'Truy cập Thư viện Bài học cao cấp',
                    ])
            
            # --- TIER 3: PRO ---
            with ui.card().classes('w-full md:w-[280px] p-6 flex flex-col justify-between pricing-card transition-all duration-300 rounded-3xl border border-slate-200 shadow-sm relative overflow-hidden'):
                with ui.column().classes('w-full'):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('smart_toy', color='blue-500').classes('text-2xl')
                        ui.label('Gia sư AI (Pro)').classes('text-2xl font-bold text-slate-800')
                        
                    ui.label('Giải pháp trọn vẹn với Omni Tutor AI phản hồi tức thì.').classes('text-slate-500 text-sm mb-6 min-h-[40px]')
                    
                    with ui.row().classes('items-baseline gap-1 mb-2'):
                        ui.label('99.000').classes('text-4xl lg:text-5xl font-extrabold text-blue-600')
                        ui.label('VNĐ/tháng').classes('text-slate-500 font-medium')
                    ui.label('').classes('text-slate-400 text-xs mb-6 h-4') # padding
                    
                    ui.button('Dùng thử Pro', on_click=lambda: handle_upgrade('pro')).props('unelevated rounded no-caps').classes('w-full bg-blue-100 text-blue-700 border border-blue-200 py-3 font-semibold mb-6 hover:bg-blue-200')
                    
                    ui.separator().classes('mb-6')
                    
                    ui.label('Mọi lợi ích trong gói Plus, và:').classes('text-sm font-semibold text-slate-700 mb-4')
                    # Features
                    create_feature_list([
                        'Mở khóa Omni Tutor AI chuyên sâu',
                        'Sinh câu hỏi trắc nghiệm/tự luận không giới hạn',
                        'Phân tích tự động lỗ hổng kiến thức',
                        'Hỗ trợ giải thích bằng Voice AI',
                        'Gợi ý lộ trình học tập tối ưu cá nhân hóa'
                    ])

            # --- TIER 4: ULTRA ---
            with ui.card().classes('w-full md:w-[280px] p-6 flex flex-col justify-between pricing-card transition-all duration-300 rounded-3xl border border-slate-200 shadow-sm bg-gradient-to-b from-white to-slate-50'):
                with ui.column().classes('w-full'):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('diamond', color='purple-500').classes('text-2xl')
                        ui.label('Tối thượng (Ultra)').classes('text-2xl font-bold text-slate-800')
                        
                    ui.label('Truy cập các Model AI mạnh mẽ nhất và Mentorship.').classes('text-slate-500 text-sm mb-6 min-h-[40px]')
                    
                    with ui.row().classes('items-baseline gap-1 mb-2'):
                        ui.label('199.000').classes('text-4xl lg:text-5xl font-extrabold text-purple-600')
                        ui.label('VNĐ/tháng').classes('text-slate-500 font-medium')
                    ui.label('').classes('text-slate-400 text-xs mb-6 h-4') # padding
                    
                    ui.button('Nâng cấp Ultra', on_click=lambda: handle_upgrade('ultra')).props('unelevated rounded no-caps').classes('w-full bg-slate-800 text-white py-3 font-semibold mb-6 hover:bg-slate-900 transition-colors')
                    
                    ui.separator().classes('mb-6')
                    
                    ui.label('Mọi lợi ích trong gói Pro, và:').classes('text-sm font-semibold text-slate-700 mb-4')
                    # Features
                    create_feature_list([
                        'Sử dụng Model AI cao cấp (Gemini 1.5 Pro, GPT-4)',
                        'Ưu tiên tốc độ phản hồi cực nhanh',
                        'Báo cáo phân tích chuyên sâu hàng tuần',
                        'Ưu tiên hỗ trợ trực tiếp (1-1 Mentorship)',
                        'Huy hiệu Tối thượng trên Bảng xếp hạng'
                    ])

        # Phím Quay lại
        if is_standalone:
            ui.button('Trở về Trang chủ', on_click=lambda: ui.navigate.to('/app'), icon='arrow_back').props('outline rounded text-color="slate-600" no-caps').classes('mt-12 mb-8 font-semibold hover:bg-slate-200 transition-colors')
        

def create_feature_list(features):
    with ui.column().classes('w-full gap-3'):
        for feature in features:
            with ui.row().classes('w-full items-start gap-2 no-wrap'):
                ui.icon('check_circle', color='blue-500').classes('text-lg mt-0.5')
                ui.label(feature).classes('text-slate-600 text-sm leading-tight flex-1')

import asyncio
import random
import string
from nicegui import ui, app
from auth_service import is_logged_in

def handle_upgrade(tier):
    if not is_logged_in():
        ui.notify('Bạn cần đăng nhập để thực hiện nâng cấp.', type='warning')
        ui.navigate.to('/login')
        return
        
    if tier == 'free':
        dialog = ui.dialog()
        with dialog, ui.card().classes('p-6 md:p-8 rounded-2xl w-full max-w-sm items-center text-center'):
            with ui.element('div').classes('w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mb-4 mx-auto'):
                ui.icon('verified', color='emerald-500').classes('text-4xl')
            ui.label('Kích hoạt thành công!').classes('text-xl font-bold text-slate-800 mb-2')
            ui.label('Bạn đang sử dụng gói Miễn phí mặc định.').classes('text-sm text-slate-500 mb-6')
            
            app.storage.user['subscription_tier'] = 'free'
            if app.storage.user.get('role') == 'premium':
                app.storage.user['role'] = 'student'
                
            ui.button('Bắt đầu học', on_click=lambda: ui.run_javascript('window.location.href = "/app"')).props('unelevated rounded no-caps').classes('w-full bg-emerald-600 text-white font-bold py-2 hover:bg-emerald-700 transition-colors')
        dialog.open()
        return

    pricing_info = {
        'plus': {'name': 'Học giả (Plus)', 'price': '49.000', 'color': 'blue'},
        'pro': {'name': 'Gia sư AI (Pro)', 'price': '99.000', 'color': 'amber'},
        'ultra': {'name': 'Tối thượng (Ultra)', 'price': '199.000', 'color': 'purple'},
    }
    
    tier_data = pricing_info.get(tier)
    if not tier_data:
        return
        
    order_id = "PKT" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    dialog = ui.dialog().props('maximized')
    with dialog:
        container = ui.column().classes('w-full h-full bg-slate-50 items-center justify-start md:justify-center p-4 py-8 overflow-y-auto')
        
    def render_step(step, payment_method=None):
        container.clear()
        with container:
            if step == 1:
                # Step 1: Order Summary & Payment Selection
                with ui.row().classes('w-full max-w-4xl bg-white rounded-3xl shadow-xl overflow-hidden min-h-[500px] flex-nowrap flex-col md:flex-row'):
                    # Left: Summary
                    with ui.column().classes('w-full md:w-1/2 p-6 md:p-10 bg-slate-800 text-white justify-between'):
                        with ui.column():
                            ui.label('Tóm tắt đơn hàng').classes('text-2xl font-bold mb-6 text-white')
                            ui.label(f"Gói nâng cấp: {tier_data['name']}").classes('text-lg font-medium text-slate-300 mb-2')
                            ui.label('Chu kỳ: 1 Tháng').classes('text-slate-400 mb-8')
                            
                            with ui.row().classes('w-full items-end justify-between border-b border-slate-700 pb-4 mb-4'):
                                ui.label('Tạm tính').classes('text-slate-400')
                                ui.label(f"{tier_data['price']} VNĐ").classes('font-medium text-white')
                                
                            with ui.row().classes('w-full items-end justify-between'):
                                ui.label('Tổng cộng').classes('text-xl font-bold')
                                ui.label(f"{tier_data['price']} VNĐ").classes(f'text-3xl font-black text-{tier_data["color"]}-400')
                        
                        with ui.column().classes('mt-12'):
                            ui.label('Bảo mật thanh toán bởi PKT Pay 🔒').classes('text-xs text-slate-500')
                            
                    # Right: Payment Method
                    with ui.column().classes('w-full md:w-1/2 p-6 md:p-10 justify-between'):
                        with ui.column().classes('w-full'):
                            with ui.row().classes('w-full items-center justify-between mb-6'):
                                ui.label('Chọn phương thức thanh toán').classes('text-xl font-bold text-slate-800')
                                ui.button(icon='close', on_click=dialog.close).props('flat round color=grey-5')
                            
                            methods = [
                                {'id': 'vnpay', 'name': 'Quét mã VNPay', 'icon': 'qr_code_scanner', 'color': 'blue'},
                                {'id': 'momo', 'name': 'Ví MoMo', 'icon': 'account_balance_wallet', 'color': 'pink'},
                                {'id': 'card', 'name': 'Thẻ tín dụng / Ghi nợ', 'icon': 'credit_card', 'color': 'slate'},
                            ]
                            
                            selected_method = [methods[0]['id']]
                            
                            def set_method(m_id):
                                selected_method[0] = m_id
                                for m in methods:
                                    card_map[m['id']].classes(replace='border-blue-500 bg-blue-50' if m['id'] == m_id else 'border-slate-200 bg-white hover:border-slate-300')
                                    icon_map[m['id']].classes(replace=f"text-{m['color']}-500" if m['id'] == m_id else 'text-slate-400')
                                    
                            card_map = {}
                            icon_map = {}
                            
                            for m in methods:
                                is_sel = m['id'] == selected_method[0]
                                border_cls = 'border-blue-500 bg-blue-50' if is_sel else 'border-slate-200 bg-white hover:border-slate-300'
                                icon_cls = f"text-{m['color']}-500" if is_sel else 'text-slate-400'
                                
                                with ui.row().classes(f'w-full p-4 rounded-xl border-2 cursor-pointer transition-all items-center gap-3 mb-3 {border_cls}').on('click', lambda mid=m['id']: set_method(mid)) as card:
                                    icon = ui.icon(m['icon']).classes(f'text-2xl {icon_cls}')
                                    ui.label(m['name']).classes('font-bold text-slate-700 flex-grow')
                                    card_map[m['id']] = card
                                    icon_map[m['id']] = icon
                                    
                        ui.button('Tiếp tục thanh toán', on_click=lambda: render_step(2, selected_method[0])).props('unelevated rounded no-caps').classes('w-full bg-blue-600 text-white font-bold py-3 hover:bg-blue-700 shadow-md transition-colors')

            elif step == 2:
                # Step 2: QR Code / Payment execution
                with ui.card().classes('w-full max-w-md p-0 overflow-hidden rounded-3xl shadow-2xl bg-white'):
                    # Header
                    with ui.row().classes('w-full bg-slate-800 p-4 items-center justify-between'):
                        with ui.row().classes('items-center gap-2'):
                            ui.button(icon='arrow_back', on_click=lambda: render_step(1)).props('flat round color=white dense')
                            ui.label('Thanh toán an toàn').classes('font-bold text-white text-lg')
                        ui.button(icon='close', on_click=dialog.close).props('flat round color=white dense')
                    
                    with ui.column().classes('w-full p-8 items-center'):
                        ui.label(f"{'Ví MoMo' if payment_method == 'momo' else 'VNPay' if payment_method == 'vnpay' else 'Thẻ thanh toán'}").classes('text-lg font-bold text-slate-800 mb-1')
                        ui.label(f"Mã đơn: {order_id}").classes('text-sm text-slate-500 mb-6 font-mono')
                        
                        if payment_method in ['momo', 'vnpay']:
                            # Fake QR Code
                            qr_data = f"PKT_{tier}_{order_id}_{random.randint(1000,9999)}"
                            ui.image(f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={qr_data}&margin=10").classes('w-48 h-48 rounded-xl shadow-sm border border-slate-200 mb-6')
                            
                            ui.label('Mở ứng dụng ngân hàng hoặc ví điện tử để quét mã').classes('text-sm text-center text-slate-600 mb-2')
                            
                            with ui.row().classes('items-center gap-1 mb-8'):
                                ui.icon('timer', color='red-500').classes('animate-pulse')
                                ui.label('Đơn hàng hết hạn sau 10:00').classes('text-xs text-red-500 font-medium')
                        else:
                            ui.icon('credit_score', color='slate-300').classes('text-[100px] mb-6')
                            ui.label('Tính năng nhập thẻ đang bảo trì mô phỏng.').classes('text-sm text-center text-slate-500 mb-8')

                        # Simulate Payment Action (For Demo)
                        with ui.column().classes('w-full gap-2 border-t border-slate-100 pt-6'):
                            ui.label('Dành cho Giám khảo / Demo:').classes('text-[10px] uppercase font-bold text-slate-400 text-center w-full')
                            ui.button('Mô phỏng Đã Thanh Toán', on_click=lambda: render_step(3)).props('unelevated rounded no-caps outline').classes('w-full border-green-500 text-green-600 font-bold hover:bg-green-50')
            
            elif step == 3:
                # Step 3: Processing
                with ui.card().classes('w-full max-w-sm p-8 items-center rounded-3xl shadow-2xl bg-white'):
                    ui.spinner('ios', size='lg', color='blue-500').classes('mb-6')
                    ui.label('Đang xác nhận giao dịch...').classes('text-lg font-bold text-slate-800 mb-2')
                    ui.label('Vui lòng không đóng cửa sổ này.').classes('text-sm text-slate-500')
                    
                    # Triggers step 4 after sleep
                    async def process():
                        await asyncio.sleep(2.5)
                        render_step(4)
                    ui.timer(0.1, process, once=True)
                    
            elif step == 4:
                # Step 4: Success
                with ui.card().classes('w-full max-w-md p-8 items-center rounded-3xl shadow-2xl bg-white text-center'):
                    with ui.element('div').classes('w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6 mx-auto'):
                        ui.icon('check_circle', color='green-500').classes('text-5xl')
                        
                    ui.label('Thanh toán thành công!').classes('text-2xl font-black text-slate-800 mb-2')
                    ui.label(f"Chào mừng bạn đến với gói {tier_data['name']}.").classes('text-slate-600 mb-6')
                    
                    with ui.row().classes('w-full p-4 bg-slate-50 rounded-xl mb-8 items-center justify-between border border-slate-100'):
                        ui.label('Mã giao dịch').classes('text-sm text-slate-500')
                        ui.label(order_id).classes('font-bold text-slate-700 font-mono')
                        
                    # Cập nhật quyền
                    app.storage.user['subscription_tier'] = tier
                    if tier in ['plus', 'pro', 'ultra']:
                        app.storage.user['role'] = 'premium'
                        
                    ui.button('Bắt đầu trải nghiệm ngay', on_click=lambda: ui.run_javascript('window.location.href = "/app"')).props('unelevated rounded no-caps').classes('w-full bg-green-600 text-white font-bold py-3 hover:bg-green-700 shadow-md transition-colors')

    dialog.open()
    render_step(1)

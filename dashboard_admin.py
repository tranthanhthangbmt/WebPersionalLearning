from nicegui import ui

def build_dashboard_admin_ui():
    with ui.column().classes('w-full p-8 bg-slate-50 min-h-screen'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-6'):
            with ui.column().classes('gap-1'):
                ui.label('Báo Cáo Tổng Hợp (Report)').classes('text-3xl font-extrabold text-slate-800 tracking-tight')
                ui.label('Dữ liệu mô phỏng từ 50 học sinh lớp 6 tại THCS [Tên Trường] trong 4 tuần').classes('text-sm text-slate-500 font-medium')
            
            # Action buttons
            with ui.row().classes('gap-4'):
                ui.button('Xuất báo cáo PDF', icon='picture_as_pdf').props('outline color=primary')
                ui.button('Cập nhật dữ liệu', icon='refresh').props('color=primary unelevated')

        # Top KPI Cards
        with ui.row().classes('w-full grid grid-cols-4 gap-6 mb-8'):
            def kpi_card(title, value, subtext, icon, color):
                with ui.card().classes(f'w-full p-6 bg-white border-l-4 border-{color}-500 shadow-sm rounded-xl'):
                    with ui.row().classes('w-full justify-between items-start mb-2'):
                        ui.label(title).classes('text-sm font-bold text-slate-500 uppercase')
                        ui.icon(icon, color=color, size='sm').classes('bg-slate-50 p-2 rounded-full')
                    ui.label(value).classes('text-3xl font-black text-slate-800')
                    ui.label(subtext).classes(f'text-xs font-bold text-{color}-600 mt-2 bg-{color}-50 px-2 py-1 rounded inline-block')

            kpi_card('Tổng Học Sinh', '50', '+100% (so với đầu kỳ)', 'group', 'blue')
            kpi_card('TG Học Trung Bình', '42 Phút', '+280% (so với baseline 15p)', 'schedule', 'emerald')
            kpi_card('Số Lỗ Hổng (TB)', '4.5', 'Được AI phát hiện / học sinh', 'troubleshoot', 'orange')
            kpi_card('Điểm Cải Thiện', '+2.1', 'Sau 4 tuần (Từ 6.2 lên 8.3)', 'trending_up', 'purple')

        # Charts Row 1
        with ui.row().classes('w-full grid grid-cols-2 gap-6 mb-6'):
            # Engagement Chart
            with ui.card().classes('w-full p-6 shadow-sm rounded-xl bg-white'):
                ui.label('Tăng Trưởng Thời Gian Học (Engagement)').classes('text-lg font-bold text-slate-700 mb-4')
                ui.echart({
                    'tooltip': {'trigger': 'axis'},
                    'legend': {'data': ['Phương pháp cũ', 'Graph 3D & AI Tutor']},
                    'xAxis': {'type': 'category', 'data': ['Tuần 1', 'Tuần 2', 'Tuần 3', 'Tuần 4']},
                    'yAxis': {'type': 'value', 'name': 'Phút / Ngày'},
                    'series': [
                        {
                            'name': 'Phương pháp cũ',
                            'type': 'line',
                            'data': [15, 14, 16, 15],
                            'color': '#cbd5e1',
                            'smooth': True,
                            'lineStyle': {'width': 3, 'type': 'dashed'}
                        },
                        {
                            'name': 'Graph 3D & AI Tutor',
                            'type': 'line',
                            'data': [25, 32, 40, 42],
                            'color': '#10b981',
                            'smooth': True,
                            'areaStyle': {'opacity': 0.1},
                            'lineStyle': {'width': 4}
                        }
                    ]
                }).classes('w-full h-72')

            # Retention Chart
            with ui.card().classes('w-full p-6 shadow-sm rounded-xl bg-white'):
                ui.label('Tỷ Lệ Giữ Chân Người Dùng (Retention Rate)').classes('text-lg font-bold text-slate-700 mb-4')
                ui.echart({
                    'tooltip': {'trigger': 'axis', 'formatter': '{b}: {c}%'},
                    'xAxis': {'type': 'category', 'data': ['Day 1', 'Day 3', 'Day 7', 'Day 14', 'Day 30']},
                    'yAxis': {'type': 'value', 'max': 100, 'name': 'Tỷ lệ (%)'},
                    'series': [
                        {
                            'data': [95, 88, 82, 75, 68],
                            'type': 'bar',
                            'color': '#3b82f6',
                            'itemStyle': {'borderRadius': [4, 4, 0, 0]},
                            'label': {'show': True, 'position': 'top', 'formatter': '{c}%'}
                        }
                    ]
                }).classes('w-full h-72')

        # Charts Row 2
        with ui.row().classes('w-full grid grid-cols-3 gap-6'):
            # Knowledge Gap Recovery
            with ui.card().classes('col-span-1 p-6 shadow-sm rounded-xl bg-white'):
                ui.label('Tỷ Lệ Lấp Đầy Lỗ Hổng').classes('text-lg font-bold text-slate-700 mb-4')
                ui.echart({
                    'tooltip': {'trigger': 'item'},
                    'legend': {'bottom': '0%', 'left': 'center'},
                    'series': [
                        {
                            'type': 'pie',
                            'radius': ['40%', '70%'],
                            'avoidLabelOverlap': False,
                            'itemStyle': {'borderRadius': 10, 'borderColor': '#fff', 'borderWidth': 2},
                            'label': {'show': False},
                            'data': [
                                {'value': 76, 'name': 'Đã lấp đầy (Xanh)', 'itemStyle': {'color': '#10b981'}},
                                {'value': 24, 'name': 'Cần ôn tập (Cam)', 'itemStyle': {'color': '#f59e0b'}}
                            ]
                        }
                    ]
                }).classes('w-full h-64')

            # Test Score Comparison
            with ui.card().classes('col-span-2 p-6 shadow-sm rounded-xl bg-white'):
                ui.label('Sự Tiến Bộ Qua Bài Kiểm Tra (Test Scores)').classes('text-lg font-bold text-slate-700 mb-4')
                ui.echart({
                    'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
                    'legend': {'data': ['Pre-test (Đầu vào)', 'Post-test (Sau 4 tuần)']},
                    'xAxis': {'type': 'value', 'max': 10},
                    'yAxis': {'type': 'category', 'data': ['Nhóm Đối Chứng', 'Nhóm Thử Nghiệm']},
                    'series': [
                        {
                            'name': 'Pre-test (Đầu vào)',
                            'type': 'bar',
                            'data': [6.1, 6.2],
                            'color': '#94a3b8'
                        },
                        {
                            'name': 'Post-test (Sau 4 tuần)',
                            'type': 'bar',
                            'data': [6.5, 8.3],
                            'color': '#8b5cf6'
                        }
                    ]
                }).classes('w-full h-64')

        # Footer / Insights
        with ui.row().classes('w-full mt-6'):
            with ui.card().classes('w-full p-6 shadow-sm rounded-xl bg-indigo-50 border border-indigo-100'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('lightbulb', size='sm', color='indigo')
                    ui.label('AI Insights & Khuyến nghị').classes('text-lg font-bold text-indigo-900')
                ui.label('Dữ liệu cho thấy phương pháp Gamification kết hợp 3D Graph đã gia tăng đáng kể thời gian tương tác tự nguyện của học sinh (gấp gần 3 lần). Tính năng Gia sư AI (Omni) xác định chính xác các node bị hổng (knowledge gaps) giúp việc học trở nên có chủ đích, trực tiếp kéo điểm số thực tế tăng trưởng +2.1 điểm chỉ trong vòng 1 tháng thử nghiệm.').classes('text-indigo-800 leading-relaxed')


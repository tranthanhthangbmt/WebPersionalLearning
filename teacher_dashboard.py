from nicegui import ui
from database import engine, Session, select, User

def register_teacher_dashboard():
    @ui.page('/teacher')
    async def teacher_dashboard():
        ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">')
        ui.query('body').classes('bg-slate-50 font-[Inter]')

        with ui.header().classes('bg-white text-slate-800 shadow-md h-16 items-center px-6 border-b-4 border-indigo-500'):
            ui.icon('school', size='1.5rem').classes('text-indigo-600 mr-2')
            ui.label('Cổng Giáo Viên').classes('text-xl font-bold text-gray-800')
            ui.space()
            ui.button('Đăng xuất', on_click=lambda: ui.navigate.to('/')).props('flat no-caps text-gray-500')

        with ui.row().classes('max-w-7xl mx-auto w-full p-6 mt-4 gap-6 items-start'):
            # Sidebar
            with ui.column().classes('w-64 gap-2'):
                ui.button('Tổng Quan Lớp', icon='dashboard').classes('w-full justify-start bg-indigo-50 text-indigo-700 font-bold shadow-none').props('flat')
                ui.button('Bản Đồ Lỗ Hổng', icon='map').classes('w-full justify-start text-gray-600 hover:bg-gray-100 shadow-none').props('flat')
                ui.button('Quản Lý Bài Tập', icon='assignment').classes('w-full justify-start text-gray-600 hover:bg-gray-100 shadow-none').props('flat')
                ui.button('Xuất Log (xAPI)', icon='download').classes('w-full justify-start text-gray-600 hover:bg-gray-100 shadow-none').props('flat')
            
            # Main Content
            with ui.column().classes('flex-grow gap-6'):
                # Header Section
                with ui.row().classes('w-full bg-white p-6 rounded-3xl shadow-sm border border-gray-100 items-center justify-between'):
                    with ui.column():
                        ui.label('Khối Lớp 10A1').classes('text-2xl font-black text-gray-800')
                        ui.label('Giáo viên: Nguyễn Văn A | Sĩ số: 35').classes('text-gray-500')
                    
                    ui.button('Thêm Học Sinh', icon='add').classes('bg-indigo-600 text-white rounded-full font-bold px-6 py-2').props('no-caps')

                # Heatmap Section (Aggregated weaknesses)
                with ui.card().classes('w-full p-6 rounded-3xl shadow-sm border border-gray-100'):
                    ui.label('Bản Đồ Lỗ Hổng Lớp (Heatmap)').classes('text-xl font-bold text-gray-800 mb-2')
                    ui.label('Những phần kiến thức học sinh sai nhiều nhất sẽ hiện màu Đỏ Hơi Đậm. Giáo viên nên ưu tiên ôn tập các phần này.').classes('text-gray-500 text-sm mb-4')
                    
                    # Mock ECharts Heatmap for concepts
                    ui.echart({
                        'xAxis': {'type': 'category', 'data': ['Unit 1', 'Unit 2', 'Unit 3', 'Unit 4', 'Unit 5', 'Unit 6']},
                        'yAxis': {'type': 'category', 'data': ['Nhóm Giỏi', 'Nhóm Khá', 'Nhóm Yếu']},
                        'visualMap': {
                            'min': 0, 'max': 100, 
                            'calculable': True, 'orient': 'horizontal', 'left': 'center', 'bottom': '0%',
                            'inRange': {'color': ['#e0f2fe', '#0ea5e9', '#ef4444']} # Light blue to Red (weakness)
                        },
                        'series': [{
                            'name': 'Tỉ lệ sai',
                            'type': 'heatmap',
                            'data': [
                                [0, 0, 10], [1, 0, 15], [2, 0, 8], [3, 0, 5], [4, 0, 2], [5, 0, 12],
                                [0, 1, 20], [1, 1, 35], [2, 1, 15], [3, 1, 10], [4, 1, 8], [5, 1, 25],
                                [0, 2, 80], [1, 2, 95], [2, 2, 60], [3, 2, 75], [4, 2, 45], [5, 2, 88]
                            ],
                            'label': {'show': True}
                        }]
                    }).classes('w-full h-80')

                # Student List
                with ui.card().classes('w-full p-6 rounded-3xl shadow-sm border border-gray-100'):
                    ui.row().classes('justify-between items-center w-full mb-4')
                    ui.label('Danh sách Học sinh cần lưu ý').classes('text-xl font-bold text-gray-800')
                    
                    # Mock table
                    columns = [
                        {'name': 'name', 'label': 'Họ Tên', 'field': 'name', 'required': True, 'align': 'left'},
                        {'name': 'score', 'label': 'Điểm BQ', 'field': 'score', 'sortable': True},
                        {'name': 'status', 'label': 'Cảnh báo AI', 'field': 'status', 'align': 'left'},
                    ]
                    rows = [
                        {'name': 'Trần Thị B', 'score': 4.5, 'status': 'Nguy cơ hổng Unit 2'},
                        {'name': 'Lê Văn C', 'score': 5.0, 'status': 'Dấu hiệu Burnout (Pin yếu liên tục)'},
                        {'name': 'Phạm D', 'score': 6.2, 'status': 'Cần đẩy mạnh luyện tập Socratic'},
                    ]
                    
                    ui.table(columns=columns, rows=rows, row_key='name').classes('w-full shadow-none border rounded-xl')

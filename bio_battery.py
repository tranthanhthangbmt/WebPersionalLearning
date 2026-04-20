from nicegui import ui

class BioBattery:
    def __init__(self, container):
        with container:
            self.battery_container = ui.html('''
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <svg width="60" height="120" viewBox="0 0 100 200" style="filter: drop-shadow(0 0 8px rgba(76,175,80,0.5)); transition: all 0.5s;" id="bio-battery-svg">
                        <defs>
                            <linearGradient id="batteryGrad" x1="0%" y1="100%" x2="0%" y2="0%">
                                <stop offset="0%" stop-color="#4caf50" id="stop1"/>
                                <stop offset="100%" stop-color="#81c784" id="stop2"/>
                            </linearGradient>
                        </defs>
                        <!-- Vỏ pin -->
                        <rect x="20" y="20" width="60" height="170" rx="10" 
                              fill="none" stroke="#888" stroke-width="6"/>
                        <!-- Núm pin -->
                        <rect x="35" y="5" width="30" height="15" rx="4" 
                              fill="#888"/>
                        <!-- Lõi pin (Mực pin) -->
                        <!-- Transform-origin: center bottom để mực pin tụt từ trên xuống -->
                        <rect x="25" y="25" width="50" height="160" rx="6" 
                              fill="url(#batteryGrad)" id="battery-core" 
                              style="transform-origin: 50% 185px; transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);"/>
                    </svg>
                </div>
            ''')
            self.label = ui.label('100%').classes('text-sm font-bold mt-2 text-center w-full text-green-400')
            self.dialog_shown = False
            
    def update(self, fatigue_level):
        """
        fatigue_level: 0.0 (Khoẻ) -> 1.0 (Kiệt sức)
        Energy = 1.0 - fatigue_level
        """
        energy = max(0.0, min(1.0, 1.0 - fatigue_level))
        percentage = int(energy * 100)
        
        color1 = '#4caf50'  # Green
        color2 = '#81c784'
        shadow = 'rgba(76,175,80,0.5)'
        text_color = 'text-green-400'
        
        if energy <= 0.5:
            color1 = '#ff9800'  # Orange
            color2 = '#ffb74d'
            shadow = 'rgba(255,152,0,0.5)'
            text_color = 'text-orange-400'
        if energy < 0.2:
            color1 = '#f44336'  # Red
            color2 = '#e57373'
            shadow = 'rgba(244,67,54,0.8)'
            text_color = 'text-red-400'
            
        animation = ""
        if energy < 0.2:
            animation = "animation: shake 0.5s infinite;"
            
        ui.run_javascript(f'''
            var core = document.getElementById('battery-core');
            var svg = document.getElementById('bio-battery-svg');
            var s1 = document.getElementById('stop1');
            var s2 = document.getElementById('stop2');
            
            if(core) {{
                core.style.transform = "scaleY({energy})";
            }}
            if (s1 && s2) {{
                s1.setAttribute('stop-color', '{color1}');
                s2.setAttribute('stop-color', '{color2}');
            }}
            if (svg) {{
                svg.style.filter = "drop-shadow(0 0 10px {shadow})";
                svg.style.cssText = svg.style.cssText.replace(/animation:.*?;/g, '') + '{animation}';
            }}
        ''')
        
        self.label.set_text(f'{percentage}%')
        self.label.classes(remove='text-green-400 text-orange-400 text-red-400', add=text_color)
        
        ui.add_head_html('''
            <style>
            @keyframes shake {
              0% { transform: translate(1px, 1px) rotate(0deg); }
              10% { transform: translate(-1px, -2px) rotate(-1deg); }
              20% { transform: translate(-3px, 0px) rotate(1deg); }
              30% { transform: translate(3px, 2px) rotate(0deg); }
              40% { transform: translate(1px, -1px) rotate(1deg); }
              50% { transform: translate(-1px, 2px) rotate(-1deg); }
              60% { transform: translate(-3px, 1px) rotate(0deg); }
              70% { transform: translate(3px, 1px) rotate(-1deg); }
              80% { transform: translate(-1px, -1px) rotate(1deg); }
              90% { transform: translate(1px, 2px) rotate(0deg); }
              100% { transform: translate(1px, -2px) rotate(-1deg); }
            }
            </style>
        ''')
        
        # Cảnh báo soft lock khi pin yếu
        if energy < 0.2 and not self.dialog_shown:
            self.show_soft_lock()
            
    def show_soft_lock(self):
        self.dialog_shown = True
        with ui.dialog() as dialog, ui.card().classes('items-center p-8 bg-gray-900 border border-red-500 rounded-2xl shadow-2xl').style('max-width: 400px;'):
            ui.icon('battery_alert', size='4rem', color='red')
            ui.label('NGUY CẤP!').classes('text-2xl font-extrabold text-red-500 mb-2 mt-2')
            
            ui.label('BioBattery của bạn đang ở mức báo động (<20%). Nhồi nhét kiến thức lúc này làm giảm 80% tỷ lệ lưu trữ dài hạn!').classes('text-center text-gray-300 text-sm mb-4 leading-relaxed')
            ui.label('🧘 Hãy nghỉ ngơi 5 phút hoặc xem Video giải trí.').classes('text-center text-amber-400 text-sm font-bold mb-6')
            
            with ui.row().classes('w-full gap-3 justify-center'):
                ui.button('😴 Đi nghỉ 5 phút', on_click=dialog.close).classes('bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded-xl').props('no-caps')
                ui.button('Cố chấp học tiếp', on_click=dialog.close).classes('bg-gray-800 hover:bg-gray-700 text-gray-400 py-2 px-4 rounded-xl').props('flat no-caps')
                
        dialog.open()

from nicegui import ui

class BioBattery:
    """
    MIT-Standard Bio Battery Widget
    Hiển thị mức năng lượng nhận thức của sinh viên dưới dạng pin sinh học.
    fatigue_level: 0.0 (Khỏe) → 1.0 (Kiệt sức)
    """

    # CSS injected once per session
    _css_injected = False

    @staticmethod
    def _inject_css():
        if BioBattery._css_injected:
            return
        BioBattery._css_injected = True
        ui.add_head_html('''
        <style>
        /* ═══════ Bio Battery MIT Premium CSS ═══════ */
        @keyframes bb-pulse { 0%,100%{opacity:0.6} 50%{opacity:1} }
        @keyframes bb-glow  { 0%,100%{filter:drop-shadow(0 0 6px var(--bb-glow))} 50%{filter:drop-shadow(0 0 14px var(--bb-glow))} }
        @keyframes bb-shake { 0%,100%{transform:translateX(0)} 10%{transform:translateX(-2px)} 20%{transform:translateX(2px)} 30%{transform:translateX(-2px)} 40%{transform:translateX(2px)} 50%{transform:translateX(0)} }
        @keyframes bb-bubble {
            0%   { transform: translateY(0) scale(1); opacity: 0.7; }
            50%  { transform: translateY(-30px) scale(1.2); opacity: 0.3; }
            100% { transform: translateY(-60px) scale(0.6); opacity: 0; }
        }
        @keyframes bb-wave {
            0%   { d: path("M 0 8 Q 15 4, 30 8 T 60 8 L 60 12 L 0 12 Z"); }
            50%  { d: path("M 0 8 Q 15 12, 30 8 T 60 8 L 60 12 L 0 12 Z"); }
            100% { d: path("M 0 8 Q 15 4, 30 8 T 60 8 L 60 12 L 0 12 Z"); }
        }
        .bb-container {
            --bb-glow: rgba(52, 211, 153, 0.4);
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            padding: 16px 12px;
        }
        .bb-svg { animation: bb-glow 3s ease-in-out infinite; transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
        .bb-svg.shake { animation: bb-shake 0.4s ease-in-out infinite, bb-glow 1s ease-in-out infinite; }
        .bb-core { transition: all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1); }
        .bb-wave-path { animation: bb-wave 2.5s ease-in-out infinite; }
        .bb-bubble { animation: bb-bubble 2s ease-out infinite; }
        .bb-info { display: flex; flex-direction: column; align-items: center; gap: 2px; }
        .bb-pct { font-size: 22px; font-weight: 900; letter-spacing: -0.5px; transition: color 0.4s; }
        .bb-status { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; transition: color 0.4s; }
        .bb-bar-bg { width: 100%; height: 5px; border-radius: 3px; background: rgba(0,0,0,0.06); overflow: hidden; margin-top: 4px; }
        .bb-bar-fill { height: 100%; border-radius: 3px; transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.4s; }
        .bb-tip { font-size: 10px; color: #94a3b8; text-align: center; line-height: 1.4; max-width: 160px; transition: color 0.4s; margin-top: 2px; }
        </style>
        ''')

    def __init__(self, container):
        BioBattery._inject_css()
        self.dialog_shown = False
        with container:
            self.widget = ui.html(self._build_html(1.0))

    def _build_html(self, energy):
        """Build the full battery SVG + info HTML."""
        pct = int(energy * 100)
        # Color scheme based on energy level
        if energy > 0.5:
            c1, c2, glow = '#34d399', '#6ee7b7', 'rgba(52,211,153,0.4)'
            status = 'TUYỆT VỜI'
            tip = '🧠 Năng lượng dồi dào! Thời điểm vàng để học.'
            pct_color, status_color = '#059669', '#10b981'
            bar_bg = 'linear-gradient(90deg, #34d399, #6ee7b7)'
            shake_cls = ''
        elif energy > 0.2:
            c1, c2, glow = '#fbbf24', '#fcd34d', 'rgba(251,191,36,0.4)'
            status = 'CẦN NGHỈ'
            tip = '⚡ Hiệu suất giảm 30%. Nên nghỉ 5 phút.'
            pct_color, status_color = '#d97706', '#f59e0b'
            bar_bg = 'linear-gradient(90deg, #fbbf24, #fcd34d)'
            shake_cls = ''
        else:
            c1, c2, glow = '#f87171', '#fca5a5', 'rgba(248,113,113,0.6)'
            status = 'KIỆT SỨC'
            tip = '🛑 Ngừng học ngay! Nhồi nhét giảm 80% ghi nhớ.'
            pct_color, status_color = '#dc2626', '#ef4444'
            bar_bg = 'linear-gradient(90deg, #f87171, #fca5a5)'
            shake_cls = ' shake'

        # Fluid fill height: max fill area is y=22 to y=148 (126 units)
        fill_h = max(2, energy * 126)
        fill_y = 148 - fill_h + 22

        # Bubbles (only when energy > 0.3)
        bubbles = ''
        if energy > 0.3:
            bubbles = f'''
            <circle class="bb-bubble" cx="38" cy="{fill_y+fill_h-10}" r="2" fill="{c2}" opacity="0.5" style="animation-delay:0s"/>
            <circle class="bb-bubble" cx="50" cy="{fill_y+fill_h-20}" r="1.5" fill="{c2}" opacity="0.4" style="animation-delay:0.7s"/>
            <circle class="bb-bubble" cx="58" cy="{fill_y+fill_h-8}" r="2.5" fill="{c2}" opacity="0.3" style="animation-delay:1.4s"/>
            '''

        # Wave on top of fluid
        wave_y = fill_y - 6
        wave = ''
        if energy > 0.05:
            wave = f'''
            <g transform="translate(22, {wave_y})">
                <path class="bb-wave-path" fill="{c1}" opacity="0.5"
                      d="M 0 8 Q 15 4, 30 8 T 60 8 L 60 12 L 0 12 Z"/>
            </g>
            '''

        # Segment lines (4 segments)
        segments = ''
        for i in range(1, 4):
            sy = 22 + i * 31.5
            segments += f'<line x1="24" y1="{sy}" x2="78" y2="{sy}" stroke="rgba(255,255,255,0.15)" stroke-width="0.5" stroke-dasharray="2,2"/>'

        return f'''
        <div class="bb-container" style="--bb-glow: {glow};">
            <svg class="bb-svg{shake_cls}" width="65" height="160" viewBox="0 0 100 175">
                <defs>
                    <linearGradient id="bbGrad" x1="0%" y1="100%" x2="0%" y2="0%">
                        <stop offset="0%" stop-color="{c1}"/>
                        <stop offset="100%" stop-color="{c2}"/>
                    </linearGradient>
                    <linearGradient id="bbShell" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#e2e8f0"/>
                        <stop offset="100%" stop-color="#cbd5e1"/>
                    </linearGradient>
                    <clipPath id="bbClip">
                        <rect x="24" y="22" width="54" height="126" rx="8"/>
                    </clipPath>
                    <filter id="bbInner" x="-10%" y="-10%" width="120%" height="120%">
                        <feGaussianBlur in="SourceAlpha" stdDeviation="2" result="blur"/>
                        <feOffset dy="2" result="offsetBlur"/>
                        <feComposite in="SourceGraphic" in2="offsetBlur" operator="over"/>
                    </filter>
                </defs>

                <!-- Shell -->
                <rect x="20" y="18" width="62" height="134" rx="12"
                      fill="none" stroke="url(#bbShell)" stroke-width="4"/>
                <!-- Inner shadow -->
                <rect x="24" y="22" width="54" height="126" rx="8"
                      fill="rgba(0,0,0,0.03)"/>

                <!-- Terminal -->
                <rect x="38" y="6" width="26" height="14" rx="5"
                      fill="url(#bbShell)" stroke="#cbd5e1" stroke-width="1"/>
                <rect x="42" y="8" width="18" height="6" rx="3" fill="{c1}" opacity="0.6"/>

                <!-- Fluid fill (clipped) -->
                <g clip-path="url(#bbClip)">
                    <rect x="24" y="{fill_y}" width="54" height="{fill_h}" rx="0"
                          fill="url(#bbGrad)" class="bb-core" opacity="0.85"/>
                    {wave}
                    {bubbles}
                </g>

                <!-- Segment lines -->
                {segments}

                <!-- Percentage text inside -->
                <text x="51" y="95" text-anchor="middle" font-size="18" font-weight="900"
                      fill="{'white' if energy > 0.4 else pct_color}" opacity="{'0.9' if energy > 0.4 else '1'}"
                      font-family="system-ui, -apple-system, sans-serif">{pct}%</text>
            </svg>

            <div class="bb-info">
                <div class="bb-status" style="color: {status_color}">{status}</div>
                <div class="bb-bar-bg">
                    <div class="bb-bar-fill" style="width: {pct}%; background: {bar_bg};"></div>
                </div>
                <div class="bb-tip">{tip}</div>
            </div>
        </div>
        '''

    def update(self, fatigue_level):
        """
        fatigue_level: 0.0 (Khỏe) → 1.0 (Kiệt sức)
        Energy = 1.0 - fatigue_level
        """
        energy = max(0.0, min(1.0, 1.0 - fatigue_level))
        self.widget.content = self._build_html(energy)

        # Low energy warning
        if energy < 0.2 and not self.dialog_shown:
            self.show_soft_lock()

    def show_soft_lock(self):
        self.dialog_shown = True
        with ui.dialog() as dialog, ui.card().classes(
            'items-center p-8 rounded-3xl shadow-2xl'
        ).style(
            'max-width: 420px; background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%); border: 1px solid rgba(248,113,113,0.3);'
        ):
            # Animated icon
            ui.html('''
                <div style="position:relative; width:80px; height:80px; margin: 0 auto;">
                    <div style="position:absolute; inset:0; border-radius:50%; background: rgba(248,113,113,0.15); animation: bb-pulse 1.5s ease-in-out infinite;"></div>
                    <div style="display:flex; align-items:center; justify-content:center; width:80px; height:80px; border-radius:50%; background: linear-gradient(135deg, #dc2626, #ef4444); box-shadow: 0 0 30px rgba(248,113,113,0.4);">
                        <span style="font-size: 36px;">🔋</span>
                    </div>
                </div>
            ''')

            ui.label('CẢNH BÁO NĂNG LƯỢNG').classes(
                'text-xl font-black text-red-400 mt-4 tracking-wider'
            )

            ui.html('''
                <div style="background: rgba(248,113,113,0.08); border: 1px solid rgba(248,113,113,0.2); border-radius: 12px; padding: 16px; margin: 12px 0; text-align: center;">
                    <p style="color: #fca5a5; font-size: 13px; line-height: 1.6; margin: 0;">
                        BioBattery dưới <b style="color:#f87171">20%</b>. Theo nghiên cứu của MIT,
                        nhồi nhét kiến thức lúc này làm <b style="color:#f87171">giảm 80%</b> tỷ lệ lưu trữ dài hạn.
                    </p>
                </div>
            ''')

            ui.html('''
                <div style="display:flex; align-items:center; gap:8px; padding:10px 16px; background: rgba(251,191,36,0.08); border-radius: 10px; border: 1px solid rgba(251,191,36,0.15);">
                    <span style="font-size:20px;">🧘</span>
                    <span style="color: #fcd34d; font-size: 12px; font-weight: 600;">Nghỉ 5 phút để hồi phục 40% năng lượng nhận thức</span>
                </div>
            ''')

            with ui.row().classes('w-full gap-3 justify-center mt-4'):
                ui.button('😴 Nghỉ ngơi 5 phút', on_click=dialog.close).classes(
                    'bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-bold py-2.5 px-5 rounded-xl shadow-lg hover:scale-105 transition-all'
                ).props('no-caps')
                ui.button('Tiếp tục học', on_click=dialog.close).classes(
                    'text-slate-400 py-2.5 px-4 rounded-xl'
                ).props('flat no-caps')

        dialog.open()

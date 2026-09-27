from nicegui import ui, run, app
import re
import os
import asyncio
from utils import get_video_base_url
from gemini_helper import get_chat_model

# ═══ AIUD Course: Actual GitHub folder paths for slide images ═══
# The AIUD repo stores images under Module_1-6/Video/Module_X/<lesson_folder>/images/
# Verified from data/lessons.js on 2026-04-24
AIUD_IMAGE_FOLDER_MAP = {
    "c1.1": "Module_1-6/Video/Module_1/Phần 1_Khai_phá_Đại_dương_Số",
    "c1.2": "Module_1-6/Video/Module_1/Phần 2_",
    "c1.3": "Module_1-6/Video/Module_1/Phần 3_LÀM_CHỦ_DỮ_LIỆU_SỐ",
    "c2.1": "Module_1-6/Video/Module_2/Phần 1_Hành trình trở thành công dân số",
    "c2.2": "Module_1-6/Video/Module_2/Phần 2_Làm chủ tương tác",
    "c3.1": "Module_1-6/Video/Module_3/Phần 1_Digital_Content_Development",
    "c3.2": "Module_1-6/Video/Module_3/Phần 2_Digital_Content_Repurposing",
    "c3.3": "Module_1-6/Video/Module_3/Phần 3_Digital_Rights_and_Programming",
    "c4.1": "Module_1-6/Video/Module_4/Phần 1_M4_T1_Digital_Safety_Blueprint",
    "c4.2": "Module_1-6/Video/Module_4/Phần 2_M4_T2_An_toàn_Mạng_và_An_sinh_số",
    "c4.3": "Module_1-6/Video/Module_4/Phần 3_M4_T3_Digital_Sustainability",
    "c5.1": "Module_1-6/Video/Module_5",
    "c6.1": "Module_1-6/Video/Module_6/Phần 1_M6_P1_AI_Foundations_and_Applications",
    "c6.2": "Module_1-6/Video/Module_6/Phần 2_M6_P2_AI_Application_Blueprint",
}

class AIVideoPlayer:
    def __init__(self, container, concept_name, script_path, folder_name=None, script_content=None, on_back=None):
        self.container = container
        self.on_back = on_back
        self.concept_name = concept_name
        self.script_path = script_path
        self.script_content = script_content
        self.base_url = get_video_base_url()
        
        # Normalize base url
        if self.base_url:
            self.base_url = self.base_url.strip()
            if not self.base_url.endswith('/'): self.base_url += '/'
        else:
            self.base_url = "https://tranthanhthangbmt.github.io/ThuongMaiDienTu_3TC/"
            
        # Resolve folder name
        if folder_name:
            self.folder_name = folder_name
        elif self.script_path and os.path.exists(os.path.dirname(self.script_path)):
            self.folder_name = os.path.basename(os.path.dirname(self.script_path))
        else:
            # Fallback parsing
            ch_match = re.search(r'(?:Chương|Chuong)[_\s-]*(\d+)', concept_name, re.IGNORECASE)
            ls_match = re.search(r'(?:Tiết|Tiet)[_\s-]*(\d+)', concept_name, re.IGNORECASE)
            if ch_match or ls_match:
                ch_num = ch_match.group(1) if ch_match else "1"
                ls_num = ls_match.group(1) if ls_match else "1"
                self.folder_name = f"Chuong_{ch_num}_Tiet_{ls_num}"
            else:
                self.folder_name = 'unknown'

        # Always check if we should override base_url for AI course
        if self.folder_name and re.match(r'^c\d+\.\d+$', self.folder_name):
            self.base_url = "https://tranthanhthangbmt.github.io/AIUD_March2026/"
            
        # Check if local images directory exists to determine asset base mode
        if self.script_path and os.path.exists(os.path.dirname(self.script_path)):
            parent_dir = os.path.dirname(self.script_path)
        else:
            parent_dir = os.path.join(os.getcwd(), 'DB', 'Video', self.folder_name)
            
        local_images_dir = os.path.join(parent_dir, 'images')
        
        if os.path.exists(local_images_dir):
            self.asset_base_url = f"/Video/{self.folder_name}/"
            print(f"[AIVideoPlayer] Local Asset Mode: {self.asset_base_url}")
        elif self.folder_name in AIUD_IMAGE_FOLDER_MAP:
            # AIUD course: use the correct nested folder path from GitHub
            import urllib.parse
            aiud_folder = AIUD_IMAGE_FOLDER_MAP[self.folder_name]
            encoded_folder = urllib.parse.quote(aiud_folder, safe='/')
            self.asset_base_url = f"https://tranthanhthangbmt.github.io/AIUD_March2026/{encoded_folder}/"
            print(f"[AIVideoPlayer] AIUD Remote Asset Mode: {self.asset_base_url}")
        else:
            clean_base = self.base_url.rstrip('/')
            self.asset_base_url = f"{clean_base}/Video/{self.folder_name}/"
            print(f"[AIVideoPlayer] Remote Github Asset Mode: {self.asset_base_url}")

        self.slides = self.parse_script(self.script_path)
        
        # Load Video Links if available
        self.video_map = {}
        video_link_path = os.path.join(os.path.dirname(script_path), 'videoLink.txt')
        if os.path.exists(video_link_path):
            self.video_map = self.parse_video_links(video_link_path)
            
        self.current_slide_index = 0
        self.sidebar_visible = True
        
        # Initialize AI
        self.chat_model = get_chat_model()
        self.chat_history_ui = None
        
        # Build UI
        self.build_ui()

    def parse_video_links(self, path):
        video_map = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            current_slide = None
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Match "Slide 6:"
                slide_match = re.match(r'^Slide\s+(\d+)[:\s]*', line, re.IGNORECASE)
                if slide_match:
                    current_slide = int(slide_match.group(1))
                    if current_slide not in video_map:
                         video_map[current_slide] = {'url': '', 'title': ''}
                elif current_slide is not None:
                     if line.startswith('http'):
                         video_map[current_slide]['url'] = line
                     elif line.startswith('Duration:'):
                         pass
                     else:
                         video_map[current_slide]['title'] = line
            print(f"[AIVideaPlayer] Loaded {len(video_map)} video links.")
        except Exception as e:
            print(f"Error parsing video links: {e}")
        return video_map

    def parse_script(self, path):
        slides = []
        try:
            content = self.script_content
            if not content and path and os.path.exists(path):
                with open(path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
            elif not content:
                # Try fetching from Github
                import urllib.request
                print(f"[AIVideoPlayer] Local script not found, fetching from remote for {self.folder_name}...")
                
                clean_base = self.base_url.rstrip('/')
                remote_url = f"{clean_base}/Video/{self.folder_name}/script.txt"
                
                try:
                    req = urllib.request.Request(remote_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=8) as response:
                        content = response.read().decode('utf-8-sig')
                        
                    if path:
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        with open(path, 'w', encoding='utf-8-sig') as out_f:
                            out_f.write(content)
                            
                except Exception as ex:
                    print(f"[AIVideoPlayer] Failed to fetch script from {remote_url}: {ex}")
                    # If this is AIUD, fallback to AIUD specific repo if not already
                    if "AIUD_March2026" not in remote_url and re.match(r'^c\d+\.\d+$', self.folder_name):
                        fallback_url = f"https://tranthanhthangbmt.github.io/AIUD_March2026/Video/{self.folder_name}/script.txt"
                        try:
                            req = urllib.request.Request(fallback_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, timeout=8) as response:
                                content = response.read().decode('utf-8-sig')
                            if path:
                                os.makedirs(os.path.dirname(path), exist_ok=True)
                                with open(path, 'w', encoding='utf-8-sig') as out_f:
                                    out_f.write(content)
                            # Override asset base url since we got it from fallback
                            self.asset_base_url = f"https://tranthanhthangbmt.github.io/AIUD_March2026/Video/{self.folder_name}/"
                        except:
                            pass
            
            if not content:
                print(f"[AIVideoPlayer] Script not found locally or remotely for: {self.folder_name}")
                return []
            
            # Basic parsing: Split by "Slide X:"
            # Strip multiple potential BOMs
            content = content.replace('\ufeff', '')
            lines = content.split('\n')
            current_slide = None
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Regex for "Slide 1:", "Slide 01", etc.
                # Use search and strip to be robust against invisible chars
                match = re.search(r'^Slide\s+(\d+)[:\s]*(.*)$', line, re.IGNORECASE)
                if match:
                    # Save previous slide
                    if current_slide: slides.append(current_slide)
                    
                    current_slide = {
                        'id': int(match.group(1)),
                        'title': match.group(2).strip(),
                        'lines': []
                    }
                elif current_slide:
                    current_slide['lines'].append(line)
            
            # Append last slide
            if current_slide: slides.append(current_slide)
            
            print(f"[AIVideoPlayer] Parsed {len(slides)} slides (Total 1 to {len(slides)})")
            if slides:
                 print(f"[AIVideoPlayer] First slide ID: {slides[0]['id']}")
            
        except Exception as e:
            print(f"[AIVideoPlayer] Error parsing script: {e}")
        
        return slides

    def build_ui(self):
        self.container.clear()
        if not self.slides:
            with self.container:
                ui.label(f"Không tìm thấy kịch bản hoặc lỗi định dạng tại: {self.script_path}").classes('text-red-500 font-bold')
            return

        # --- THEME CONFIG ---
        self.container.classes('p-0 gap-0 w-full h-[85vh] bg-gradient-to-br from-gray-900 via-slate-900 to-black text-white overflow-hidden relative shadow-2xl rounded-xl border border-white/10')
        
        # --- GLOBAL CSS FIX: Force all chat/tab children to respect container width ---
        ui.add_css('''
            .q-tab-panel { overflow-x: hidden !important; max-width: 100% !important; }
            .q-message { max-width: 100% !important; overflow-wrap: break-word !important; word-break: break-word !important; }
            .q-message-text { max-width: 100% !important; overflow-wrap: break-word !important; }
            .q-message-text div { white-space: pre-wrap !important; word-break: break-word !important; }
            .q-message-container { max-width: 100% !important; }
            .q-message-avatar { flex-shrink: 0 !important; }
            
            /* ═══ MIT STANDARDS: FULLSCREEN FIXES ═══ */
            :fullscreen { 
                height: 100vh !important; 
                width: 100vw !important; 
                max-height: 100vh !important; 
                max-width: 100vw !important;
                border-radius: 0 !important;
                border: none !important;
                padding: 0 !important;
                background: black !important;
            }
            :fullscreen .q-splitter, 
            :fullscreen .q-splitter__panel, 
            :fullscreen .q-tab-panels, 
            :fullscreen .q-panel { 
                height: 100% !important; 
                border-radius: 0 !important;
            }
            /* Remove extreme padding in fullscreen to maximize content */
            :fullscreen .left-cinema-col { padding: 0 !important; }
            :fullscreen .right-sidebar-col { border-left: 1px solid rgba(255,255,255,0.1); }

            /* ═══ MIT STANDARDS: MOBILE RESPONSIVE ═══ */
            @media (max-width: 768px) {
                /* Force splitter into vertical stack */
                .q-splitter--vertical {
                    flex-direction: column !important;
                }
                .q-splitter--vertical > .q-splitter__panel {
                    width: 100% !important;
                    max-width: 100% !important;
                }
                .q-splitter--vertical > .q-splitter__before {
                    height: 42vh !important;
                    min-height: 180px !important;
                    max-height: 45vh !important;
                }
                .q-splitter--vertical > .q-splitter__after {
                    height: 58vh !important;
                    flex: 1 !important;
                    border-left: none !important;
                    border-top: 1px solid rgba(255,255,255,0.1) !important;
                }
                .q-splitter--vertical > .q-splitter__separator {
                    display: none !important;
                }
                /* Cinema padding */
                .left-cinema-col {
                    padding: 4px !important;
                }
                /* Playback bar compact */
                .left-cinema-col > .absolute.bottom-4 {
                    bottom: 4px !important;
                    padding: 2px 10px !important;
                    gap: 4px !important;
                }
                /* Toolbar compact */
                .left-cinema-col > .absolute.top-3.right-3 {
                    top: 2px !important;
                    right: 2px !important;
                    padding: 2px 4px !important;
                    gap: 0 !important;
                    border-radius: 8px !important;
                }
                .left-cinema-col > .absolute.top-3.right-3 .q-btn {
                    min-width: 28px !important;
                    min-height: 28px !important;
                }
                .left-cinema-col > .absolute.top-3.right-3 label {
                    font-size: 7px !important;
                }
                /* Back button compact */
                .left-cinema-col > .absolute.top-4.left-4 {
                    top: 2px !important;
                    left: 2px !important;
                    padding: 1px !important;
                }
                .left-cinema-col > .absolute.top-4.left-4 label {
                    display: none !important;
                }
                /* Sidebar / Transcript */
                .right-sidebar-col {
                    border-left: none !important;
                }
                .right-sidebar-col .q-tab {
                    font-size: 11px !important;
                    min-height: 36px !important;
                    padding: 4px 8px !important;
                }
                .right-sidebar-col .q-tab__icon {
                    font-size: 16px !important;
                }
                /* Transcript text */
                .right-sidebar-col .overflow-y-auto {
                    padding: 10px !important;
                    gap: 6px !important;
                }
                .right-sidebar-col .text-sm,
                .right-sidebar-col .text-\\[15px\\] {
                    font-size: 12px !important;
                    line-height: 1.5 !important;
                }
                /* Chat input compact */
                .right-sidebar-col .q-textarea {
                    font-size: 13px !important;
                }
                /* Spinner smaller */
                .q-spinner {
                    font-size: 2em !important;
                }
            }
            @media (max-width: 480px) {
                .q-splitter--vertical > .q-splitter__before {
                    height: 35vh !important;
                    min-height: 150px !important;
                    max-height: 40vh !important;
                }
                .q-splitter--vertical > .q-splitter__after {
                    height: 65vh !important;
                }
                .right-sidebar-col .text-sm,
                .right-sidebar-col .text-\\[15px\\] {
                    font-size: 11px !important;
                }
                .right-sidebar-col .overflow-y-auto {
                    padding: 8px !important;
                }
            }
        ''')
        
        with self.container:
             # Layout: Splitter (Image 75%, Sidebar 25%)
             with ui.splitter(horizontal=False, value=75).classes('w-full h-full transition-all duration-500') as self.main_splitter:
                 
                 # --- LEFT: CINEMA VIEW (Video/Slide) ---
                 with self.main_splitter.before, ui.column().classes('w-full h-full items-center justify-center bg-black relative overflow-hidden p-12 left-cinema-col') as self.left_col:
                     # Main Visual
                     self.img = ui.image().classes('max-w-full max-h-full shadow-2xl').props('no-spinner').style('object-fit: contain;')
                     
                     # Video Element
                     self.video_player = ui.video(src='').classes('hidden max-w-full max-h-full').style('object-fit: contain;')
                     self.video_player.on('ended', self.next_slide)
                     
                     # Audio Element
                     self.audio = ui.audio(src='').classes('hidden')
                     self.audio.on('ended', self.next_slide)
                     
                     # Loading Spinner
                     self.spinner = ui.spinner('dots', size='3em', color='blue-400').classes('absolute')
                     
                     def handle_img_error():
                         self.spinner.set_visibility(False)
                         self.img.classes('hidden') # Ẩn thẻ ảnh đi nếu lỗi, để lộ hình nền đen
                         ui.notify('Không thể tải ảnh từ máy chủ. Vẫn có thể xem chữ.', type='warning')
                         
                     self.img.on('load', lambda: self.spinner.set_visibility(False))
                     self.img.on('error', handle_img_error)

                     # ═══ COMPACT PLAYBACK BAR (Bottom Center) ═══
                     # Slim, YouTube-style: only prev/play/next + counter
                     with ui.row().classes('absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black/70 backdrop-blur-lg border border-white/15 rounded-full px-4 py-1 items-center gap-3 transition-all duration-300 opacity-80 hover:opacity-100 shadow-xl z-30'):
                         ui.button(icon='skip_previous', on_click=self.prev_slide).props('flat round color=white size=sm').classes('hover:bg-white/10')
                         self.btn_play = ui.button(icon='play_arrow', on_click=self.toggle_play).props('flat round color=white size=md').classes('hover:text-blue-400 transition-colors')
                         ui.button(icon='skip_next', on_click=self.next_slide).props('flat round color=white size=sm').classes('hover:bg-white/10')
                         self.lbl_counter = ui.label('00 / 00').classes('font-mono text-[11px] text-blue-200/80 tracking-wider ml-1')

                     # ═══ TOP-LEFT TOOLBAR (Back to Tree) ═══
                     if self.on_back:
                         with ui.row().classes('absolute top-4 left-4 bg-black/40 backdrop-blur-md border border-white/10 rounded-full p-1 items-center transition-all duration-300 opacity-60 hover:opacity-100 z-40 shadow-lg'):
                             ui.button(icon='hub', on_click=self.on_back).props('flat round color=white size=md').tooltip('Quay lại Cây tri thức (Graph Studio)')
                             ui.label('QUAY LẠI CÂY').classes('text-[10px] font-bold text-white pr-3 tracking-tighter')

                     # ═══ TOP-RIGHT TOOLBAR (Secondary Controls) ═══
                     # Small icon row, semi-transparent, doesn't block the slide
                     with ui.row().classes('absolute top-3 right-3 bg-black/50 backdrop-blur-md border border-white/10 rounded-lg px-2 py-1 items-center gap-1 transition-all duration-300 opacity-60 hover:opacity-100 z-30'):
                         # Auto toggle
                         self.switch_auto = ui.switch(value=True).props('dense color=blue size=xs').tooltip('Tự động chuyển slide')
                         ui.label('Auto').classes('text-[9px] text-gray-300 uppercase tracking-wider font-bold mr-2')

                         # AI Exam toggle
                         self.switch_examiner = ui.switch(value=False).props('dense color=cyan size=xs keep-color').tooltip('Chế độ AI kiểm tra bài')
                         ui.label('Exam').classes('text-[9px] text-cyan-400 uppercase tracking-wider font-bold mr-1')

                         # Separator
                         ui.element('div').classes('w-px h-4 bg-white/20 mx-1')

                         # Sidebar Toggle
                         self.toggle_btn = ui.button(icon='menu_open', on_click=self.toggle_sidebar).props('flat round color=white size=xs').classes('hover:bg-white/10').tooltip('Transcript & Chat')
                         
                         # Fullscreen
                         self.fs_btn = ui.button(icon='fullscreen').props('flat round color=white size=xs').classes('hover:bg-white/10').tooltip('Toàn màn hình')
                         
                         container_id = self.container.id
                         def toggle_fs():
                             ui.run_javascript(f'''
                                const elem = document.getElementById("c{container_id}");
                                if (elem) {{
                                    if (!document.fullscreenElement) {{
                                        (elem.requestFullscreen || elem.webkitRequestFullscreen || elem.msRequestFullscreen).call(elem).catch(e => console.error(e));
                                    }} else {{
                                        document.exitFullscreen();
                                    }}
                                }}
                             ''')
                             curr = self.fs_btn.props.get('icon')
                             self.fs_btn.props(f'icon={"fullscreen_exit" if curr == "fullscreen" else "fullscreen"}')
                             
                         self.fs_btn.on('click', toggle_fs)


                 # --- RIGHT: INTELLIGENT SIDEBAR ---
                 with self.main_splitter.after, ui.column().classes('w-full h-full bg-gray-900 border-l border-white/10 p-0 overflow-hidden right-sidebar-col') as self.right_col:
                     # --- MIT Standard Tab Interface ---
                     with ui.tabs().classes('w-full text-gray-400 bg-slate-900 shrink-0 border-b border-white/10 shadow-md') as tabs:
                         script_tab = ui.tab('Transcript', icon='description').classes('w-1/2')
                         chat_tab = ui.tab('AI Tutor', icon='smart_toy').classes('w-1/2')
                     
                     with ui.tab_panels(tabs, value=script_tab).classes('w-full flex-grow bg-transparent p-0'):
                         
                         # TAB: TRANSCRIPT
                         with ui.tab_panel(script_tab).classes('w-full h-full p-0 flex flex-col'):
                             # We use native CSS overflow-y-auto to guarantee NO horizontal scrollbars
                             with ui.column().classes('w-full flex-grow overflow-y-auto overflow-x-hidden p-6 gap-4') as self.script_container:
                                 pass # Will be populated by load_slide
                                 
                         # TAB: AI TUTOR
                         with ui.tab_panel(chat_tab).classes('w-full h-full p-0 flex flex-col bg-slate-900 justify-between'):
                             # Chat History
                             with ui.column().classes('w-full flex-grow overflow-y-auto overflow-x-hidden p-4 gap-4') as self.chat_scroll:
                                 self.chat_container = ui.column().classes('w-full gap-4')
                                 # Welcome using standard ui.chat_message
                                 with self.chat_container:
                                     ui.chat_message('Chào bạn! Mình là AI Tutor. Hỏi mình bất cứ điều gì về bài học nhé!',
                                         name='AI Tutor',
                                         stamp='Online',
                                         avatar='https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg',
                                         sent=False).classes('w-full text-sm')
                             
                             # Input (Sleek sticky bottom bar)
                             with ui.row().classes('w-full p-3 bg-slate-800/80 backdrop-blur-md border-t border-white/10 items-end gap-2 no-wrap shrink-0 relative z-20 shadow-[0_-5px_15px_rgba(0,0,0,0.3)]'):
                                 self.chat_input = ui.textarea(placeholder='Nhắn tin cho AI Tutor...').props('rounded outlined bg-color=dark dense autogrow rows="1" input-class="text-white"').classes('flex-grow text-white min-w-0 transition-all focus:shadow-[0_0_10px_rgba(6,182,212,0.5)]')
                                 self.chat_input.on('keyup.enter', self.send_chat)
                                 ui.button(icon='send', on_click=self.send_chat).props('round flat color=cyan').classes('mb-1 shrink-0 transition-transform hover:scale-110 hover:bg-cyan-900/30')

        # Use Timer to load first slide to ensure UI is ready
        ui.timer(0.1, lambda: self.load_slide(0), once=True)

        # --- PRE-CREATE DIALOGS (Styled) ---
        
        # 1. Processing Dialog
        with ui.dialog() as self.processing_dialog, ui.card().classes('bg-gray-900 border border-blue-500/50 items-center justify-center p-8 rounded-2xl shadow-2xl'):
             ui.spinner('orbit', size='3em', color='cyan-400')
             self.processing_label = ui.label('AI đang phân tích kiến thức...').classes('text-cyan-200 animate-pulse mt-4 font-bold tracking-wide')

        # 2. Quiz Dialog
        with ui.dialog() as self.quiz_dialog, ui.card().classes('w-full max-w-2xl bg-slate-900 border border-white/10 rounded-2xl shadow-2xl p-0 overflow-hidden'):
            # Header
            with ui.row().classes('w-full bg-gradient-to-r from-blue-900 to-slate-900 p-4 items-center gap-3 border-b border-white/10'):
                 ui.icon('psychology', color='white').classes('text-2xl')
                 ui.label('AI EXAMINER').classes('text-xl font-black text-white tracking-widest')
            
            with ui.column().classes('p-6 w-full gap-6'):
                self.quiz_question_label = ui.label('').classes('text-xl font-medium text-white leading-relaxed')
                
                # Options Grid
                self.quiz_option_btns = []
                with ui.column().classes('w-full gap-3'):
                    for i in range(4):
                        btn = ui.button('', on_click=lambda ix=i: self.submit_quiz_answer(ix)).props('no-caps align=left').classes('w-full p-4 text-left text-gray-200 bg-white/5 border border-white/10 rounded-xl hover:bg-blue-600/20 hover:border-blue-500 transition-all duration-300 hidden text-md')
                        self.quiz_option_btns.append(btn)

                self.quiz_result_area = ui.label('').classes('font-bold text-center w-full min-h-[20px]')

    async def check_understanding(self, slide_id):
        """Generates a question for the current slide and blocks navigation until answered."""
        slide = self.slides[self.current_slide_index]
        context_text = "\n".join(slide.get('lines', []))
        
        # Skip if too short
        if len(context_text) < 50:
            self.load_slide(self.current_slide_index + 1)
            return

        # Show processing
        self.processing_dialog.open()

        prompt = f"""
        CONTENT:
        {context_text}
        
        TASK:
        Đóng vai một giáo viên nghiêm khắc và thông minh. Hãy tạo 1 câu hỏi trắc nghiệm (4 lựa chọn) để kiểm tra kiến thức quan trọng trong nội dung trên.
        
        YÊU CẦU QUAN TRỌNG:
        1. Ngôn ngữ: TIẾNG VIỆT 100%.
        2. Độ khó: Các phương án nhiễu (distractors) phải hợp lý, GẦN GIỐNG đáp án đúng, không quá ngớ ngẩn.
        3. Độ dài: Cố gắng để các lựa chọn có độ dài TƯƠNG ĐƯƠNG nhau. Đừng để đáp án đúng dài nhất một cách lộ liễu.
        
        Return ONLY valid RAW JSON format (No Markdown code blocks):
        {{
            "question": "Câu hỏi ở đây?",
            "options": ["A. Lựa chọn 1", "B. Lựa chọn 2", "C. Lựa chọn 3", "D. Lựa chọn 4"],
            "correct_index": 0,
            "explanation": "Giải thích ngắn gọn tại sao đúng."
        }}
        """
        
        try:
            # Generate Question
            response = await run.io_bound(self.chat_model.generate_content, prompt)
            
            # Clean up JSON
            text = response.text
            # Remove markdown code blocks if present
            text = text.replace('```json', '').replace('```', '').strip()
            
            import json
            # Find JSON block using strict regex if simple clean fails
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                 self.current_quiz_data = json.loads(match.group(0))
            else:
                 # Try parsing the whole text if regex fails (sometimes it's just raw json)
                 try:
                    self.current_quiz_data = json.loads(text)
                 except:
                    print(f"Failed JSON Text: {text}")
                    raise Exception("No valid JSON found")

            self.processing_dialog.close()

            # Update Quiz Dialog UI
            self.quiz_question_label.text = self.current_quiz_data['question']
            self.quiz_result_area.text = ''
            
            # Update Buttons
            options = self.current_quiz_data.get('options', [])
            for i, btn in enumerate(self.quiz_option_btns):
                if i < len(options):
                    btn.text = options[i]
                    btn.classes(remove='hidden')
                    btn.enable()
                else:
                    btn.classes(add='hidden')
            
            self.quiz_dialog.open()
            
        except Exception as e:
            print(f"Error generating quiz: {e}")
            self.processing_dialog.close()
            # ui.notify needs context, safer to skip
            self.load_slide(self.current_slide_index + 1)

    def submit_quiz_answer(self, idx):
        if not hasattr(self, 'current_quiz_data'): return
        
        if idx == self.current_quiz_data['correct_index']:
            self.quiz_result_area.text = "✅ Chính xác! " + self.current_quiz_data['explanation']
            self.quiz_result_area.classes('text-green-600')
            ui.timer(2.0, lambda: [self.quiz_dialog.close(), self.load_slide(self.current_slide_index + 1)], once=True)
        else:
            self.quiz_result_area.text = "❌ Chưa đúng. Hãy thử lại!"
            self.quiz_result_area.classes('text-red-500')

    async def send_chat(self):
        text = self.chat_input.value
        if not text: return
        
        self.chat_input.value = ''
        
        # Display User Message
        with self.chat_container:
            ui.chat_message(text, sent=True)
        ui.run_javascript(f'var e = document.getElementById("c{self.chat_scroll.id}"); if(e) e.scrollTop = e.scrollHeight;')
        
        # Prepare Context
        current_slide = self.slides[self.current_slide_index]
        context_lines = current_slide.get('lines', [])
        context_text = "\n".join(context_lines)
        
        prompt = f"""
        CONTEXT (Nội dung Slide/Video hiện tại):
        {context_text}
        
        CÂU HỎI CỦA SINH VIÊN:
        {text}
        
        YÊU CẦU:
        Bạn là AI Tutor. Hãy trả lời câu hỏi dựa trên CONTEXT trên.
        - Nếu câu trả lời có trong context, hãy giải thích rõ ràng.
        - Nếu context không đề cập, hãy dùng kiến thức chung của bạn để trả lời nhưng nhớ nói thêm là "Slide này chưa đề cập, nhưng theo kiến thức mở rộng thì...".
        - Trả lời ngắn gọn, thân thiện, khuyến khích học tập.
        """
        
        # Show Typing Indicator
        with self.chat_container:
            spinner = ui.spinner(type='dots')
        ui.run_javascript(f'var e = document.getElementById("c{self.chat_scroll.id}"); if(e) e.scrollTop = e.scrollHeight;')
        
        # Call AI (Run in thread to avoid blocking)
        try:
            if self.chat_model:
                response = await run.io_bound(self.chat_model.generate_content, prompt)
                response_text = response.text
            else:
                response_text = "Lỗi: Không kết nối được với AI Model."
        except Exception as e:
            response_text = f"Đã có lỗi xảy ra: {str(e)}"
        
        # Remove spinner and show response
        self.chat_container.remove(spinner)
        with self.chat_container:
            ui.chat_message(response_text, sent=False, avatar='https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg')
        ui.run_javascript(f'var e = document.getElementById("c{self.chat_scroll.id}"); if(e) e.scrollTop = e.scrollHeight;')



    def load_slide(self, index):
        if 0 <= index < len(self.slides):
            self.current_slide_index = index
            slide = self.slides[index]
            slide_id = slide['id']
            
            # Check if this slide is a VIDEO
            is_video = slide_id in self.video_map
            
            self.spinner.set_visibility(True)
            self.lbl_counter.text = f"{index + 1:02d} / {len(self.slides):02d}"

            if is_video:
                 video_data = self.video_map[slide_id]
                 print(f"[Debug] Slide {slide_id} is Video: {video_data['url']}")
                 
                 # Show Video, Hide Image
                 self.img.classes('hidden')
                 self.video_player.classes(remove='hidden')
                 
                 self.video_player.source = video_data['url']
                 self.audio.pause() # Ensure audio is off
                 
                 if self.switch_auto.value:
                     self.video_player.play()
                     self.btn_play.props('icon=pause')
                 else:
                     self.btn_play.props('icon=play_arrow')
                     
                 self.spinner.set_visibility(False) # Immediate hide for video
                 
            else:
                # Normal Slide (Image + Audio)
                img_url = f"{self.asset_base_url}images/slide-{slide_id}.png"
                audio_url = f"{self.asset_base_url}audio/slide_{slide_id}.mp3"
                
                print(f"[Debug] Loading Slide {slide_id}: {img_url}")
                
                # Show Image, Hide Video
                self.video_player.classes('hidden')
                self.video_player.pause()
                self.img.classes(remove='hidden')
                
                # Reset spinner for new image
                self.spinner.set_visibility(True)
                self.img.source = img_url
                
                # Cập nhật Audio
                self.audio.source = audio_url
                
                if self.switch_auto.value: 
                    # Phát audio, nhưng nếu không có audio thì sao?
                    # Để an toàn, audio play có thể thất bại. Ta không thể bắt exception sync,
                    # nhưng trình duyệt sẽ tự động gọi 'error' trên thẻ audio nếu 404.
                    # Khi thẻ audio lỗi, sự kiện 'ended' sẽ KHÔNG xảy ra, do đó auto-next sẽ dừng.
                    # Thêm JS bắt lỗi audio để auto-next nếu cần (phức tạp). Tạm thời để play().
                    self.audio.play()
                    self.btn_play.props('icon=pause')
                else:
                    self.btn_play.props('icon=play_arrow')

            # Update Script (Teleprompter Style)
            self.script_container.clear()
            with self.script_container:
                # Title
                ui.label(f"SLIDE {slide['id']}: {slide['title'].upper()}").classes('font-bold text-blue-400 text-sm tracking-widest mb-4 break-words')
                # Dialog content
                for line in slide['lines']:
                    # Highlight Speaker
                    if ':' in line:
                        parts = line.split(':', 1)
                        # HTML div block ensures 100% native wrapping without flex layout issues
                        with ui.element('div').classes('w-full mb-3 leading-relaxed break-words'):
                            ui.label(parts[0] + ':').classes('font-bold text-cyan-400 text-sm inline mr-1')
                            ui.label(parts[1]).classes('text-gray-300 text-[15px] font-light inline')
                    else:
                        ui.label(line).classes('text-gray-400 leading-relaxed italic text-sm pl-4 border-l-2 border-gray-700 break-words w-full block mb-3')
            
            # Scroll to top of script
            ui.run_javascript(f'var e = document.getElementById("c{self.script_container.id}"); if(e) e.scrollTop = 0;')
            
            # --- SYNC TO OMNI-CONTEXT ---
            if 'omni_context' in app.storage.user:
                ctx = app.storage.user['omni_context']
                ctx['current_tab'] = 'video_lessons'
                ctx['node_id'] = f"{self.concept_name}_Slide_{slide_id}"
                ctx['node_content'] = f"""
Đang xem bài học: {self.concept_name}
Slide số: {slide_id}
Tiêu đề slide: {slide['title']}
Nội dung slide (Transcript):
{chr(10).join(slide['lines'])}
"""

    def toggle_play(self):
        # We need a way to check state. But ui.audio doesn't expose 'paused' prop easily in Python sync.
        # We will assume toggle based on icon or just call JS.
        # Simplify: Just toggle icon and call corresponding method.
        # But we don't know if it's playing.
        # Let's use run_javascript to check or simple toggle logic.
        curr_icon = self.btn_play.props['icon']
        if curr_icon == 'play_arrow':
            self.audio.play()
            self.btn_play.props('icon=pause')
        else:
            self.audio.pause()
            self.btn_play.props('icon=play_arrow')


    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        if self.sidebar_visible:
            self.main_splitter.value = 75
            self.toggle_btn.props('icon=menu_open')
        else:
            self.main_splitter.value = 100
            self.toggle_btn.props('icon=menu')




    def next_slide(self):
        # Helper to actually move
        def force_next():
             if self.current_slide_index < len(self.slides) - 1:
                self.load_slide(self.current_slide_index + 1)

        if self.current_slide_index < len(self.slides) - 1:
            # Check if Examiner Mode is ON
            if self.switch_examiner.value:
                # Run async check
                # We need to run async function from sync event handler
                # NiceGUI handles this if we just loop.create_task or similar, 
                # but better to use background task
                asyncio.create_task(self.check_understanding(self.current_slide_index))
            else:
                self.load_slide(self.current_slide_index + 1)
    
    def prev_slide(self):
         if self.current_slide_index > 0:
            self.load_slide(self.current_slide_index - 1)


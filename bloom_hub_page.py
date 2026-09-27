# bloom_hub_page.py
"""Bloom Learning Hub — 3 tabs: Study, Assess (Bloom Ladder), Progress."""

from nicegui import ui, run, app
import json, os, re
from bloom_taxonomy import (
    BLOOM_LEVELS, get_effective_levels, check_level_unlocked,
    load_bloom_state, save_bloom_state, create_node_bloom_scores,
    update_bloom_score, get_bloom_color, calculate_overall_bloom,
    update_ebbinghaus_after_review, calibrate_tree_bloom
)
from node_content_engine import get_or_create_content_pack, get_content_pack_sync
from gemini_helper import get_chat_model, extract_json_from_text
from knowledge_tracing import update_node_mastery, get_dynamic_difficulty


async def build_bloom_hub_ui(container, subject_id: str, node_id: str, username: str, switch_back_callback=None, node_label: str = ''):
    container.clear()
    with container.classes('w-full h-full bg-gradient-to-br from-[#0f172a] to-[#0d1117] overflow-y-auto font-[Inter] text-white'):
        ui.add_head_html("""
        <style>
        .bloom-fc-container { perspective: 1200px; width: 100%; max-width: 600px; height: 350px; margin: 0 auto; cursor: pointer; }
        .bloom-fc-inner { position: relative; width: 100%; height: 100%; transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1); transform-style: preserve-3d; }
        .bloom-fc-inner.flipped { transform: rotateY(180deg); }
        .bloom-fc-front, .bloom-fc-back { position: absolute; width: 100%; height: 100%; -webkit-backface-visibility: hidden; backface-visibility: hidden; border-radius: 24px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 32px; box-sizing: border-box; }
        .bloom-fc-front { background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%); color: white; border: 2px solid rgba(99, 102, 241, 0.3); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1); }
        .bloom-fc-back { background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%); color: white; transform: rotateY(180deg); border: 2px solid rgba(16, 185, 129, 0.3); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1); }
        .bloom-fc-mini { perspective: 1200px; width: 280px; height: 180px; cursor: pointer; flex-shrink: 0; }
        .bloom-fc-mini .bloom-fc-front, .bloom-fc-mini .bloom-fc-back { padding: 16px; border-radius: 16px; }
        </style>
        """)
        try:
            user_id = app.storage.user.get('id')
        except RuntimeError:
            user_id = username
        if not username:
            ui.label('Vui lòng đăng nhập').classes('text-red-500 font-bold p-8')
            return

        # Load tree
        tree_file = f"user_data/{username}/trees/{subject_id}.json"
        if not os.path.exists(tree_file):
            ui.label('Không tìm thấy dữ liệu.').classes('text-red-400 p-8')
            return
        with open(tree_file, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)

        # Find node
        node_info = None
        for key in ['micro_nodes', 'macro_nodes', 'assess_nodes']:
            for n in tree_data.get(key, []):
                if n.get('id') == node_id:
                    node_info = n
                    break
        if not node_info:
            if 'nodes' in tree_data and isinstance(tree_data['nodes'], dict):
                node_info = tree_data['nodes'].get(node_id, {})
        if not node_info:
            # Fallback for dynamic nodes (like m1_Meso_1)
            node_info = {
                'id': node_id,
                'title': node_label if node_label else f"Tổng hợp {node_id}",
                'content': f"Bài kiểm tra và đánh giá tổng hợp các kiến thức cốt lõi của {node_label if node_label else node_id}."
            }

        node_title = node_info.get('title') or node_info.get('label') or node_id
        node_content = node_info.get('content') or node_info.get('description') or ''
        bloom_profile = node_info.get('bloom_profile', {})
        target_levels = get_effective_levels(bloom_profile) if bloom_profile else [1, 2]
        alpha = node_info.get('alpha_base', 15)

        # Load user bloom state
        bloom_state = load_bloom_state(username, subject_id)
        if node_id not in bloom_state.get('nodes', {}):
            bloom_state.setdefault('nodes', {})[node_id] = create_node_bloom_scores(target_levels)
            save_bloom_state(username, subject_id, bloom_state)
        node_state = bloom_state['nodes'][node_id]
        
        # --- UPDATE OMNI-CONTEXT ---
        if 'omni_context' in app.storage.user:
            app.storage.user['omni_context']['node_id'] = node_id
            app.storage.user['omni_context']['subject_id'] = subject_id
            app.storage.user['omni_context']['current_tab'] = 'bloom_hub'
            summary = node_content[:500] if node_content else f"Học tập về {node_title}"
            app.storage.user['omni_context']['node_content'] = summary

        # Main layout
        with ui.column().classes('w-full max-w-5xl mx-auto p-4 min-h-screen'):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-4'):
                if switch_back_callback:
                    ui.button(icon='arrow_back', on_click=switch_back_callback).props('flat round color=white').classes('hover:bg-white/10 transition-colors shadow-lg bg-white/5')
                else:
                    ui.button(icon='arrow_back', on_click=lambda: ui.run_javascript('window.close()')).props('flat round color=grey')
                ui.label(f'🧬 {node_title}').classes('text-xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400 truncate max-w-lg')
                color = get_bloom_color(node_state.get('overall_bloom', 0))
                ui.html(f'<div style="width:24px;height:24px;border-radius:50%;background:{color};box-shadow:0 0 12px {color}"></div>')

            # Tabs
            with ui.tabs().classes('w-full') as tabs:
                tab_study = ui.tab('📖 Học tập').classes('text-white')
                tab_assess = ui.tab('🧪 Đánh giá').classes('text-white')
                tab_progress = ui.tab('📊 Tiến độ').classes('text-white')

            with ui.tab_panels(tabs, value=tab_study).classes('w-full flex-grow bg-transparent'):
                # ==================== TAB 1: STUDY ====================
                with ui.tab_panel(tab_study):
                    study_area = ui.column().classes('w-full')
                    with study_area:
                        ui.label('Đang tải nội dung học tập...').classes('text-gray-400 animate-pulse')

                    async def load_study():
                        pack = get_content_pack_sync(node_id, node_info, tree_data, username)
                        if not pack:
                            try:
                                study_area.clear()
                            except RuntimeError:
                                return
                            with study_area:
                                with ui.row().classes('items-center gap-2'):
                                    ui.spinner('dots', size='lg', color='cyan')
                                    ui.label('AI đang sinh nội dung...').classes('text-cyan-300 animate-pulse')
                            pack = await get_or_create_content_pack(node_id, node_info, tree_data, username)

                        try:
                            study_area.clear()
                        except RuntimeError:
                            return
                            
                        sm = pack.get('study_material', {})
                        with study_area:
                            # Learning objectives
                            objs = sm.get('learning_objectives', [])
                            if objs:
                                with ui.card().classes('w-full p-4 bg-indigo-900/30 border border-indigo-700 rounded-xl mb-4'):
                                    ui.label('🎯 Mục tiêu học tập').classes('font-bold text-indigo-300 mb-2')
                                    for o in objs:
                                        ui.label(f'• {o}').classes('text-gray-300 text-sm')

                            # Key concepts
                            concepts = sm.get('key_concepts', [])
                            if concepts:
                                with ui.card().classes('w-full p-4 bg-emerald-900/30 border border-emerald-700 rounded-xl mb-4'):
                                    ui.label('📚 Khái niệm cốt lõi').classes('font-bold text-emerald-300 mb-2')
                                    for c in concepts:
                                        t = c.get('term', '') if isinstance(c, dict) else str(c)
                                        d = c.get('definition', '') if isinstance(c, dict) else ''
                                        ui.label(f'▸ {t}: {d}').classes('text-gray-300 text-sm mb-1')

                            # --- ADAPTIVE CONTENT RENDERING ---
                            import math, time
                            eb_node = bloom_state.get('ebbinghaus', {}).get(node_id, {})
                            last_review = eb_node.get('last_review', 0)
                            strength = eb_node.get('strength', 2.0)
                            retention = 1.0
                            if last_review > 0:
                                hours = (time.time() - last_review) / 3600.0
                                retention = max(0.0, min(1.0, math.exp(-hours / max(0.5, strength))))

                            is_low_retention = (retention < 0.6 and last_review > 0)
                            
                            if is_low_retention:
                                ui.label('🚨 Dữ liệu Ebbinghaus: Bạn đang có dấu hiệu quên bài học này!').classes('text-red-400 font-bold mb-1 text-sm')
                                ui.label('Hệ thống đã tự động chuyển sang chế độ Micro-learning (Flashcards & Mindmap) để tối ưu hóa thời gian ôn tập của bạn.').classes('text-red-300 mb-4 text-xs italic')
                                
                            # Multimedia Diagram (Mindmap/Flowchart)
                            diagram = sm.get('multimedia_diagram', '')
                            if diagram:
                                diagram_code = diagram.replace('```mermaid', '').replace('```', '').strip()
                                with ui.card().classes('w-full p-4 bg-purple-900/20 border border-purple-700/50 rounded-xl mb-4 relative group'):
                                    ui.label('🗺️ Sơ đồ Tư duy (Mayer\'s Multimedia Principle) - Bấm để phóng to').classes('font-bold text-purple-300 mb-2')
                                    
                                    # Dialog for Fullscreen view
                                    with ui.dialog() as diagram_dialog, ui.card().classes('w-[95vw] h-[95vh] bg-[#0d1117] overflow-auto flex flex-col items-center justify-center relative border border-purple-500/50'):
                                        ui.button(icon='close', on_click=diagram_dialog.close).props('flat round color=white size=lg').classes('absolute top-2 right-2 z-50 hover:bg-white/10')
                                        try:
                                            ui.mermaid(diagram_code).classes('w-full h-full scale-[1.5] origin-center') # Phóng to gấp 1.5 lần
                                        except Exception:
                                            ui.markdown(f"```mermaid\\n{diagram_code}\\n```").classes('w-full h-full')

                                    # Clickable preview
                                    with ui.element('div').on('click', diagram_dialog.open).classes('w-full cursor-pointer hover:opacity-80 transition-opacity relative'):
                                        try:
                                            ui.mermaid(diagram_code).classes('w-full')
                                        except Exception:
                                            ui.markdown(f"```mermaid\\n{diagram_code}\\n```")
                                        # Overlay zoom icon
                                        ui.icon('zoom_in', size='xl').classes('absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity text-white drop-shadow-2xl bg-black/60 p-4 rounded-full pointer-events-none')
                            
                            # Micro-learning Flashcards
                            flashcards = sm.get('micro_learning_flashcards', [])
                            
                            def render_mini_flashcard(q, a):
                                ui.add_head_html("""
                                <style>
                                .mini-fc-box { perspective: 1200px; width: 280px; height: 180px; cursor: pointer; flex-shrink: 0; }
                                .mini-fc-flip { position: relative; width: 100%; height: 100%; transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1); transform-style: preserve-3d; }
                                .mini-fc-flip.flipped { transform: rotateY(180deg); }
                                .mini-fc-side { position: absolute; width: 100%; height: 100%; backface-visibility: hidden; -webkit-backface-visibility: hidden; border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 16px; box-sizing: border-box; }
                                .mini-fc-side.front { background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%); color: white; border: 2px solid rgba(99, 102, 241, 0.3); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3); }
                                .mini-fc-side.back { background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%); color: white; transform: rotateY(180deg); border: 2px solid rgba(16, 185, 129, 0.3); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3); }
                                </style>
                                """)
                                state = {"flipped": False}
                                card_wrapper = ui.element('div').classes('mini-fc-box')
                                with card_wrapper:
                                    inner = ui.element('div').classes('mini-fc-flip')
                                    with inner:
                                        with ui.element('div').classes('mini-fc-side front'):
                                            ui.label('💡 CÂU HỎI').classes('text-[10px] text-indigo-300 font-bold tracking-widest mb-1 uppercase')
                                            ui.label(q).classes('text-sm font-bold text-center leading-snug text-white line-clamp-4')
                                            ui.label('Nhấp để lật →').classes('text-[10px] text-indigo-400 mt-2 italic')
                                        with ui.element('div').classes('mini-fc-side back'):
                                            ui.label('📖 ĐÁP ÁN').classes('text-[10px] text-emerald-300 font-bold tracking-widest mb-1 uppercase')
                                            ui.label(a).classes('text-sm text-center leading-snug text-white overflow-y-auto')
                                def toggle():
                                    state["flipped"] = not state["flipped"]
                                    if state["flipped"]: inner.classes(add='flipped')
                                    else: inner.classes(remove='flipped')
                                card_wrapper.on('click', toggle)

                            if flashcards and is_low_retention:
                                with ui.card().classes('w-full p-4 bg-pink-900/20 border border-pink-700/50 rounded-xl mb-4'):
                                    ui.label('⚡ Flashcards Ôn Tập Nhanh (Micro-learning)').classes('font-bold text-pink-300 mb-4')
                                    with ui.row().classes('w-full gap-4 flex-wrap justify-center'):
                                        for fc in flashcards:
                                            render_mini_flashcard(fc.get('q', 'Câu hỏi'), fc.get('a', ''))
                            elif flashcards and not is_low_retention:
                                with ui.expansion('⚡ Flashcards Ôn Tập (Tùy chọn)', icon='bolt').classes('w-full bg-pink-900/10 mb-4 rounded-xl'):
                                    with ui.row().classes('w-full gap-4 flex-wrap justify-center p-4'):
                                        for fc in flashcards:
                                            render_mini_flashcard(fc.get('q', 'Câu hỏi'), fc.get('a', ''))

                            # Detailed Content
                            content_md = sm.get('detailed_content', '')
                            if content_md and not is_low_retention:
                                with ui.card().classes('w-full p-6 bg-gray-800/50 border border-gray-700 rounded-xl mb-4'):
                                    ui.markdown(content_md).classes('text-gray-200')
                            elif content_md and is_low_retention:
                                with ui.expansion('📖 Xem lại toàn bộ tài liệu chi tiết (Detailed Text)', icon='menu_book').classes('w-full bg-gray-800/50 mb-4 rounded-xl'):
                                    ui.markdown(content_md).classes('text-gray-200 p-4')

                            # Examples
                            examples = sm.get('practical_examples', [])
                            if examples:
                                with ui.card().classes('w-full p-4 bg-amber-900/30 border border-amber-700 rounded-xl mb-4'):
                                    ui.label('💡 Ví dụ thực tiễn').classes('font-bold text-amber-300 mb-2')
                                    for ex in examples:
                                        ui.label(f'• {ex}').classes('text-gray-300 text-sm mb-1')

                            # Resources
                            resources = node_info.get('resources', [])
                            if resources:
                                with ui.card().classes('w-full p-4 bg-cyan-900/30 border border-cyan-700 rounded-xl mb-4'):
                                    ui.label('🔗 Tài nguyên đính kèm').classes('font-bold text-cyan-300 mb-2')
                                    for r in resources:
                                        icon = r.get('icon', '🔗')
                                        title = r.get('title', r.get('url', ''))
                                        url = r.get('url', '#')
                                        ui.link(f'{icon} {title}', url, new_tab=True).classes('text-cyan-400 text-sm hover:text-cyan-200')

                            # Mark as studied
                            def mark_studied():
                                bloom_state['nodes'][node_id]['study_completed'] = True
                                save_bloom_state(username, subject_id, bloom_state)
                                ui.notify('✅ Đã đánh dấu hoàn thành!', type='positive')
                            if not node_state.get('study_completed'):
                                ui.button('✅ Đánh dấu đã học xong', on_click=mark_studied).classes('w-full bg-green-700 text-white font-bold py-3 rounded-xl mt-2').props('no-caps')

                            # Publish to shared library
                            async def publish_content():
                                from node_content_engine import publish_to_library, get_content_pack_sync
                                p = get_content_pack_sync(node_id, node_info, tree_data, username)
                                if p:
                                    publish_to_library(p, author=username)
                                    ui.notify('📤 Đã chia sẻ lên thư viện chung! Người dùng khác sẽ nhận được nội dung này.', type='positive')
                                else:
                                    ui.notify('⚠️ Chưa có nội dung để chia sẻ. Hãy tải nội dung trước.', type='warning')

                            # Check if already in library
                            from node_content_engine import load_from_library, _make_course_id, delete_content_pack
                            course_id = _make_course_id(tree_data.get('course_name', 'Môn học'))
                            lib_exists = load_from_library(course_id, node_id) is not None
                            
                            async def force_regenerate():
                                deleted = delete_content_pack(username, tree_data.get('course_name', 'Môn học'), node_id)
                                # Show what sources are available
                                sources = []
                                if node_info.get('description_md'):
                                    sources.append('📝 Mô tả chi tiết')
                                if node_info.get('resources'):
                                    sources.append(f"📎 {len(node_info['resources'])} tài nguyên")
                                if node_info.get('content') or node_info.get('description'):
                                    sources.append('📄 Nội dung node')
                                src_text = ', '.join(sources) if sources else 'tiêu đề bài học'
                                ui.notify(f'🔄 Đang sinh lại AI dựa trên: {src_text}...', type='info')
                                await load_study()

                            if lib_exists:
                                ui.html('<span style="color:#4ade80;font-size:12px;display:block;margin-top:8px">📗 Đã có bản chia sẻ trong thư viện chung</span>')
                            
                            with ui.row().classes('w-full gap-2 mt-2 flex-wrap'):
                                ui.button(
                                    '📤 Chia sẻ thư viện' if not lib_exists else '📤 Cập nhật thư viện',
                                    on_click=publish_content
                                ).classes('flex-grow bg-indigo-700 text-white py-2 rounded-xl border border-indigo-600 hover:bg-indigo-600 transition-colors').props('no-caps' if not lib_exists else 'no-caps outline')
                                
                                ui.button(
                                    '🔄 Sinh lại AI',
                                    on_click=force_regenerate
                                ).classes('flex-grow bg-red-900/40 text-red-300 py-2 rounded-xl border border-red-800 hover:bg-red-800 hover:text-white transition-colors').props('no-caps outline')

                    ui.timer(0.1, load_study, once=True)

                # ==================== TAB 2: ASSESS (BLOOM LADDER) ====================
                with ui.tab_panel(tab_assess):
                    assess_area = ui.column().classes('w-full gap-4')

                    async def delayed_render_bloom_ladder():
                        from nicegui import background_tasks
                        import asyncio
                        await asyncio.sleep(0.1)
                        render_bloom_ladder()

                    def render_bloom_ladder():
                        assess_area.clear()
                        # Reload state
                        bs = load_bloom_state(username, subject_id)
                        ns = bs.get('nodes', {}).get(node_id, node_state)

                        with assess_area:
                            ui.label('🧬 Bloom Assessment Ladder').classes('text-xl font-bold text-white mb-2')
                            ui.label('Hoàn thành mỗi bậc ≥70% với 2 loại đánh giá để mở khóa bậc tiếp').classes('text-xs text-gray-500 mb-4')

                            # --- Gamification: Daily Quests ---
                            try:
                                from smart_review_queue import get_daily_review_summary
                                bs_summary = get_daily_review_summary(bs)
                                if bs_summary['critical_nodes'] > 0:
                                    with ui.card().classes('w-full p-3 bg-amber-900/30 border border-amber-500 rounded-xl mb-3 shadow-[0_0_15px_rgba(245,158,11,0.2)]'):
                                        with ui.row().classes('items-center gap-2 w-full'):
                                            ui.icon('emoji_events', color='amber').classes('text-2xl animate-bounce')
                                            ui.label(f"Nhiệm vụ Khẩn: Tiêu diệt đường cong lãng quên ({bs_summary['critical_nodes']} bài)!").classes('text-amber-400 text-sm font-bold uppercase tracking-wide')
                                        ui.label('Phần thưởng: +50 EXP. Lời khuyên: Hãy nhờ Huấn luyện viên Học tập lập chiến thuật giải cứu não bộ ngay lập tức!').classes('text-amber-200 text-xs mt-1 ml-8 italic')
                            except Exception:
                                pass
                                
                            # --- Social Learning Widget (Peer Matchmaking) ---
                            try:
                                from social_learning_engine import find_peer_mentors
                                import math, time
                                eb_node = bs.get('ebbinghaus', {}).get(node_id, {})
                                last_review = eb_node.get('last_review', 0)
                                strength = eb_node.get('strength', 2.0)
                                retention = 1.0
                                if last_review > 0:
                                    hours = (time.time() - last_review) / 3600.0
                                    retention = max(0.0, min(1.0, math.exp(-hours / max(0.5, strength))))

                                is_struggling = retention < 0.6 or ns.get('overall_bloom', 0) < 3.0
                                
                                mentors = find_peer_mentors(username, subject_id, node_id)
                                if mentors and is_struggling:
                                    with ui.card().classes('w-full p-3 bg-blue-900/30 border border-blue-600 rounded-xl mb-3'):
                                        ui.label('🤝 Mạng lưới Học tập Xã hội (Peer Matchmaking)').classes('text-blue-300 text-xs font-bold mb-1')
                                        ui.label(f"Hệ thống tìm thấy {len(mentors)} sinh viên đã đạt mức độ xuất sắc (Bloom L{mentors[0]['bloom_level']}) ở bài học này!").classes('text-blue-200 text-xs mb-2')
                                        for m in mentors[:2]:
                                            with ui.row().classes('w-full items-center justify-between'):
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label('👤').classes('text-sm')
                                                    ui.label(f"{m['username']}").classes('text-blue-100 font-bold text-xs')
                                                ui.button('Nhờ hỗ trợ', on_click=lambda u=m['username']: ui.notify(f"Đã gửi yêu cầu kết nối tới Mentor {u}!", type='positive')).props('dense outline size=sm color=blue').classes('ml-auto')
                            except Exception as e:
                                print(f"Lỗi Social Learning Widget: {e}")
                                pass
                            
                            with ui.row().classes('w-full mb-4'):
                                ui.button('🧭 Huấn luyện viên Học tập (GROW Coach)', on_click=lambda: _start_learning_coach('pre_session')).classes('w-full bg-emerald-700 text-white font-bold py-2 rounded-xl shadow-lg').props('no-caps')

                            # Soft Prerequisite: tính bloom_ceiling
                            try:
                                from soft_prerequisite import get_access_status
                                edges = tree_data.get('edges', [])
                                access = get_access_status(node_id, target_levels, edges, bs)
                                bloom_ceiling = access.get('bloom_ceiling', 6)
                                prereq_gaps = access.get('prereq_gaps', [])
                                
                                # Hiển thị prerequisite warning nếu bị giới hạn
                                if prereq_gaps and bloom_ceiling < max(target_levels):
                                    gap_names = ', '.join(g['node_id'] for g in prereq_gaps[:3])
                                    with ui.card().classes('w-full p-3 bg-amber-900/30 border border-amber-600 rounded-xl mb-3'):
                                        ui.label(f'⚠️ Bloom Ceiling: L{bloom_ceiling} — Cần hoàn thành {gap_names} để mở thêm').classes('text-amber-300 text-xs')
                            except ImportError:
                                bloom_ceiling = 6

                            for lvl in target_levels:
                                bl = BLOOM_LEVELS[lvl]
                                scores = ns.get('bloom_scores', {})
                                lvl_data = scores.get(str(lvl), {'score': 0, 'total': 0, 'types_done': []})
                                score_pct = lvl_data.get('score', 0)
                                types_done = lvl_data.get('types_done', [])
                                unlocked = check_level_unlocked(lvl, scores, target_levels, bloom_ceiling)
                                passed = score_pct >= bl['pass_threshold'] and len(types_done) >= 2

                                # Status — phân biệt giữa prereq-locked và score-locked
                                if passed:
                                    status_icon, status_text, border_color = '✅', 'Đã vượt qua', bl['hex']
                                elif unlocked:
                                    status_icon, status_text, border_color = '🔓', 'Đang học', '#374151'
                                elif lvl > bloom_ceiling:
                                    status_icon, status_text, border_color = '⛔', f'Cần prerequisite (≤L{bloom_ceiling})', '#7f1d1d'
                                else:
                                    status_icon, status_text, border_color = '🔒', 'Chưa mở khóa', '#1f2937'

                                with ui.card().classes(f'w-full p-4 rounded-xl border-2').style(f'border-color:{border_color};background:{"rgba(0,0,0,0.3)" if unlocked else "rgba(0,0,0,0.6)"}'):
                                    with ui.row().classes('w-full items-center justify-between'):
                                        with ui.row().classes('items-center gap-3'):
                                            ui.label(f'{bl["icon"]}').classes('text-2xl')
                                            with ui.column().classes('gap-0'):
                                                ui.label(f'L{lvl} {bl["vi"]}').classes(f'font-bold {"text-white" if unlocked else "text-gray-600"}')
                                                ui.label(bl['description']).classes('text-xs text-gray-500')
                                        with ui.column().classes('items-end gap-0'):
                                            ui.label(f'{status_icon} {status_text}').classes('text-sm font-bold')
                                            ui.label(f'{score_pct:.0%}').classes('text-xs text-gray-400')

                                    # Progress bar
                                    with ui.element('div').classes('w-full bg-gray-800 rounded-full h-2 mt-2'):
                                        w = min(100, score_pct * 100)
                                        ui.element('div').classes('h-2 rounded-full transition-all').style(f'width:{w}%;background:{bl["hex"]}')

                                    # Assessment buttons (only if unlocked)
                                    if unlocked:
                                        with ui.row().classes('w-full mt-3 gap-2 flex-wrap'):
                                            for atype in bl['assessment_types']:
                                                done = atype in types_done
                                                label = _assessment_label(atype)
                                                btn = ui.button(
                                                    f'{"✓ " if done else ""}{label}',
                                                    on_click=lambda l=lvl, a=atype: start_assessment(l, a)
                                                ).classes(
                                                    f'text-xs py-1 px-3 rounded-lg {"bg-gray-700 text-gray-300" if not done else "bg-green-800 text-green-300"}'
                                                ).props('no-caps dense')

                    def _assessment_label(atype):
                        labels = {
                            'mcq_recall': '🗳️ Trắc nghiệm', 'flashcard': '📚 Flashcard',
                            'matching_basic': '🔗 Nối từ', 'mcq_comprehension': '💡 MCQ Giải thích',
                            'fill_blank': '✍️ Điền từ', 'matching': '🔗 Nối từ', 'explain': '💬 Giải thích',
                            'scenario_mcq': '🎯 Tình huống', 'case_study': '📋 Case Study',
                            'fill_blank_advanced': '✍️ Điền từ NC', 'socratic': '🤖 Socratic',
                            'compare_contrast': '⚖️ So sánh', 'analysis_essay': '📝 Phân tích',
                            'debate': '🎭 Biện luận', 'critique': '🔍 Phê bình',
                            'socratic_advanced': '🤖 Socratic NC',
                            'design_task': '🎨 Thiết kế', 'project': '🏗️ Dự án',
                            'creative_proposal': '💡 Đề xuất',
                            'practice_exercise': '📝 Bài tập',
                        }
                        return labels.get(atype, atype)

                    async def start_assessment(bloom_level, assessment_type):
                        # === SOCRATIC MODE ===
                        if assessment_type in ('socratic', 'socratic_advanced'):
                            await _start_socratic_assessment(bloom_level, assessment_type)
                            return
                        
                        # === PRACTICE EXERCISE MODE ===
                        if assessment_type == 'practice_exercise':
                            await _start_practice_exercise(bloom_level)
                            return

                        import asyncio; await asyncio.sleep(0.1)
                        assess_area.clear()
                        with assess_area:
                            ui.button(icon='arrow_back', on_click=lambda: __import__('nicegui').background_tasks.create(delayed_render_bloom_ladder())).props('flat color=white')
                            bl = BLOOM_LEVELS[bloom_level]
                            ui.label(f'{bl["icon"]} L{bloom_level} {bl["vi"]} — {_assessment_label(assessment_type)}').classes('text-lg font-bold text-white mb-4')
                            with ui.row().classes('items-center gap-2'):
                                ui.spinner('dots', size='lg', color='cyan')
                                ui.label('AI đang sinh câu hỏi...').classes('text-cyan-300 animate-pulse')

                        # Load content pack for questions
                        pack = get_content_pack_sync(node_id, node_info, tree_data, username)
                        if not pack:
                            pack = await get_or_create_content_pack(node_id, node_info, tree_data, username)

                        qbank = pack.get('question_bank', {})
                        questions = qbank.get(f'L{bloom_level}', [])

                        # Filter by type
                        typed_qs = [q for q in questions if q.get('type') == assessment_type]
                        
                        # Only fallback to first 5 if NOT socratic and NOT flashcard and NOT matching (specific types need their formats)
                        if not typed_qs and assessment_type not in ('matching', 'matching_basic', 'flashcard', 'socratic', 'socratic_advanced'):
                            typed_qs = questions[:5] if questions else []

                        if not typed_qs:
                            # Enrich node_content with study material if available
                            enriched_content = node_content
                            if pack and pack.get('study_material'):
                                sm = pack['study_material']
                                sm_content = sm.get('detailed_content', '')
                                if sm_content:
                                    enriched_content += f"\n\n[NỘI DUNG HỌC TẬP]\n{sm_content}"
                                
                                concepts = sm.get('key_concepts', [])
                                if concepts:
                                    enriched_content += "\n\n[KHÁI NIỆM CỐT LÕI]\n" + "\n".join(
                                        [f"- {c.get('term', '')}: {c.get('definition', '')}" if isinstance(c, dict) else str(c) for c in concepts]
                                    )
                                    
                            # Generate on the fly
                            typed_qs = await _generate_questions_live(bloom_level, assessment_type, node_title, enriched_content)

                        if not typed_qs:
                            assess_area.clear()
                            with assess_area:
                                ui.label('❌ Không thể tạo câu hỏi.').classes('text-red-400')
                                ui.button('Quay lại', on_click=lambda: __import__('nicegui').background_tasks.create(delayed_render_bloom_ladder())).props('color=blue outline')
                            return

                        await render_assessment_session(typed_qs, bloom_level, assessment_type)

                    async def _start_practice_exercise(bloom_level):
                        """Bài tập thực hành 2 pha: Guided → Assessment."""
                        bl = BLOOM_LEVELS[bloom_level]
                        assessment_type = 'practice_exercise'

                        # Gather context for exercise generation
                        from node_content_engine import _gather_node_context
                        ref_materials = _gather_node_context(node_id, node_info, tree_data)

                        exercise_state = {
                            'phase': 'guided',  # 'guided' or 'assessment'
                            'problem': None,
                            'similar_problem': None,
                        }

                        async def _generate_exercise(phase_type='guided', previous_problem=''):
                            """AI sinh bài tập dựa trên tài nguyên node."""
                            model = get_chat_model()
                            if not model:
                                return None
                            ref_text = ref_materials[:4000] if ref_materials else ''
                            bloom_verbs = ', '.join(bl['verbs_vi'])

                            if phase_type == 'assessment' and previous_problem:
                                prompt = f"""Bạn là chuyên gia giáo dục. Hãy tạo 1 bài tập TƯƠNG TỰ (cùng dạng, khác dữ liệu/số liệu) với bài tập sau để ĐÁNH GIÁ năng lực sinh viên.

BÀI TẬP GỐC (đã làm ở pha hướng dẫn):
{previous_problem}

MÔN HỌC: {tree_data.get('course_name', 'Môn học')}
BÀI HỌC: {node_title}
MỨC BLOOM: L{bloom_level} {bl['vi']} — Động từ: {bloom_verbs}

TÀI LIỆU THAM KHẢO:
{ref_text}

OUTPUT FORMAT (JSON):
{{
    "title": "Tiêu đề bài tập",
    "problem": "Đề bài chi tiết (Markdown). Nếu có tính toán, đưa số liệu cụ thể.",
    "hints": ["Gợi ý 1 (ẩn)", "Gợi ý 2 (ẩn)"],
    "rubric": ["Tiêu chí chấm 1", "Tiêu chí chấm 2", "Tiêu chí chấm 3"],
    "sample_answer": "Đáp án mẫu chi tiết"
}}
}}
YÊU CẦU: Bài tập phải KHÁC dữ liệu so với bài gốc nhưng CÙNG DẠNG và CÙNG ĐỘ KHÓ. Tiếng Việt. Chỉ trả về JSON. BẮT BUỘC bao bọc TẤT CẢ công thức/ký hiệu toán học, nhiệt độ bằng `$` (trong dòng) hoặc `$$` (tách dòng). TRONG JSON BẮT BUỘC DÙNG \\ CHO LATEX (ví dụ \\frac thay vì \\frac). KHÔNG DÙNG DẤU GẠCH CHÉO NGƯỢC (\\) NGOẠI TRỪ CÁC KÝ TỰ ĐIỀU KHIỂN CHUẨN CỦA JSON."""
                            else:
                                prompt = f"""Bạn là chuyên gia giáo dục. Hãy tạo 1 bài tập thực hành cho sinh viên.

MÔN HỌC: {tree_data.get('course_name', 'Môn học')}
BÀI HỌC: {node_title}
NỘI DUNG: {node_content[:500]}
MỨC BLOOM: L{bloom_level} {bl['vi']} — Động từ: {bloom_verbs}

TÀI LIỆU THAM KHẢO:
{ref_text}

OUTPUT FORMAT (JSON):
{{
    "title": "Tiêu đề bài tập",
    "problem": "Đề bài chi tiết (Markdown). Nếu có tính toán, đưa số liệu cụ thể. Nếu là phân tích, đưa tình huống rõ ràng.",
    "hints": ["Gợi ý 1 (ẩn)", "Gợi ý 2 (ẩn)"],
    "rubric": ["Tiêu chí chấm 1", "Tiêu chí chấm 2", "Tiêu chí chấm 3"],
    "sample_answer": "Đáp án mẫu chi tiết"
}}
}}
YÊU CẦU: Bài tập phải BÁM SÁT tài liệu tham khảo, phù hợp mức Bloom {bl['vi']}. Tiếng Việt. Chỉ trả về JSON. BẮT BUỘC bao bọc TẤT CẢ công thức/ký hiệu toán học, nhiệt độ bằng `$` (trong dòng) hoặc `$$` (tách dòng). TRONG JSON BẮT BUỘC DÙNG \\ CHO LATEX (ví dụ \\frac thay vì \\frac). KHÔNG DÙNG DẤU GẠCH CHÉO NGƯỢC (\\) NGOẠI TRỪ CÁC KÝ TỰ ĐIỀU KHIỂN CHUẨN CỦA JSON."""

                            try:
                                response = await run.io_bound(model.generate_content, prompt)
                                import re as _re
                                match = _re.search(r'\{.*\}', response.text, _re.DOTALL)
                                if match:
                                    json_str = match.group(0)
                                    try:
                                        return json.loads(json_str, strict=False)
                                    except json.JSONDecodeError:
                                        # Fallback cleanup for unescaped backslashes
                                        json_str = json_str.replace('\\', '\\\\')
                                        json_str = json_str.replace('\\\\n', '\\n').replace('\\\\"', '\\"')
                                        return json.loads(json_str, strict=False)
                            except Exception as e:
                                print(f"[PracticeExercise] Generate error: {e}")
                            return None

                        async def _ai_grade(problem_text, student_answer, rubric, sample_answer):
                            """AI chấm bài làm của sinh viên."""
                            model = get_chat_model()
                            if not model:
                                return None
                            prompt = f"""Bạn là giảng viên đại học. Hãy chấm bài làm của sinh viên.

ĐỀ BÀI:
{problem_text}

BÀI LÀM CỦA SINH VIÊN:
{student_answer}

ĐÁP ÁN MẪU:
{sample_answer}

TIÊU CHÍ CHẤM (RUBRIC):
{chr(10).join(f'- {r}' for r in rubric)}

OUTPUT FORMAT (JSON):
{{
    "score": 0.0,
    "max_score": 1.0,
    "verdict": "passed hoặc failed",
    "feedback": "Nhận xét chi tiết về bài làm (Markdown, 3-5 câu)",
    "strengths": ["Điểm mạnh 1", "Điểm mạnh 2"],
    "improvements": ["Cần cải thiện 1", "Cần cải thiện 2"],
    "rubric_scores": [
        {{"criterion": "Tiêu chí 1", "score": "Đạt/Chưa đạt", "comment": "Nhận xét"}}
    ]
}}
QUY TẮC: score từ 0.0 đến 1.0. verdict="passed" nếu score >= 0.6. Công bằng, khuyến khích. Tiếng Việt. Chỉ trả về JSON."""

                            try:
                                response = await run.io_bound(model.generate_content, prompt)
                                import re as _re
                                match = _re.search(r'\{.*\}', response.text, _re.DOTALL)
                                if match:
                                    return json.loads(match.group(0))
                            except Exception as e:
                                print(f"[PracticeExercise] Grade error: {e}")
                            return None

                        async def render_exercise_phase(phase_type='guided'):
                            """Generate exercise then redirect to Gia sư AI tab."""
                            import asyncio; await asyncio.sleep(0.1)
                            assess_area.clear()
                            with assess_area:
                                ui.button(icon='arrow_back', on_click=lambda: __import__('nicegui').background_tasks.create(delayed_render_bloom_ladder())).props('flat color=white')
                                phase_label = '📝 Pha 1: Bài tập Hướng dẫn' if phase_type == 'guided' else '🎯 Pha 2: Bài tập Đánh giá'
                                with ui.row().classes('items-center gap-2 mb-2'):
                                    ui.label(f'{bl["icon"]} L{bloom_level} {bl["vi"]}').classes('text-lg font-bold text-white')
                                    ui.badge(phase_label).props(f'color={"blue" if phase_type == "guided" else "orange"}')
                                with ui.row().classes('items-center gap-2'):
                                    ui.spinner('dots', size='lg', color='cyan')
                                    ui.label('AI đang sinh bài tập...').classes('text-cyan-300 animate-pulse')

                            # Generate exercise
                            if phase_type == 'guided':
                                exercise = await _generate_exercise('guided')
                                exercise_state['problem'] = exercise
                            else:
                                prev_problem = exercise_state['problem'].get('problem', '') if exercise_state['problem'] else ''
                                exercise = await _generate_exercise('assessment', prev_problem)
                                exercise_state['similar_problem'] = exercise

                            if not exercise:
                                import asyncio; await asyncio.sleep(0.1)
                                assess_area.clear()
                                with assess_area:
                                    ui.label('❌ Không thể tạo bài tập.').classes('text-red-400')
                                    ui.button('Quay lại', on_click=lambda: __import__('nicegui').background_tasks.create(delayed_render_bloom_ladder())).props('color=blue outline')
                                return

                            # === REDIRECT TO GIA SƯ AI TAB ===
                            # Save exercise data for the tutor tab to pick up
                            app.storage.user['pending_exercise'] = {
                                'exercise': exercise,
                                'phase': phase_type,
                                'bloom_level': bloom_level,
                                'bloom_vi': bl['vi'],
                                'bloom_icon': bl['icon'],
                                'bloom_hex': bl['hex'],
                                'node_id': node_id,
                                'node_title': node_title,
                                'subject_id': subject_id,
                                'username': username,
                                'target_levels': target_levels,
                                'course_name': tree_data.get('course_name', 'Môn học'),
                            }

                            # Also update omni_context for the AI tutor
                            if 'omni_context' in app.storage.user:
                                app.storage.user['omni_context']['context_mode'] = 'exercise_tutor'
                                app.storage.user['omni_context']['exercise_problem'] = exercise.get('problem', '')
                                app.storage.user['omni_context']['exercise_title'] = exercise.get('title', '')
                                app.storage.user['omni_context']['exercise_bloom_level'] = f"L{bloom_level} {bl['vi']}"
                                app.storage.user['omni_context']['node_content'] = f"[BÀI TẬP] {exercise.get('title', '')}\n{exercise.get('problem', '')}"

                            # Show confirmation then navigate
                            assess_area.clear()
                            with assess_area:
                                with ui.card().classes('w-full max-w-lg mx-auto p-8 bg-gradient-to-br from-blue-900/60 to-indigo-900/60 border border-blue-500 rounded-2xl text-center'):
                                    ui.html('<div style="font-size:64px">📝</div>').classes('mb-3')
                                    ui.label('Đề bài đã được tạo!').classes('text-2xl font-extrabold text-white mb-2')
                                    ui.label(f'{exercise.get("title", "Bài tập")}').classes('text-lg text-blue-200 mb-4')
                                    if phase_type == 'guided':
                                        ui.label('Đang chuyển sang Gia sư AI để làm bài...').classes('text-sm text-blue-300 animate-pulse')
                                    else:
                                        ui.label('Đang chuyển sang Gia sư AI — Bài đánh giá (không có hỗ trợ)...').classes('text-sm text-orange-300 animate-pulse')

                            # Trigger python-side tab switch safely
                            import asyncio
                            await asyncio.sleep(1.5)
                            app.storage.user['force_tab_switch'] = 'Gia sư AI (Omni)'

                        # Start pha 1
                        await render_exercise_phase('guided')

                    async def _start_learning_coach(phase):
                        """Bắt đầu phiên Learning Coach (GROW Model)."""
                        import asyncio; await asyncio.sleep(0.1)
                        assess_area.clear()
                        with assess_area:
                            ui.button(icon='arrow_back', on_click=lambda: __import__('nicegui').background_tasks.create(delayed_render_bloom_ladder())).props('flat color=white')
                            with ui.row().classes('items-center gap-2 mb-3 w-full'):
                                ui.label('🧭').classes('text-3xl')
                                with ui.column().classes('gap-0'):
                                    ui.label('Huấn luyện viên Học tập').classes('text-lg font-bold text-white')
                                    ui.label('Tự học (Self-Regulated Learning)').classes('text-xs text-gray-400')
                                mood_label = ui.label('Trạng thái: 😐 Bình thường').classes('ml-auto bg-gray-800 text-gray-300 px-3 py-1 rounded-full text-xs font-bold border border-gray-600 transition-colors')

                            chat_area = ui.scroll_area().classes('w-full border-2 border-gray-800 rounded-xl bg-[#0d1117] p-4 transition-colors').style('height:400px')
                            with ui.row().classes('w-full no-wrap items-center gap-2 mt-3'):
                                user_input = ui.input(placeholder='Nhập câu trả lời...').props('rounded outlined dark dense').classes('w-full')
                                btn_send = ui.button(icon='send').props('round flat color=emerald')

                        from persona_engine import build_coach_prompt, get_learning_coach
                        coach = get_learning_coach()
                        node_ctx = {
                            'title': node_title, 
                            'content': node_content[:5000],
                        }
                        
                        try:
                            from analytics_engine import get_learning_profile
                            learning_profile = get_learning_profile(username, subject_id, node_id)
                        except Exception as e:
                            print(f"Lỗi tải learning_profile: {e}")
                            learning_profile = ""
                            
                            
                        system_prompt = build_coach_prompt(phase, node_ctx, learning_profile, "neutral")

                        chat_state = {'chat_session': None, 'sentiment': 'neutral'}

                        def update_mood_ui(sentiment: str):
                            moods = {
                                'neutral': ('😐 Bình thường', 'bg-gray-800 text-gray-300 border-gray-600', 'border-gray-800'),
                                'confused': ('🤔 Bối rối', 'bg-amber-900/50 text-amber-300 border-amber-600', 'border-amber-900/50'),
                                'frustrated': ('😫 Tuyệt vọng / Áp lực', 'bg-red-900/50 text-red-300 border-red-600', 'border-red-900/50'),
                                'excited': ('😎 Tự tin / Phấn khích', 'bg-purple-900/50 text-purple-300 border-purple-600', 'border-purple-900/50')
                            }
                            text, btn_class, border_class = moods.get(sentiment, moods['neutral'])
                            mood_label.set_text(f"Trạng thái: {text}")
                            mood_label.classes(replace=f'ml-auto px-3 py-1 rounded-full text-xs font-bold border transition-colors {btn_class}')
                            chat_area.classes(replace=f'w-full border-2 rounded-xl bg-[#0d1117] p-4 transition-colors {border_class}')

                        def process_ai_response(raw_text: str):
                            import re
                            from gemini_helper import extract_json_from_text
                            sentiment_data = extract_json_from_text(raw_text)
                            sentiment = sentiment_data.get('sentiment', 'neutral')
                            chat_state['sentiment'] = sentiment
                            update_mood_ui(sentiment)
                            
                            # --- PHÁT HIỆN LỖ HỔNG VÀ TỰ ĐỘNG TẠO MICRO-NODE ---
                            gap = sentiment_data.get('prerequisite_gap')
                            if gap and str(gap).strip().lower() != 'null':
                                import time
                                new_node_id = f"micro_gap_{int(time.time())}"
                                if 'nodes' not in tree_data: tree_data['nodes'] = {}
                                tree_data['nodes'][new_node_id] = {
                                    "id": new_node_id,
                                    "type": "micro",
                                    "title": f"Bổ trợ: {gap}",
                                    "description": f"AI tự động tạo bài học này vì phát hiện bạn bị hổng kiến thức nền tảng về '{gap}'.",
                                    "bloom_profile": {"1": 1.0, "2": 1.0},
                                    "alpha_base": 10
                                }
                                if 'edges' not in tree_data: tree_data['edges'] = []
                                # Cho bài học mới là tiền đề của bài học hiện tại
                                tree_data['edges'].append({"source": new_node_id, "target": node_id})
                                
                                # Lưu lại tree_data
                                tree_file = f"user_data/{username}/trees/{subject_id}.json"
                                import json
                                try:
                                    with open(tree_file, 'w', encoding='utf-8') as f:
                                        json.dump(tree_data, f, ensure_ascii=False, indent=2)
                                    ui.notify(f"🌱 Đã tự động tạo Bài học Bổ trợ: {gap} trên đồ thị!", type='positive', position='center')
                                except Exception as e:
                                    print(f"Lỗi lưu Micro-Node: {e}")
                            
                            # Xóa block JSON khỏi text hiển thị
                            clean_text = re.sub(r'\{[^{}]*"sentiment"[^{}]*\}', '', raw_text, flags=re.IGNORECASE)
                            clean_text = clean_text.replace('--- YÊU CẦU BẮT BUỘC (PHÂN TÍCH CẢM XÚC & KIẾN THỨC) ---', '').replace('--- YÊU CẦU BẮT BUỘC (PHÂN TÍCH CẢM XÚC) ---', '').replace('---SEPARATOR---', '').strip()
                            return clean_text

                        async def append_msg(is_ai, content):
                            with chat_area:
                                align = '' if is_ai else 'flex-row-reverse'
                                bg = 'bg-emerald-900/30 border-emerald-800' if is_ai else 'bg-purple-900/30 border-purple-800'
                                icon_name = coach['icon'] if is_ai else '👤'
                                with ui.row().classes(f'w-full no-wrap items-start gap-3 mb-4 {align}'):
                                    ui.label(icon_name).classes('text-2xl mt-1')
                                    with ui.column().classes(f'{bg} p-3 rounded-2xl max-w-[85%] border'):
                                        ui.markdown(content)
                            try:
                                chat_area.scroll_to(percent=100)
                            except Exception:
                                pass

                        async def init_chat():
                            try:
                                from gemini_helper import get_chat_model
                                from nicegui import run
                                model = get_chat_model()
                                if not model:
                                    await append_msg(True, '**Lỗi:** Không kết nối được AI.')
                                    return
                                chat = model.start_chat()
                                chat_state['chat_session'] = chat
                                response = await run.io_bound(chat.send_message, system_prompt)
                                clean_text = process_ai_response(response.text)
                                await append_msg(True, clean_text)
                            except Exception as e:
                                await append_msg(True, f'**Lỗi khởi tạo Coach:** {str(e)}')

                        async def send_msg():
                            msg = user_input.value.strip()
                            if not msg or not chat_state['chat_session']:
                                return
                            user_input.value = ''
                            await append_msg(False, msg)
                            try:
                                from nicegui import run
                                
                                # Auto-Persona Shifting injection
                                injection = ""
                                if chat_state['sentiment'] == 'frustrated' or chat_state['sentiment'] == 'confused':
                                    injection = "\n[SYSTEM INSTRUCTION: Phát hiện sinh viên đang bối rối/áp lực. Hãy sử dụng Persona 'Gia sư thấu cảm' (Empathetic Guide) để xoa dịu, an ủi ngay lập tức! ĐỪNG QUÊN XUẤT JSON SENTIMENT CUỐI CÙNG.]\n"
                                elif chat_state['sentiment'] == 'excited':
                                    injection = "\n[SYSTEM INSTRUCTION: Phát hiện sinh viên đang quá tự tin/tự mãn. Hãy sử dụng Persona 'Luật sư của Quỷ' (Devil's Advocate) để phản biện, đưa ra câu hỏi hóc búa để thử thách! ĐỪNG QUÊN XUẤT JSON SENTIMENT CUỐI CÙNG.]\n"
                                
                                full_msg = msg + injection
                                
                                response = await run.io_bound(chat_state['chat_session'].send_message, full_msg)
                                clean_text = process_ai_response(response.text)
                                await append_msg(True, clean_text)
                            except Exception as ex:
                                await append_msg(True, f'**Lỗi:** {ex}')

                        user_input.on('keydown.enter', send_msg)
                        btn_send.on_click(send_msg)
                        
                        import asyncio
                        await asyncio.sleep(0.1)
                        await init_chat()

                    async def _start_socratic_assessment(bloom_level, assessment_type):
                        try:
                            from socratic_tutor_engine import SocraticSession, save_session_result
                        except ImportError:
                            assess_area.clear()
                            with assess_area:
                                ui.label('❌ Module socratic_tutor_engine chưa cài.').classes('text-red-400')
                                ui.button('Quay lại', on_click=lambda: __import__('nicegui').background_tasks.create(delayed_render_bloom_ladder())).props('color=blue outline')
                            return

                        session = SocraticSession(
                            bloom_level=bloom_level,
                            difficulty_alpha=node_info.get('alpha_base', 50),
                            use_grow=(bloom_level >= 3),
                        )
                        from node_content_engine import _gather_node_context
                        ref_materials = _gather_node_context(node_id, node_info, tree_data)
                        
                        node_ctx = {
                            'title': node_title, 
                            'content': node_content[:10000],
                            'ref_materials': ref_materials
                        }
                        system_prompt = session.start(node_ctx)

                        assess_area.clear()
                        with assess_area:
                            # Header
                            ui.button(icon='arrow_back', on_click=lambda: __import__('nicegui').background_tasks.create(delayed_render_bloom_ladder())).props('flat color=white')
                            bl = BLOOM_LEVELS[bloom_level]
                            with ui.row().classes('items-center gap-2 mb-3'):
                                ui.label(f'{session.persona["icon"]}').classes('text-3xl')
                                with ui.column().classes('gap-0'):
                                    ui.label(f'{session.persona["name"]}').classes('text-lg font-bold text-white')
                                    ui.label(f'L{bloom_level} {bl["vi"]} — {session.persona["strategy"]}').classes('text-xs text-gray-400')

                            # Chat area
                            chat_area = ui.scroll_area().classes('w-full border border-gray-800 rounded-xl bg-[#0d1117] p-4').style('height:400px')
                            with ui.row().classes('w-full no-wrap items-center gap-2 mt-3'):
                                user_input = ui.input(placeholder='Nhập câu trả lời...').props('rounded outlined dark dense').classes('w-full')
                                btn_send = ui.button(icon='send').props('round flat color=cyan')

                        chat_state = {'chat_session': None, 'socratic': session}

                        async def append_msg(is_ai, content):
                            with chat_area:
                                align = '' if is_ai else 'flex-row-reverse'
                                bg = 'bg-cyan-900/30 border-cyan-800' if is_ai else 'bg-purple-900/30 border-purple-800'
                                icon_name = session.persona['icon'] if is_ai else '👤'
                                with ui.row().classes(f'w-full no-wrap items-start gap-3 mb-4 {align}'):
                                    ui.label(icon_name).classes('text-2xl mt-1')
                                    with ui.column().classes(f'{bg} p-3 rounded-2xl max-w-[85%] border'):
                                        ui.markdown(content)
                            try:
                                chat_area.scroll_to(percent=100)
                            except Exception:
                                pass

                        async def init_chat():
                            try:
                                model = get_chat_model()
                                if not model:
                                    await append_msg(True, '**Lỗi:** Không kết nối được AI.')
                                    return
                                chat = model.start_chat()
                                chat_state['chat_session'] = chat
                                response = await run.io_bound(chat.send_message, system_prompt)
                                result = session.process_ai_response(response.text)
                                await append_msg(True, result['clean_text'])
                            except Exception as e:
                                await append_msg(True, f'**Lỗi khởi tạo AI:** {str(e)}')

                        async def send_msg():
                            msg = user_input.value.strip()
                            if not msg or not chat_state['chat_session']:
                                return
                            user_input.value = ''
                            await append_msg(False, msg)
                            try:
                                response = await run.io_bound(chat_state['chat_session'].send_message, msg)
                                result = session.process_ai_response(response.text)
                                await append_msg(True, result['clean_text'])

                                if result['should_stop']:
                                    btn_send.disable()
                                    user_input.disable()
                                    report = session.get_report()
                                    is_correct = (report['final_verdict'] == 'passed')
                                    # Update scores
                                    bs2 = load_bloom_state(username, subject_id)
                                    ns2 = bs2.get('nodes', {}).get(node_id, create_node_bloom_scores(target_levels))
                                    update_bloom_score(ns2, bloom_level, is_correct, assessment_type, target_levels)
                                    bs2.setdefault('nodes', {})[node_id] = ns2
                                    save_bloom_state(username, subject_id, bs2)
                                    # Save session
                                    try:
                                        save_session_result(username, subject_id, node_id, report)
                                    except Exception:
                                        pass
                                    # Show result
                                    trophy = '🏆' if is_correct else '💪'
                                    with chat_area:
                                        verdict_text = 'ĐẠT CHUẨN! Chúc mừng!' if is_correct else 'Chưa đạt. Hãy ôn tập và thử lại!'
                                        ui.label(f'{trophy} {verdict_text}').classes(f'text-lg font-bold mt-3 {"text-green-400" if is_correct else "text-amber-400"}')
                                        ui.button('🔙 Quay lại Bloom Ladder', on_click=lambda: __import__('nicegui').background_tasks.create(delayed_render_bloom_ladder())).classes('mt-2 bg-indigo-600 text-white').props('no-caps')
                            except Exception as ex:
                                await append_msg(True, f'**Lỗi:** {ex}')

                        user_input.on('keydown.enter', send_msg)
                        btn_send.on_click(send_msg)
                        
                        import asyncio
                        await asyncio.sleep(0.1) # yield to event loop to render UI
                        await init_chat()

                    async def _generate_questions_live(bloom_level, atype, title, content):
                        model = get_chat_model()
                        if not model:
                            return []
                        bl = BLOOM_LEVELS[bloom_level]
                        # Gather reference materials for better question quality
                        from node_content_engine import _gather_node_context
                        ref_materials = _gather_node_context(node_id, node_info, tree_data)
                        ref_section = ''
                        if ref_materials:
                            ref_section = f"\n\nTÀI LIỆU THAM KHẢO:\n{ref_materials[:3000]}\n"
                        
                        if atype in ('matching', 'matching_basic'):
                            prompt = f"""Tạo 1 bài loại Nối từ (matching) cho bài "{title}", mức Bloom L{bloom_level} ({bl['vi']}).
Nội dung: {content[:500]}
{ref_section}
OUTPUT: JSON array có 1 phần tử (vì nối từ là 1 bài lớn), định dạng:
{{
  "type": "{atype}",
  "question": "Nối các thuật ngữ với định nghĩa đúng",
  "pairs": [
    {{"left": "Thuật ngữ 1", "right": "Định nghĩa 1"}},
    {{"left": "Thuật ngữ 2", "right": "Định nghĩa 2"}},
    {{"left": "Thuật ngữ 3", "right": "Định nghĩa 3"}},
    {{"left": "Thuật ngữ 4", "right": "Định nghĩa 4"}}
  ],
  "explanation": "Giải thích tại sao các cặp này đi với nhau"
}}
Chỉ trả về JSON array."""
                        else:
                            prompt = f"""Tạo 3 câu hỏi loại {atype} cho bài "{title}", mức Bloom L{bloom_level} ({bl['vi']}).
Nội dung: {content[:500]}
{ref_section}
OUTPUT: JSON array, mỗi phần tử có "type":"{atype}", "question", "options":{{"A":"..","B":"..","C":"..","D":".."}}, "correct":"A", "explanation"
{'Hãy dựa trên tài liệu tham khảo để tạo câu hỏi chính xác.' if ref_materials else ''}
Chỉ trả về JSON array."""

                        try:
                            response = await run.io_bound(model.generate_content, prompt)
                            match = re.search(r'\[.*\]', response.text, re.DOTALL)
                            if match:
                                return [q for q in json.loads(match.group(0)) if isinstance(q, dict)]
                        except Exception as e:
                            print(f"[BloomHub] Live gen error: {e}")
                        return []

                    async def render_assessment_session(questions, bloom_level, assessment_type):
                        state = {'idx': 0, 'correct': 0, 'total': len(questions)}
                        bl = BLOOM_LEVELS[bloom_level]

                        def render_q():
                            assess_area.clear()
                            if state['idx'] >= state['total']:
                                render_results()
                                return

                            q = questions[state['idx']]
                            with assess_area:
                                ui.button(icon='arrow_back', on_click=lambda: __import__('nicegui').background_tasks.create(delayed_render_bloom_ladder())).props('flat color=white')
                                # Progress
                                pct = state['idx'] / state['total'] * 100
                                with ui.element('div').classes('w-full bg-gray-800 rounded-full h-2 mb-4'):
                                    ui.element('div').classes('h-2 rounded-full').style(f'width:{pct}%;background:{bl["hex"]}')
                                ui.label(f'Câu {state["idx"]+1}/{state["total"]}').classes('text-sm text-gray-400 mb-2')

                                # Question
                                q_text = q.get('question', q.get('front', q.get('sentence', str(q))))
                                
                                # MCQ options
                                opts = q.get('options', {})
                                if assessment_type == 'flashcard':
                                    answer = q.get('back', q.get('answer', q.get('correct', '')))
                                    
                                    # Inject flashcard CSS (same as flashcard_page.py)
                                    ui.add_head_html("""
                                    <style>
                                    .bloom-flashcard-box { perspective: 1200px; width: 100%; max-width: 600px; height: 320px; margin: 0 auto; }
                                    .bloom-flashcard-flip { position: relative; width: 100%; height: 100%; transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1); transform-style: preserve-3d; }
                                    .bloom-flashcard-flip.flipped { transform: rotateY(180deg); }
                                    .bloom-flashcard-face { position: absolute; width: 100%; height: 100%; backface-visibility: hidden; -webkit-backface-visibility: hidden; border-radius: 24px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 32px; box-sizing: border-box; }
                                    .bloom-flashcard-face.front { background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%); color: white; border: 2px solid rgba(99, 102, 241, 0.3); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1); }
                                    .bloom-flashcard-face.back { background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%); color: white; transform: rotateY(180deg); border: 2px solid rgba(16, 185, 129, 0.3); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1); }
                                    </style>
                                    """)
                                    
                                    fc_state = {"flipped": False}
                                    card_wrapper = ui.element('div').classes('bloom-flashcard-box cursor-pointer')
                                    with card_wrapper:
                                        inner = ui.element('div').classes('bloom-flashcard-flip')
                                        with inner:
                                            with ui.element('div').classes('bloom-flashcard-face front'):
                                                ui.label('💡 CÂU HỎI').classes('text-xs text-indigo-300 font-bold tracking-widest mb-4 uppercase')
                                                ui.label(q_text).classes('text-xl font-bold text-center leading-relaxed')
                                                ui.label('Nhấp để lật thẻ →').classes('text-xs text-indigo-400 mt-4 italic')
                                            with ui.element('div').classes('bloom-flashcard-face back'):
                                                ui.label('📖 ĐÁP ÁN').classes('text-xs text-emerald-300 font-bold tracking-widest mb-4 uppercase')
                                                ui.label(answer).classes('text-base text-center leading-relaxed')
                                    
                                    def toggle_flip():
                                        fc_state["flipped"] = not fc_state["flipped"]
                                        if fc_state["flipped"]:
                                            inner.classes(add='flipped')
                                        else:
                                            inner.classes(remove='flipped')
                                    card_wrapper.on('click', toggle_flip)
                                    
                                    # Action buttons (always visible, same as flashcard_page.py)
                                    with ui.row().classes('w-full max-w-xl mx-auto gap-6 mt-8 justify-center'):
                                        ui.button('❌ Chưa biết', on_click=lambda: _record_and_next(False, q)).classes(
                                            'bg-red-600/80 text-white px-8 py-3 rounded-xl font-bold text-lg hover:bg-red-500 transition-all shadow-lg'
                                        ).props('no-caps')
                                        ui.button('✅ Đã biết', on_click=lambda: _record_and_next(True, q)).classes(
                                            'bg-green-600/80 text-white px-8 py-3 rounded-xl font-bold text-lg hover:bg-green-500 transition-all shadow-lg'
                                        ).props('no-caps')

                                elif assessment_type in ('matching', 'matching_basic'):
                                    pairs = q.get('pairs', [])
                                    if not pairs:
                                        ui.label('Dữ liệu Nối từ bị lỗi (thiếu cặp). Đang bỏ qua...').classes('text-red-400')
                                        ui.timer(2, lambda: _record_and_next(False, q), once=True)
                                        return

                                    import random
                                    left_items = [p['left'] for p in pairs]
                                    right_items = [p['right'] for p in pairs]
                                    random.shuffle(left_items)
                                    random.shuffle(right_items)
                                    
                                    # Create a closure-safe state
                                    m_state = {
                                        'selected_l': None,
                                        'selected_r': None,
                                        'matches': {}, # L -> R
                                        'l_btns': {},
                                        'r_btns': {}
                                    }
                                    
                                    ui.label(q.get('question', 'Nối các khái niệm tương ứng')).classes('text-lg font-bold text-white mb-6 bg-white/5 p-4 rounded-xl border border-white/10')
                                    
                                    with ui.row().classes('w-full gap-8 items-start justify-center'):
                                        # Left Column
                                        with ui.column().classes('w-64 gap-3'):
                                            ui.label('KHÁI NIỆM').classes('text-xs font-bold text-gray-500 tracking-widest text-center w-full')
                                            for it in left_items:
                                                def select_l(item=it):
                                                    m_state['selected_l'] = item
                                                    for b in m_state['l_btns'].values():
                                                        b.classes(remove='bg-cyan-600 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.4)]', add='bg-gray-800/40 border-gray-700')
                                                    m_state['l_btns'][item].classes(add='bg-cyan-600 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.4)]', remove='bg-gray-800/40 border-gray-700')
                                                    check_match()
                                                
                                                m_state['l_btns'][it] = ui.button(it, on_click=select_l).classes('w-full text-center px-4 py-4 bg-gray-800/40 text-gray-200 rounded-2xl border border-gray-700 transition-all hover:border-cyan-500/50').props('no-caps')
                                        
                                        # Right Column
                                        with ui.column().classes('w-64 gap-3'):
                                            ui.label('ĐỊNH NGHĨA').classes('text-xs font-bold text-gray-500 tracking-widest text-center w-full')
                                            for it in right_items:
                                                def select_r(item=it):
                                                    m_state['selected_r'] = item
                                                    for b in m_state['r_btns'].values():
                                                        b.classes(remove='bg-emerald-600 border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.4)]', add='bg-gray-800/40 border-gray-700')
                                                    m_state['r_btns'][item].classes(add='bg-emerald-600 border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.4)]', remove='bg-gray-800/40 border-gray-700')
                                                    check_match()
                                                    
                                                m_state['r_btns'][it] = ui.button(it, on_click=select_r).classes('w-full text-center px-4 py-4 bg-gray-800/40 text-gray-200 rounded-2xl border border-gray-700 transition-all hover:border-emerald-500/50').props('no-caps')

                                    def check_match():
                                        l = m_state['selected_l']
                                        r = m_state['selected_r']
                                        if l and r:
                                            m_state['matches'][l] = r
                                            # Visually mark as matched
                                            m_state['l_btns'][l].classes(add='opacity-30 border-dashed scale-95 grayscale', remove='bg-cyan-600 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.4)]')
                                            m_state['r_btns'][r].classes(add='opacity-30 border-dashed scale-95 grayscale', remove='bg-emerald-600 border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.4)]')
                                            m_state['l_btns'][l].disable()
                                            m_state['r_btns'][r].disable()
                                            m_state['selected_l'] = None
                                            m_state['selected_r'] = None
                                            
                                            if len(m_state['matches']) == len(pairs):
                                                correct_count = 0
                                                for ml, mr in m_state['matches'].items():
                                                    for p in pairs:
                                                        if p['left'] == ml and p['right'] == mr:
                                                            correct_count += 1
                                                            break
                                                
                                                accuracy = correct_count / len(pairs)
                                                ui.notify(f'📊 Hoàn thành: {correct_count}/{len(pairs)} đúng', type='positive' if accuracy >= 0.7 else 'warning')
                                                ui.timer(1.5, lambda: _record_and_next(accuracy >= 0.7, q), once=True)

                                    ui.label('💡 Chọn 1 khái niệm bên trái, sau đó chọn 1 định nghĩa bên phải để nối.').classes('text-xs text-gray-500 mt-8 text-center w-full italic')
                                    
                                else:
                                    # Show question card for non-flashcard types
                                    with ui.card().classes('w-full p-5 bg-gray-800/80 border border-gray-700 rounded-xl mb-4'):
                                        ui.label(q_text).classes('text-lg font-bold text-white')
                                    
                                    if isinstance(opts, dict) and opts:
                                        for key in ['A', 'B', 'C', 'D']:
                                            if key in opts:
                                                ui.button(
                                                    f'{key}. {opts[key]}',
                                                    on_click=lambda k=key: handle_answer(k, q)
                                                ).classes('w-full text-left px-4 py-3 bg-gray-700/50 text-gray-200 rounded-xl border border-gray-600 hover:border-cyan-500 mb-2').props('no-caps align=left')
                                    elif isinstance(opts, list) and opts:
                                        for i, opt in enumerate(opts):
                                            lbl = chr(65+i)
                                            ui.button(
                                                f'{lbl}. {opt}',
                                                on_click=lambda l=lbl: handle_answer(l, q)
                                            ).classes('w-full text-left px-4 py-3 bg-gray-700/50 text-gray-200 rounded-xl border border-gray-600 hover:border-cyan-500 mb-2').props('no-caps align=left')
                                    else:
                                        # fill_blank / fallback
                                        answer = q.get('back', q.get('answer', ''))
                                        inp = ui.input('Nhập câu trả lời...').classes('w-full mb-2')
                                        ui.button('Kiểm tra', on_click=lambda: handle_text_answer(inp.value, answer, q)).classes('bg-cyan-600 text-white').props('no-caps')


                        def handle_answer(selected, q):
                            correct_key = q.get('correct', 'A')
                            if isinstance(correct_key, int):
                                correct_key = chr(65 + correct_key)
                            is_correct = selected.upper() == correct_key.upper()
                            _record_and_next(is_correct, q)

                        def handle_text_answer(user_ans, correct_ans, q):
                            is_correct = user_ans.strip().lower() == str(correct_ans).strip().lower()
                            _record_and_next(is_correct, q)

                        def _record_and_next(is_correct, q):
                            if is_correct:
                                state['correct'] += 1
                            # Update bloom score
                            bs = load_bloom_state(username, subject_id)
                            ns = bs.get('nodes', {}).get(node_id, create_node_bloom_scores(target_levels))
                            update_bloom_score(ns, bloom_level, is_correct, assessment_type, target_levels)
                            bs.setdefault('nodes', {})[node_id] = ns
                            save_bloom_state(username, subject_id, bs)
                            # Gamification
                            if user_id:
                                try:
                                    from gamification.gamification_ui import process_gamification_event
                                    process_gamification_event(user_id, 'quiz_correct' if is_correct else 'quiz_wrong')
                                except Exception:
                                    pass
                            state['idx'] += 1
                            render_q()

                        def render_results():
                            assess_area.clear()
                            acc = state['correct'] / max(1, state['total'])
                            # Update ebbinghaus
                            bs = load_bloom_state(username, subject_id)
                            eb = bs.get('ebbinghaus', {})
                            update_ebbinghaus_after_review(eb, node_id, acc)
                            bs['ebbinghaus'] = eb
                            save_bloom_state(username, subject_id, bs)

                            with assess_area:
                                trophy = '🏆' if acc >= 0.8 else '⭐' if acc >= 0.6 else '💪'
                                with ui.card().classes('w-full max-w-md mx-auto p-8 rounded-3xl bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 text-center'):
                                    ui.html(f'<div style="font-size:64px">{trophy}</div>').classes('mb-4')
                                    ui.label(f'{bl["icon"]} L{bloom_level} {bl["vi"]}').classes('text-lg font-bold text-white')
                                    ui.label(f'{state["correct"]}/{state["total"]} đúng — {acc:.0%}').classes('text-2xl font-extrabold text-cyan-400 my-4')
                                    passed = acc >= bl['pass_threshold']
                                    if passed:
                                        ui.label('✅ ĐẠT CHUẨN!').classes('text-green-400 font-bold')
                                    else:
                                        ui.label(f'Cần ≥{bl["pass_threshold"]:.0%} để vượt qua').classes('text-amber-400 text-sm')
                                    ui.button('🔙 Quay lại Bloom Ladder', on_click=lambda: __import__('nicegui').background_tasks.create(delayed_render_bloom_ladder())).classes('w-full bg-indigo-600 text-white font-bold py-3 rounded-xl mt-4').props('no-caps')

                        render_q()

                    render_bloom_ladder()

                # ==================== TAB 3: PROGRESS ====================
                with ui.tab_panel(tab_progress):
                    prog_area = ui.column().classes('w-full')

                    def render_progress():
                        prog_area.clear()
                        bs = load_bloom_state(username, subject_id)
                        ns = bs.get('nodes', {}).get(node_id, node_state)
                        overall = ns.get('overall_bloom', 0)

                        with prog_area:
                            ui.label('📊 Tiến Độ Bloom').classes('text-xl font-bold text-white mb-4')
                            # Overall score
                            color = get_bloom_color(overall)
                            with ui.card().classes('w-full p-6 bg-gray-800/50 border border-gray-700 rounded-xl mb-4 text-center'):
                                ui.html(f'<div style="font-size:48px;color:{color}">{overall:.2f}</div>')
                                ui.label('Overall Bloom Score (0-6)').classes('text-xs text-gray-500')
                                ui.html(f'<div style="width:80px;height:80px;border-radius:50%;background:{color};box-shadow:0 0 30px {color};margin:12px auto"></div>')

                            # Per-level breakdown
                            for lvl in target_levels:
                                bl = BLOOM_LEVELS[lvl]
                                ld = ns.get('bloom_scores', {}).get(str(lvl), {})
                                sc = ld.get('score', 0)
                                total = ld.get('total', 0)
                                correct = ld.get('correct', 0)
                                types = ld.get('types_done', [])

                                with ui.row().classes('w-full items-center gap-3 mb-2'):
                                    ui.label(f'{bl["icon"]} L{lvl}').classes('w-12 font-bold text-white')
                                    with ui.element('div').classes('flex-grow bg-gray-800 rounded-full h-4'):
                                        w = min(100, sc * 100)
                                        ui.element('div').classes('h-4 rounded-full').style(f'width:{w}%;background:{bl["hex"]}')
                                    ui.label(f'{sc:.0%}').classes('w-12 text-right text-sm text-gray-400')
                                    ui.label(f'{correct}/{total}').classes('w-12 text-right text-xs text-gray-600')

                            # Study status
                            studied = ns.get('study_completed', False)
                            ui.label(f'📖 Học tập: {"✅ Hoàn thành" if studied else "⏳ Chưa hoàn thành"}').classes('text-sm text-gray-400 mt-4')

                            # Smart Review Widget
                            try:
                                from smart_review_queue import get_review_queue
                                review_queue = get_review_queue(bs, max_items=3)
                                if review_queue:
                                    with ui.card().classes('w-full p-4 bg-amber-900/20 border border-amber-700 rounded-xl mt-4'):
                                        ui.label('📅 Cần ôn tập').classes('font-bold text-amber-300 mb-2 text-sm')
                                        for rq in review_queue:
                                            ret_color = '#4ade80' if rq['retention'] > 0.7 else '#fbbf24' if rq['retention'] > 0.4 else '#f87171'
                                            with ui.row().classes('w-full items-center gap-2 mb-1'):
                                                ui.label(f'📌 {rq["node_id"]}').classes('text-xs text-gray-300 w-24 truncate')
                                                with ui.element('div').classes('flex-grow bg-gray-800 rounded-full h-2'):
                                                    w = max(2, rq['retention'] * 100)
                                                    ui.element('div').classes('h-2 rounded-full').style(f'width:{w}%;background:{ret_color}')
                                                ui.html(f'<span style="color:{ret_color};font-size:11px;font-weight:700">{rq["retention"]:.0%}</span>')
                            except ImportError:
                                pass

                            # Library & Retention Info
                            with ui.card().classes('w-full p-4 bg-gray-800/30 border border-gray-700 rounded-xl mt-4'):
                                ui.label('📚 Thông tin Thư viện & Lưu giữ').classes('font-bold text-gray-300 mb-2 text-sm')
                                
                                # Check library status
                                from node_content_engine import load_from_library, _make_course_id, _load_user_cache
                                c_id = _make_course_id(tree_data.get('course_name', 'Môn học'))
                                lib_pack = load_from_library(c_id, node_id)
                                cache_pack = _load_user_cache(username, c_id, node_id)
                                
                                with ui.row().classes('gap-4 text-xs text-gray-500'):
                                    ui.label(f'📗 Thư viện: {"✅ Có" if lib_pack else "❌ Chưa"}')
                                    ui.label(f'💾 Cache: {"✅ Có" if cache_pack else "❌ Chưa"}')
                                    if lib_pack:
                                        ui.label(f'👤 Tác giả: {lib_pack.get("author", "system")}')
                                        ui.label(f'v{lib_pack.get("version", 1)}')
                                
                                # Ebbinghaus retention
                                eb_data = bs.get('ebbinghaus', {}).get(node_id, {})
                                if eb_data.get('last_review', 0) > 0:
                                    import time, math
                                    hours = (time.time() - eb_data['last_review']) / 3600
                                    strength = eb_data.get('strength', 2.0)
                                    retention = math.exp(-hours / max(0.5, strength))
                                    retention = max(0.1, min(1.0, retention))
                                    ret_color = '#4ade80' if retention > 0.7 else '#fbbf24' if retention > 0.4 else '#f87171'
                                    ui.separator().classes('my-2')
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label('🧠 Độ nhớ Ebbinghaus:').classes('text-xs text-gray-500')
                                        ui.html(f'<span style="color:{ret_color};font-weight:800">{retention:.0%}</span>').classes('text-sm')
                                        ui.label(f'(ôn tập {eb_data.get("reviews", 0)} lần, sức nhớ {strength:.1f}h)').classes('text-xs text-gray-600')

                    render_progress()
                    # Auto-refresh when tab is selected
                    tabs.on('update:model-value', lambda e: render_progress() if e.args == '📊 Tiến độ' else None)

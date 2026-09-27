# tree_editor_ui.py — Interactive Knowledge Tree Editor (MIT Standard)
"""
Full-screen dialog for manually editing Knowledge Tree JSON.
Supports: edit course name, add/edit/delete macro/micro/assess nodes, manage edges.
"""

import json
import os
import copy
from nicegui import ui, run


def open_tree_editor(json_path: str, username: str, on_save_callback=None):
    """Open full-screen tree editor dialog."""

    # Load tree data
    with open(json_path, 'r', encoding='utf-8') as f:
        original_tree = json.load(f)
    tree = copy.deepcopy(original_tree)

    # State
    state = {'selected_type': None, 'selected_id': None, 'dirty': False}

    with ui.dialog().props('maximized persistent') as dialog, \
         ui.card().classes('w-full h-full p-0 rounded-none').props('id="studio-canvas"').style('background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); overflow: hidden;'):

        # ═══════════ HEADER ═══════════
        with ui.row().classes('w-full items-center px-6 py-3 gap-4').style('background: rgba(15,23,42,0.95); border-bottom: 1px solid rgba(255,255,255,0.08); backdrop-filter: blur(12px);'):
            ui.icon('account_tree', color='indigo').classes('text-3xl')
            with ui.column().classes('gap-0 flex-1'):
                ui.label('✏️ Knowledge Tree Editor').classes('text-lg font-black text-white tracking-wide')
                course_input = ui.input(value=tree.get('course_name', ''), placeholder='Tên khóa học').props('dense dark borderless').classes('text-indigo-300 font-bold text-sm').style('max-width: 400px;')

            stats_label = ui.label('').classes('text-xs bg-white/5 text-slate-300 font-mono px-3 py-1.5 rounded-full border border-white/10')

            def update_stats():
                nm = len(tree.get('macro_nodes', []))
                nmi = len(tree.get('micro_nodes', []))
                na = len(tree.get('assess_nodes', []))
                ne = len(tree.get('edges', []))
                stats_label.text = f'📌 {nm} Chương · 📖 {nmi} Bài · 📝 {na} Kiểm tra · 🔗 {ne} Edges'
            update_stats()

            ui.button('', icon='close', on_click=lambda: _try_close()).props('flat round color=white size=sm')

        # ═══════════ MAIN SPLITTER ═══════════
        with ui.splitter(value=30).classes('w-full flex-1').style('height: calc(100vh - 60px);') as splitter:

            # ─── LEFT PANEL: Tree View ───
            with splitter.before:
                with ui.column().classes('w-full h-full p-0').style('background: rgba(0,0,0,0.15);'):
                    # Search
                    with ui.row().classes('w-full px-3 pt-3 pb-1 gap-2'):
                        search_input = ui.input(placeholder='🔍 Tìm kiếm...').props('dense outlined dark clearable').classes('flex-1 text-xs')

                    tree_scroll = ui.scroll_area().classes('w-full flex-1')

                    # Add buttons
                    with ui.row().classes('w-full p-3 gap-2 justify-center').style('border-top: 1px solid rgba(255,255,255,0.06);'):
                        ui.button('+ Chương', icon='create_new_folder', on_click=lambda: _add_macro()).props('dense flat color=blue size=sm id="btn-group-chapter"').classes('text-xs')

            # ─── RIGHT PANEL: Tabbed Editor ───
            with splitter.after:
                with ui.column().classes('w-full h-full p-0'):
                    # Tab header
                    with ui.tabs().classes('w-full').props('dense active-color=indigo indicator-color=indigo align=left inline-label') as right_tabs:
                        tab_edit = ui.tab('edit', label='📝 Chỉnh sửa', icon='edit')
                        tab_ai = ui.tab('ai', label='🤖 AI Refine', icon='auto_awesome')

                    with ui.tab_panels(right_tabs, value='edit').classes('w-full flex-1 bg-transparent'):
                        # ── TAB 1: Manual Edit ──
                        with ui.tab_panel('edit').classes('p-0'):
                            detail_area = ui.scroll_area().classes('w-full h-full')
                            with detail_area:
                                placeholder_col = ui.column().classes('w-full h-full items-center justify-center gap-3')
                                with placeholder_col:
                                    ui.icon('touch_app', color='gray').classes('text-6xl opacity-30')
                                    ui.label('Chọn một node từ danh sách bên trái để chỉnh sửa').classes('text-slate-500 text-sm')

                        # ── TAB 2: AI Refine ──
                        with ui.tab_panel('ai').classes('p-0'):
                            ai_panel = ui.scroll_area().classes('w-full h-full')
                            with ai_panel:
                                ai_placeholder = ui.column().classes('w-full h-full items-center justify-center gap-3')
                                with ai_placeholder:
                                    ui.icon('auto_awesome', color='amber').classes('text-6xl opacity-30')
                                    ui.label('Chọn một node/chương, sau đó dùng AI để refine').classes('text-slate-500 text-sm')

        # ═══════════ FOOTER ═══════════
        with ui.row().classes('w-full px-6 py-3 gap-3 justify-end items-center').style('background: rgba(15,23,42,0.95); border-top: 1px solid rgba(255,255,255,0.08);'):
            dirty_label = ui.label('').classes('text-yellow-400 text-xs flex-1')
            ui.button('Hủy bỏ', icon='cancel', on_click=lambda: _try_close()).props('flat color=white rounded').classes('text-sm')
            ui.button('💾 Lưu & Cập nhật 3D', icon='save', on_click=lambda: _save_and_close()).classes('bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-bold px-6 shadow-xl hover:scale-105 transition-all text-sm').props('rounded id="btn-save-tree"')

        # ═══════════ HELPER FUNCTIONS ═══════════

        def _mark_dirty():
            state['dirty'] = True
            dirty_label.text = '⚠️ Có thay đổi chưa lưu'

        def _gen_id(prefix, existing_ids):
            """Generate unique ID."""
            i = 1
            while f'{prefix}{i}' in existing_ids:
                i += 1
            return f'{prefix}{i}'

        # ─── RENDER TREE ───
        def _render_tree():
            tree_scroll.clear()
            q = (search_input.value or '').lower()
            macros = tree.get('macro_nodes', [])
            micros = tree.get('micro_nodes', [])

            with tree_scroll:
                with ui.column().classes('w-full gap-0.5 p-2'):
                    for macro in macros:
                        mid = macro['id']
                        mtitle = macro.get('title', mid)
                        children = [m for m in micros if m.get('parent_macro') == mid]

                        if q and q not in mtitle.lower() and not any(q in c.get('title', '').lower() for c in children):
                            continue

                        is_sel_macro = state['selected_type'] == 'macro' and state['selected_id'] == mid
                        macro_cls = 'bg-indigo-500/20 border-indigo-400/50' if is_sel_macro else 'bg-white/3 border-white/5 hover:bg-white/5'

                        with ui.card().classes(f'w-full p-0 mb-1 rounded-lg border transition-all {macro_cls}'):
                            with ui.row().classes('w-full items-center px-3 py-2 cursor-pointer gap-2').on('click', lambda _mid=mid: _select('macro', _mid)):
                                ui.icon('folder', color='blue').classes('text-base')
                                ui.label(f'{mid}: {mtitle}').classes('text-white text-xs font-bold flex-1 truncate')
                                ui.badge(str(len(children))).props('color=indigo').classes('text-[10px]')

                            for micro in children:
                                cid = micro['id']
                                ctitle = micro.get('title', cid)
                                if q and q not in ctitle.lower() and q not in mtitle.lower():
                                    continue
                                is_sel_micro = state['selected_type'] == 'micro' and state['selected_id'] == cid
                                micro_cls = 'bg-green-500/20 border-l-green-400' if is_sel_micro else 'hover:bg-white/5 border-l-transparent'
                                with ui.row().classes(f'w-full items-center px-4 py-1.5 cursor-pointer gap-2 border-l-2 transition-all {micro_cls}').on('click', lambda _cid=cid: _select('micro', _cid)):
                                    ui.icon('article', color='green').classes('text-sm')
                                    ui.label(f'{cid}: {ctitle}').classes('text-slate-300 text-[11px] flex-1 truncate')
                                    # Check for assess
                                    has_assess = any(a.get('target_micro') == cid for a in tree.get('assess_nodes', []))
                                    if has_assess:
                                        ui.icon('quiz', color='yellow').classes('text-xs opacity-60')

        search_input.on('change', lambda: _render_tree())

        # ─── SELECT NODE ───
        def _select(node_type, node_id):
            state['selected_type'] = node_type
            state['selected_id'] = node_id
            _render_tree()
            _render_detail()

        # ─── RENDER DETAIL PANEL ───
        def _render_detail():
            detail_area.clear()
            ntype = state['selected_type']
            nid = state['selected_id']

            with detail_area:
                if ntype == 'macro':
                    _render_macro_detail(nid)
                elif ntype == 'micro':
                    _render_micro_detail(nid)

            # Also refresh AI panel
            _render_ai_panel()

        def _render_macro_detail(mid):
            macro = next((m for m in tree['macro_nodes'] if m['id'] == mid), None)
            if not macro:
                return

            with ui.column().classes('w-full p-5 gap-4'):
                # Header
                with ui.row().classes('items-center gap-3 mb-2'):
                    ui.icon('folder', color='blue').classes('text-3xl')
                    with ui.column().classes('gap-0 flex-1'):
                        ui.label('CHƯƠNG (Macro Node)').classes('text-blue-400 text-[10px] font-bold tracking-widest uppercase')
                        ui.label(f'ID: {mid}').classes('text-slate-500 text-xs font-mono')
                    ui.button('🗑️ Xóa Chương', on_click=lambda: _delete_macro(mid)).props('flat color=red dense size=sm').classes('text-xs')

                # Title
                with ui.card().classes('w-full p-4 bg-white/3 border border-white/8 rounded-xl'):
                    ui.label('Tiêu đề Chương').classes('text-slate-400 text-xs font-bold mb-1')
                    title_input = ui.input(value=macro.get('title', ''), placeholder='Nhập tiêu đề chương...').props('dense outlined dark').classes('w-full')
                    title_input.on('change', lambda e, m=macro: [m.__setitem__('title', e.value), _mark_dirty()])

                # Children list
                children = [m for m in tree['micro_nodes'] if m.get('parent_macro') == mid]
                with ui.card().classes('w-full p-4 bg-white/3 border border-white/8 rounded-xl'):
                    with ui.row().classes('items-center justify-between mb-2'):
                        ui.label(f'Bài học thuộc chương ({len(children)})').classes('text-slate-400 text-xs font-bold')
                        ui.button('+ Thêm Bài', icon='add', on_click=lambda: _add_micro(mid)).props('dense flat color=green size=sm id="btn-add-node"').classes('text-xs')
                    if children:
                        for child in children:
                            with ui.row().classes('w-full items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer').on('click', lambda _cid=child['id']: _select('micro', _cid)):
                                ui.icon('article', color='green').classes('text-sm')
                                ui.label(f"{child['id']}: {child.get('title', '')}").classes('text-slate-300 text-xs flex-1')
                    else:
                        ui.label('Chưa có bài học nào').classes('text-slate-500 text-xs italic')

        def _render_micro_detail(cid):
            micro = next((m for m in tree['micro_nodes'] if m['id'] == cid), None)
            if not micro:
                return

            with ui.column().classes('w-full p-5 gap-4'):
                # Header
                with ui.row().classes('items-center gap-3 mb-2'):
                    ui.icon('article', color='green').classes('text-3xl')
                    with ui.column().classes('gap-0 flex-1'):
                        ui.label('BÀI HỌC (Micro Node)').classes('text-green-400 text-[10px] font-bold tracking-widest uppercase')
                        ui.label(f'ID: {cid} · Parent: {micro.get("parent_macro", "?")}').classes('text-slate-500 text-xs font-mono')
                    ui.button('🗑️ Xóa Bài', on_click=lambda: _delete_micro(cid)).props('flat color=red dense size=sm').classes('text-xs')

                # Title & Content
                with ui.card().classes('w-full p-4 bg-white/3 border border-white/8 rounded-xl'):
                    ui.label('Tiêu đề').classes('text-slate-400 text-xs font-bold mb-1')
                    t_input = ui.input(value=micro.get('title', ''), placeholder='Tiêu đề bài học').props('dense outlined dark').classes('w-full mb-3')
                    t_input.on('change', lambda e, m=micro: [m.__setitem__('title', e.value), _mark_dirty()])

                    ui.label('Nội dung tóm tắt').classes('text-slate-400 text-xs font-bold mb-1')
                    c_input = ui.textarea(value=micro.get('content', ''), placeholder='Nội dung bài học...').props('id="btn-add-resource" outlined dark rows=4').classes('w-full mb-3')
                    c_input.on('change', lambda e, m=micro: [m.__setitem__('content', e.value), _mark_dirty()])

                    with ui.row().classes('gap-4'):
                        with ui.column().classes('gap-1 flex-1'):
                            ui.label('Alpha Base (Độ khó)').classes('text-slate-400 text-xs font-bold')
                            a_input = ui.number(value=micro.get('alpha_base', 15), min=10, max=30, step=1).props('dense outlined dark').classes('w-full')
                            a_input.on('change', lambda e, m=micro: [m.__setitem__('alpha_base', int(e.value)), _mark_dirty()])
                        with ui.column().classes('gap-1 flex-1'):
                            ui.label('Parent Macro').classes('text-slate-400 text-xs font-bold')
                            macro_opts = {m['id']: f"{m['id']}: {m.get('title', '')}" for m in tree['macro_nodes']}
                            p_select = ui.select(options=macro_opts, value=micro.get('parent_macro', '')).props('dense outlined dark').classes('w-full')
                            p_select.on('change', lambda e, m=micro: [m.__setitem__('parent_macro', e.value), _mark_dirty()])

                # Assess nodes
                assess_nodes = [a for a in tree.get('assess_nodes', []) if a.get('target_micro') == cid]
                with ui.card().classes('w-full p-4 bg-white/3 border border-white/8 rounded-xl'):
                    with ui.row().classes('items-center justify-between mb-3'):
                        ui.label(f'📝 Câu hỏi kiểm tra ({sum(len(a.get("questions", [])) for a in assess_nodes)})').classes('text-yellow-300 text-xs font-bold')
                        ui.button('+ Thêm', icon='add', on_click=lambda: _add_assess(cid)).props('dense flat color=yellow size=sm').classes('text-xs')

                    for assess in assess_nodes:
                        for qi, question in enumerate(assess.get('questions', [])):
                            with ui.card().classes('w-full p-3 mb-2 bg-black/20 border border-white/5 rounded-lg'):
                                with ui.row().classes('items-start gap-2'):
                                    ui.label(f'Q{qi+1}').classes('text-yellow-400 text-xs font-mono font-bold mt-1')
                                    with ui.column().classes('flex-1 gap-1'):
                                        q_input = ui.input(value=question.get('question', ''), placeholder='Câu hỏi...').props('dense outlined dark').classes('w-full text-xs')
                                        q_input.on('change', lambda e, q=question: [q.__setitem__('question', e.value), _mark_dirty()])

                                        for oi, opt in enumerate(question.get('options', [])):
                                            o_input = ui.input(value=opt, placeholder=f'Lựa chọn {chr(65+oi)}').props('dense outlined dark').classes('w-full text-xs')
                                            o_input.on('change', lambda e, q=question, idx=oi: [q['options'].__setitem__(idx, e.value), _mark_dirty()])

                                        ans_select = ui.select(options=['A', 'B', 'C', 'D'], value=question.get('answer', 'A'), label='Đáp án').props('dense outlined dark').classes('w-24')
                                        ans_select.on('change', lambda e, q=question: [q.__setitem__('answer', e.value), _mark_dirty()])

                                    ui.button(icon='delete', on_click=lambda _a=assess, _qi=qi: _delete_question(_a, _qi)).props('flat round color=red size=xs')

                # Edges
                related_edges = [e for e in tree.get('edges', []) if e.get('source') == cid or e.get('target') == cid]
                with ui.card().classes('w-full p-4 bg-white/3 border border-white/8 rounded-xl'):
                    with ui.row().classes('items-center justify-between mb-3'):
                        ui.label(f'🔗 Edges liên quan ({len(related_edges)})').classes('text-indigo-300 text-xs font-bold')
                        ui.button('+ Thêm Edge', icon='add', on_click=lambda: _add_edge(cid)).props('dense flat color=indigo size=sm').classes('text-xs')

                    for edge in related_edges:
                        direction = '→' if edge['source'] == cid else '←'
                        other = edge['target'] if edge['source'] == cid else edge['source']
                        with ui.row().classes('w-full items-center gap-2 px-3 py-1.5 rounded-lg bg-black/10 mb-1'):
                            ui.label(f'{edge["source"]} {direction} {edge["target"]}').classes('text-slate-300 text-xs font-mono flex-1')
                            ui.label(edge.get('reason', '')[:50]).classes('text-slate-500 text-[10px] flex-1 truncate')
                            ui.button(icon='delete', on_click=lambda _e=edge: _delete_edge(_e)).props('flat round color=red size=xs')

        # ─── AI REFINE PANEL ───
        def _render_ai_panel():
            ai_panel.clear()
            ntype = state['selected_type']
            nid = state['selected_id']

            with ai_panel:
                with ui.column().classes('w-full p-5 gap-4'):
                    # Header
                    with ui.row().classes('items-center gap-3 mb-1'):
                        ui.icon('auto_awesome', color='amber').classes('text-3xl')
                        with ui.column().classes('gap-0'):
                            ui.label('🤖 AI REFINEMENT ENGINE').classes('text-amber-400 text-[10px] font-bold tracking-widest uppercase')
                            if nid:
                                ui.label(f'Target: {nid} ({ntype})').classes('text-slate-500 text-xs font-mono')
                            else:
                                ui.label('Chọn node/chương trước khi dùng AI').classes('text-slate-500 text-xs')

                    # Mode selector
                    modes = {}
                    if ntype == 'micro':
                        modes = {
                            'expand': '🔀 Tách nhỏ (Expand) — tách 1 bài → nhiều bài chi tiết',
                            'update': '🔄 Cập nhật (Update) — sửa nội dung bài hiện tại',
                        }
                    elif ntype == 'macro':
                        modes = {
                            'refine': '📌 Làm chi tiết chương (Refine) — thêm bài mới vào chương',
                        }
                    # Always available
                    modes['add'] = '📄 Bổ sung từ tài liệu (Add) — upload tài liệu mới → merge'

                    if not ntype and len(modes) == 1:
                        with ui.card().classes('w-full p-4 bg-amber-500/5 border border-amber-400/20 rounded-xl'):
                            ui.label('⚠️ Chọn một node (bài học) hoặc chương ở panel bên trái để mở khóa các chế độ Expand, Update, Refine.').classes('text-amber-300 text-xs')
                            ui.label('Chế độ "Bổ sung từ tài liệu" luôn sẵn sàng.').classes('text-slate-400 text-[10px] mt-1')

                    with ui.card().classes('w-full p-4 bg-white/3 border border-white/8 rounded-xl'):
                        ui.label('Chế độ AI').classes('text-slate-400 text-xs font-bold mb-2')
                        mode_select = ui.select(options=modes, value=list(modes.keys())[0] if modes else 'add').props('dense outlined dark').classes('w-full')

                    # Prompt input
                    with ui.card().classes('w-full p-4 bg-white/3 border border-white/8 rounded-xl'):
                        ui.label('Prompt cho AI').classes('text-slate-400 text-xs font-bold mb-2')
                        prompt_input = ui.textarea(
                            placeholder='Ví dụ: "Tách thành 3 phần chi tiết hơn", "Thêm ví dụ thực tế VN", "Bổ sung 2 bài về bảo mật"...'
                        ).props('outlined dark rows=3').classes('w-full')

                    # Document upload (optional)
                    ai_doc_state = {'text': None}
                    with ui.card().classes('w-full p-4 bg-white/3 border border-white/8 rounded-xl'):
                        ui.label('📎 Tài liệu bổ sung (tuỳ chọn)').classes('text-slate-400 text-xs font-bold mb-2')
                        doc_status = ui.label('Chưa upload').classes('text-slate-500 text-[10px] mb-2')

                        async def _handle_ai_doc(e):
                            # Robust filename extraction
                            if isinstance(e, dict):
                                fname = e.get('name') or e.get('filename') or 'doc.txt'
                            else:
                                fname = getattr(e, 'name', None) or getattr(e, 'filename', None) or 'doc.txt'

                            try:
                                if isinstance(e, dict):
                                    cb = e.get('content') or await e.get('file').read()
                                else:
                                    if hasattr(e, 'content'): cb = e.content.read()
                                    elif hasattr(e, 'file'): cb = await e.file.read()
                                    else: raise ValueError("Không tìm thấy nội dung file.")
                            except Exception as read_ex:
                                doc_status.text = f'❌ Lỗi đọc file: {str(read_ex)}'
                                doc_status.classes(remove='text-slate-500', add='text-red-400')
                                return

                            try:
                                from document_parser import parse_document
                                text = parse_document(fname, cb)
                                ai_doc_state['text'] = text
                                doc_status.text = f'✅ Đã đọc {len(text)} ký tự từ {fname}'
                                doc_status.classes(remove='text-slate-500', add='text-green-400')
                            except Exception as ex:
                                doc_status.text = f'❌ {ex}'
                                doc_status.classes(remove='text-slate-500', add='text-red-400')

                        ui.upload(on_upload=_handle_ai_doc, auto_upload=True, multiple=False,
                                  label='Upload .txt/.pdf/.docx').props(
                            'bordered accept=".txt,.pdf,.docx" flat color=amber dense'
                        ).classes('w-full')

                    # Preview area
                    preview_card = ui.card().classes('w-full p-4 bg-white/3 border border-white/8 rounded-xl')
                    preview_card.set_visibility(False)
                    with preview_card:
                        ui.label('📋 Xem trước kết quả AI').classes('text-amber-300 text-xs font-bold mb-2')
                        preview_text = ui.label('').classes('text-slate-300 text-xs whitespace-pre-wrap font-mono')

                    # Action buttons
                    ai_status = ui.label('').classes('text-slate-400 text-xs italic')
                    ai_progress = ui.linear_progress(value=0).props('color=amber track-color=white/10 stripe size=6px rounded').classes('w-full')
                    ai_progress.set_visibility(False)

                    ai_result_state = {'result': None, 'mode': None}

                    with ui.row().classes('gap-3 mt-2'):
                        async def _run_ai():
                            selected_mode = mode_select.value
                            prompt = prompt_input.value
                            if not prompt or not prompt.strip():
                                ui.notify('Vui lòng nhập prompt cho AI', type='warning')
                                return

                            ai_progress.set_visibility(True)
                            ai_progress.value = 0.1
                            ai_status.text = '🤖 Đang gọi Gemini AI...'
                            preview_card.set_visibility(False)

                            try:
                                from tree_editor_ai import (
                                    ai_expand_node, ai_update_node,
                                    ai_refine_region, ai_add_from_document,
                                    format_ai_result_preview
                                )
                                ai_progress.value = 0.3
                                doc_text = ai_doc_state.get('text')

                                if selected_mode == 'expand' and ntype == 'micro':
                                    result = await run.io_bound(ai_expand_node, tree, nid, prompt, doc_text)
                                elif selected_mode == 'update' and ntype == 'micro':
                                    result = await run.io_bound(ai_update_node, tree, nid, prompt, doc_text)
                                elif selected_mode == 'refine' and ntype == 'macro':
                                    result = await run.io_bound(ai_refine_region, tree, nid, prompt, doc_text)
                                elif selected_mode == 'add':
                                    if not doc_text:
                                        doc_text = prompt
                                    result = await run.io_bound(ai_add_from_document, tree, doc_text, prompt)
                                else:
                                    ui.notify(f'Chọn node phù hợp cho chế độ {selected_mode}', type='warning')
                                    ai_progress.set_visibility(False)
                                    ai_status.text = ''
                                    return

                                ai_progress.value = 0.8
                                ai_result_state['result'] = result
                                ai_result_state['mode'] = selected_mode

                                # Show preview
                                preview_text.text = format_ai_result_preview(result, selected_mode)
                                preview_card.set_visibility(True)
                                ai_progress.value = 1.0
                                ai_status.text = '✅ AI đã phân tích xong — xem trước bên dưới'

                            except Exception as ex:
                                ai_status.text = f'❌ Lỗi: {str(ex)}'
                                ai_progress.value = 0

                        ui.button('🤖 Gọi AI Phân Tích', icon='auto_awesome', on_click=_run_ai).classes(
                            'bg-gradient-to-r from-amber-500 to-orange-600 text-white font-bold px-5 shadow-xl hover:scale-105 transition-all text-sm'
                        ).props('rounded')

                        def _apply_ai_result():
                            result = ai_result_state.get('result')
                            mode = ai_result_state.get('mode')
                            if not result:
                                ui.notify('Chưa có kết quả AI để áp dụng', type='warning')
                                return
                            from tree_editor_ai import merge_ai_result_into_tree
                            merge_ai_result_into_tree(tree, result, mode=mode)
                            _mark_dirty()
                            _render_tree()
                            update_stats()
                            preview_card.set_visibility(False)
                            ai_status.text = '🎉 Đã áp dụng thay đổi vào cây!'
                            ai_result_state['result'] = None
                            ui.notify('✅ Đã merge kết quả AI vào cây tri thức!', type='positive')

                        ui.button('✅ Áp dụng vào Cây', icon='check_circle', on_click=_apply_ai_result).classes(
                            'bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-bold px-5 shadow-xl hover:scale-105 transition-all text-sm'
                        ).props('rounded')

        # ─── ADD/DELETE OPERATIONS ───
        def _add_macro():
            existing = {m['id'] for m in tree['macro_nodes']}
            new_id = _gen_id('m', existing)
            tree['macro_nodes'].append({'id': new_id, 'title': 'Chương mới'})
            _mark_dirty()
            _select('macro', new_id)
            update_stats()

        def _add_micro(parent_macro):
            existing = {m['id'] for m in tree['micro_nodes']}
            # Find parent index
            macro_idx = next((i+1 for i, m in enumerate(tree['macro_nodes']) if m['id'] == parent_macro), 1)
            child_count = sum(1 for m in tree['micro_nodes'] if m.get('parent_macro') == parent_macro)
            new_id = f'c{macro_idx}.{child_count + 1}'
            if new_id in existing:
                new_id = _gen_id(f'c{macro_idx}.', existing)
            tree['micro_nodes'].append({
                'id': new_id, 'parent_macro': parent_macro,
                'title': 'Bài học mới', 'content': '', 'alpha_base': 15
            })
            _mark_dirty()
            _select('micro', new_id)
            update_stats()

        def _add_assess(target_micro):
            existing = {a['id'] for a in tree.get('assess_nodes', [])}
            new_id = _gen_id('a', existing)
            if 'assess_nodes' not in tree:
                tree['assess_nodes'] = []
            # Check if assess already exists for this micro
            existing_assess = next((a for a in tree['assess_nodes'] if a.get('target_micro') == target_micro), None)
            if existing_assess:
                existing_assess['questions'].append({
                    'question': 'Câu hỏi mới?',
                    'options': ['A. ...', 'B. ...', 'C. ...', 'D. ...'],
                    'answer': 'A'
                })
            else:
                tree['assess_nodes'].append({
                    'id': new_id, 'target_micro': target_micro, 'theta_pass': 0.6,
                    'questions': [{'question': 'Câu hỏi mới?', 'options': ['A. ...', 'B. ...', 'C. ...', 'D. ...'], 'answer': 'A'}]
                })
            _mark_dirty()
            _render_detail()
            update_stats()

        def _add_edge(from_cid):
            micro_ids = [m['id'] for m in tree['micro_nodes'] if m['id'] != from_cid]
            if not micro_ids:
                ui.notify('Không có node nào khác để tạo edge', type='warning')
                return

            with ui.dialog() as edge_dialog, ui.card().classes('p-5 bg-slate-900 border border-white/10 rounded-2xl w-96'):
                ui.label('Thêm Edge mới').classes('text-white font-bold text-sm mb-3')
                ui.label(f'Source: {from_cid}').classes('text-slate-400 text-xs mb-2')
                target_select = ui.select(options=micro_ids, label='Target node').props('dense outlined dark').classes('w-full mb-2')
                reason_input = ui.input(placeholder='Lý do quan hệ tiên quyết...').props('dense outlined dark').classes('w-full mb-3')
                with ui.row().classes('gap-2 justify-end'):
                    ui.button('Hủy', on_click=edge_dialog.close).props('flat color=white size=sm')
                    def _confirm_edge():
                        if target_select.value:
                            tree.setdefault('edges', []).append({
                                'source': from_cid, 'target': target_select.value,
                                'reason': reason_input.value or ''
                            })
                            _mark_dirty()
                            edge_dialog.close()
                            _render_detail()
                            update_stats()
                    ui.button('Thêm', icon='add', on_click=_confirm_edge).props('color=indigo size=sm')
            edge_dialog.open()

        def _delete_macro(mid):
            tree['macro_nodes'] = [m for m in tree['macro_nodes'] if m['id'] != mid]
            child_ids = {m['id'] for m in tree['micro_nodes'] if m.get('parent_macro') == mid}
            tree['micro_nodes'] = [m for m in tree['micro_nodes'] if m.get('parent_macro') != mid]
            tree['assess_nodes'] = [a for a in tree.get('assess_nodes', []) if a.get('target_micro') not in child_ids]
            tree['edges'] = [e for e in tree.get('edges', []) if e.get('source') not in child_ids and e.get('target') not in child_ids]
            state['selected_type'] = None
            state['selected_id'] = None
            _mark_dirty()
            _render_tree()
            _render_detail()
            update_stats()
            ui.notify(f'Đã xóa chương {mid} và tất cả bài học liên quan', type='info')

        def _delete_micro(cid):
            tree['micro_nodes'] = [m for m in tree['micro_nodes'] if m['id'] != cid]
            tree['assess_nodes'] = [a for a in tree.get('assess_nodes', []) if a.get('target_micro') != cid]
            tree['edges'] = [e for e in tree.get('edges', []) if e.get('source') != cid and e.get('target') != cid]
            state['selected_type'] = None
            state['selected_id'] = None
            _mark_dirty()
            _render_tree()
            _render_detail()
            update_stats()
            ui.notify(f'Đã xóa bài {cid}', type='info')

        def _delete_question(assess, qi):
            assess['questions'].pop(qi)
            if not assess['questions']:
                tree['assess_nodes'] = [a for a in tree['assess_nodes'] if a['id'] != assess['id']]
            _mark_dirty()
            _render_detail()
            update_stats()

        def _delete_edge(edge):
            tree['edges'] = [e for e in tree['edges'] if not (e['source'] == edge['source'] and e['target'] == edge['target'])]
            _mark_dirty()
            _render_detail()
            update_stats()

        # ─── SAVE & CLOSE ───
        async def _save_and_close():
            tree['course_name'] = course_input.value or tree.get('course_name', '')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(tree, f, ensure_ascii=False, indent=2)
            ui.notify('✅ Đã lưu cây tri thức!', type='positive')

            # Re-render 3D
            try:
                from step2_5_visualize_tree import visualize_knowledge_tree
                await run.io_bound(visualize_knowledge_tree, username, json_path)
            except Exception as ex:
                ui.notify(f'⚠️ Lỗi render 3D: {ex}', type='warning')

            state['dirty'] = False
            dialog.close()
            if on_save_callback:
                on_save_callback(tree)

        def _try_close():
            if state['dirty']:
                with ui.dialog() as confirm_dlg, ui.card().classes('p-5 bg-slate-900 border border-white/10 rounded-2xl'):
                    ui.label('Bạn có thay đổi chưa lưu!').classes('text-white font-bold mb-3')
                    with ui.row().classes('gap-3 justify-end'):
                        ui.button('Quay lại', on_click=confirm_dlg.close).props('flat color=white size=sm')
                        ui.button('Bỏ thay đổi', on_click=lambda: [confirm_dlg.close(), dialog.close()]).props('color=red size=sm')
                confirm_dlg.open()
            else:
                dialog.close()

        # Initial render
        _render_tree()

    dialog.open()
    return dialog

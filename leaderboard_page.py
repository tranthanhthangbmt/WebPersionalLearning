# leaderboard_page.py
"""
Leaderboard Page - Rankings by XP, Streak, and Accuracy
- Weekly/Monthly/All-time filters
- Top 3 with crown icons
- Current user always visible
- Beautiful card-based UI
"""

from nicegui import ui, app
from database import engine, Session, select, User, UserProgress


def create_leaderboard_section(current_user, parent_container):
    """Render leaderboard within the main app tab"""

    parent_container.clear()
    with parent_container:
        with ui.column().classes('w-full max-w-3xl mx-auto p-6 gap-6'):

            # --- HEADER ---
            with ui.row().classes('w-full items-center justify-between'):
                with ui.column().classes('gap-1'):
                    ui.label('🏆 Bảng Xếp Hạng').classes('text-3xl font-extrabold text-gray-800 tracking-tight')
                    ui.label('So tài cùng bạn bè!').classes('text-gray-400')

            # --- FILTER CONTROLS ---
            metric_select = ui.toggle(
                {'xp': '⚡ XP', 'streak': '🔥 Streak', 'accuracy': '🎯 Chính xác'},
                value='xp'
            ).classes('mb-4')

            # --- LEADERBOARD TABLE ---
            leaderboard_container = ui.column().classes('w-full gap-3')

            def render_leaderboard():
                leaderboard_container.clear()
                metric = metric_select.value

                # Fetch all users with progress
                with Session(engine) as session:
                    users = session.exec(select(User)).all()
                    all_progress = session.exec(select(UserProgress)).all()

                # Build progress lookup
                progress_map = {p.user_id: p for p in all_progress}

                # Build ranking data
                ranking = []
                for u in users:
                    p = progress_map.get(u.id)
                    if not p:
                        continue
                    
                    accuracy = (p.total_correct / max(1, p.total_quizzes_done)) * 100 if p.total_quizzes_done > 0 else 0

                    ranking.append({
                        "user_id": u.id,
                        "username": u.username,
                        "full_name": u.full_name,
                        "avatar_url": u.avatar_url,
                        "total_xp": p.total_xp,
                        "level": p.current_level,
                        "streak": p.current_streak,
                        "accuracy": round(accuracy, 1),
                        "quizzes": p.total_quizzes_done,
                    })

                # Sort by selected metric
                sort_keys = {
                    'xp': lambda x: x['total_xp'],
                    'streak': lambda x: x['streak'],
                    'accuracy': lambda x: (x['accuracy'], x['quizzes']),
                }
                ranking.sort(key=sort_keys.get(metric, sort_keys['xp']), reverse=True)

                # Find current user's rank
                current_rank = None
                for i, r in enumerate(ranking):
                    if r["user_id"] == current_user.id:
                        current_rank = i
                        break

                with leaderboard_container:
                    if not ranking:
                        ui.label('Chưa có dữ liệu xếp hạng.').classes('text-gray-400 italic text-center w-full py-8')
                        return

                    # --- TOP 3 PODIUM ---
                    top3 = ranking[:3]
                    if len(top3) >= 1:
                        with ui.row().classes('w-full justify-center items-end gap-4 mb-6 py-4'):
                            # Podium order: 2nd, 1st, 3rd
                            podium_order = []
                            if len(top3) >= 2:
                                podium_order.append((top3[1], 2, 'h-28', 'from-gray-300 to-gray-400', '🥈'))
                            if len(top3) >= 1:
                                podium_order.append((top3[0], 1, 'h-36', 'from-yellow-400 to-amber-500', '👑'))
                            if len(top3) >= 3:
                                podium_order.append((top3[2], 3, 'h-24', 'from-orange-300 to-orange-400', '🥉'))

                            for entry, rank, height, gradient, crown in podium_order:
                                is_me = entry["user_id"] == current_user.id
                                border = 'ring-4 ring-blue-400' if is_me else ''
                                
                                with ui.column().classes(f'items-center gap-2 {border} rounded-2xl p-3'):
                                    ui.html(f'<span style="font-size:28px;">{crown}</span>')
                                    
                                    if entry.get("avatar_url"):
                                        ui.image(entry["avatar_url"]).classes('w-14 h-14 rounded-full object-cover border-2 border-white shadow-md')
                                    else:
                                        ui.avatar(icon='person', color='blue-100', text_color='blue-600').props('size=56px').classes('shadow-md')
                                    
                                    ui.label(entry["full_name"]).classes('font-bold text-sm text-gray-800 text-center max-w-[100px] truncate')
                                    
                                    # Metric value
                                    if metric == 'xp':
                                        ui.label(f'⚡ {entry["total_xp"]} XP').classes('text-xs font-bold text-indigo-600')
                                    elif metric == 'streak':
                                        ui.label(f'🔥 {entry["streak"]} ngày').classes('text-xs font-bold text-orange-600')
                                    else:
                                        ui.label(f'🎯 {entry["accuracy"]}%').classes('text-xs font-bold text-green-600')
                                    
                                    # Podium block
                                    ui.element('div').classes(
                                        f'w-20 {height} bg-gradient-to-t {gradient} rounded-t-xl shadow-inner'
                                    )

                    # --- FULL RANKING LIST ---
                    with ui.card().classes('w-full rounded-xl shadow-md overflow-hidden'):
                        # Header row
                        with ui.row().classes('w-full bg-gray-50 p-3 items-center border-b border-gray-200'):
                            ui.label('#').classes('w-10 text-center font-bold text-gray-400 text-sm')
                            ui.label('Người học').classes('flex-grow font-bold text-gray-400 text-sm')
                            ui.label('Level').classes('w-16 text-center font-bold text-gray-400 text-sm')
                            if metric == 'xp':
                                ui.label('XP').classes('w-20 text-right font-bold text-gray-400 text-sm')
                            elif metric == 'streak':
                                ui.label('Streak').classes('w-20 text-right font-bold text-gray-400 text-sm')
                            else:
                                ui.label('Chính xác').classes('w-20 text-right font-bold text-gray-400 text-sm')

                        # Data rows
                        for i, entry in enumerate(ranking):
                            rank = i + 1
                            is_me = entry["user_id"] == current_user.id
                            bg = 'bg-blue-50 border-l-4 border-blue-500' if is_me else 'hover:bg-gray-50'
                            
                            with ui.row().classes(f'w-full p-3 items-center border-b border-gray-100 {bg} transition-colors'):
                                # Rank
                                rank_icons = {1: '🥇', 2: '🥈', 3: '🥉'}
                                rank_display = rank_icons.get(rank, str(rank))
                                ui.label(rank_display).classes('w-10 text-center font-bold text-gray-600')
                                
                                # User info
                                with ui.row().classes('flex-grow items-center gap-3'):
                                    if entry.get("avatar_url"):
                                        ui.image(entry["avatar_url"]).classes('w-8 h-8 rounded-full object-cover')
                                    else:
                                        ui.avatar(icon='person', color='blue-50', text_color='blue-500').props('size=32px')
                                    
                                    with ui.column().classes('gap-0'):
                                        name_cls = 'font-bold text-sm text-blue-700' if is_me else 'font-medium text-sm text-gray-700'
                                        ui.label(entry["full_name"]).classes(name_cls)
                                        ui.label(f'@{entry["username"]}').classes('text-[10px] text-gray-400')
                                
                                # Level
                                from gamification.xp_engine import XPEngine
                                level_info = XPEngine.get_level_info(entry["level"])
                                ui.label(f'{level_info["icon"]} {entry["level"]}').classes('w-16 text-center text-sm')
                                
                                # Metric value
                                if metric == 'xp':
                                    ui.label(f'{entry["total_xp"]:,}').classes('w-20 text-right font-bold text-indigo-600 text-sm')
                                elif metric == 'streak':
                                    ui.label(f'{entry["streak"]} 🔥').classes('w-20 text-right font-bold text-orange-600 text-sm')
                                else:
                                    ui.label(f'{entry["accuracy"]}%').classes('w-20 text-right font-bold text-green-600 text-sm')

                    # --- CURRENT USER HIGHLIGHT (if not in view) ---
                    if current_rank is not None and current_rank >= 10:
                        with ui.card().classes('w-full p-4 rounded-xl bg-blue-50 border border-blue-200 mt-4'):
                            with ui.row().classes('items-center gap-3'):
                                ui.label(f'📍 Bạn đang ở vị trí #{current_rank + 1}').classes('font-bold text-blue-700')
                                entry = ranking[current_rank]
                                if metric == 'xp':
                                    ui.label(f'⚡ {entry["total_xp"]} XP').classes('text-sm text-blue-500')
                                elif metric == 'streak':
                                    ui.label(f'🔥 {entry["streak"]} ngày').classes('text-sm text-orange-500')
                                else:
                                    ui.label(f'🎯 {entry["accuracy"]}%').classes('text-sm text-green-500')

            # Initial render
            render_leaderboard()

            # Re-render on metric change
            metric_select.on_value_change(lambda _: render_leaderboard())

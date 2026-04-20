# profile_page.py - User Profile & Settings Page
"""
Displays user profile card with:
- Avatar, name, email
- Stats: XP, Level, Streak, Badges
- Badge showcase (unlocked achievements)
- Activity heatmap (GitHub-style)
- Settings: Change password, preferences
"""
from nicegui import ui, app
from database import (
    get_user_by_username, get_user_progress, 
    Session, engine, select, User, hash_password, verify_password
)
from gamification.xp_engine import XPEngine, LEVEL_CONFIG
from gamification.streak_service import StreakService
from gamification.achievement_service import AchievementService
from datetime import date, timedelta


def create_profile_section(user, parent_container):
    """Render profile section within the main app"""
    progress = get_user_progress(user.id)
    stats = XPEngine.get_user_stats(user.id)
    streak_info = StreakService.get_streak_info(user.id)
    all_achievements = AchievementService.get_all_achievements(user.id)
    unlocked_badges = AchievementService.get_unlocked_badges(user.id)
    unlocked_count, total_count = AchievementService.get_unlocked_count(user.id)
    activity_data = StreakService.get_activity_heatmap(user.id, days=90)
    
    level_info = XPEngine.get_level_info(stats["current_level"])
    level_name = level_info["name"]
    level_icon = level_info["icon"]
    xp_progress = stats["xp_progress"]
    next_threshold = stats["next_level_xp"]
    
    parent_container.clear()
    with parent_container:
        with ui.column().classes('w-full max-w-3xl mx-auto p-6 gap-6'):
            
            # --- PROFILE CARD ---
            with ui.card().classes('w-full p-6 rounded-2xl bg-white shadow-lg border-t-4 border-blue-500'):
                with ui.row().classes('items-center gap-6'):
                    # Avatar
                    avatar_url = user.avatar_url or None
                    if avatar_url:
                        ui.image(avatar_url).classes('w-20 h-20 rounded-full object-cover border-4 border-blue-100')
                    else:
                        ui.avatar(
                            icon='person', color='blue-100', text_color='blue-600'
                        ).props('size=80px').classes('border-4 border-blue-100')
                    
                    with ui.column().classes('gap-1 flex-grow'):
                        ui.label(user.full_name).classes('text-2xl font-extrabold text-gray-800')
                        ui.label(f'@{user.username}').classes('text-sm text-gray-400')
                        if user.email:
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('email', color='gray-400').classes('text-sm')
                                ui.label(user.email).classes('text-sm text-gray-500')
                        
                        with ui.row().classes('items-center gap-2 mt-1'):
                            role_badges = {
                                'student': ('🎓 Học sinh', 'bg-blue-100 text-blue-700'),
                                'teacher': ('👨‍🏫 Giáo viên', 'bg-green-100 text-green-700'),
                                'parent': ('👨‍👩‍👧 Phụ huynh', 'bg-purple-100 text-purple-700'),
                            }
                            role_text, role_class = role_badges.get(user.role, ('Người dùng', 'bg-gray-100 text-gray-700'))
                            ui.label(role_text).classes(f'text-xs font-bold px-2 py-0.5 rounded-full {role_class}')
                    
                    # Level badge
                    with ui.column().classes('items-center'):
                        ui.html(f'<div style="font-size:36px;">{level_icon}</div>')
                        ui.label(level_name).classes('text-sm font-bold text-blue-700')
                        ui.label(f'Lv.{stats["current_level"]}').classes('text-xs text-gray-400')

            # --- STATS GRID ---
            with ui.row().classes('w-full gap-4'):
                stat_items = [
                    ('⚡', 'XP', f'{stats["total_xp"]:,}', 'from-blue-500 to-indigo-500'),
                    ('🔥', 'Streak', f'{streak_info["current_streak"]} ngày', 'from-orange-500 to-red-500'),
                    ('📝', 'Quiz', str(stats["total_quizzes"]), 'from-green-500 to-emerald-500'),
                    ('✅', 'Chính xác', f'{stats["accuracy"]:.0f}%', 'from-purple-500 to-pink-500'),
                    ('🏆', 'Huy hiệu', f'{unlocked_count}/{total_count}', 'from-amber-500 to-orange-500'),
                ]
                
                for icon, label, value, gradient in stat_items:
                    with ui.card().classes('flex-1 p-4 rounded-xl bg-white shadow-md hover:shadow-lg transition-all'):
                        with ui.column().classes('items-center gap-1'):
                            ui.label(icon).classes('text-2xl')
                            ui.label(value).classes('text-xl font-extrabold text-gray-800')
                            ui.label(label).classes('text-xs text-gray-400 font-medium')

            # --- XP PROGRESS BAR ---
            with ui.card().classes('w-full p-5 rounded-xl bg-white shadow-md'):
                with ui.row().classes('justify-between items-center mb-2'):
                    ui.label(f'{level_icon} Level {stats["current_level"]}: {level_name}').classes('font-bold text-gray-800')
                    ui.label(f'{stats["total_xp"]:,} / {next_threshold:,} XP').classes('text-sm text-gray-500')
                
                with ui.element('div').classes('w-full bg-gray-100 rounded-full h-3'):
                    ui.element('div').classes(
                        'bg-gradient-to-r from-blue-500 to-indigo-500 h-3 rounded-full transition-all duration-500'
                    ).style(f'width:{xp_progress * 100}%')
                
                with ui.row().classes('justify-between mt-1'):
                    remaining_xp = int((1 - xp_progress) * (next_threshold - XPEngine.get_xp_for_next_level(stats["current_level"] - 1)))
                    ui.label(f'{max(0, remaining_xp):,} XP còn lại để lên level').classes('text-xs text-gray-400')
                    
                    # Multiplier badge
                    mult = stats["multiplier"]
                    if mult > 1.0:
                        ui.label(f'🔥 Streak x{mult}').classes(
                            'text-xs font-bold text-white bg-gradient-to-r from-orange-500 to-red-500 '
                            'px-2 py-0.5 rounded-full'
                        )

            # --- BADGE SHOWCASE ---
            with ui.card().classes('w-full p-5 rounded-xl bg-white shadow-md'):
                with ui.row().classes('items-center justify-between mb-4'):
                    ui.label('🏆 Tủ Huy Hiệu').classes('font-bold text-gray-800 text-lg')
                    ui.label(f'{unlocked_count}/{total_count} đã mở khóa').classes('text-sm text-gray-400')
                
                if unlocked_badges:
                    with ui.row().classes('w-full gap-3 flex-wrap'):
                        for badge in unlocked_badges:
                            with ui.card().classes(
                                'w-[90px] p-3 rounded-xl bg-gradient-to-br from-amber-50 to-yellow-50 '
                                'border border-amber-200 shadow-sm hover:shadow-md hover:scale-105 '
                                'transition-all cursor-pointer text-center'
                            ).tooltip(f'{badge["name"]}: {badge["description"]}'):
                                ui.html(f'<div style="font-size:32px;">{badge["icon"]}</div>').classes('mb-1')
                                ui.label(badge["name"]).classes('text-[10px] font-bold text-gray-700 leading-tight')
                else:
                    ui.label('Chưa có huy hiệu nào. Hãy bắt đầu chinh phục!').classes('text-sm text-gray-400 italic')
                
                # Locked achievements preview
                locked = [a for a in all_achievements if not a["is_unlocked"]]
                if locked:
                    with ui.expansion('Xem thành tựu chưa mở khóa', icon='lock').classes('w-full mt-4'):
                        with ui.column().classes('gap-2 p-2'):
                            # Group by category
                            categories = {}
                            for a in locked:
                                cat = a["category"]
                                if cat not in categories:
                                    categories[cat] = []
                                categories[cat].append(a)
                            
                            cat_names = {
                                'beginner': '🌱 Người mới',
                                'streak': '🔥 Streak',
                                'mastery': '🧠 Thông thạo',
                                'combat': '⚔️ Chiến đấu',
                                'socratic': '📜 Socratic',
                                'easter_egg': '🥚 Easter Egg',
                                'milestone': '⭐ Cột mốc',
                            }
                            
                            for cat, items in categories.items():
                                ui.label(cat_names.get(cat, cat)).classes('font-bold text-sm text-gray-600 mt-2')
                                for a in items:
                                    progress_pct = (a["progress"] / max(1, a["threshold"])) * 100
                                    with ui.row().classes('w-full items-center gap-3 py-1'):
                                        ui.html(f'<span style="font-size:20px;opacity:0.4;">{a["icon"]}</span>')
                                        with ui.column().classes('flex-grow gap-0'):
                                            ui.label(f'{a["name"]} — {a["description"]}').classes('text-xs text-gray-500')
                                            with ui.element('div').classes('w-full bg-gray-100 rounded-full h-1.5 mt-1'):
                                                ui.element('div').classes(
                                                    'bg-amber-400 h-1.5 rounded-full transition-all'
                                                ).style(f'width:{min(100, progress_pct)}%')
                                        ui.label(f'{a["progress"]}/{a["threshold"]}').classes('text-[10px] text-gray-400 font-mono')

            # --- ACTIVITY HEATMAP (GitHub-style) ---
            with ui.card().classes('w-full p-5 rounded-xl bg-white shadow-md'):
                ui.label('📊 Lịch Hoạt Động (90 ngày)').classes('font-bold text-gray-800 mb-3')
                
                if activity_data:
                    # Build 90-day grid
                    today = date.today()
                    weeks = []
                    current_week = []
                    
                    for i in range(89, -1, -1):
                        d = today - timedelta(days=i)
                        d_str = d.isoformat()
                        count = activity_data.get(d_str, 0)
                        current_week.append({"date": d_str, "count": count, "weekday": d.weekday()})
                        if len(current_week) == 7 or i == 0:
                            weeks.append(current_week)
                            current_week = []
                    
                    # Render grid using HTML for compactness
                    cells_html = '<div style="display:flex;gap:2px;flex-wrap:wrap;">'
                    for d_info in sum(weeks, []):
                        count = d_info["count"]
                        if count == 0:
                            color = '#ebedf0'
                        elif count <= 2:
                            color = '#9be9a8'
                        elif count <= 5:
                            color = '#40c463'
                        elif count <= 10:
                            color = '#30a14e'
                        else:
                            color = '#216e39'
                        cells_html += f'<div title="{d_info["date"]}: {count} hoạt động" style="width:12px;height:12px;background:{color};border-radius:2px;cursor:pointer;" ></div>'
                    cells_html += '</div>'
                    
                    ui.html(cells_html)
                    
                    # Legend
                    with ui.row().classes('mt-2 items-center gap-1'):
                        ui.label('Ít').classes('text-[10px] text-gray-400')
                        for color in ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']:
                            ui.element('div').style(
                                f'width:10px;height:10px;background:{color};border-radius:2px;'
                            )
                        ui.label('Nhiều').classes('text-[10px] text-gray-400')
                else:
                    ui.label('Dòng thời gian hoạt động sẽ hiển thị khi bạn sử dụng.').classes('text-sm text-gray-400 italic')

            # --- SETTINGS ---
            with ui.card().classes('w-full p-5 rounded-xl bg-white shadow-md'):
                ui.label('⚙️ Cài đặt').classes('font-bold text-gray-800 mb-4')
                
                with ui.expansion('Đổi mật khẩu', icon='lock').classes('w-full'):
                    with ui.column().classes('gap-3 p-2'):
                        old_pw = ui.input(label='Mật khẩu hiện tại', password=True, password_toggle_button=True).classes('w-full')
                        new_pw = ui.input(label='Mật khẩu mới', password=True, password_toggle_button=True).classes('w-full')
                        confirm_pw = ui.input(label='Xác nhận mật khẩu mới', password=True, password_toggle_button=True).classes('w-full')
                        pw_msg = ui.label('').classes('text-sm hidden')
                        
                        def change_password():
                            if not verify_password(old_pw.value, user.password):
                                pw_msg.text = '❌ Mật khẩu hiện tại không đúng'
                                pw_msg.classes(remove='hidden text-green-600', add='text-red-500')
                                return
                            if len(new_pw.value) < 6:
                                pw_msg.text = '❌ Mật khẩu mới phải ít nhất 6 ký tự'
                                pw_msg.classes(remove='hidden text-green-600', add='text-red-500')
                                return
                            if new_pw.value != confirm_pw.value:
                                pw_msg.text = '❌ Mật khẩu xác nhận không khớp'
                                pw_msg.classes(remove='hidden text-green-600', add='text-red-500')
                                return
                            
                            # Update password
                            with Session(engine) as session:
                                stmt = select(User).where(User.id == user.id)
                                db_user = session.exec(stmt).first()
                                if db_user:
                                    db_user.password = hash_password(new_pw.value)
                                    session.add(db_user)
                                    session.commit()
                            
                            pw_msg.text = '✅ Đổi mật khẩu thành công!'
                            pw_msg.classes(remove='hidden text-red-500', add='text-green-600')
                            old_pw.value = ''
                            new_pw.value = ''
                            confirm_pw.value = ''
                        
                        ui.button('Cập nhật mật khẩu', on_click=change_password).props('color=blue outline').classes('w-full')

                # Account info
                with ui.expansion('Thông tin tài khoản', icon='info').classes('w-full mt-2'):
                    with ui.column().classes('gap-2 p-2'):
                        ui.label(f'ID: {user.id}').classes('text-sm text-gray-500')
                        ui.label(f'Ngày tạo: {user.created_at.strftime("%d/%m/%Y %H:%M")}').classes('text-sm text-gray-500')
                        ui.label(f'Nhóm thí nghiệm: {user.group}').classes('text-sm text-gray-500')
                        ui.label(f'Streak dài nhất: {streak_info["longest_streak"]} ngày').classes('text-sm text-gray-500')
                        ui.label(f'Tổng quiz: {stats["total_quizzes"]}').classes('text-sm text-gray-500')
                        ui.label(f'Số câu đúng: {stats["total_correct"]}').classes('text-sm text-gray-500')

# gamification/gamification_ui.py
"""
Gamification UI Components for NiceGUI
- XP gain toast with animation
- Level-up celebration (confetti + modal)
- Achievement unlock toast
- Streak display widget
- XP/Level header widget
"""

from nicegui import ui


# ============================================================
#  CONFETTI JS (inline, no external dependency)
# ============================================================
CONFETTI_JS = """
(function() {
    const canvas = document.createElement('canvas');
    canvas.id = '__confetti_canvas';
    canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:99999;';
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const colors = ['#ff0','#f0f','#0ff','#f00','#0f0','#00f','#ff6b35','#ffd700','#7b2ff7','#00e5ff'];
    const particles = [];
    
    for (let i = 0; i < 150; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height - canvas.height,
            w: Math.random() * 10 + 5,
            h: Math.random() * 6 + 3,
            color: colors[Math.floor(Math.random() * colors.length)],
            vx: (Math.random() - 0.5) * 6,
            vy: Math.random() * 4 + 2,
            rot: Math.random() * 360,
            rotSpeed: (Math.random() - 0.5) * 10,
            opacity: 1,
        });
    }
    
    let frame = 0;
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        frame++;
        
        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.05;
            p.rot += p.rotSpeed;
            if (frame > 80) p.opacity -= 0.02;
            
            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.rotate(p.rot * Math.PI / 180);
            ctx.globalAlpha = Math.max(0, p.opacity);
            ctx.fillStyle = p.color;
            ctx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
            ctx.restore();
        });
        
        if (frame < 150) {
            requestAnimationFrame(animate);
        } else {
            canvas.remove();
        }
    }
    animate();
})();
"""

# ============================================================
#  XP GAIN TOAST STYLES
# ============================================================
GAMIFICATION_CSS = """
<style>
@keyframes xp-pop {
    0% { transform: scale(0.3) translateY(20px); opacity: 0; }
    50% { transform: scale(1.15) translateY(-5px); opacity: 1; }
    100% { transform: scale(1) translateY(0); opacity: 1; }
}
@keyframes xp-float-up {
    0% { transform: translateY(0); opacity: 1; }
    100% { transform: translateY(-60px); opacity: 0; }
}
@keyframes badge-unlock {
    0% { transform: scale(0) rotate(-180deg); opacity: 0; }
    60% { transform: scale(1.3) rotate(10deg); opacity: 1; }
    100% { transform: scale(1) rotate(0); opacity: 1; }
}
@keyframes level-up-glow {
    0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.7); }
    50% { box-shadow: 0 0 40px 20px rgba(99, 102, 241, 0.3); }
    100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
}
@keyframes streak-fire {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.2); }
}
.xp-toast {
    animation: xp-pop 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards;
}
.xp-float {
    animation: xp-float-up 1.5s ease-out forwards;
}
.badge-unlock-anim {
    animation: badge-unlock 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards;
}
.level-up-glow {
    animation: level-up-glow 1.5s ease-out;
}
.streak-fire-anim {
    animation: streak-fire 0.5s ease-in-out infinite;
}
</style>
"""


def inject_gamification_css():
    """Inject gamification CSS animations (call once in app header)"""
    ui.add_head_html(GAMIFICATION_CSS, shared=True)


def show_xp_gain(xp_gained: int, multiplier: float = 1.0, action_label: str = ""):
    """Show a floating XP gain notification"""
    mult_text = f" (x{multiplier})" if multiplier > 1.0 else ""
    label = f" • {action_label}" if action_label else ""
    
    ui.notify(
        f"⚡ +{xp_gained} XP{mult_text}{label}",
        type="positive",
        position="top-right",
        timeout=2500,
        classes="xp-toast",
    )


def show_level_up(new_level: int, level_name: str, level_icon: str):
    """Show level-up celebration with confetti"""
    # Fire confetti
    ui.run_javascript(CONFETTI_JS)
    
    # Show prominent notification
    with ui.dialog() as dialog, ui.card().classes(
        'p-8 rounded-3xl bg-gradient-to-br from-indigo-600 to-purple-700 text-white text-center '
        'shadow-2xl level-up-glow max-w-sm'
    ):
        ui.html(f'<div style="font-size:72px;" class="mb-2">{level_icon}</div>')
        ui.label('🎉 LEVEL UP!').classes('text-3xl font-extrabold tracking-wide mb-2')
        ui.label(f'Level {new_level}: {level_name}').classes('text-xl font-bold text-indigo-100 mb-4')
        ui.label('Tiếp tục chinh phục tri thức!').classes('text-sm text-indigo-200 mb-6')
        ui.button('Tuyệt vời! 🚀', on_click=dialog.close).classes(
            'w-full bg-white text-indigo-700 font-bold py-3 rounded-xl hover:bg-indigo-50 transition-all shadow-lg'
        ).props('no-caps')
    
    dialog.open()


def show_achievement_unlock(achievement: dict):
    """Show achievement unlock toast with animation"""
    icon = achievement.get("icon", "🏆")
    name = achievement.get("name", "Thành tựu")
    desc = achievement.get("description", "")
    xp = achievement.get("xp_reward", 0)
    
    # Audio feedback (optional - plays unlock sound if exists)
    ui.run_javascript("""
        try {
            const audio = new Audio('/audio/success.mp3');
            audio.volume = 0.5;
            audio.play().catch(()=>{});
        } catch(e) {}
    """)
    
    with ui.dialog() as dialog, ui.card().classes(
        'p-6 rounded-2xl bg-gradient-to-br from-amber-50 to-yellow-50 border-2 border-amber-300 '
        'shadow-2xl max-w-sm text-center badge-unlock-anim'
    ):
        ui.html(f'<div style="font-size:64px;" class="badge-unlock-anim mb-2">{icon}</div>')
        ui.label('🏆 THÀNH TỰU MỚI!').classes('text-lg font-extrabold text-amber-700 tracking-widest mb-1')
        ui.label(name).classes('text-2xl font-extrabold text-gray-800 mb-1')
        ui.label(desc).classes('text-sm text-gray-500 mb-3')
        if xp:
            ui.label(f'+{xp} XP Bonus').classes('text-amber-600 font-bold text-sm bg-amber-100 px-3 py-1 rounded-full inline-block mb-4')
        ui.button('Tuyệt vời!', on_click=dialog.close).classes(
            'w-full bg-amber-500 text-white font-bold py-2 rounded-xl hover:bg-amber-600 transition-all'
        ).props('no-caps')
    
    dialog.open()


def show_streak_milestone(streak_days: int):
    """Show streak milestone celebration"""
    emojis = {3: "🕯️", 7: "🔥", 14: "🔥🔥", 30: "🌋", 60: "💥", 100: "⭐"}
    emoji = emojis.get(streak_days, "🔥")
    
    ui.notify(
        f"{emoji} Streak {streak_days} ngày! Cháy lên nào!",
        type="positive",
        position="top",
        timeout=4000,
    )


def show_correct_streak(correct_count: int):
    """Show combo notification for consecutive correct answers"""
    if correct_count < 3:
        return
    
    combo_texts = {
        3: ("⚡ COMBO 3!", "Bắt đầu chuỗi!"),
        5: ("⚡⚡ COMBO 5!", "Tia chớp!"),
        7: ("⚡⚡⚡ COMBO 7!", "Siêu tốc!"),
        10: ("🌩️ COMBO 10!", "THẦN SẤM!"),
        15: ("💫 COMBO 15!", "HUYỀN THOẠI!"),
    }
    
    # Find closest milestone
    text = None
    for threshold in sorted(combo_texts.keys(), reverse=True):
        if correct_count >= threshold:
            text = combo_texts[threshold]
            break
    
    if text and correct_count in combo_texts:
        ui.notify(
            f"{text[0]} {text[1]}",
            type="warning",
            position="top",
            timeout=2000,
        )


def create_xp_header_widget(stats: dict) -> None:
    """Create a compact XP/Level/Streak widget for the app header"""
    level_icon = stats.get("level_icon", "🌱")
    level = stats.get("current_level", 1)
    total_xp = stats.get("total_xp", 0)
    streak = stats.get("current_streak", 0)
    multiplier = stats.get("multiplier", 1.0)
    
    with ui.row().classes('items-center gap-2 bg-gray-50 rounded-full px-3 py-1 border border-gray-200'):
        # Level badge
        ui.html(f'<span style="font-size:18px;">{level_icon}</span>').classes('leading-none')
        ui.label(f'Lv.{level}').classes('text-xs font-bold text-indigo-700')
        
        # XP
        ui.label(f'⚡{total_xp}').classes('text-xs font-bold text-blue-600')
        
        # Streak
        if streak > 0:
            fire_class = 'streak-fire-anim' if streak >= 7 else ''
            ui.html(f'<span class="{fire_class}" style="font-size:14px;">🔥</span>').classes('leading-none')
            ui.label(f'{streak}').classes('text-xs font-bold text-orange-600')
        
        # Multiplier badge
        if multiplier > 1.0:
            ui.label(f'x{multiplier}').classes(
                'text-[10px] font-extrabold text-white bg-gradient-to-r from-purple-500 to-pink-500 '
                'px-1.5 py-0.5 rounded-full'
            )


def process_gamification_event(user_id: int, action_type: str, extra_data: dict = None) -> dict:
    """
    Central gamification event processor. 
    Call this after any user action to handle all gamification logic.
    
    Args:
        user_id: The user's database ID
        action_type: One of the XP_REWARDS keys (e.g., 'quiz_correct', 'socratic_passed')
        extra_data: Optional dict with extra context (e.g., {'correct_streak': 5})
    
    Returns: dict with all gamification results
    """
    from gamification.xp_engine import XPEngine
    from gamification.streak_service import StreakService
    from gamification.achievement_service import AchievementService

    results = {"xp": None, "streak": None, "achievements": [], "level_up": False}

    # 1. Daily check-in
    streak_result = StreakService.check_in(user_id)
    results["streak"] = streak_result

    # Award daily login bonus if new day
    if streak_result.get("daily_bonus_awarded"):
        daily_xp = XPEngine.add_xp(user_id, "daily_login")
        show_xp_gain(daily_xp["xp_gained"], daily_xp["multiplier"], "Bonus đăng nhập")
        
        # Check streak milestones
        streak = streak_result["streak"]
        if streak in (3, 7, 14, 30, 60, 100):
            show_streak_milestone(streak)

    # 2. Add XP for action
    xp_result = XPEngine.add_xp(user_id, action_type)
    results["xp"] = xp_result

    # Show XP gain notification
    action_labels = {
        "quiz_correct": "Trắc nghiệm đúng",
        "fill_blank_correct": "Điền từ đúng",
        "matching_correct": "Nối từ đúng",
        "socratic_passed": "Socratic thành công",
        "video_watched": "Xem video",
        "tree_created": "Tạo cây tri thức",
    }
    show_xp_gain(xp_result["xp_gained"], xp_result["multiplier"], action_labels.get(action_type, ""))

    # 3. Level up check
    if xp_result.get("leveled_up"):
        results["level_up"] = True
        info = xp_result["level_info"]
        show_level_up(xp_result["new_level"], info["name"], info["icon"])

    # 4. Achievement checks
    # Check night owl easter egg
    night_achievements = AchievementService.check_night_owl(user_id)
    
    # Increment relevant counter
    counter_map = {
        "quiz_correct": None,  # Handled by total_quizzes in check_all
        "fill_blank_correct": None,
        "matching_correct": None,
        "socratic_passed": "socratic_passed",
        "tree_created": "trees_created",
        "onboarding_done": "onboarding_done",
    }
    counter_key = counter_map.get(action_type)
    if counter_key:
        AchievementService.increment_counter(user_id, counter_key)

    # Handle correct streak
    if extra_data and "correct_streak" in extra_data:
        streak_val = extra_data["correct_streak"]
        AchievementService.set_counter(user_id, "correct_streak", streak_val)
        show_correct_streak(streak_val)

    # Run full achievement check
    new_achievements = AchievementService.check_all(user_id)
    results["achievements"] = new_achievements

    # Show achievement unlock notifications
    for ach in new_achievements:
        show_achievement_unlock(ach)
        # Award bonus XP for achievement
        if ach.get("xp_reward"):
            XPEngine.add_xp(user_id, "achievement_bonus", custom_xp=ach["xp_reward"])

    # Also add achievements from night owl check (avoid duplicates)
    for ach in night_achievements:
        if ach not in new_achievements:
            show_achievement_unlock(ach)

    return results

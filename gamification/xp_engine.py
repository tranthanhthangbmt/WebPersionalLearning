# gamification/xp_engine.py
"""
XP (Experience Points) Engine
- Handles XP rewards for all user actions
- Level system with thresholds
- XP multiplier based on streak
- Level-up detection
"""

from database import engine, Session, select, UserProgress
from datetime import datetime, date
from nicegui import app


# ============================================================
#  LEVEL & XP CONFIGURATION
# ============================================================

LEVEL_CONFIG = {
    1: {"name": "Tân binh",    "icon": "🌱", "min_xp": 0},
    2: {"name": "Học trò",     "icon": "📖", "min_xp": 100},
    3: {"name": "Chiến binh",  "icon": "⚔️", "min_xp": 500},
    4: {"name": "Bậc thầy",    "icon": "🏅", "min_xp": 1500},
    5: {"name": "Huyền thoại", "icon": "👑", "min_xp": 5000},
    6: {"name": "Thần thoại",  "icon": "💎", "min_xp": 15000},
}

XP_THRESHOLDS = [0, 100, 500, 1500, 5000, 15000, 50000]

# XP rewards per action type
XP_REWARDS = {
    "quiz_correct":      10,
    "fill_blank_correct": 15,
    "matching_correct":   15,
    "socratic_passed":    25,
    "video_watched":      5,
    "daily_login":        20,
    "tree_created":       30,
    "onboarding_done":    50,
}

# Streak multiplier tiers
STREAK_MULTIPLIERS = {
    0:  1.0,
    3:  1.2,   # 3-day streak → x1.2
    7:  1.5,   # 7-day streak → x1.5
    14: 1.8,   # 14-day streak → x1.8
    30: 2.0,   # 30-day streak → x2.0
}


class XPEngine:
    """Core XP engine - handles XP calculation, level detection, and multipliers"""

    @staticmethod
    def get_streak_multiplier(streak_days: int) -> float:
        """Calculate XP multiplier based on current streak"""
        multiplier = 1.0
        for threshold, mult in sorted(STREAK_MULTIPLIERS.items()):
            if streak_days >= threshold:
                multiplier = mult
        return multiplier

    @staticmethod
    def calculate_level(total_xp: int) -> int:
        """Determine level from total XP"""
        level = 1
        for lvl, config in sorted(LEVEL_CONFIG.items()):
            if total_xp >= config["min_xp"]:
                level = lvl
        return level

    @staticmethod
    def get_level_info(level: int) -> dict:
        """Get level name and icon"""
        return LEVEL_CONFIG.get(level, LEVEL_CONFIG[1])

    @staticmethod
    def get_xp_for_next_level(current_level: int) -> int:
        """Get XP required to reach next level"""
        idx = min(current_level + 1, len(XP_THRESHOLDS) - 1)
        return XP_THRESHOLDS[idx]

    @staticmethod
    def get_xp_progress(total_xp: int, current_level: int) -> float:
        """Get progress towards next level as 0.0 - 1.0"""
        current_threshold = XP_THRESHOLDS[min(current_level, len(XP_THRESHOLDS) - 1)]
        next_threshold = XP_THRESHOLDS[min(current_level + 1, len(XP_THRESHOLDS) - 1)]
        if next_threshold <= current_threshold:
            return 1.0
        return max(0.0, min(1.0, (total_xp - current_threshold) / (next_threshold - current_threshold)))

    @staticmethod
    def add_xp(user_id: int, action_type: str, custom_xp: int = None) -> dict:
        """
        Award XP for an action. Returns a dict with details about the XP gain.
        
        Returns:
            {
                "xp_gained": int,
                "multiplier": float,
                "base_xp": int,
                "total_xp": int,
                "old_level": int,
                "new_level": int,
                "leveled_up": bool,
                "level_info": dict,
                "streak": int,
            }
        """
        if user_id == 0:
            # GUEST MODE: Use session storage
            if 'guest_progress' not in app.storage.user:
                app.storage.user['guest_progress'] = {
                    'total_xp': 100, # BẮT ĐẦU VỚI 100 XP NHƯ YÊU CẦU
                    'current_level': 1,
                    'current_streak': 0,
                    'daily_xp_earned': 0,
                    'total_quizzes_done': 0,
                    'total_correct': 0,
                }
            
            p_dict = app.storage.user['guest_progress']
            base_xp = custom_xp if custom_xp is not None else XP_REWARDS.get(action_type, 5)
            multiplier = XPEngine.get_streak_multiplier(p_dict.get('current_streak', 0))
            xp_gained = int(base_xp * multiplier)
            
            old_level = p_dict.get('current_level', 1)
            p_dict['total_xp'] = max(0, p_dict.get('total_xp', 0) + xp_gained)
            p_dict['daily_xp_earned'] += xp_gained
            
            if "correct" in action_type or "passed" in action_type:
                p_dict['total_quizzes_done'] += 1
                p_dict['total_correct'] += 1
            elif action_type in ("quiz_wrong", "fill_blank_wrong", "matching_wrong", "socratic_failed"):
                p_dict['total_quizzes_done'] += 1
                
            new_level = XPEngine.calculate_level(p_dict['total_xp'])
            p_dict['current_level'] = new_level
            app.storage.user['guest_progress'] = p_dict # Persist
            
            return {
                "xp_gained": xp_gained, "multiplier": multiplier, "base_xp": base_xp,
                "total_xp": p_dict['total_xp'], "old_level": old_level, "new_level": new_level,
                "leveled_up": new_level > old_level, "level_info": XPEngine.get_level_info(new_level),
                "streak": p_dict.get('current_streak', 0), "daily_xp": p_dict['daily_xp_earned'],
            }

        with Session(engine) as session:
            progress = session.exec(
                select(UserProgress).where(UserProgress.user_id == user_id)
            ).first()
            
            if not progress:
                progress = UserProgress(user_id=user_id)
                session.add(progress)
                session.flush()

            # Calculate base XP
            base_xp = custom_xp if custom_xp is not None else XP_REWARDS.get(action_type, 5)
            
            # Apply streak multiplier
            multiplier = XPEngine.get_streak_multiplier(progress.current_streak)
            xp_gained = int(base_xp * multiplier)

            # Save old level
            old_level = progress.current_level

            # Update progress
            progress.total_xp += xp_gained
            progress.daily_xp_earned += xp_gained

            # Update quiz stats for quiz-related actions
            if "correct" in action_type or "passed" in action_type:
                progress.total_quizzes_done += 1
                progress.total_correct += 1
            elif action_type in ("quiz_wrong", "fill_blank_wrong", "matching_wrong", "socratic_failed"):
                progress.total_quizzes_done += 1

            # Calculate new level
            new_level = XPEngine.calculate_level(progress.total_xp)
            progress.current_level = new_level

            session.add(progress)
            session.commit()

            leveled_up = new_level > old_level

            return {
                "xp_gained": xp_gained,
                "multiplier": multiplier,
                "base_xp": base_xp,
                "total_xp": progress.total_xp,
                "old_level": old_level,
                "new_level": new_level,
                "leveled_up": leveled_up,
                "level_info": XPEngine.get_level_info(new_level),
                "streak": progress.current_streak,
                "daily_xp": progress.daily_xp_earned,
            }

    @staticmethod
    def get_user_stats(user_id: int) -> dict:
        """Get full user gamification stats"""
        if user_id == 0:
            # GUEST MODE: Use session storage
            if 'guest_progress' not in app.storage.user:
                app.storage.user['guest_progress'] = {
                    'total_xp': 100, # BẮT ĐẦU VỚI 100 XP NHƯ YÊU CẦU
                    'current_level': 1,
                    'current_streak': 0,
                    'daily_xp_earned': 0,
                    'total_quizzes_done': 0,
                    'total_correct': 0,
                    'longest_streak': 0,
                }
            p = app.storage.user['guest_progress']
            level_info = XPEngine.get_level_info(p['current_level'])
            return {
                "total_xp": p['total_xp'],
                "current_level": p['current_level'],
                "level_name": level_info["name"],
                "level_icon": level_info["icon"],
                "xp_progress": XPEngine.get_xp_progress(p['total_xp'], p['current_level']),
                "next_level_xp": XPEngine.get_xp_for_next_level(p['current_level']),
                "current_streak": p['current_streak'],
                "longest_streak": p.get('longest_streak', 0),
                "daily_xp": p['daily_xp_earned'],
                "total_quizzes": p['total_quizzes_done'],
                "total_correct": p['total_correct'],
                "accuracy": (p['total_correct'] / max(1, p['total_quizzes_done'])) * 100,
                "multiplier": XPEngine.get_streak_multiplier(p['current_streak']),
            }

        with Session(engine) as session:
            progress = session.exec(
                select(UserProgress).where(UserProgress.user_id == user_id)
            ).first()
            
            if not progress:
                progress = UserProgress(user_id=user_id)
                session.add(progress)
                session.commit()

            level_info = XPEngine.get_level_info(progress.current_level)
            xp_progress = XPEngine.get_xp_progress(progress.total_xp, progress.current_level)
            next_level_xp = XPEngine.get_xp_for_next_level(progress.current_level)

            return {
                "total_xp": progress.total_xp,
                "current_level": progress.current_level,
                "level_name": level_info["name"],
                "level_icon": level_info["icon"],
                "xp_progress": xp_progress,
                "next_level_xp": next_level_xp,
                "current_streak": progress.current_streak,
                "longest_streak": progress.longest_streak,
                "daily_xp": progress.daily_xp_earned,
                "total_quizzes": progress.total_quizzes_done,
                "total_correct": progress.total_correct,
                "accuracy": (progress.total_correct / max(1, progress.total_quizzes_done)) * 100,
                "multiplier": XPEngine.get_streak_multiplier(progress.current_streak),
            }

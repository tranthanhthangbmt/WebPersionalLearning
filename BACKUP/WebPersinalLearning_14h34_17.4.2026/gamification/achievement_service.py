# gamification/achievement_service.py
"""
Achievement & Badge System
- Badge definitions with criteria
- Progress tracking per achievement
- Unlock check after each interaction
- Badge showcase data provider
"""

from database import engine, Session, select, UserProgress
from datetime import datetime, date
import json
import os


# ============================================================
#  ACHIEVEMENT DEFINITIONS
# ============================================================

ACHIEVEMENTS = {
    # --- BEGINNER ---
    "first_quiz": {
        "name": "Khởi đầu",
        "icon": "🏅",
        "description": "Hoàn thành bài quiz đầu tiên",
        "category": "beginner",
        "criteria": {"type": "total_quizzes", "threshold": 1},
        "xp_reward": 50,
    },
    "first_tree": {
        "name": "Người trồng cây",
        "icon": "🌳",
        "description": "Tạo cây tri thức đầu tiên",
        "category": "beginner",
        "criteria": {"type": "custom", "key": "trees_created", "threshold": 1},
        "xp_reward": 50,
    },
    "onboarding_complete": {
        "name": "Nhập môn",
        "icon": "🎒",
        "description": "Hoàn thành onboarding wizard",
        "category": "beginner",
        "criteria": {"type": "custom", "key": "onboarding_done", "threshold": 1},
        "xp_reward": 30,
    },

    # --- STREAK ---
    "streak_3": {
        "name": "Ngọn lửa nhỏ",
        "icon": "🕯️",
        "description": "Duy trì streak 3 ngày liên tiếp",
        "category": "streak",
        "criteria": {"type": "streak", "threshold": 3},
        "xp_reward": 30,
    },
    "streak_7": {
        "name": "Ngọn lửa bất diệt",
        "icon": "🔥",
        "description": "Duy trì streak 7 ngày liên tiếp",
        "category": "streak",
        "criteria": {"type": "streak", "threshold": 7},
        "xp_reward": 100,
    },
    "streak_30": {
        "name": "Hỏa diệm sơn",
        "icon": "🌋",
        "description": "Duy trì streak 30 ngày liên tiếp",
        "category": "streak",
        "criteria": {"type": "streak", "threshold": 30},
        "xp_reward": 500,
    },

    # --- MASTERY ---
    "chapter_master": {
        "name": "Bộ não siêu việt",
        "icon": "🧠",
        "description": "Đạt 100% mastery 1 chương",
        "category": "mastery",
        "criteria": {"type": "custom", "key": "chapter_mastered", "threshold": 1},
        "xp_reward": 200,
    },
    "tree_graduate": {
        "name": "Tốt nghiệp",
        "icon": "🎓",
        "description": "Hoàn thành toàn bộ cây tri thức",
        "category": "mastery",
        "criteria": {"type": "custom", "key": "tree_completed", "threshold": 1},
        "xp_reward": 500,
    },

    # --- COMBAT ---
    "correct_streak_5": {
        "name": "Tia chớp",
        "icon": "⚡",
        "description": "Trả lời đúng 5 câu liên tiếp",
        "category": "combat",
        "criteria": {"type": "custom", "key": "correct_streak", "threshold": 5},
        "xp_reward": 50,
    },
    "correct_streak_10": {
        "name": "Sấm sét",
        "icon": "⛈️",
        "description": "Trả lời đúng 10 câu liên tiếp",
        "category": "combat",
        "criteria": {"type": "custom", "key": "correct_streak", "threshold": 10},
        "xp_reward": 150,
    },
    "quiz_50": {
        "name": "Chiến binh tri thức",
        "icon": "⚔️",
        "description": "Hoàn thành 50 bài quiz",
        "category": "combat",
        "criteria": {"type": "total_quizzes", "threshold": 50},
        "xp_reward": 100,
    },
    "quiz_200": {
        "name": "Bất khả chiến bại",
        "icon": "🛡️",
        "description": "Hoàn thành 200 bài quiz",
        "category": "combat",
        "criteria": {"type": "total_quizzes", "threshold": 200},
        "xp_reward": 300,
    },

    # --- SOCRATIC ---
    "socratic_5": {
        "name": "Triết gia tập sự",
        "icon": "📜",
        "description": "Vượt qua 5 phiên Socratic",
        "category": "socratic",
        "criteria": {"type": "custom", "key": "socratic_passed", "threshold": 5},
        "xp_reward": 100,
    },
    "socratic_10": {
        "name": "Socrates",
        "icon": "💎",
        "description": "Vượt qua 10 phiên Socratic",
        "category": "socratic",
        "criteria": {"type": "custom", "key": "socratic_passed", "threshold": 10},
        "xp_reward": 300,
    },

    # --- EASTER EGGS ---
    "night_owl": {
        "name": "Cú đêm",
        "icon": "🦉",
        "description": "Học lúc 23h - 5h sáng",
        "category": "easter_egg",
        "criteria": {"type": "custom", "key": "night_study", "threshold": 1},
        "xp_reward": 30,
    },
    "xp_1000": {
        "name": "Ngàn sao",
        "icon": "🌟",
        "description": "Tích lũy 1,000 XP",
        "category": "milestone",
        "criteria": {"type": "total_xp", "threshold": 1000},
        "xp_reward": 50,
    },
    "xp_5000": {
        "name": "Vạn tinh",
        "icon": "✨",
        "description": "Tích lũy 5,000 XP",
        "category": "milestone",
        "criteria": {"type": "total_xp", "threshold": 5000},
        "xp_reward": 200,
    },
}


def _get_user_achievements_file(user_id: int) -> str:
    """Get path to user's achievements file"""
    return os.path.join("user_data", f"_achievements_{user_id}.json")


def _load_user_achievements(user_id: int) -> dict:
    """Load user's unlocked achievements and custom counters"""
    filepath = _get_user_achievements_file(user_id)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"unlocked": {}, "counters": {}}


def _save_user_achievements(user_id: int, data: dict):
    """Save user's achievement data"""
    filepath = _get_user_achievements_file(user_id)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class AchievementService:
    """Manages achievement unlocking and progress tracking"""

    @staticmethod
    def increment_counter(user_id: int, counter_key: str, amount: int = 1) -> list:
        """
        Increment a custom counter and check for any newly unlocked achievements.
        
        Returns: list of newly unlocked achievement dicts
        """
        data = _load_user_achievements(user_id)
        
        # Increment counter
        if counter_key not in data["counters"]:
            data["counters"][counter_key] = 0
        data["counters"][counter_key] += amount
        
        _save_user_achievements(user_id, data)
        
        # Check achievements
        return AchievementService.check_all(user_id)

    @staticmethod
    def set_counter(user_id: int, counter_key: str, value: int) -> list:
        """Set a custom counter to a specific value (for max-type counters)"""
        data = _load_user_achievements(user_id)
        current = data["counters"].get(counter_key, 0)
        data["counters"][counter_key] = max(current, value)
        _save_user_achievements(user_id, data)
        return AchievementService.check_all(user_id)

    @staticmethod
    def check_all(user_id: int) -> list:
        """
        Check all achievements and unlock any that meet criteria.
        Returns list of NEWLY unlocked achievements.
        """
        data = _load_user_achievements(user_id)
        newly_unlocked = []

        # Load user progress from DB for stats-based checks
        with Session(engine) as session:
            progress = session.exec(
                select(UserProgress).where(UserProgress.user_id == user_id)
            ).first()

        if not progress:
            return []

        for ach_id, ach_def in ACHIEVEMENTS.items():
            # Skip already unlocked
            if ach_id in data["unlocked"]:
                continue

            criteria = ach_def["criteria"]
            unlocked = False

            if criteria["type"] == "total_quizzes":
                unlocked = progress.total_quizzes_done >= criteria["threshold"]
            elif criteria["type"] == "streak":
                unlocked = progress.current_streak >= criteria["threshold"]
            elif criteria["type"] == "total_xp":
                unlocked = progress.total_xp >= criteria["threshold"]
            elif criteria["type"] == "custom":
                counter_val = data["counters"].get(criteria["key"], 0)
                unlocked = counter_val >= criteria["threshold"]

            if unlocked:
                data["unlocked"][ach_id] = {
                    "unlocked_at": datetime.now().isoformat(),
                    "name": ach_def["name"],
                    "icon": ach_def["icon"],
                }
                newly_unlocked.append({
                    "id": ach_id,
                    **ach_def,
                })

        if newly_unlocked:
            _save_user_achievements(user_id, data)

        return newly_unlocked

    @staticmethod
    def check_night_owl(user_id: int) -> list:
        """Check Easter egg: studying between 23h-5h"""
        hour = datetime.now().hour
        if hour >= 23 or hour < 5:
            return AchievementService.increment_counter(user_id, "night_study", 1)
        return []

    @staticmethod
    def get_all_achievements(user_id: int) -> list:
        """Get all achievements with user's unlock status"""
        data = _load_user_achievements(user_id)
        result = []

        for ach_id, ach_def in ACHIEVEMENTS.items():
            is_unlocked = ach_id in data["unlocked"]
            unlock_info = data["unlocked"].get(ach_id, {})
            
            # Calculate progress
            criteria = ach_def["criteria"]
            current_progress = 0

            if criteria["type"] == "custom":
                current_progress = data["counters"].get(criteria["key"], 0)
            else:
                # Need DB data
                with Session(engine) as session:
                    progress = session.exec(
                        select(UserProgress).where(UserProgress.user_id == user_id)
                    ).first()
                    if progress:
                        if criteria["type"] == "total_quizzes":
                            current_progress = progress.total_quizzes_done
                        elif criteria["type"] == "streak":
                            current_progress = progress.current_streak
                        elif criteria["type"] == "total_xp":
                            current_progress = progress.total_xp

            result.append({
                "id": ach_id,
                "name": ach_def["name"],
                "icon": ach_def["icon"],
                "description": ach_def["description"],
                "category": ach_def["category"],
                "is_unlocked": is_unlocked,
                "unlocked_at": unlock_info.get("unlocked_at"),
                "progress": min(current_progress, criteria.get("threshold", 1)),
                "threshold": criteria.get("threshold", 1),
                "xp_reward": ach_def["xp_reward"],
            })

        return result

    @staticmethod
    def get_unlocked_count(user_id: int) -> tuple:
        """Returns (unlocked_count, total_count)"""
        data = _load_user_achievements(user_id)
        return len(data["unlocked"]), len(ACHIEVEMENTS)

    @staticmethod
    def get_unlocked_badges(user_id: int) -> list:
        """Get only unlocked badges for showcase"""
        data = _load_user_achievements(user_id)
        badges = []
        for ach_id, unlock_info in data["unlocked"].items():
            if ach_id in ACHIEVEMENTS:
                badges.append({
                    "id": ach_id,
                    "name": ACHIEVEMENTS[ach_id]["name"],
                    "icon": ACHIEVEMENTS[ach_id]["icon"],
                    "description": ACHIEVEMENTS[ach_id]["description"],
                    "unlocked_at": unlock_info.get("unlocked_at"),
                })
        return badges

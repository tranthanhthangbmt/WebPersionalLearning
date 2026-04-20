# gamification/streak_service.py
"""
Streak Service - Daily streak tracking
- Check-in logic (auto on any activity)
- Streak freeze mechanism
- Daily XP reset
- Activity history for heatmap
"""

from database import engine, Session, select, UserProgress
from datetime import datetime, date, timedelta
import json
import os


class StreakService:
    """Manages daily streak tracking and activity history"""

    @staticmethod
    def check_in(user_id: int) -> dict:
        """
        Process a daily check-in. Called on any user activity.
        Handles streak increment, break detection, and daily XP reset.
        
        Returns:
            {
                "streak": int,
                "streak_changed": bool,
                "is_new_day": bool,
                "daily_bonus_awarded": bool,
                "longest_streak": int,
            }
        """
        today_str = date.today().isoformat()  # "YYYY-MM-DD"

        with Session(engine) as session:
            progress = session.exec(
                select(UserProgress).where(UserProgress.user_id == user_id)
            ).first()

            if not progress:
                progress = UserProgress(user_id=user_id)
                session.add(progress)
                session.flush()

            last_active = progress.last_active_date
            streak_changed = False
            is_new_day = False
            daily_bonus = False

            if last_active == today_str:
                # Already checked in today - no change
                pass
            elif last_active == (date.today() - timedelta(days=1)).isoformat():
                # Consecutive day! Increment streak
                progress.current_streak += 1
                progress.daily_xp_earned = 0  # Reset daily XP
                streak_changed = True
                is_new_day = True
                daily_bonus = True
            elif last_active is None:
                # First ever activity
                progress.current_streak = 1
                progress.daily_xp_earned = 0
                streak_changed = True
                is_new_day = True
                daily_bonus = True
            else:
                # Streak broken! Check for streak freeze
                frozen = StreakService._check_streak_freeze(user_id)
                if frozen:
                    # Freeze used - keep streak
                    progress.current_streak += 1
                    streak_changed = True
                else:
                    # Streak reset
                    progress.current_streak = 1
                    streak_changed = True
                progress.daily_xp_earned = 0
                is_new_day = True
                daily_bonus = True

            # Update longest streak
            if progress.current_streak > progress.longest_streak:
                progress.longest_streak = progress.current_streak

            progress.last_active_date = today_str
            session.add(progress)
            session.commit()

            # Save activity to heatmap file
            StreakService._log_activity(user_id, today_str)

            return {
                "streak": progress.current_streak,
                "streak_changed": streak_changed,
                "is_new_day": is_new_day,
                "daily_bonus_awarded": daily_bonus,
                "longest_streak": progress.longest_streak,
            }

    @staticmethod
    def _check_streak_freeze(user_id: int) -> bool:
        """Check if user has an active streak freeze (Premium feature)"""
        # For now, streak freeze is a placeholder for premium feature
        # TODO: Implement streak freeze inventory system
        return False

    @staticmethod
    def _log_activity(user_id: int, date_str: str):
        """Log daily activity for heatmap visualization"""
        activity_dir = f"user_data"
        # We need the username, but we only have user_id
        # Store in a generic location keyed by user_id
        heatmap_file = os.path.join(activity_dir, f"_activity_{user_id}.json")
        
        activity_data = {}
        if os.path.exists(heatmap_file):
            try:
                with open(heatmap_file, 'r', encoding='utf-8') as f:
                    activity_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                activity_data = {}

        # Increment activity count for today
        if date_str not in activity_data:
            activity_data[date_str] = 0
        activity_data[date_str] += 1

        # Keep only last 365 days
        cutoff = (date.today() - timedelta(days=365)).isoformat()
        activity_data = {k: v for k, v in activity_data.items() if k >= cutoff}

        try:
            os.makedirs(os.path.dirname(heatmap_file), exist_ok=True)
            with open(heatmap_file, 'w', encoding='utf-8') as f:
                json.dump(activity_data, f, ensure_ascii=False)
        except IOError:
            pass  # Non-critical - don't fail on heatmap logging

    @staticmethod
    def get_activity_heatmap(user_id: int, days: int = 90) -> dict:
        """
        Get activity data for heatmap rendering.
        Returns dict of {date_str: activity_count} for last N days.
        """
        heatmap_file = os.path.join("user_data", f"_activity_{user_id}.json")
        
        activity_data = {}
        if os.path.exists(heatmap_file):
            try:
                with open(heatmap_file, 'r', encoding='utf-8') as f:
                    activity_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Filter to requested date range
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return {k: v for k, v in activity_data.items() if k >= cutoff}

    @staticmethod
    def get_streak_info(user_id: int) -> dict:
        """Get current streak information"""
        with Session(engine) as session:
            progress = session.exec(
                select(UserProgress).where(UserProgress.user_id == user_id)
            ).first()

            if not progress:
                return {"current_streak": 0, "longest_streak": 0, "last_active": None}

            # Check if streak is still active (not expired)
            today_str = date.today().isoformat()
            yesterday_str = (date.today() - timedelta(days=1)).isoformat()
            
            streak_active = progress.last_active_date in (today_str, yesterday_str)

            return {
                "current_streak": progress.current_streak if streak_active else 0,
                "longest_streak": progress.longest_streak,
                "last_active": progress.last_active_date,
                "is_active_today": progress.last_active_date == today_str,
            }

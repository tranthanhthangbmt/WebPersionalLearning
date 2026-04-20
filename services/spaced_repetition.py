import math
from datetime import datetime, timedelta
from sqlmodel import Session, select
from database import engine, ReviewSchedule

def calculate_sm2(quality: int, repetitions: int, previous_interval: int, previous_ef: float):
    """
    SuperMemo-2 (SM-2) algorithm.
    :param quality: 0-5 (0=Blackout, 5=Perfect)
    :param repetitions: number of consecutive correct responses
    :param previous_interval: previous interval in days
    :param previous_ef: previous easiness factor
    :return: (new_interval, new_repetitions, new_ef)
    """
    quality = max(0, min(5, quality))
    
    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(previous_interval * previous_ef)
        
        repetitions += 1
    else:
        repetitions = 0
        interval = 1
    
    new_ef = previous_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)  # Minimum EF is 1.3
    
    return interval, repetitions, round(new_ef, 3)

def update_review_schedule(user_id: int, subject_id: str, node_id: str, quality: int):
    with Session(engine) as session:
        statement = select(ReviewSchedule).where(
            (ReviewSchedule.user_id == user_id) &
            (ReviewSchedule.subject_id == subject_id) &
            (ReviewSchedule.node_id == node_id)
        )
        schedule = session.exec(statement).first()
        
        if not schedule:
            schedule = ReviewSchedule(
                user_id=user_id,
                subject_id=subject_id,
                node_id=node_id,
                easiness_factor=2.5,
                interval_days=0,
                repetitions=0
            )
            session.add(schedule)
            
        new_interval, new_reps, new_ef = calculate_sm2(
            quality, 
            schedule.repetitions, 
            schedule.interval_days, 
            schedule.easiness_factor
        )
        
        schedule.interval_days = new_interval
        schedule.repetitions = new_reps
        schedule.easiness_factor = new_ef
        schedule.last_quality = quality
        
        # Calculate next review date
        now = datetime.now()
        schedule.next_review_date = now + timedelta(days=new_interval)
        
        session.add(schedule)
        session.commit()
        
        return schedule

def get_due_reviews_today(user_id: int, subject_id: str):
    """Lấy danh sách các node tới hạn ôn tập (next_review_date <= now)"""
    with Session(engine) as session:
        now = datetime.now()
        statement = select(ReviewSchedule).where(
            (ReviewSchedule.user_id == user_id) &
            (ReviewSchedule.subject_id == subject_id) &
            (ReviewSchedule.next_review_date <= now)
        ).order_by(ReviewSchedule.next_review_date)
        
        return session.exec(statement).all()

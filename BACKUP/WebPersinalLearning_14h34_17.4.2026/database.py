from typing import Optional, List
from sqlmodel import Field, SQLModel, create_engine, Session, select
from datetime import datetime, date
import json
import os
import bcrypt

# --- ĐỊNH NGHĨA BẢNG (TABLES) ---

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str  # bcrypt hashed
    email: str = Field(default="", index=True)
    full_name: str
    avatar_url: str = ""
    bio: str = ""
    role: str = "student"  # student, parent, teacher, admin
    group: str = "experimental"  # control vs experimental
    is_onboarded: bool = False  # Đã hoàn thành onboarding chưa
    created_at: datetime = Field(default_factory=datetime.now)

class UserProgress(SQLModel, table=True):
    """Gamification: XP, Streak, Level tracking"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    total_xp: int = 0
    current_level: int = 1
    current_streak: int = 0
    longest_streak: int = 0
    last_active_date: Optional[str] = None  # "YYYY-MM-DD"
    daily_xp_earned: int = 0
    total_quizzes_done: int = 0
    total_correct: int = 0
    total_study_minutes: int = 0

class InteractionLog(SQLModel, table=True):
    """Bảng này lưu từng click chuột, từng câu chat"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    timestamp: datetime = Field(default_factory=datetime.now)
    concept_id: str
    action_type: str # quiz_answer, chat_query, video_pause, tab_switch
    
    # Các chỉ số quan trọng cho Bio-PKT
    mastery_score: float = 0.0
    fatigue_level: float = 0.0
    sentiment: str = "neutral"
    
    # Lưu chi tiết (JSON string) để phân tích sâu sau này
    details: str = "{}" 

class KnowledgeState(SQLModel, table=True):
    """Lưu trạng thái hiện tại (Snapshot) để resume khi user đăng nhập lại"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    concept_id: str
    elo_rating: float = 1200.0
    last_review: datetime = Field(default_factory=datetime.now)

class ReviewSchedule(SQLModel, table=True):
    """Spaced Repetition SM-2 Schedule"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    subject_id: str = Field(index=True)
    node_id: str = Field(index=True)
    
    # SM-2 Parameters
    easiness_factor: float = 2.5
    interval_days: int = 0
    repetitions: int = 0
    
    next_review_date: datetime = Field(default_factory=datetime.now, index=True)
    last_quality: int = 0


# --- CẤU HÌNH ENGINE ---
sqlite_file_name = "pkt_research.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# --- PASSWORD HASHING ---

def hash_password(plain_password: str) -> str:
    """Hash password with bcrypt"""
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # Fallback: plain text comparison for legacy users (pre-bcrypt)
        return plain_password == hashed_password

# --- CÁC HÀM TIỆN ÍCH (CRUD) ---

def get_user_by_username(username: str):
    with Session(engine, expire_on_commit=False) as session:
        statement = select(User).where(User.username == username)
        results = session.exec(statement)
        return results.first()

def get_user_by_email(email: str):
    with Session(engine, expire_on_commit=False) as session:
        statement = select(User).where(User.email == email)
        results = session.exec(statement)
        return results.first()

def create_user(username, password, full_name, email="", role="student"):
    """Create a new user with hashed password"""
    with Session(engine, expire_on_commit=False) as session:
        hashed = hash_password(password)
        user = User(
            username=username, 
            password=hashed, 
            full_name=full_name, 
            email=email,
            role=role
        )
        session.add(user)
        session.commit()
        
        # Create initial UserProgress
        progress = UserProgress(user_id=user.id)
        session.add(progress)
        session.commit()
        
        return user

def authenticate_user(username: str, password: str):
    """Authenticate user - returns User object or None"""
    user = get_user_by_username(username)
    if user and verify_password(password, user.password):
        return user
    return None

def get_user_progress(user_id: int):
    """Get or create UserProgress for a user"""
    with Session(engine, expire_on_commit=False) as session:
        statement = select(UserProgress).where(UserProgress.user_id == user_id)
        progress = session.exec(statement).first()
        if not progress:
            progress = UserProgress(user_id=user_id)
            session.add(progress)
            session.commit()
        return progress

def update_user_onboarded(user_id: int):
    """Mark user as onboarded"""
    with Session(engine) as session:
        statement = select(User).where(User.id == user_id)
        user = session.exec(statement).first()
        if user:
            user.is_onboarded = True
            session.add(user)
            session.commit()

def log_interaction(user_id, concept, action, mastery, fatigue, sentiment, details_dict):
    with Session(engine) as session:
        log = InteractionLog(
            user_id=user_id,
            concept_id=concept,
            action_type=action,
            mastery_score=mastery,
            fatigue_level=fatigue,
            sentiment=sentiment,
            details=json.dumps(details_dict, ensure_ascii=False)
        )
        session.add(log)
        session.commit()

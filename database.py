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
    # --- Sprint 01: Google OAuth fields ---
    google_id: str = Field(default="", index=True)  # Google Account ID
    google_avatar_url: str = ""  # URL avatar từ Google
    google_refresh_token: str = ""  # Refresh token để đổi access_token mới
    drive_root_folder_id: str = ""  # ID thư mục KnowledgeGalaxy_Data trên Drive
    drive_subjects_folder_id: str = ""  # ID thư mục Subjects trên Drive
    drive_profile_file_id: str = ""  # ID file profile.json trên Drive

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

from sqlalchemy import event
from sqlalchemy.pool import NullPool

# Sử dụng NullPool cho SQLite để tránh lỗi I/O trên ổ đĩa ngoài/mạng
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False, "timeout": 60},
    poolclass=NullPool
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # Tối ưu hóa cho độ tin cậy cao trên I/O chậm
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000") # 64MB cache
    cursor.close()

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

def get_user_by_id(user_id: int):
    with Session(engine, expire_on_commit=False) as session:
        statement = select(User).where(User.id == user_id)
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
        
        # Create initial UserProgress with starting XP
        progress = UserProgress(user_id=user.id, total_xp=100)
        session.add(progress)
        session.commit()
        
        return user

def get_user_by_id(user_id: int):
    with Session(engine, expire_on_commit=False) as session:
        statement = select(User).where(User.id == user_id)
        results = session.exec(statement)
        return results.first()

def authenticate_user(username: str, password: str):
    """Authenticate user - returns User object or None"""
    user = get_user_by_username(username)
    if user and verify_password(password, user.password):
        return user
    return None

def get_user_progress(user_id: int):
    """Get or create UserProgress for a user"""
    if user_id == 0:
        # GUEST MODE: Return a mock progress object (not saved to DB)
        return UserProgress(user_id=0, total_xp=0, current_level=1)
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


# --- Sprint 01: Google OAuth User Management ---

def get_user_by_google_id(google_id: str):
    """Tìm user theo Google Account ID."""
    with Session(engine, expire_on_commit=False) as session:
        statement = select(User).where(User.google_id == google_id)
        return session.exec(statement).first()


def get_or_create_google_user(
    google_id: str,
    email: str,
    full_name: str,
    avatar_url: str = "",
    refresh_token: str = "",
) -> User:
    """
    Tìm hoặc tạo user dựa trên Google Account.
    
    Luồng:
    1. Tìm theo google_id → Nếu có, cập nhật refresh_token (nếu có mới) và trả về.
    2. Tìm theo email → Nếu có, liên kết google_id vào user cũ.
    3. Không tìm thấy → Tạo user mới.
    """
    with Session(engine, expire_on_commit=False) as session:
        # Strategy 1: Tìm theo google_id
        user = session.exec(
            select(User).where(User.google_id == google_id)
        ).first()
        if user:
            # Cập nhật refresh_token nếu Google cấp mới
            if refresh_token:
                user.google_refresh_token = refresh_token
            if avatar_url:
                user.google_avatar_url = avatar_url
                user.avatar_url = avatar_url
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

        # Strategy 2: Tìm theo email (User đã đăng ký bằng username/password trước đó)
        user = session.exec(
            select(User).where(User.email == email)
        ).first()
        if user:
            user.google_id = google_id
            user.google_avatar_url = avatar_url
            if not user.avatar_url:
                user.avatar_url = avatar_url
            if refresh_token:
                user.google_refresh_token = refresh_token
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"[DB] Liên kết Google Account vào user hiện có: {user.username}")
            return user

        # Strategy 3: Tạo user mới
        # Sinh username an toàn từ email (vd: john.doe@gmail.com → john_doe)
        base_username = email.split("@")[0].replace(".", "_").replace("-", "_")[:20]
        username = base_username
        counter = 1
        while session.exec(select(User).where(User.username == username)).first():
            username = f"{base_username}_{counter}"
            counter += 1

        new_user = User(
            username=username,
            password="",  # Không cần password cho Google Login
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
            google_id=google_id,
            google_avatar_url=avatar_url,
            google_refresh_token=refresh_token,
            role="student",
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        # Tạo UserProgress ban đầu
        progress = UserProgress(user_id=new_user.id, total_xp=100)
        session.add(progress)
        session.commit()

        print(f"[DB] ✅ Tạo user mới từ Google: {new_user.username} ({email})")
        return new_user


def update_user_drive_ids(user_id: int, root_folder_id: str, subjects_folder_id: str, profile_file_id: str = ""):
    """Lưu Drive folder/file IDs vào user record sau khi init_drive_environment()."""
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == user_id)).first()
        if user:
            user.drive_root_folder_id = root_folder_id
            user.drive_subjects_folder_id = subjects_folder_id
            if profile_file_id:
                user.drive_profile_file_id = profile_file_id
            session.add(user)
            session.commit()

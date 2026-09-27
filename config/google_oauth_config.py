# config/google_oauth_config.py
# ============================================================
# Cấu hình Google OAuth 2.0 cho Sprint 01
# Đọc từ biến môi trường (.env) hoặc fallback sang giá trị mặc định
# ============================================================

import os
from dotenv import load_dotenv

# Load .env file nếu tồn tại
load_dotenv()


class GoogleOAuthConfig:
    """Quản lý cấu hình Google OAuth 2.0 tập trung."""

    # --- OAuth 2.0 Credentials ---
    CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8081/auth/google/callback"
    )

    # --- Scopes ---
    # drive.file: Chỉ truy cập các file do chính app tạo ra (An toàn, dễ qua kiểm duyệt Google)
    # userinfo.email + userinfo.profile: Lấy thông tin cơ bản của người dùng
    SCOPES: list = [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]

    # --- Google API Endpoints ---
    AUTH_URI: str = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    USERINFO_URI: str = "https://www.googleapis.com/oauth2/v2/userinfo"

    # --- Tên thư mục gốc trên Google Drive ---
    DRIVE_ROOT_FOLDER: str = "KnowledgeGalaxy_Data"
    DRIVE_PROFILE_FILE: str = "profile.json"
    DRIVE_SUBJECTS_FOLDER: str = "Subjects"

    # --- Mock Mode (Dùng cho Testing khi chưa có Client ID/Secret) ---
    MOCK_MODE: bool = os.getenv("GOOGLE_MOCK_MODE", "false").lower() == "true"

    @classmethod
    def is_configured(cls) -> bool:
        """Kiểm tra xem Google OAuth đã được cấu hình chưa hoặc đang ở Mock Mode."""
        if cls.MOCK_MODE:
            return True
        return bool(cls.CLIENT_ID and cls.CLIENT_SECRET)

    @classmethod
    def get_client_config(cls) -> dict:
        """Trả về cấu hình dạng dict cho google-auth library."""
        return {
            "web": {
                "client_id": cls.CLIENT_ID,
                "client_secret": cls.CLIENT_SECRET,
                "auth_uri": cls.AUTH_URI,
                "token_uri": cls.TOKEN_URI,
                "redirect_uris": [cls.REDIRECT_URI],
            }
        }

# services/google_drive_service.py
# ============================================================
# Google Drive Service - Sprint 01
# Xử lý toàn bộ luồng OAuth 2.0 và thao tác CRUD trên Google Drive
# ============================================================

import json
import os
from datetime import datetime
from urllib.parse import urlencode

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload, MediaFileUpload, MediaIoBaseDownload
import io

from config.google_oauth_config import GoogleOAuthConfig


class GoogleDriveService:
    """
    Service xử lý toàn bộ giao tiếp với Google OAuth 2.0 và Google Drive API.
    
    Luồng hoạt động:
    1. get_auth_url()         → Tạo URL redirect tới Google Login
    2. exchange_code(code)    → Đổi auth code lấy tokens
    3. get_user_info(tokens)  → Lấy thông tin người dùng
    4. init_drive_env(tokens) → Tạo thư mục KnowledgeGalaxy_Data
    """

    # ─────────────────────────────────────────────
    #  BƯỚC 1: Tạo URL Xác thực (Auth URL)
    # ─────────────────────────────────────────────
    @staticmethod
    def get_auth_url(state: str = "") -> str:
        """
        Tạo URL redirect tới trang đăng nhập Google.
        
        Args:
            state: CSRF token để bảo vệ chống tấn công giả mạo request.
            
        Returns:
            URL dạng string để redirect trình duyệt người dùng.
        """
        params = {
            "client_id": GoogleOAuthConfig.CLIENT_ID,
            "redirect_uri": GoogleOAuthConfig.REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(GoogleOAuthConfig.SCOPES),
            "access_type": "offline",       # Lấy refresh_token để đổi token mới khi hết hạn
            "prompt": "select_account consent", # Hiện trình chọn tài khoản và consent screen
            "state": state,
        }
        return f"{GoogleOAuthConfig.AUTH_URI}?{urlencode(params)}"

    # ─────────────────────────────────────────────
    #  BƯỚC 2: Đổi Authorization Code lấy Tokens
    # ─────────────────────────────────────────────
    @staticmethod
    def exchange_code(code: str) -> dict:
        """
        Đổi authorization code (nhận từ callback) lấy access_token và refresh_token.
        
        Args:
            code: Authorization code từ Google redirect.
            
        Returns:
            Dict chứa access_token, refresh_token, expires_in, token_type.
            
        Raises:
            Exception: Nếu exchange thất bại (VD: code hết hạn).
        """
        if GoogleOAuthConfig.MOCK_MODE and code == 'mock_auth_code_123':
            return {
                "access_token": "mock_access_token_456",
                "refresh_token": "mock_refresh_token_789",
                "expires_in": 3600,
                "token_type": "Bearer"
            }

        payload = {
            "code": code,
            "client_id": GoogleOAuthConfig.CLIENT_ID,
            "client_secret": GoogleOAuthConfig.CLIENT_SECRET,
            "redirect_uri": GoogleOAuthConfig.REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        print(f"[Exchange] Payload sent to Google: {payload}")
        response = requests.post(GoogleOAuthConfig.TOKEN_URI, data=payload, timeout=30)
        print(f"[Exchange] Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"[Exchange] Error payload: {response.text}")
            error_detail = response.json().get("error_description", response.text)
            raise Exception(f"Google Token Exchange Failed: {error_detail}")

        return response.json()

    # ─────────────────────────────────────────────
    #  BƯỚC 3: Lấy thông tin Người dùng từ Google
    # ─────────────────────────────────────────────
    @staticmethod
    def get_user_info(access_token: str) -> dict:
        """
        Gọi Google UserInfo API để lấy email, tên, avatar.
        
        Args:
            access_token: Token hợp lệ từ bước exchange_code().
            
        Returns:
            Dict: {id, email, name, picture, verified_email}
        """
        if GoogleOAuthConfig.MOCK_MODE and access_token == "mock_access_token_456":
            return {
                "id": "123456789",
                "email": "dev.tester@mock.com",
                "name": "Dev Tester (Mock)",
                "picture": "https://www.gstatic.com/images/branding/product/2x/avatar_anonymous_64dp.png",
                "verified_email": True
            }

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            GoogleOAuthConfig.USERINFO_URI, headers=headers, timeout=15
        )

        if response.status_code != 200:
            raise Exception(f"Không thể lấy thông tin Google User: {response.text}")

        return response.json()

    # ─────────────────────────────────────────────
    #  BƯỚC 4: Khởi tạo Môi trường Google Drive
    # ─────────────────────────────────────────────
    @staticmethod
    def _build_drive_service(access_token: str, refresh_token: str = ""):
        """
        Tạo Google Drive API service object.
        Nếu có refresh_token, credentials sẽ tự động làm mới khi access_token hết hạn.
        """
        if refresh_token:
            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri=GoogleOAuthConfig.TOKEN_URI,
                client_id=GoogleOAuthConfig.CLIENT_ID,
                client_secret=GoogleOAuthConfig.CLIENT_SECRET,
            )
        else:
            credentials = Credentials(token=access_token)
            
        return build("drive", "v3", credentials=credentials)

    @staticmethod
    def find_folder(service, folder_name: str, parent_id: str = None) -> str | None:
        """
        Tìm thư mục theo tên trên Google Drive.
        
        Args:
            service: Google Drive service object.
            folder_name: Tên thư mục cần tìm.
            parent_id: ID thư mục cha (None = root).
            
        Returns:
            folder_id nếu tìm thấy, None nếu không tồn tại.
        """
        query = (
            f"name = '{folder_name}' "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = (
            service.files()
            .list(q=query, spaces="drive", fields="files(id, name)", pageSize=1)
            .execute()
        )
        files = results.get("files", [])
        return files[0]["id"] if files else None

    @staticmethod
    def create_folder(service, folder_name: str, parent_id: str = None) -> str:
        """
        Tạo thư mục mới trên Google Drive.
        
        Returns:
            folder_id của thư mục vừa tạo.
        """
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]

        folder = service.files().create(body=file_metadata, fields="id").execute()
        return folder.get("id")

    @classmethod
    def init_drive_environment(cls, access_token: str) -> dict:
        """
        Kiểm tra và tự động tạo cấu trúc thư mục gốc trên Google Drive.
        
        Cấu trúc:
        KnowledgeGalaxy_Data/
        ├── profile.json
        └── Subjects/
        
        Args:
            access_token: Token hợp lệ.
            
        Returns:
            Dict: {root_folder_id, subjects_folder_id, profile_file_id, created_new}
        """
        if GoogleOAuthConfig.MOCK_MODE and access_token == "mock_access_token_456":
            return {
                "root_folder_id": "mock_root_id_001",
                "subjects_folder_id": "mock_subjects_id_002",
                "profile_file_id": "mock_profile_id_003",
                "created_new": True,
            }

        service = cls._build_drive_service(access_token)
        created_new = False

        # 1. Tìm hoặc tạo thư mục gốc
        root_id = cls.find_folder(service, GoogleOAuthConfig.DRIVE_ROOT_FOLDER)
        if not root_id:
            root_id = cls.create_folder(service, GoogleOAuthConfig.DRIVE_ROOT_FOLDER)
            created_new = True
            print(f"[DriveService] ✅ Đã tạo thư mục gốc: {GoogleOAuthConfig.DRIVE_ROOT_FOLDER}")

        # 2. Tìm hoặc tạo thư mục Subjects
        subjects_id = cls.find_folder(
            service, GoogleOAuthConfig.DRIVE_SUBJECTS_FOLDER, parent_id=root_id
        )
        if not subjects_id:
            subjects_id = cls.create_folder(
                service, GoogleOAuthConfig.DRIVE_SUBJECTS_FOLDER, parent_id=root_id
            )
            print(f"[DriveService] ✅ Đã tạo thư mục: {GoogleOAuthConfig.DRIVE_SUBJECTS_FOLDER}")

        # 3. Tìm hoặc tạo profile.json
        profile_id = cls._find_file(service, GoogleOAuthConfig.DRIVE_PROFILE_FILE, root_id)
        if not profile_id:
            profile_data = {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "total_xp": 0,
                "current_level": 1,
                "current_streak": 0,
                "longest_streak": 0,
                "subjects": [],
                "settings": {
                    "theme": "dark",
                    "language": "vi",
                    "notifications": True,
                },
            }
            profile_id = cls._create_json_file(
                service,
                GoogleOAuthConfig.DRIVE_PROFILE_FILE,
                profile_data,
                parent_id=root_id,
            )
            print(f"[DriveService] ✅ Đã tạo file: {GoogleOAuthConfig.DRIVE_PROFILE_FILE}")

        result = {
            "root_folder_id": root_id,
            "subjects_folder_id": subjects_id,
            "profile_file_id": profile_id,
            "created_new": created_new,
        }
        print(f"[DriveService] Drive Environment: {result}")
        return result

    # ─────────────────────────────────────────────
    #  Helpers: Thao tác File trên Drive
    # ─────────────────────────────────────────────
    @staticmethod
    def _find_file(service, file_name: str, parent_id: str = None) -> str | None:
        """Tìm file (không phải folder) theo tên."""
        query = (
            f"name = '{file_name}' "
            f"and mimeType != 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = (
            service.files()
            .list(q=query, spaces="drive", fields="files(id, name)", pageSize=1)
            .execute()
        )
        files = results.get("files", [])
        return files[0]["id"] if files else None

    @staticmethod
    def _create_json_file(
        service, file_name: str, data: dict, parent_id: str = None
    ) -> str:
        """Tạo file JSON mới trên Google Drive."""
        file_metadata = {"name": file_name, "mimeType": "application/json"}
        if parent_id:
            file_metadata["parents"] = [parent_id]

        content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        media = MediaInMemoryUpload(content, mimetype="application/json")

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        return file.get("id")

    @staticmethod
    def update_json_file(service, file_id: str, data: dict) -> bool:
        """
        Ghi đè (Update) nội dung file JSON hiện có trên Google Drive.
        Tránh sinh ra các file trùng tên.
        """
        try:
            content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            media = MediaInMemoryUpload(content, mimetype="application/json")

            service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            return True
        except Exception as e:
            print(f"[DriveService] ❌ Lỗi update file {file_id}: {e}")
            return False

    @staticmethod
    def download_json_file(service, file_id: str) -> dict | None:
        """Tải và parse nội dung file JSON từ Google Drive."""
        try:
            results = service.files().get_media(fileId=file_id).execute()
            return json.loads(results.decode("utf-8"))
        except Exception as e:
            print(f"[DriveService] ❌ Lỗi download file {file_id}: {e}")
            return None

    @staticmethod
    def upload_file(service, local_path: str, file_name: str, parent_id: str = None, mimetype: str = None) -> str:
        """Tải một file bất kỳ (PDF, Index, v.v.) lên Google Drive."""
        file_metadata = {'name': file_name}
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        media = MediaFileUpload(local_path, mimetype=mimetype, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')

    @staticmethod
    def download_file(service, file_id: str, save_path: str) -> bool:
        """Tải một file từ Google Drive về máy cục bộ."""
        try:
            request = service.files().get_media(fileId=file_id)
            fh = io.FileIO(save_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            return True
        except Exception as e:
            print(f"[DriveService] ❌ Lỗi download file {file_id}: {e}")
            return False

    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict:
        """
        Dùng refresh_token để lấy access_token mới khi token cũ hết hạn.
        
        Returns:
            Dict chứa access_token mới.
        """
        payload = {
            "client_id": GoogleOAuthConfig.CLIENT_ID,
            "client_secret": GoogleOAuthConfig.CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        response = requests.post(GoogleOAuthConfig.TOKEN_URI, data=payload, timeout=15)

        if response.status_code != 200:
            raise Exception(f"Refresh Token Failed: {response.text}")

        return response.json()

    @classmethod
    def get_user_service(cls, user_id: int):
        """
        Lấy Google Drive service đã được xác thực cho một user.
        Tự động lấy token từ DB và hỗ trợ tự động refresh.
        """
        if GoogleOAuthConfig.MOCK_MODE:
            return None # Mock service not implemented for real calls

        from database import get_user_by_id
        user = get_user_by_id(user_id)
        if not user or not user.google_refresh_token:
            return None
            
        # Lấy access_token từ session
        from nicegui import app
        access_token = app.storage.user.get('google_access_token', '')
        
        # Nếu chưa có access_token trong session, thử refresh ngay
        if not access_token:
            try:
                refresh_data = cls.refresh_access_token(user.google_refresh_token)
                access_token = refresh_data.get('access_token')
                app.storage.user['google_access_token'] = access_token
                print(f"[DriveService] 🔄 Đã tự động refresh token cho user {user_id}")
            except Exception as e:
                print(f"[DriveService] ❌ Không thể refresh token cho user {user_id}: {e}")
                return None
        
        return cls._build_drive_service(access_token, user.google_refresh_token)

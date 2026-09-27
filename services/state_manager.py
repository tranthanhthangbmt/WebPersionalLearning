import asyncio
import time
import json
from typing import Dict, Any, Optional
from nicegui import app, ui
from services.google_drive_service import GoogleDriveService

class SyncStateManager:
    """
    Quản lý trạng thái dữ liệu cục bộ và tự động đồng bộ lên Google Drive.
    Áp dụng kỹ thuật Debounce để tối ưu hóa số lượng API calls.
    """
    _instance = None
    
    def __init__(self):
        self.profile_data: Dict[str, Any] = {}
        self.subjects_cache: Dict[str, Dict[str, Any]] = {}
        self.is_dirty = False
        self.last_change_time = 0
        self.sync_interval = 5.0  # Debounce 5 giây
        self.is_syncing = False
        
        # Lưu trữ ID để dùng trong luồng chạy ngầm
        self.user_id: Optional[int] = None
        self.profile_file_id: Optional[str] = None
        
        # Bắt đầu vòng lặp đồng bộ ngầm bằng Asyncio (không phụ thuộc UI context)
        asyncio.create_task(self._auto_sync_loop())

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SyncStateManager()
        return cls._instance

    def load_profile(self, data: Dict[str, Any], user_id: int, file_id: str):
        """Load dữ liệu từ Drive vào RAM kèm theo thông tin định danh."""
        self.profile_data = data
        self.user_id = user_id
        self.profile_file_id = file_id
        self.is_dirty = False
        print(f"[StateManager] ✅ Đã nạp profile cho User {user_id}. File ID: {file_id}")
        print(f"[StateManager] XP hiện tại: {self.profile_data.get('total_xp', 0)}")

    async def auto_rehydrate(self):
        """Tự động nạp lại thông tin từ Database nếu bị trống (sau khi restart server)."""
        if self.user_id and self.profile_file_id and self.profile_data:
            return True
            
        # Lấy user_id từ session của NiceGUI
        u_id = app.storage.user.get('id')
        if not u_id:
            return False
            
        try:
            from database import get_user_by_id
            user = await asyncio.to_thread(get_user_by_id, u_id)
            if user and user.drive_profile_file_id:
                # Lấy access token
                token = app.storage.user.get('google_access_token')
                if not token: return False
                
                # Tải profile từ Drive
                service = GoogleDriveService._build_drive_service(token)
                data = await asyncio.to_thread(GoogleDriveService.download_json_file, service, user.drive_profile_file_id)
                
                if data:
                    self.load_profile(data, user.id, user.drive_profile_file_id)
                    return True
        except Exception as e:
            print(f"[StateManager] ❌ Không thể tự động nạp lại dữ liệu: {e}")
            
        return False

    def update_profile(self, updates: Dict[str, Any]):
        """Cập nhật dữ liệu profile và đánh dấu cần sync."""
        self.profile_data.update(updates)
        self.mark_dirty()

    def add_xp(self, amount: int):
        """Helper để cộng XP nhanh (Tương thích với cấu trúc phẳng)."""
        # Cập nhật cả ở root (cũ) và dự phòng cho cấu trúc mới
        current_xp = self.profile_data.get("total_xp", 0)
        self.profile_data["total_xp"] = current_xp + amount
        
        # Nếu có user_stats thì cập nhật luôn
        if "user_stats" in self.profile_data:
            self.profile_data["user_stats"]["total_xp"] = self.profile_data["total_xp"]
            
        self.mark_dirty()
        print(f"[StateManager] ⭐ +{amount} XP (Total: {self.profile_data['total_xp']})")

    def mark_dirty(self):
        """Đánh dấu dữ liệu đã thay đổi."""
        self.is_dirty = True
        self.last_change_time = time.time()

    async def _auto_sync_loop(self):
        """Vòng lặp vô tận kiểm tra và đẩy dữ liệu lên Drive."""
        while True:
            try:
                await asyncio.sleep(2.0) # Kiểm tra mỗi 2 giây
                
                # Task 2.4: Thử nạp lại dữ liệu nếu bị trống
                if not self.user_id:
                    await self.auto_rehydrate()

                if not self.is_dirty or self.is_syncing:
                    continue

                # Kiểm tra thời gian debounce (5 giây sau thao tác cuối)
                if time.time() - self.last_change_time < self.sync_interval:
                    continue

                await self.sync_to_drive()
            except Exception as e:
                print(f"[StateManager] ❌ Lỗi trong vòng lặp Sync: {e}")
                await asyncio.sleep(5.0)

    async def sync_to_drive(self):
        """Đẩy dữ liệu từ RAM lên Google Drive."""
        if not self.user_id or not self.profile_file_id:
            print("[StateManager] ⚠️ Thiếu ID người dùng hoặc File ID, không thể đồng bộ.")
            return

        self.is_syncing = True
        print(f"[StateManager] ☁️ Đang đồng bộ lên Google Drive (File: {self.profile_file_id})...")
        
        try:
            # Lấy Google Drive service cho user hiện tại
            service = GoogleDriveService.get_user_service(self.user_id)
            if not service:
                raise Exception("Không thể khởi tạo Drive Service")

            # Thực hiện update
            print(f"[StateManager] Payload gửi đi: {json.dumps(self.profile_data, ensure_ascii=False)}")
            success = await asyncio.to_thread(
                GoogleDriveService.update_json_file, 
                service, 
                self.profile_file_id, 
                self.profile_data
            )
            
            if success:
                self.is_dirty = False
                print("[StateManager] ✅ Đồng bộ thành công!")
            else:
                print("[StateManager] ❌ Đồng bộ thất bại")
                
        except Exception as e:
            print(f"[StateManager] ❌ Lỗi khi đồng bộ: {e}")
        finally:
            self.is_syncing = False

# Export singleton instance
state_manager = SyncStateManager.get_instance()

import sys
import os

# Add project root to path
sys.path.append(r'I:\MY_CODE\WebPersionalLearning')

from config.google_oauth_config import GoogleOAuthConfig
import sqlite3

print("--- KIỂM TRA SẴN SÀNG SPRINT 1 ---")
# 1. Kiểm tra cấu hình
if GoogleOAuthConfig.is_configured():
    print("✅ Cấu hình Google OAuth: ĐÃ SẴN SÀNG")
else:
    print("❌ Cấu hình Google OAuth: CHƯA CÓ (Thiếu .env hoặc keys)")

# 2. Kiểm tra DB
db_path = r'I:\MY_CODE\WebPersionalLearning\pkt_research.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(user)")
    columns = [col[1] for col in cursor.fetchall()]
    required = ['google_id', 'drive_root_folder_id']
    missing = [r for r in required if r not in columns]
    if not missing:
        print("✅ Cấu trúc Database: ĐÃ CẬP NHẬT")
    else:
        print(f"❌ Cấu trúc Database: CÒN THIẾU {missing}")
    conn.close()
else:
    print("❌ Không tìm thấy file database.")

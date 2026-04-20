from database import create_db_and_tables

print("Bắt đầu Patch Database cho Phase 5...")
try:
    create_db_and_tables()
    print("Patch thành công: Đã tạo bảng ReviewSchedule (nếu chưa có).")
except Exception as e:
    print(f"Lỗi: {e}")

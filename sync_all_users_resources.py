import os
import glob
from resource_sync import sync_resources_to_tree

def sync_all():
    print("--- BẮT ĐẦU ĐỒNG BỘ TÀI NGUYÊN TOÀN HỆ THỐNG ---")
    
    # 1. Đồng bộ các bản mẫu công khai (Public Templates)
    # Đây là nguồn khi người dùng mới thêm cây vào thư viện
    public_trees = glob.glob("DB/public_trees/*.json")
    for pt in public_trees:
        if pt.endswith('.backup'): continue
        print(f"\n[Public] Đang xử lý: {pt}")
        sync_resources_to_tree(pt)
    
    # 2. Đồng bộ cây của tất cả người dùng hiện có
    # Đảm bảo tất cả tài khoản đều có tài nguyên mới nhất
    user_trees = glob.glob("user_data/*/trees/*.json")
    for ut in user_trees:
        if ut.endswith('.backup'): continue
        print(f"\n[User] Đang xử lý: {ut}")
        sync_resources_to_tree(ut)

    print("\n--- HOÀN TẤT ĐỒNG BỘ ---")

if __name__ == "__main__":
    sync_all()

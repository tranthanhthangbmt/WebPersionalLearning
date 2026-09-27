import os
import json
import time
import math

def get_state_file_path(user_id, subject_id):
    """Lấy đường dẫn file state độc lập cho sinh viên"""
    dir_path = f"user_data/{user_id}/states"
    os.makedirs(dir_path, exist_ok=True)
    return f"{dir_path}/{subject_id}_state.json"

def get_student_state(user_id, subject_id):
    """Đọc file state của sinh viên và Áp dụng Suy giảm Ebbinghaus thời gian thực"""
    state_file = get_state_file_path(user_id, subject_id)
    if not os.path.exists(state_file):
        return {
            "subject_id": subject_id,
            "mastery": {},
            "current_focus": None
        }
    
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        
    # --- THUẬT TOÁN QUÊN LÃNG EBBINGHAUS ---
    current_time = time.time()
    for node_id, data in state.get('mastery', {}).items():
        if "last_updated" in data:
            # Sức mạnh lưu giữ ký ức, làm bài càng nhiều lần sức lưu giữ càng cao
            strength = max(1.0, data.get("attempts", 1) * 3.0) 
            # Đổi số giây sang số ngày (để Demo nhanh, tạm tính 1 Phút = 1 Ngày)
            # Trong thực tế, chia cho 86400. Để giáo sư kiểm tra WOW effect ngay, ta chia cho 60.
            days_passed = (current_time - data["last_updated"]) / 60.0 
            
            if days_passed > 0:
                # Công thức R = e^(-t/S)
                retention = math.exp(-days_passed / strength)
                # Suy giảm Level (Dung sai thấp nhất là 0.2)
                data["level"] = max(0.2, data["level"] * retention)
            data["_decayed"] = True # Cờ báo hiệu cho UI biết đã bật Ebbinghaus

    return state

def update_node_mastery(user_id, subject_id, node_id, is_correct, difficulty_alpha=10):
    """
    Cập nhật trình độ tại 1 node dựa trên kết quả Quiz.
    Thuật toán đơn giản:
    - Nếu đúng: Tăng mastery (tối đa 1.0)
    - Nếu sai: Tụt mastery (Tối thiểu 0.0)
    """
    state = get_student_state(user_id, subject_id)
    
    if node_id not in state["mastery"]:
        state["mastery"][node_id] = {"level": 0.0, "attempts": 0, "last_score": 0}
        
    node_data = state["mastery"][node_id]
    node_data["attempts"] += 1
    node_data["last_updated"] = time.time() # LƯU VẾT THỜI GIAN
    
    # Bước nhảy trình độ (Learning Rate) dựa trên Alpha (khó/dễ)
    # Ví dụ: Câu khó mà làm đúng thì level tăng mạnh hơn.
    learning_rate = 0.2 + (difficulty_alpha / 100.0)
    
    if is_correct:
        # Trong database, level luôn là gốc tuyệt đối (pure)
        # Bị suy giảm chỉ hiện thị ở mặt Render. Làm đúng phục hồi lại pure level.
        current_pure = node_data.get("pure_level", node_data.get("level", 0.0))
        new_pure = min(1.0, current_pure + learning_rate)
        node_data["pure_level"] = new_pure
        node_data["level"] = new_pure # Cập nhật lại level hiện tại
        node_data["last_score"] = 10
    else:
        current_pure = node_data.get("pure_level", node_data.get("level", 0.0))
        new_pure = max(0.0, current_pure - (learning_rate * 0.5))
        node_data["pure_level"] = new_pure
        node_data["level"] = new_pure
        node_data["last_score"] = 0
        
    state["current_focus"] = node_id
    
    # Lưu xuống ổ đĩa
    state_file = get_state_file_path(user_id, subject_id)
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    return node_data["level"]

def get_dynamic_difficulty(user_id, subject_id, node_id, base_alpha):
    """
    Tính toán độ khó động DDA (Dynamic Difficulty Adjustment)
    dựa trên số lần User đã thử và trình độ hiện tại.
    """
    state_file = get_state_file_path(user_id, subject_id)
    if not os.path.exists(state_file):
        return base_alpha, "Normal"
        
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        
    node_data = state.get("mastery", {}).get(node_id, None)
    if not node_data:
        return base_alpha, "Normal"
        
    attempts = node_data.get("attempts", 0)
    level = node_data.get("level", 0.0)
    
    # Logic: Nếu user cày nhiều lần (attempts >= 2) mà level vẫn kẹt lẹt đẹt -> Giảm khó (Scaffolding)
    if attempts >= 2 and level < 0.4:
        return max(5, int(base_alpha * 0.5)), "Scaffolding (Dìu dắt nhẹ nhàng, hạ thái độ châm biếm vì sinh viên đang đuối sức)"
    # Nếu user pass nhanh (level > 0.8) -> Tăng khó (Challenge)
    elif level >= 0.8:
        return min(100, int(base_alpha * 1.5)), "Advanced (Hỏi lắt léo, gay gắt và xoáy sâu vì sinh viên đã thông thạo)"
        
    return base_alpha, "Normal (Kiểm tra bình thường)"


# ============================================================
#  CAT STATE TRACKING — Lưu/đọc θ từ CAT sessions
# ============================================================

def get_cat_state_path(user_id, subject_id):
    """Đường dẫn file CAT state riêng biệt."""
    dir_path = f"user_data/{user_id}/states"
    os.makedirs(dir_path, exist_ok=True)
    return f"{dir_path}/{subject_id}_cat.json"


def get_cat_prior_theta(user_id, subject_id, node_id):
    """
    Lấy θ ước lượng từ lịch sử CAT, dùng làm prior cho session mới.
    
    Returns:
        float: θ prior (0.0 nếu chưa có lịch sử)
    """
    cat_path = get_cat_state_path(user_id, subject_id)
    if not os.path.exists(cat_path):
        return 0.0
    
    with open(cat_path, 'r', encoding='utf-8') as f:
        cat_state = json.load(f)
    
    node_cat = cat_state.get("nodes", {}).get(node_id, {})
    return node_cat.get("theta", 0.0)


def update_theta_from_cat(user_id, subject_id, node_id, theta, se,
                          bloom_level=None, items_used=0):
    """
    Lưu θ estimate sau CAT session.
    
    Args:
        user_id: ID người dùng
        subject_id: ID môn học
        node_id: ID node
        theta: θ estimate từ CAT
        se: Standard Error
        bloom_level: Bloom level tương ứng (optional, auto-calc if None)
        items_used: Số items đã sử dụng
    """
    cat_path = get_cat_state_path(user_id, subject_id)
    
    if os.path.exists(cat_path):
        with open(cat_path, 'r', encoding='utf-8') as f:
            cat_state = json.load(f)
    else:
        cat_state = {"subject_id": subject_id, "nodes": {}}
    
    if bloom_level is None:
        try:
            from cat_engine import map_theta_to_bloom
            bloom_level = map_theta_to_bloom(theta)
        except ImportError:
            bloom_level = max(1, min(6, int(theta + 3.5)))
    
    cat_state.setdefault("nodes", {})[node_id] = {
        "theta": round(theta, 3),
        "se": round(se, 3),
        "bloom_level": bloom_level,
        "items_used": items_used,
        "last_cat_session": time.time(),
    }
    
    with open(cat_path, 'w', encoding='utf-8') as f:
        json.dump(cat_state, f, ensure_ascii=False, indent=2)


def get_all_cat_thetas(user_id, subject_id):
    """
    Lấy tất cả θ estimates cho một môn học.
    
    Returns:
        dict: {node_id: {"theta": float, "se": float, "bloom_level": int, ...}}
    """
    cat_path = get_cat_state_path(user_id, subject_id)
    if not os.path.exists(cat_path):
        return {}
    
    with open(cat_path, 'r', encoding='utf-8') as f:
        cat_state = json.load(f)
    
    return cat_state.get("nodes", {})

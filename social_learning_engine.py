# social_learning_engine.py
"""
Social Learning Orchestrator
============================
Công cụ điều phối Học tập Đồng đẳng (Peer Matchmaking) dựa trên PLiF (Chương 5, 6, 8).
Xây dựng mạng lưới học tập xã hội bằng cách phân tích Bloom profiles của toàn bộ người dùng,
từ đó tự động ghép cặp sinh viên Giỏi (Mentor) với sinh viên yếu (Mentee).
"""

import os
import json
from bloom_taxonomy import get_bloom_state_path

def find_peer_mentors(current_username: str, subject_id: str, node_id: str) -> list:
    """
    Quét dữ liệu tất cả người dùng để tìm "Peer Mentor" cho node hiện tại.
    Điều kiện làm Mentor: Đạt Bloom >= L4 (Analyze) hoặc tối thiểu L3 cứng ở node này.
    
    Returns:
        List of dicts: [{'username': 'userB', 'bloom_level': 4.5}, ...]
    """
    mentors = []
    user_dir = 'user_data'
    if not os.path.exists(user_dir):
        return mentors
        
    for user in os.listdir(user_dir):
        if user == current_username or user.startswith('.') or user == '__pycache__':
            continue
            
        path = get_bloom_state_path(user, subject_id)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    
                node_data = state.get('nodes', {}).get(node_id, {})
                overall_bloom = node_data.get('overall_bloom', 0.0)
                
                # Điều kiện: Bloom >= L4 là lý tưởng để làm mentor
                if overall_bloom >= 3.5:
                    mentors.append({
                        'username': user,
                        'bloom_level': round(overall_bloom, 1)
                    })
            except Exception as e:
                print(f"Lỗi đọc dữ liệu mentor từ {user}: {e}")
                pass
                
    # Sort mentors by bloom level (highest first)
    mentors.sort(key=lambda x: x['bloom_level'], reverse=True)
    return mentors

import os
import json
from bloom_taxonomy import load_bloom_state
try:
    from smart_review_queue import get_review_queue, get_daily_review_summary
except ImportError:
    get_review_queue = lambda *args, **kwargs: []
    get_daily_review_summary = lambda *args, **kwargs: {"nodes_need_review": 0, "critical_nodes": 0}

def load_all_subjects(username: str) -> list:
    """
    Tải danh sách môn học của người dùng.
    """
    subjects_file = f"user_data/{username}/subjects.json"
    if not os.path.exists(subjects_file):
        return []
    
    try:
        with open(subjects_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("subjects", [])
    except Exception:
        return []

def get_subject_card_data(username: str, subject: dict) -> dict:
    """
    Tính toán tiến độ cho một môn học cụ thể.
    """
    subject_id = subject.get("id")
    title = subject.get("title", "Unknown")
    total_nodes = subject.get("total_nodes", 0)
    
    if not subject_id:
        return {
            "subject_id": "", "title": title, "total_nodes": total_nodes,
            "nodes_learned": 0, "completion_pct": 0.0, "avg_bloom": 0.0,
            "review_urgency": 0, "last_activity": 0
        }
        
    bloom_state = load_bloom_state(username, subject_id)
    nodes = bloom_state.get("nodes", {})
    
    nodes_learned = sum(1 for n in nodes.values() if n.get("overall_bloom", 0) >= 0.1)
    
    if total_nodes > 0:
        completion_pct = round((nodes_learned / total_nodes) * 100, 1)
    else:
        completion_pct = 0.0
        
    avg_bloom = 0.0
    if nodes_learned > 0:
        total_bloom = sum(n.get("overall_bloom", 0) for n in nodes.values() if n.get("overall_bloom", 0) >= 0.1)
        avg_bloom = round(total_bloom / nodes_learned, 2)
        
    review_summary = get_daily_review_summary(bloom_state)
    review_urgency = review_summary.get("nodes_need_review", 0)
    
    # Tìm last_activity từ ebbinghaus
    ebbinghaus = bloom_state.get("ebbinghaus", {})
    last_activity = 0
    if ebbinghaus:
        last_activity = max((eb.get("last_review", 0) for eb in ebbinghaus.values()), default=0)
        
    return {
        "subject_id": subject_id,
        "title": title,
        "total_nodes": total_nodes,
        "nodes_learned": nodes_learned,
        "completion_pct": min(100.0, max(0.0, completion_pct)),
        "avg_bloom": avg_bloom,
        "review_urgency": review_urgency,
        "last_activity": last_activity
    }

def get_cross_subject_summary(username: str) -> dict:
    """
    Tổng hợp tiến độ trên tất cả các môn.
    """
    subjects = load_all_subjects(username)
    total_subjects = len(subjects)
    total_nodes = 0
    total_learned = 0
    total_bloom = 0.0
    total_review_needed = 0
    critical_review_count = 0
    
    for subj in subjects:
        card = get_subject_card_data(username, subj)
        total_nodes += card.get("total_nodes", 0)
        total_learned += card.get("nodes_learned", 0)
        total_bloom += card.get("avg_bloom", 0.0) * card.get("nodes_learned", 0)
        total_review_needed += card.get("review_urgency", 0)
        
        bloom_state = load_bloom_state(username, subj.get("id"))
        review_summary = get_daily_review_summary(bloom_state)
        critical_review_count += review_summary.get("critical_nodes", 0)
        
    overall_pct = 0.0
    if total_nodes > 0:
        overall_pct = round((total_learned / total_nodes) * 100, 1)
        
    avg_bloom = 0.0
    if total_learned > 0:
        avg_bloom = round(total_bloom / total_learned, 2)
        
    return {
        "total_subjects": total_subjects,
        "total_nodes": total_nodes,
        "total_learned": total_learned,
        "overall_pct": min(100.0, max(0.0, overall_pct)),
        "avg_bloom": avg_bloom,
        "total_review_needed": total_review_needed,
        "critical_review_count": critical_review_count
    }

def get_unified_review_queue(username: str, max_items: int = 10) -> list:
    """
    Hàng đợi ôn tập gộp tất cả các môn.
    """
    subjects = load_all_subjects(username)
    all_queues = []
    
    for subj in subjects:
        subj_id = subj.get("id")
        subj_title = subj.get("title", "Unknown")
        bloom_state = load_bloom_state(username, subj_id)
        
        queue = get_review_queue(bloom_state, max_items=max_items)
        for item in queue:
            item["subject_id"] = subj_id
            item["subject_title"] = subj_title
            all_queues.append(item)
            
    # Sort by priority desc
    all_queues.sort(key=lambda x: x["priority"], reverse=True)
    return all_queues[:max_items]

def get_bloom_radar_data(username: str, subject_id: str) -> dict:
    """
    Dữ liệu biểu đồ Radar cho 6 mức độ Bloom.
    """
    bloom_state = load_bloom_state(username, subject_id)
    nodes = bloom_state.get("nodes", {})
    
    # 6 mức độ: L1->L6
    sums = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0}
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    
    for n in nodes.values():
        overall_bloom = n.get("overall_bloom", 0.0)
        if overall_bloom >= 0.1:
            level = max(1, min(6, round(overall_bloom)))
            # Tính điểm (tương đối) của node đó cho level này.
            # Thực tế overall_bloom / 6 là một cách đơn giản hóa,
            # Hoặc ta lấy điểm trung bình của tất cả các node.
            # Ở đây ta map theo mức độ pass (0 -> 1.0) của từng bậc.
            # Do không có chi tiết từng bài, ta giả lập score dựa trên overall_bloom.
            score = min(1.0, overall_bloom / level)
            sums[level] += score
            counts[level] += 1
            
    data = []
    for i in range(1, 7):
        if counts[i] > 0:
            data.append(round(sums[i] / counts[i], 2))
        else:
            data.append(0.0)
            
    return {
        "labels": ["L1 Remember", "L2 Understand", "L3 Apply", "L4 Analyze", "L5 Evaluate", "L6 Create"],
        "data": data
    }

def get_ebbinghaus_heatmap(username: str, subject_id: str) -> list:
    """
    Bản đồ nhiệt Ebbinghaus cho môn học.
    """
    bloom_state = load_bloom_state(username, subject_id)
    ebbinghaus = bloom_state.get("ebbinghaus", {})
    
    import time
    import math
    now = time.time()
    
    heatmap = []
    for node_id, eb in ebbinghaus.items():
        last_review = eb.get("last_review", 0)
        strength = eb.get("strength", 2.0)
        if last_review > 0:
            hours = (now - last_review) / 3600.0
            retention = math.exp(-hours / max(0.5, strength))
            retention = max(0.0, min(1.0, retention))
            
            if retention < 0.3:
                status = "critical"
            elif retention < 0.6:
                status = "warning"
            elif retention < 0.85:
                status = "good"
            else:
                status = "excellent"
                
            heatmap.append({
                "node_id": node_id,
                "node_title": f"Node {node_id}", # Ideal: get title from tree
                "retention": round(retention, 3),
                "status": status
            })
            
    heatmap.sort(key=lambda x: x["retention"])
    return heatmap

def get_study_streak_data(username: str) -> dict:
    """
    Thống kê Streak và Hoạt động tuần.
    (Giả lập từ gamification hoặc socratic history nếu có)
    """
    try:
        from gamification.streak_service import StreakService
        user_id = 1 # Placeholder for now, real UI might pass DB user_id
        streak_info = StreakService.get_streak_info(user_id)
        streak = streak_info.get("current_streak", 0)
    except Exception:
        streak = 0
        
    # Giả lập weekly activity cho UI
    import random
    weekly = [random.randint(0, 5) for _ in range(7)]
    total_sessions = sum(weekly)
    active_days = sum(1 for w in weekly if w > 0)
    
    return {
        "total_sessions": total_sessions,
        "active_days": active_days,
        "streak_estimate": streak,
        "weekly_activity": weekly
    }

# ============================================================
#  SPRINT 2.3 — Access Policy & Recommendations
# ============================================================

def save_access_policy(username: str, policy_id: str):
    """
    Lưu cấu hình Access Policy của user.
    Các loại policy: k12_strict, university_flexible, professional_open
    """
    valid_policies = ["k12_strict", "university_flexible", "professional_open"]
    if policy_id not in valid_policies:
        return
        
    settings_file = f"user_data/{username}/settings.json"
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    
    settings = {}
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            pass
            
    settings["access_policy"] = policy_id
    
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def load_access_policy(username: str) -> str:
    """
    Tải cấu hình Access Policy của user. Mặc định là university_flexible.
    """
    settings_file = f"user_data/{username}/settings.json"
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get("access_policy", "university_flexible")
        except Exception:
            pass
    return "university_flexible"

def get_recommended_next_nodes(username: str, max_items: int = 5) -> list:
    """
    Gợi ý học tiếp (KST Fringe) từ tất cả các môn.
    """
    try:
        from soft_prerequisite import get_knowledge_space_fringe
        from bloom_taxonomy import load_bloom_state
    except ImportError:
        return []
        
    subjects = load_all_subjects(username)
    all_fringe = []
    
    for subj in subjects:
        subj_id = subj.get("id")
        filename = subj.get("filename")
        if not filename or not os.path.exists(filename):
            continue
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
        except Exception:
            continue
            
        all_node_ids = [n.get("id") for n in tree_data.get("micro_nodes", [])]
        edges = tree_data.get("edges", [])
        bloom_state = load_bloom_state(username, subj_id)
        
        fringe = get_knowledge_space_fringe(all_node_ids, edges, bloom_state)
        # Bổ sung subject info vào từng node trong fringe
        for f in fringe:
            f["subject_id"] = subj_id
            f["subject_title"] = subj.get("title", "Unknown")
            # Tìm title của node
            node_title = f.get("node_id")
            for mn in tree_data.get("micro_nodes", []):
                if mn.get("id") == f.get("node_id"):
                    node_title = mn.get("title", node_title)
                    break
            f["title"] = node_title
            all_fringe.append(f)
            
    # Sort by readiness_score desc
    all_fringe.sort(key=lambda x: x.get("readiness_score", 0), reverse=True)
    return all_fringe[:max_items]

def get_daily_tasks(username: str, max_tasks: int = 5) -> list:
    """
    Tạo nhiệm vụ hàng ngày: Ôn tập khẩn cấp + Học bài mới (Fringe) + Luyện tập.
    """
    tasks = []
    
    # 1. Ôn tập (lấy 2 mục khẩn cấp nhất)
    review_queue = get_unified_review_queue(username, max_items=2)
    for i, r in enumerate(review_queue):
        tasks.append({
            "type": "review_node",
            "title": f"Ôn tập: {r.get('node_id')}",
            "description": f"Độ nhớ đang giảm (Môn: {r.get('subject_title')})",
            "subject_id": r.get('subject_id'),
            "node_id": r.get('node_id'),
            "priority": 100 - i, # High priority
            "xp_reward": 50
        })
        
    # 2. Học bài mới (lấy 2 mục fringe tốt nhất)
    recs = get_recommended_next_nodes(username, max_items=2)
    for i, rec in enumerate(recs):
        tasks.append({
            "type": "learn_next",
            "title": f"Bài mới: {rec.get('title', rec.get('node_id'))}",
            "description": f"Bạn đã sẵn sàng (Môn: {rec.get('subject_title')})",
            "subject_id": rec.get('subject_id'),
            "node_id": rec.get('node_id'),
            "priority": 80 - i,
            "xp_reward": 100
        })
        
    # 3. Luyện tập Socratic (Random from passed nodes, or just a general task)
    if len(tasks) < max_tasks:
        tasks.append({
            "type": "socratic_practice",
            "title": "Thử thách Gia sư AI",
            "description": "Nâng cao tư duy với Socratic",
            "subject_id": None,
            "node_id": None,
            "priority": 50,
            "xp_reward": 150
        })
        
    tasks.sort(key=lambda x: x["priority"], reverse=True)
    return tasks[:max_tasks]

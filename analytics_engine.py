# analytics_engine.py
"""
Learning Analytics Engine
=========================
Công cụ trích xuất và phân tích dữ liệu học tập để cung cấp "Hồ sơ Học tập" (Learning Profile)
cho AI Coach (Chương 7 - PLiF). 

Chức năng chính:
- Phân tích biểu đồ Ebbinghaus (Tỷ lệ quên)
- Phân tích lỗ hổng Bloom (Bloom Gaps)
- Tổng hợp thành đoạn văn bản Prompt để nạp vào AI.
"""

from bloom_hub_page import load_bloom_state
from smart_review_queue import get_daily_review_summary, get_review_queue
import json

def get_learning_profile(username: str, subject_id: str, current_node_id: str = None) -> str:
    """
    Trích xuất hồ sơ học tập của user để gửi cho AI Coach.
    """
    try:
        bs = load_bloom_state(username, subject_id)
        if not bs or not bs.get('nodes'):
            return "Sinh viên này mới bắt đầu khóa học, chưa có nhiều dữ liệu học tập. Hãy hướng dẫn họ cách thiết lập mục tiêu cơ bản."

        # 1. Tóm tắt tổng quan
        summary = get_daily_review_summary(bs)
        
        # 2. Phân tích Ebbinghaus (Quên kiến thức)
        review_queue = get_review_queue(bs, max_items=3)
        forget_warnings = []
        for q in review_queue:
            if q['retention'] < 0.6:
                forget_warnings.append(f"Node {q['node_id']} (Nhớ: {q['retention']*100:.0f}%, Bỏ lỡ: {q['hours_since_review']:.1f}h)")

        # 3. Phân tích Bloom hiện tại của Node đang học
        current_node_status = ""
        if current_node_id and current_node_id in bs.get('nodes', {}):
            ns = bs['nodes'][current_node_id]
            scores = ns.get('bloom_scores', {})
            max_passed = 0
            for lvl, data in scores.items():
                if data.get('score', 0) >= 0.7:  # Threshold tạm
                    max_passed = max(max_passed, int(lvl))
            
            current_node_status = f"Tại bài học hiện tại ({current_node_id}), sinh viên đang đạt mức Bloom L{max_passed}."

        # Tổng hợp thành Prompt
        profile = (
            "--- HỒ SƠ HỌC TẬP (DATA-DRIVEN) ---\n"
            f"- Tổng số bài đã học: {summary['total_nodes_learned']}\n"
            f"- Mức độ ghi nhớ trung bình toàn khóa: {summary['avg_retention']*100:.0f}%\n"
            f"- Số bài học báo động cần ôn tập ngay (Retention < 30%): {summary['critical_nodes']}\n"
        )

        if forget_warnings:
            profile += "- Cảnh báo quên kiến thức nghiêm trọng tại các Node: " + ", ".join(forget_warnings) + "\n"
            
        if current_node_status:
            profile += f"- {current_node_status}\n"

        profile += "-----------------------------------\n"
        profile += "CHỈ THỊ CHO COACH: Dựa vào dữ liệu trên, hãy điều chỉnh giọng điệu và chủ động nhắc nhở sinh viên (nếu họ đang có nguy cơ hổng kiến thức) trong câu hỏi đầu tiên của bạn."

        return profile

    except Exception as e:
        print(f"Lỗi khi trích xuất Learning Profile: {e}")
        return "Không thể tải dữ liệu phân tích hiện tại."

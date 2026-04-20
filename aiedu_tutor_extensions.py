import os
import json
import glob
from nicegui import app
from knowledge_tracing import get_student_state

def get_latest_subject(username):
    """Tìm môn học (subject_id) mà học sinh tương tác gần nhất dựa trên file state"""
    state_dir = f"user_data/{username}/states"
    if not os.path.exists(state_dir):
        return None
    
    files = glob.glob(f"{state_dir}/*_state.json")
    if not files:
        return None
        
    latest_file = max(files, key=os.path.getmtime)
    basename = os.path.basename(latest_file)
    return basename.replace("_state.json", "")

def build_context_diagnosis_prompt(username):
    """Đọc Tình trạng học tập và sinh Prompt Chẩn đoán (Tính năng 1)"""
    subject_id = get_latest_subject(username)
    if not subject_id:
        return "Xin lỗi, tôi chưa tìm thấy Hồ sơ Học tập (State) nào của bạn. Hãy qua tab Tạo Cây và học thử một môn nhé!"
        
    state = get_student_state(username, subject_id)
    mastery_data = state.get("mastery", {})
    
    # Phân tích
    good_nodes = []
    bad_nodes = []
    for node_id, data in mastery_data.items():
        lvl = data.get("level", 0.0)
        if lvl >= 0.8: good_nodes.append(node_id)
        elif lvl <= 0.5: bad_nodes.append(node_id)
        
    prompt = f"""[LỆNH ĐIỀU KHIỂN HỆ THỐNG - KHÔNG HIỂN THỊ DÒNG NÀY CHO NGƯỜI DÙNG]
Ngươi là Trợ lý Giáo sư AI Toàn tri (Omnipresent Tutor) của hệ thống AIEdu PKT.
Hệ thống vừa tiêm cho ngươi Hồ sơ Bệnh án Học tập của sinh viên:
- Môn học ID đang học: {subject_id}
- Các điểm kiến thức (Nodes) sinh viên rất GIỎI (Mastery > 0.8): {', '.join(good_nodes) if good_nodes else 'Chưa có'}
- Các điểm kiến thức (Nodes) sinh viên cực kỳ YẾU (Mastery <= 0.5) và hay làm sai: {', '.join(bad_nodes) if bad_nodes else 'Chưa có'}

NHIỆM VỤ CỦA NGƯƠI LÚC NÀY:
1. Đóng vai một trợ lý trí tuệ, tự động nói CHÀO MỪNG sinh viên một cách ngạc nhiên vì ngươi đã có khả năng đọc thấu tâm can họ.
2. Nêu chính xác ra (nhắc tên Node) những phần họ đang Yếu Kém.
3. Đề nghị một cách ân cần rắng: "Ngươi sẽ dùng các khái niệm từ vùng GIỎI của họ để làm ví dụ giải thích bù đắp cho vùng YẾU".
4. Khuyến khích họ đặt câu hỏi.
Trả về bằng Markdown siêu ngầu và chuyên nghiệp.
"""
    return prompt

def build_gantt_planner_prompt(username):
    """Đọc Cây và State để sinh Lộ trình GANTT (Tính năng 3)"""
    subject_id = get_latest_subject(username)
    if not subject_id:
        return "Xin lỗi, tôi chưa tìm thấy Biểu đồ Tri thức nào của bạn hoạt động gần đây."
        
    # Đọc cấu trúc cây
    tree_file = f"user_data/{username}/trees/{subject_id}.json"
    content_map = {}
    if os.path.exists(tree_file):
        with open(tree_file, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)
            for c in tree_data.get('micro_nodes', []):
                content_map[c.get('id')] = c.get('title', c.get('id'))
                
    state = get_student_state(username, subject_id)
    mastery_data = state.get("mastery", {})
    
    weak_topics = []
    unattempted_topics = []
    
    # Quy hoạch
    for node_id, title in content_map.items():
        if node_id in mastery_data:
            if mastery_data[node_id].get("level", 0.0) < 0.8:
                weak_topics.append(title)
        else:
            unattempted_topics.append(title)

    prompt = f"""[LỆNH ĐIỀU KHIỂN HỆ THỐNG - KHÔNG HIỂN THỊ DÒNG NÀY]
Ngươi là Chuyên gia Cố vấn Học tập (Academic Planner) của dự án AIEdu quốc tế.
Sinh viên vừa yêu cầu một Bản Kế Hoạch Nhồi Nhét 7 Ngày (7-Day Sprint).
Dữ liệu trích xuất từ Bản Đồ Tri Thức của sinh viên (Môn: {subject_id}):
- Kiến thức yếu (cần ôn lại gấp): {', '.join(weak_topics[:5]) if weak_topics else 'Không có'}
- Kiến thức chưa thèm học: {', '.join(unattempted_topics[:10]) if unattempted_topics else 'Đã quét hết'}

NHIỆM VỤ:
Tạo ra một Checklist Kế Hoạch 7 Ngày cực kỳ tàn khốc nhưng khoa học. Dàn trải các bài học (lấy từ dữ liệu trên) rải rác trong 7 ngày. Yêu cầu định dạng bảng Markdown (Ngày, Nhiệm vụ chính, Phương pháp học). Kết thúc bằng một lời thách thức động lực rực lửa!
"""
    return prompt

import os
import glob
import json
import re

def sync_knowledge_tree(user_id="sv01"):
    # 1. Tìm File Đích gốc
    subjects_file = f"user_data/{user_id}/subjects.json"
    if not os.path.exists(subjects_file):
        print(f"Không tìm thấy {subjects_file}. Kết thúc.")
        return
        
    with open(subjects_file, "r", encoding="utf-8") as f:
        subj_data = json.load(f)
        
    target_filename = None
    for s in subj_data.get("subjects", []):
        if "Thương mại điện tử" in s.get("title", "") or "TMĐT" in s.get("title", ""):
            target_filename = s.get("filename")
            break
            
    if not target_filename or not os.path.exists(target_filename):
        print(f"Không tìm thấy Cây Tri Thức gốc tại {target_filename}. Đang tự động lưu dưới dạng sv01_tmdt.json")
        target_filename = f"user_data/{user_id}/trees/sv01_tmdt.json"
        os.makedirs(os.path.dirname(target_filename), exist_ok=True)

    print(f"Sẽ đồng bộ dữ liệu vào: {target_filename}")

    # 2. Đọc toàn bộ 30+ Bài học từ DB/JSON_Data/
    json_path = "DB/JSON_Data/*.json"
    files = glob.glob(json_path)
    
    concepts = []
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            try:
                content = json.load(file)
                concept_id = content['metadata']['concept_id']
                # Lấy 2 câu hỏi đầu làm assess node info
                sample_questions = content.get('questions', [])[:2]
                extracted_qs = []
                for sq in sample_questions:
                    extracted_qs.append({
                        "question": sq.get("content", ""),
                        "options": [f"{opt['key']}. {opt['text']}" for opt in sq.get("options", [])],
                        "answer": sq.get("correct_answer", "A")
                    })
                    
                concepts.append({
                    "id": concept_id,
                    "name": content['metadata'].get('concept_name', concept_id),
                    "questions": extracted_qs,
                    "source_file": os.path.basename(f)
                })
            except Exception as e:
                pass

    # 3. Phân loại theo Regex (như main.py)
    chapter_pattern = re.compile(r"(ch(?:ương|uong)[_ ]?(\d+))", re.IGNORECASE)
    lesson_pattern = re.compile(r"(ti[eết]+[_ ]?(\d+))", re.IGNORECASE)
    
    chapters = {}
    
    # Init 5 Chương Cứng nếu chưa có
    for i in range(1, 6):
        chapters[i] = {
            "id": f"m{i}",
            "title": f"Chương {i}",
            "lessons": []
        }

    for c in concepts:
        c_name = c['name']
        chap_match = chapter_pattern.search(c_name)
        chap_num = int(chap_match.group(2)) if chap_match else 999
        
        less_match = lesson_pattern.search(c_name)
        less_num = int(less_match.group(2)) if less_match else 999
        
        if chap_num not in chapters:
            chapters[chap_num] = {"id": f"m{chap_num}", "title": f"Chương {chap_num} (Mở rộng)", "lessons": []}
            
        # Tên gọn cho node
        clean_name = chapter_pattern.sub("", c_name)
        clean_name = lesson_pattern.sub("", clean_name)
        clean_name = clean_name.replace("_", " ").strip()
        clean_name = re.sub(r"^[^\w]+", "", clean_name)
        display_name = f"Tiết {less_num}: {clean_name}" if less_num != 999 else c_name
        
        chapters[chap_num]["lessons"].append({
            "id": c["id"],
            "title": display_name,
            "num": less_num,
            "raw": c
        })

    # Xếp các tiết theo số
    for k in chapters:
        chapters[k]["lessons"] = sorted(chapters[k]["lessons"], key=lambda x: x["num"])

    # 4. Tạo Object Tree
    tree = {
        "course_name": "Thương mại điện tử Đồng bộ",
        "macro_nodes": [],
        "micro_nodes": [],
        "assess_nodes": [],
        "user_id": user_id,
        "edges": []
    }
    
    sorted_chap_nums = sorted(chapters.keys())
    
    prev_chap_id = None
    last_lesson_of_prev_chap = None
    
    for c_num in sorted_chap_nums:
        chap_data = chapters[c_num]
        
        # Chỉ lấy các Chương có bài học (để tránh chèn rác)
        if len(chap_data["lessons"]) == 0:
            continue
            
        # Thêm Macro Node
        tree["macro_nodes"].append({
            "id": chap_data["id"],
            "title": chap_data["title"]
        })
        
        # Liên kết từ Chương trước sang Chương này
        if prev_chap_id:
            tree["edges"].append({
                "source": prev_chap_id,
                "target": chap_data["id"],
                "reason": "Học tuần tự theo cấp Chương."
            })
            
        prev_l_id = None
        for l_idx, lesson in enumerate(chap_data["lessons"]):
            micro_id = lesson["id"]
            
            # Thêm Micro Node
            tree["micro_nodes"].append({
                "id": micro_id,
                "parent_macro": chap_data["id"],
                "title": lesson["title"],
                "content": f"Tài liệu tương ứng với: {lesson['raw']['source_file']}",
                "alpha_base": 15,
                "metadata": {
                    "mapped_concept_id": micro_id
                }
            })
            
            # Thêm Assess Node (Quiz)
            assess_id = f"a_{micro_id}"
            tree["assess_nodes"].append({
                "id": assess_id,
                "target_micro": micro_id,
                "theta_pass": 0.6,
                "questions": lesson["raw"]["questions"]
            })
            
            # Nối Edge: Tiếp nối tuần tự trong cùng chương
            if prev_l_id:
                tree["edges"].append({
                    "source": prev_l_id,
                    "target": micro_id,
                    "reason": "Học tuần tự."
                })
            elif last_lesson_of_prev_chap: # Nếu là bài đầu tiên của chương, nối với bài cuối của chương trước
                tree["edges"].append({
                    "source": last_lesson_of_prev_chap,
                    "target": micro_id,
                    "reason": "Chuyển tiếp sang chương mới."
                })
                
            prev_l_id = micro_id
            
        last_lesson_of_prev_chap = prev_l_id
        prev_chap_id = chap_data["id"]

    # Đếm số node
    total_nodes = len(tree["macro_nodes"]) + len(tree["micro_nodes"]) + len(tree["assess_nodes"])
    print(f"Tổng hợp thành công {total_nodes} nodes.")

    # 5. Lưu File Tree
    with open(target_filename, "w", encoding="utf-8") as out:
        json.dump(tree, out, indent=4, ensure_ascii=False)
        
    # Cập nhật số node vào subjects.json
    for s in subj_data.get("subjects", []):
        if s.get("filename") == target_filename:
            s["total_nodes"] = total_nodes
            
    with open(subjects_file, "w", encoding="utf-8") as sf:
        json.dump(subj_data, sf, indent=2, ensure_ascii=False)
        
    print(f"✅ Đã ghi đè {target_filename} thành công! Nodes: {total_nodes}")

if __name__ == "__main__":
    sync_knowledge_tree("sv01")

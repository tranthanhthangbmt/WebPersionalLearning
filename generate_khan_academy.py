import json
import uuid
from datetime import datetime

# Current time
created_at = datetime.now().isoformat()

# Base bloom profile
def get_bloom_profile(base=20, levels=[1, 2, 3]):
    return {
        "auto_calibrated_levels": levels,
        "user_adjusted_levels": None,
        "effective_levels": levels,
        "calibration_method": "alpha_base",
        "alpha_base": base,
        "created_at": created_at
    }

# Read existing Chapter 1 data if possible, or just generate from scratch
def generate_course():
    course = {
        "course_name": "Toán lớp 6 - Khan Academy",
        "macro_nodes": [],
        "micro_nodes": [],
        "assess_nodes": []
    }
    
    chapters = [
        {"id": "m1", "title": "Chương 1: Số tự nhiên"},
        {"id": "m2", "title": "Chương 2: Số nguyên"},
        {"id": "m3", "title": "Chương 3: Hình học trực quan"},
        {"id": "m4", "title": "Chương 4: Một số yếu tố thống kê và xác suất"},
        {"id": "m5", "title": "Chương 5: Phân số và số thập phân"},
        {"id": "m6", "title": "Chương 6: Hình học phẳng"},
        {"id": "m7", "title": "Chương 7: Phần mở rộng"}
    ]
    
    # Define micro nodes for each chapter
    topics = {
        "m1": [
            ("Ôn tập về số tự nhiên", "Ôn tập về hàng giá trị của số tự nhiên và cách viết số tự nhiên."),
            ("Phép cộng, phép trừ các số tự nhiên", "Thực hiện cộng và trừ các số tự nhiên có nhiều chữ số."),
            ("Phép nhân, phép chia các số tự nhiên", "Thực hiện nhân và chia số tự nhiên, tính chất của phép nhân."),
            ("Lũy thừa với số mũ tự nhiên", "Các phép tính với lũy thừa."),
            ("Thứ tự thực hiện các phép tính", "Áp dụng thứ tự nhân chia trước, cộng trừ sau."),
            ("Quan hệ chia hết", "Tìm hiểu về ước và bội của một số."),
            ("Dấu hiệu chia hết", "Dấu hiệu chia hết cho 2, 3, 5, 9."),
            ("Số nguyên tố và hợp số", "Phân biệt số nguyên tố và hợp số."),
            ("Phân tích ra thừa số nguyên tố", "Phương pháp phân tích một số ra thừa số nguyên tố.")
        ],
        "m2": [
            ("Làm quen với số nguyên âm", "Khái niệm số nguyên âm và ý nghĩa trong thực tế."),
            ("Thứ tự trong tập hợp các số nguyên", "So sánh số nguyên và biểu diễn trên trục số."),
            ("Phép cộng số nguyên", "Cộng hai số nguyên cùng dấu và khác dấu."),
            ("Phép trừ số nguyên", "Quy tắc trừ số nguyên."),
            ("Phép nhân số nguyên", "Nhân hai số nguyên cùng dấu và khác dấu."),
            ("Phép chia hết và phép chia có dư trong tập số nguyên", "Thực hiện phép chia trong Z.")
        ],
        "m3": [
            ("Hình vuông, tam giác đều, lục giác đều", "Nhận biết các hình phẳng cơ bản."),
            ("Hình chữ nhật, hình thoi, hình bình hành, hình thang cân", "Các tính chất của hình phẳng."),
            ("Chu vi và diện tích của một số hình phẳng", "Công thức tính chu vi và diện tích."),
            ("Trục đối xứng và tâm đối xứng", "Tính đối xứng của các hình.")
        ],
        "m4": [
            ("Thu thập và tổ chức dữ liệu", "Cách thu thập và phân loại dữ liệu."),
            ("Biểu đồ cột và biểu đồ cột kép", "Vẽ và đọc dữ liệu từ biểu đồ cột."),
            ("Biểu đồ tranh", "Đọc dữ liệu từ biểu đồ tranh."),
            ("Xác suất thực nghiệm", "Tính xác suất của một sự kiện đơn giản.")
        ],
        "m5": [
            ("Phân số với tử và mẫu là số nguyên", "Mở rộng khái niệm phân số."),
            ("Tính chất cơ bản của phân số", "Rút gọn và quy đồng mẫu số."),
            ("So sánh phân số", "Cách so sánh hai phân số."),
            ("Các phép tính với phân số", "Cộng, trừ, nhân, chia phân số."),
            ("Số thập phân và các phép tính", "Cộng, trừ, nhân, chia số thập phân."),
            ("Làm tròn số và ước lượng", "Quy tắc làm tròn số thập phân."),
            ("Tỉ số và phần trăm", "Tính tỉ số phần trăm của hai số.")
        ],
        "m6": [
            ("Điểm, đường thẳng, tia", "Khái niệm cơ bản về hình học phẳng."),
            ("Đoạn thẳng. Độ dài đoạn thẳng", "Đo và vẽ đoạn thẳng."),
            ("Góc. Số đo góc", "Nhận biết các loại góc (vuông, nhọn, tù, bẹt).")
        ],
        "m7": [
            ("Ứng dụng toán học thực tiễn", "Áp dụng kiến thức vào các bài toán thực tế nâng cao."),
            ("Toán tư duy", "Phát triển tư duy logic toán học.")
        ]
    }
    
    for ch in chapters:
        course["macro_nodes"].append({
            "id": ch["id"],
            "title": ch["title"],
            "resources": [],
            "bloom_profile": get_bloom_profile(base=20)
        })
        
        c_index = int(ch["id"].replace("m", ""))
        
        for i, (t_title, t_content) in enumerate(topics[ch["id"]]):
            micro_id = f"c{c_index}.{i+1}"
            course["micro_nodes"].append({
                "id": micro_id,
                "parent_macro": ch["id"],
                "title": f"Topic {i+1}: {t_title}",
                "content": t_content,
                "url": "https://vi.khanacademy.org/math/toan-lop-6-viet-nam",
                "alpha_base": 20,
                "resources": [
                    {
                        "id": f"res_ext_{uuid.uuid4().hex[:8]}",
                        "url": "https://vi.khanacademy.org/math/toan-lop-6-viet-nam",
                        "title": f"Tài nguyên: {t_title}",
                        "type": "web",
                        "icon": "🌐",
                        "added_at": "auto-sync"
                    }
                ],
                "bloom_profile": get_bloom_profile(base=20, levels=[1, 2, 3] if i < 3 else [2, 3, 4])
            })
            
    # Add some assess nodes
    for ch in chapters:
        c_index = int(ch["id"].replace("m", ""))
        course["assess_nodes"].append({
            "id": f"q_{ch['id']}",
            "parent_micro": f"c{c_index}.1",
            "title": f"Bài kiểm tra Chương {c_index}",
            "content": f"Kiểm tra tổng hợp kiến thức chương {c_index}.",
            "alpha_base": 30,
            "bloom_profile": get_bloom_profile(base=30, levels=[3, 4, 5])
        })
            
    with open("khan_academy_toan_6.json", "w", encoding="utf-8") as f:
        json.dump(course, f, ensure_ascii=False, indent=4)
        
    print("Created khan_academy_toan_6.json")

if __name__ == "__main__":
    generate_course()

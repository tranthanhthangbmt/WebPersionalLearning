import re
import json
import uuid
from datetime import datetime

def get_bloom_profile(base=20, levels=None):
    if levels is None:
        levels = [1, 2, 3]
    return {
        "auto_calibrated_levels": levels,
        "user_adjusted_levels": None,
        "effective_levels": levels,
        "calibration_method": "alpha_base",
        "alpha_base": base,
        "created_at": datetime.now().isoformat()
    }

def scrape():
    filepath = r"C:\Users\thanh\.gemini\antigravity-ide\brain\5b4112b2-797b-4f18-8bbf-1aea3b13dd98\.system_generated\steps\182\content.md"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    course = {
        "course_name": "Ngữ văn 6 - Kết nối tri thức với cuộc sống (OLM)",
        "macro_nodes": [],
        "micro_nodes": []
    }
    
    current_macro = None
    current_micro = None
    
    # In Literature, chapters are like "Bài 1: Tôi và các bạn"
    chapter_pattern = re.compile(r'^\[(Bài \d+:\s*.*?)\]\((.*?)\)')
    resource_link_pattern = re.compile(r'\[(.*?)\]\((.*?)\)')
    bare_url_pattern = re.compile(r'(https://olm\.vn/chu-de/.*?)(?:\s|$)')
    
    macro_id_counter = 1
    micro_id_counter = 1
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check Chapter
        m_chapter = chapter_pattern.search(line)
        if m_chapter:
            title = m_chapter.group(1)
            current_macro = {
                "id": f"m{macro_id_counter}",
                "title": title,
                "resources": [],
                "bloom_profile": get_bloom_profile(20)
            }
            course["macro_nodes"].append(current_macro)
            macro_id_counter += 1
            micro_id_counter = 1
            current_micro = None
            continue
            
        if not current_macro:
            continue
            
        # Check Lesson
        # Lessons are usually things like "Văn bản:", "Thực hành", "Viết", "Nói và nghe", "Củng cố"
        # We can detect them by finding a link that starts with these keywords, OR we can just check any link that is structurally a lesson.
        # Looking at the markdown, lessons start after a bullet point or "thi-dau?category=".
        
        is_lesson_line = ("thi-dau?category=" in line) or line.startswith("-") or line.startswith("[Văn bản:") or line.startswith("[Thực hành") or line.startswith("[Viết") or line.startswith("[Nói và nghe") or line.startswith("[Củng cố") or line.startswith("[Nâng cao")
        
        if is_lesson_line:
            res = resource_link_pattern.findall(line)
            for text, url in res:
                # Text should not be generic like "HS", "Free", "PPT", "Mới"
                if text not in ["HS", "Free", "PPT", "Mới", "Tuần trước", "Phiếu bài tập tổng hợp"] and len(text) > 5 and not text.startswith("https:"):
                    # This is likely a lesson
                    current_micro = {
                        "id": f"c{macro_id_counter-1}.{micro_id_counter}",
                        "parent_macro": current_macro["id"],
                        "title": text,
                        "content": "Nội dung bài học: " + text,
                        "url": url,
                        "alpha_base": 20,
                        "resources": [],
                        "bloom_profile": get_bloom_profile(20, [1,2,3])
                    }
                    course["micro_nodes"].append(current_micro)
                    micro_id_counter += 1
                    break
            # Continue so we don't treat the lesson title itself as a sub-resource
            # Wait, sometimes the lesson line only contains the lesson title.
            # Next lines contain the sub-resources.
            continue
            
        # If we have a current_micro, add resources
        if current_micro:
            # Check for resource links
            res = resource_link_pattern.findall(line)
            added = False
            for text, url in res:
                if text not in ["HS", "Free", "PPT", "Mới"] and len(text) > 0 and not text.startswith("Bài "):
                    current_micro["resources"].append({
                        "id": f"res_ext_{uuid.uuid4().hex[:8]}",
                        "url": url,
                        "title": text,
                        "type": "web",
                        "icon": "🌐",
                        "added_at": "auto-sync"
                    })
                    added = True
                elif text == "PPT":
                    current_micro["resources"].append({
                        "id": f"res_ext_{uuid.uuid4().hex[:8]}",
                        "url": url,
                        "title": "Bài giảng PPT",
                        "type": "document",
                        "icon": "📊",
                        "added_at": "auto-sync"
                    })
                    added = True
                    
            if not added:
                bare = bare_url_pattern.findall(line)
                for url in bare:
                    title_slug = url.split('/')[-1]
                    title_parts = title_slug.split('-')
                    if len(title_parts) > 1 and title_parts[-1].isdigit():
                        title = " ".join(title_parts[:-1]).capitalize()
                    else:
                        title = " ".join(title_parts).capitalize()
                        
                    current_micro["resources"].append({
                        "id": f"res_ext_{uuid.uuid4().hex[:8]}",
                        "url": url,
                        "title": f"Tài liệu: {title}",
                        "type": "web",
                        "icon": "🌐",
                        "added_at": "auto-sync"
                    })
                    
    with open('olm_ngu_van_6.json', 'w', encoding='utf-8') as f:
        json.dump(course, f, ensure_ascii=False, indent=4)
        
    print(f"Scraped {len(course['macro_nodes'])} chapters and {len(course['micro_nodes'])} lessons.")

if __name__ == "__main__":
    scrape()

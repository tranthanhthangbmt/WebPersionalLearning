import os
import json
import urllib.request
import urllib.error
import re
import uuid

# Base URLs
TMDT_BASE = "https://tranthanhthangbmt.github.io/ThuongMaiDienTu_3TC"
AIUD_BASE = "https://tranthanhthangbmt.github.io/AIUD_March2026"

def get_script_url(concept_id):
    # Match AIUD e.g. c1.1
    if re.match(r'^c\d+\.\d+$', concept_id):
        return f"{AIUD_BASE}/Video/{concept_id}/script.txt"
        
    # Match TMDT e.g. Chuong_1_Tiet_1
    chuong_match = re.match(r'^(Chuong_\d+_Tiet_\d+)', concept_id)
    if chuong_match:
        base_id = chuong_match.group(1) # Lấy phần gốc, ví dụ Chuong_1_Tiet_1 từ Chuong_1_Tiet_1_Intro
        return f"{TMDT_BASE}/Video/{base_id}/script.txt"
        
    return None

def main():
    json_dir = os.path.join("DB", "JSON_Data")
    if not os.path.exists(json_dir):
        print(f"Directory not found: {json_dir}")
        return

    success_count = 0
    fail_count = 0
    
    for filename in os.listdir(json_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(json_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            concept_id = data.get('metadata', {}).get('concept_id')
            if not concept_id:
                continue
                
            url = get_script_url(concept_id)
            if not url:
                continue
                
            # Fetch script
            print(f"[{concept_id}] Đang tải {url}...")
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                response = urllib.request.urlopen(req, timeout=5)
                script_content = response.read().decode('utf-8-sig').strip()
                
                # Update JSON
                data['script_content'] = script_content
                
                # Add to resources list as link
                if 'resources' not in data:
                    data['resources'] = []
                    
                has_script = any(r.get('url') == url for r in data['resources'])
                if not has_script:
                    title = data.get('metadata', {}).get('concept_name', concept_id)
                    data['resources'].append({
                        "id": f"res_script_{concept_id}_{uuid.uuid4().hex[:4]}",
                        "url": url,
                        "title": f"📄 Kịch bản Video: {title}",
                        "type": "document", 
                        "icon": "📄", 
                        "added_at": "auto-sync"
                    })
                    
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
                print(f"   ✅ Đã nhúng nội dung kịch bản vào {filename} (Độ dài: {len(script_content)} ký tự)")
                success_count += 1
                
            except urllib.error.HTTPError as e:
                print(f"   ❌ HTTP Error {e.code}: Kịch bản không tồn tại.")
                fail_count += 1
            except Exception as e:
                print(f"   ❌ Lỗi: {e}")
                fail_count += 1
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    print(f"\n🎉 Hoàn thành! Đã nhúng thành công {success_count} scripts. Thất bại/Bỏ qua: {fail_count}")

if __name__ == "__main__":
    main()

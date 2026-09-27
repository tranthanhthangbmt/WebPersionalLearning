import json

def fix_youtube_resources(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    count = 0
    for m in data.get('micro_nodes', []):
        for r in m.get('resources', []):
            if 'youtube.com' in r.get('url', ''):
                if r.get('type') != 'video':
                    r['type'] = 'video'
                    r['icon'] = '▶️'
                    if r['title'] == 'Bài giảng PPT':
                        r['title'] = 'Video Bài giảng'
                    elif 'Tài liệu:' in r['title']:
                        r['title'] = r['title'].replace('Tài liệu:', 'Video:')
                    count += 1
                    
    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Fixed {count} youtube resources in {filepath}")
    else:
        print(f"No youtube resources needed fixing in {filepath}")

fix_youtube_resources('DB/public_trees/f2c8d7e9.json')
fix_youtube_resources('user_data/thanhthangbmt/trees/f2c8d7e9.json')
fix_youtube_resources('DB/public_trees/c4d5e6f7.json')
fix_youtube_resources('user_data/thanhthangbmt/trees/c4d5e6f7.json')

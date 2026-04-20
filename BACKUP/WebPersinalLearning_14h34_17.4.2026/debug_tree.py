import os
import glob
import json
import re

json_path = "DB/JSON_Data/*.json"
files = glob.glob(json_path)

data = {}
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        try:
            content = json.load(file)
            concept_id = content['metadata']['concept_id']
            data[concept_id] = content
        except Exception as e:
            pass

concepts = [{"id": k, "name": v['metadata']['concept_name']} for k, v in data.items()]
chapters = {}
chapter_pattern = re.compile(r"(ch(?:ương|uong)[_ ]?(\d+))", re.IGNORECASE)

for c in concepts:
    c_name = c['name']
    chap_match = chapter_pattern.search(c_name)
    chap_num = int(chap_match.group(2)) if chap_match else 999
    chap_key = f"CHAPTER_{chap_num}"
    if chap_num == 999: chap_display = "Tài nguyên bổ trợ"
    else: chap_display = f"Chương {chap_num}"

    if chap_key not in chapters:
        chapters[chap_key] = {'id': chap_key, 'label': chap_display, 'children': [], 'num': chap_num}
    
    chapters[chap_key]['children'].append({'id': c['id'], 'label': c_name})

sorted_chapters = sorted(chapters.values(), key=lambda x: x['num'])
for chap in sorted_chapters:
    print(f"{chap['label']}")
    for child in chap['children']:
        print(f"  - {child['label']}")

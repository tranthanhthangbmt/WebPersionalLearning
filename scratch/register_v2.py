import json

subj_file = 'user_data/thanhthangbmt7/subjects.json'
with open(subj_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Add the v2.0 tree
data['subjects'].append({
    'id': '95a7dbf9',
    'title': 'Thương mại điện tử v2.0 (MIT)',
    'filename': 'user_data/thanhthangbmt7/trees/95a7dbf9.json',
    'total_nodes': 66
})

with open(subj_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done! Added to thanhthangbmt7/subjects.json")
print(json.dumps(data, ensure_ascii=False, indent=2))

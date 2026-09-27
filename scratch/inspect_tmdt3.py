import json

with open('user_data/thanhthangbmt/trees/e69bf65f.json', 'r', encoding='utf-8') as f:
    tree = json.load(f)

nodes = tree.get('nodes', {})

# Print chapter-level summary with ALL resources
print("=== SUMMARY OF ALL NODES WITH RESOURCES ===")
total_res = 0
total_q = 0
for node_id, node_data in nodes.items():
    ntype = node_data.get('type', '?')
    label = node_data.get('label', '?')
    resources = node_data.get('resources', [])
    questions = node_data.get('questions', [])
    total_res += len(resources)
    total_q += len(questions)
    if resources:
        print(f"\n  [{node_id}] ({ntype}) {label} -- {len(resources)} resources, {len(questions)} questions")
        for r in resources:
            print(f"    -> {r.get('type','?')}: {r.get('title','?')[:60]} | {r.get('url','')[:60]}")

print(f"\n=== TOTALS ===")
print(f"  Total nodes: {len(nodes)}")
print(f"  Total resources: {total_res}")
print(f"  Total questions: {total_q}")

# Count by type
type_counts = {}
for n in nodes.values():
    t = n.get('type', '?')
    type_counts[t] = type_counts.get(t, 0) + 1
print(f"  By type: {type_counts}")

# Print the chapter structure  
print("\n=== CHAPTER STRUCTURE (what belongs to which chapter) ===")
chapters = {}
for node_id, node_data in nodes.items():
    ntype = node_data.get('type', '?')
    if ntype == 'macro':
        chapters[node_id] = {'title': node_data.get('label', '?'), 'children': []}

# Group micro/assess by chapter prefix
import re
for node_id, node_data in nodes.items():
    ntype = node_data.get('type', '?')
    if ntype != 'macro':
        # Try to determine parent chapter from ID
        match = re.match(r'(?:a_)?Chuong_(\d+)', node_id)
        if match:
            chap_num = match.group(1)
            macro_key = f"m{chap_num}"
            if macro_key in chapters:
                chapters[macro_key]['children'].append({
                    'id': node_id,
                    'type': ntype,
                    'label': node_data.get('label', '?'),
                    'resources': len(node_data.get('resources', [])),
                    'questions': len(node_data.get('questions', []))
                })
            else:
                print(f"  ORPHAN: [{node_id}] -> expected parent {macro_key} not found")
        else:
            print(f"  ORPHAN: [{node_id}] ({ntype}) {node_data.get('label','?')} - no chapter pattern")

for macro_id, chap in sorted(chapters.items()):
    micros = [c for c in chap['children'] if c['type'] == 'micro']
    assesses = [c for c in chap['children'] if c['type'] == 'assess']
    print(f"\n  {macro_id}: {chap['title']}")
    print(f"    Micro nodes ({len(micros)}):")
    for m in micros:
        print(f"      [{m['id']}] {m['label']} (res={m['resources']}, q={m['questions']})")
    print(f"    Assess nodes ({len(assesses)}):")
    for a in assesses:
        print(f"      [{a['id']}] {a['label']} (q={a['questions']})")

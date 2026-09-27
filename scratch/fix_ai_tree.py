"""
Fix the AI tree structure by adding proper edges for better graph visualization.
Preserves ALL existing data (resources, content, questions, etc).
Only adds missing structural edges to improve layout.
"""
import json
import copy

INPUT = 'user_data/thanhthangbmt7/trees/faa95c0b.json'

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Backup original
with open(INPUT + '.backup_structure', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("✅ Backup saved")

# Build lookup maps
macro_ids = [m['id'] for m in data['macro_nodes']]
micro_by_macro = {}
for c in data['micro_nodes']:
    pm = c.get('parent_macro')
    if pm not in micro_by_macro:
        micro_by_macro[pm] = []
    micro_by_macro[pm].append(c)

existing_edges = set()
for e in data['edges']:
    existing_edges.add((e['source'], e['target']))

new_edges = []

# 1. Add macro->macro chain edges (m1->m2->m3->...)
for i in range(len(macro_ids) - 1):
    src, tgt = macro_ids[i], macro_ids[i+1]
    if (src, tgt) not in existing_edges:
        new_edges.append({"source": src, "target": tgt, "relation": "prerequisite_for"})
        existing_edges.add((src, tgt))
        print(f"  + Macro chain: {src} -> {tgt}")

# 2. Add sequential micro->micro edges within each chapter
for mid in macro_ids:
    micros = micro_by_macro.get(mid, [])
    for i in range(len(micros) - 1):
        src = micros[i]['id']
        tgt = micros[i+1]['id']
        if (src, tgt) not in existing_edges:
            new_edges.append({"source": src, "target": tgt, "relation": "prerequisite_for"})
            existing_edges.add((src, tgt))
            print(f"  + Micro chain: {src} -> {tgt}")

# 3. Add cross-chapter bridge edges (last micro of chapter N -> first micro of chapter N+1)
for i in range(len(macro_ids) - 1):
    cur_micros = micro_by_macro.get(macro_ids[i], [])
    next_micros = micro_by_macro.get(macro_ids[i+1], [])
    if cur_micros and next_micros:
        src = cur_micros[-1]['id']
        tgt = next_micros[0]['id']
        if (src, tgt) not in existing_edges:
            new_edges.append({"source": src, "target": tgt, "relation": "prerequisite_for"})
            existing_edges.add((src, tgt))
            print(f"  + Bridge: {src} -> {tgt}")

data['edges'].extend(new_edges)
print(f"\n📊 Added {len(new_edges)} new edges (total: {len(data['edges'])})")

with open(INPUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("✅ Tree structure updated!")

# Regenerate the graph
from step2_5_visualize_tree import visualize_knowledge_tree
visualize_knowledge_tree('thanhthangbmt7', INPUT)

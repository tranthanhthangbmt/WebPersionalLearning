import json
import os

with open('user_data/thanhthangbmt/trees/e69bf65f.json', 'r', encoding='utf-8') as f:
    tree = json.load(f)

print("=== TMDT Dong Bo Structure ===")
print(f"course_name: {tree.get('course_name')}")
macros = tree.get('macro_nodes', [])
micros = tree.get('micro_nodes', [])
assess = tree.get('assess_nodes', [])
edges = tree.get('edges', [])
print(f"macro: {len(macros)}, micro: {len(micros)}, assess: {len(assess)}, edges: {len(edges)}")

print("\n--- MACROS ---")
for m in macros:
    print(f"  [{m['id']}] {m['title']}")

print("\n--- MICROS ---")
for m in micros:
    pm = m.get('parent_macro', '?')
    res_count = len(m.get('resources', []))
    q_count = len(m.get('questions', []))
    print(f"  [{m['id']}] {m['title']}")
    print(f"    parent={pm}, resources={res_count}, questions={q_count}")

print("\n--- ASSESS ---")
for a in assess:
    pm = a.get('parent_micro', '?')
    q_count = len(a.get('questions', []))
    print(f"  [{a['id']}] {a.get('title','?')} | parent_micro={pm}, questions={q_count}")

print("\n--- EDGES ---")
for e in edges:
    print(f"  {e['source']} -> {e['target']}")

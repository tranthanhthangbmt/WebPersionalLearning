import json

path = 'user_data/thanhthangbmt/trees/2e288b09.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"course_name: {data.get('course_name', 'N/A')}")
macros = data.get('macro_nodes', [])
micros = data.get('micro_nodes', [])
print(f"macro_nodes: {len(macros)}, micro_nodes: {len(micros)}")

for m in macros[:5]:
    print(f"\n  MACRO: {m.get('id')} - {m.get('title')}")
    res = m.get('resources', [])
    for r in res[:5]:
        print(f"    -> {r.get('type','?')} | {r.get('title','')[:50]} | {r.get('url','')[:100]}")

for mi in micros[:8]:
    print(f"\n  MICRO: {mi.get('id')} - {mi.get('title')}")
    res = mi.get('resources', [])
    for r in res[:5]:
        print(f"    -> {r.get('type','?')} | {r.get('title','')[:50]} | {r.get('url','')[:100]}")
    if not res:
        print(f"    -> (no resources)")

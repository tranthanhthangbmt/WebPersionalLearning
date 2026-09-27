import json

with open('user_data/thanhthangbmt/trees/e69bf65f.json', 'r', encoding='utf-8') as f:
    tree = json.load(f)

print("=== ALL TOP-LEVEL KEYS ===")
for k in tree.keys():
    v = tree[k]
    if isinstance(v, list):
        print(f"  {k}: list[{len(v)}]")
    elif isinstance(v, dict):
        print(f"  {k}: dict with keys {list(v.keys())[:5]}")
    elif isinstance(v, str):
        print(f"  {k}: '{v[:80]}'")
    else:
        print(f"  {k}: {type(v).__name__} = {v}")

# Check if it uses a different schema (concepts instead of macro/micro)
if 'concepts' in tree:
    print("\n=== CONCEPTS ===")
    for c in tree['concepts']:
        res = c.get('resources', [])
        q = c.get('questions', [])
        print(f"  [{c.get('id')}] {c.get('name','?')}")
        print(f"    resources: {len(res)}, questions: {len(q)}")
        for r in res:
            print(f"      RES: {r.get('title','?')[:60]} | {r.get('url','')[:60]}")

if 'nodes' in tree:
    print("\n=== NODES ===")
    for n in tree['nodes'][:5]:
        print(f"  {n}")

import json
# Check where the missing resources are
with open('user_data/thanhthangbmt/trees/e69bf65f.json', 'r', encoding='utf-8') as f:
    tree = json.load(f)

nodes = tree.get('nodes', {})
for nid, nd in nodes.items():
    ntype = nd.get('type', '?')
    res = nd.get('resources', [])
    if res and ntype == 'macro':
        print(f"MACRO with resources: [{nid}] {nd.get('label','?')} -> {len(res)} resources")
        for r in res:
            print(f"  {r.get('type','?')}: {r.get('title','?')[:60]}")
    if res and ntype == 'assess':
        print(f"ASSESS with resources: [{nid}] -> {len(res)} resources")

# Also check: resources on macro vs micro vs assess
macro_res = sum(len(n.get('resources',[])) for n in nodes.values() if n.get('type') == 'macro')
micro_res = sum(len(n.get('resources',[])) for n in nodes.values() if n.get('type') == 'micro')
assess_res = sum(len(n.get('resources',[])) for n in nodes.values() if n.get('type') == 'assess')
print(f"\nmacro_res={macro_res}, micro_res={micro_res}, assess_res={assess_res}, total={macro_res+micro_res+assess_res}")

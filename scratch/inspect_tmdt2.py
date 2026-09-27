import json

with open('user_data/thanhthangbmt/trees/e69bf65f.json', 'r', encoding='utf-8') as f:
    tree = json.load(f)

print("=== METADATA ===")
print(json.dumps(tree.get('metadata', {}), indent=2, ensure_ascii=False))

print("\n=== STUDENT_STATE ===")
ss = tree.get('student_state', {})
print(json.dumps({k: v for k,v in ss.items() if k != 'node_progress'}, indent=2, ensure_ascii=False))

print("\n=== NODES STRUCTURE (dict-based) ===")
nodes = tree.get('nodes', {})
for node_id, node_data in nodes.items():
    print(f"\n  MACRO NODE: [{node_id}]")
    if isinstance(node_data, dict):
        # Print macro-level info
        for k, v in node_data.items():
            if k == 'children':
                children = v
                if isinstance(children, dict):
                    print(f"    children: {len(children)} items")
                    for child_id, child_data in children.items():
                        if isinstance(child_data, dict):
                            title = child_data.get('title', '?')
                            res = child_data.get('resources', [])
                            q = child_data.get('questions', [])
                            bloom = child_data.get('bloom_level', '?')
                            print(f"      [{child_id}] {title}")
                            print(f"        bloom={bloom}, resources={len(res)}, questions={len(q)}")
                            for r in res:
                                print(f"          RES: {r.get('title','?')[:50]} | type={r.get('type','?')}")
                        else:
                            print(f"      [{child_id}] (non-dict: {type(child_data).__name__})")
                elif isinstance(children, list):
                    print(f"    children: list[{len(children)}]")
                    for ch in children[:3]:
                        print(f"      {ch}")
            elif isinstance(v, (str, int, float, bool)):
                print(f"    {k}: {v}")
            elif isinstance(v, list):
                print(f"    {k}: list[{len(v)}]")
                if len(v) > 0 and k == 'questions':
                    for qi, q in enumerate(v[:2]):
                        print(f"      Q{qi}: {str(q)[:100]}")
            elif isinstance(v, dict):
                print(f"    {k}: dict keys={list(v.keys())[:5]}")

print("\n=== EDGES SAMPLE ===")
edges = tree.get('edges', [])
for e in edges[:10]:
    print(f"  {e}")

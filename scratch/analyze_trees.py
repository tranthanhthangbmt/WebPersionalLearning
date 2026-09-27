import json

# AI tree
with open('user_data/thanhthangbmt7/trees/faa95c0b.json', 'r', encoding='utf-8') as f:
    ai = json.load(f)

print("=== AI MACRO NODES ===")
for m in ai['macro_nodes']:
    mid = m['id']
    children = [c for c in ai['micro_nodes'] if c.get('parent_macro') == mid]
    print(f"  {mid}: {m['title']} ({len(children)} micros)")

print("\n=== AI EDGES ===")
for e in ai['edges']:
    print(f"  {e['source']} -> {e['target']} ({e.get('relation','?')})")

# TMDT tree
with open('user_data/thanhthangbmt7/trees/95a7dbf9.json', 'r', encoding='utf-8') as f:
    tmdt = json.load(f)

print("\n=== TMDT MIT MACRO NODES ===")
for m in tmdt['macro_nodes']:
    mid = m['id']
    children = [c for c in tmdt['micro_nodes'] if c.get('parent_macro') == mid]
    print(f"  {mid}: {m['title']} ({len(children)} micros)")

print("\n=== TMDT EDGES ===")
for e in tmdt['edges']:
    print(f"  {e['source']} -> {e['target']} ({e.get('relation','?')})")

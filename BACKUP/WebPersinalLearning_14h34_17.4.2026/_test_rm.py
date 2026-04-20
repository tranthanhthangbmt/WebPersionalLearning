from resource_manager import get_all_nodes_summary, detect_resource_type

nodes = get_all_nodes_summary('user_data/thanhthangbmt/trees/e69bf65f.json')
print(f'Total nodes: {len(nodes)}')
for n in nodes[:10]:
    print(f'  {n["type"]:6s} | {n["id"]:25s} | res={n["resource_count"]} | {n["label"][:40]}')
print('---')
t, i, d = detect_resource_type('https://youtube.com/watch?v=abc')
print(f'YouTube: {t} {i} {d}')
t, i, d = detect_resource_type('https://colab.research.google.com/drive/xyz')
print(f'Colab: {t} {i} {d}')
t, i, d = detect_resource_type('https://example.com/notes.pdf')
print(f'PDF: {t} {i} {d}')

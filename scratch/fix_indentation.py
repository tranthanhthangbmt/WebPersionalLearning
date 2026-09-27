import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We look for the exact wrong indentation:
# '                      omni_ui[\'context_label\'].text = f\'Đang theo dõi: Graph Studio ({subj_title})\'\n\n                       if hasattr(tree_preview_container'
# And replace with correct indentation:

wrong_part = """                          omni_ui['context_label'].text = f'Đang theo dõi: Graph Studio ({subj_title})'

                       if hasattr(tree_preview_container, 'studio_timer') and tree_preview_container.studio_timer:
                           try:
                               tree_preview_container.studio_timer.delete()
                           except:
                               pass
                       tree_preview_container.clear()
                      show_graph_view()"""

correct_part = """                          omni_ui['context_label'].text = f'Đang theo dõi: Graph Studio ({subj_title})'

                      if hasattr(tree_preview_container, 'studio_timer') and tree_preview_container.studio_timer:
                          try:
                              tree_preview_container.studio_timer.delete()
                          except:
                              pass
                      tree_preview_container.clear()
                      show_graph_view()"""

if wrong_part in content:
    content = content.replace(wrong_part, correct_part)
    print("Exact match replaced!")
else:
    # Let's do a regex replace to be absolutely sure
    print("Exact match not found, trying regex...")
    pattern = re.compile(
        r"(\s+)omni_ui\['context_label'\].text = f'Đang theo dõi: Graph Studio \(\{subj_title\}\)'\s*\n\s*\n\s+if hasattr\(tree_preview_container, 'studio_timer'\) and tree_preview_container.studio_timer:\s*\n\s+try:\s*\n\s+tree_preview_container.studio_timer.delete\(\)\s*\n\s+except:\s*\n\s+pass\s*\n\s+tree_preview_container.clear\(\)\s*\n\s+show_graph_view\(\)"
    )
    # Let's find it line by line
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        if "if hasattr(tree_preview_container, 'studio_timer')" in line:
            print(f"Found line {idx+1}: {repr(line)}")
            lines[idx] = "                      if hasattr(tree_preview_container, 'studio_timer') and tree_preview_container.studio_timer:"
            lines[idx+1] = "                          try:"
            lines[idx+2] = "                              tree_preview_container.studio_timer.delete()"
            lines[idx+3] = "                          except:"
            lines[idx+4] = "                              pass"
            lines[idx+5] = "                      tree_preview_container.clear()"
            lines[idx+6] = "                      show_graph_view()"
            print(f"Fixed lines around {idx+1}")
            break
    content = "\n".join(lines) + "\n"

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done fixing main.py!")

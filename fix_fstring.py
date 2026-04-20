import json

with open('step2_5_visualize_tree.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure f-strings are escaped correctly: ${resIcon} -> ${{resIcon}}
text = text.replace('${resIcon}', '${{resIcon}}')
text = text.replace('${resTitle}', '${{resTitle}}')

with open('step2_5_visualize_tree.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Patch applied for f-strings.")

try:
    from step2_5_visualize_tree import visualize_knowledge_tree
    visualize_knowledge_tree('thanhthangbmt7', 'user_data/thanhthangbmt7/trees/66cb66e0.json')
    print("Test render successful.")
except Exception as e:
    print("Error:", e)

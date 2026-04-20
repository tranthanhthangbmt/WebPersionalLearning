import codecs

with codecs.open("new_layout4.txt", "r", "utf-8") as f:
    new_text = f.read()

with codecs.open("main.py", "r", "utf-8") as f:
    content = f.read()

start_marker = "             with ui.splitter(value=20).classes('w-full h-full').props('separator-class=\"bg-blue-100\"') as main_splitter:"
end_marker = "                                             ui.label('Đang phân tích đề bài...').classes('text-gray-400 text-xs italic')"

start_pos = content.find(start_marker)
end_pos = content.find(end_marker)

if start_pos != -1 and end_pos != -1:
    end_pos_full = end_pos + len(end_marker)
    patched = content[:start_pos] + new_text + content[end_pos_full:]
    with codecs.open("main.py", "w", "utf-8") as f:
        f.write(patched)
    print("SUCCESS")
else:
    print(f"FAILED: start_pos={start_pos}, end_pos={end_pos}")

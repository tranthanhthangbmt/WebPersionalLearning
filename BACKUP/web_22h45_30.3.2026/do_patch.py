import codecs
import sys

with codecs.open("new_layout.txt", "r", "utf-8") as f:
    new_text = f.read()

with codecs.open("main.py", "r", "utf-8") as f:
    content = f.read()

start_marker = "             with ui.row().classes('w-full h-full no-wrap gap-0'):"
end_marker = "                             ui.button(icon='send', on_click=tutor_send_message).props('flat round dense color=blue').classes('absolute right-1 top-1/2 transform -translate-y-1/2')"

start_pos = content.find(start_marker)
end_pos = content.find(end_marker)

if start_pos == -1 or end_pos == -1:
    print(f"FAILED: start_pos={start_pos}, end_pos={end_pos}")
    sys.exit(1)

end_pos_full = end_pos + len(end_marker)

patched = content[:start_pos] + new_text + "\n" + content[end_pos_full:]

with codecs.open("main.py", "w", "utf-8") as f:
    f.write(patched)
print("SUCCESSFULLY PATCHED")

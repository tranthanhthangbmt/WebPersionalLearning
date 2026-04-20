import codecs

with codecs.open('new_layout.txt', 'r', 'utf-8') as f:
    new_content = f.read()

with codecs.open('main.py', 'r', 'utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.strip() == "with ui.row().classes('w-full h-full no-wrap gap-0'):":
        start_idx = i
    if line.strip().startswith("ui.button(icon='send', on_click=tutor_send_message)"):
        end_idx = i

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + [new_content + "\n"] + lines[end_idx+1:]
    with codecs.open('main.py', 'w', 'utf-8') as f:
        f.writelines(new_lines)
    print("Patched main.py successfully.")
else:
    print(f"Could not find bounds: {start_idx}, {end_idx}")

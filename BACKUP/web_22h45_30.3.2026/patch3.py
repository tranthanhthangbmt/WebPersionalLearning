with open("new_layout.txt", "r", encoding="utf-8") as f:
    new_text = f.read()

with open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "no-wrap gap-0" in line and "ui.row().classes" in line:
        start_idx = i
        break

if start_idx != -1:
    for i in range(start_idx, len(lines)):
        if "icon='send'" in line and "tutor_send_message" in line:
            end_idx = i
        elif "icon='send'" in lines[i] and "tutor_send_message" in lines[i]:
            end_idx = i

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + [new_text + "\n"] + lines[end_idx+1:]
    with open("main.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("SUCCESS: Patched main.py")
else:
    print(f"FAILED: start={start_idx}, end={end_idx}")

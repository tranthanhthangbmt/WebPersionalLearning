import codecs

with codecs.open('main.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "no-wrap gap-0" in line:
        print(f"Line {i}: {repr(line)}")
        if i+1 < len(lines):
            print(f"Next line: {repr(lines[i+1])}")

    if "ui.button(icon='send'" in line and "tutor_send_message" in line:
        print(f"End line {i}: {repr(line)}")

import re
import codecs

with codecs.open("main.py", "r", "utf-8") as f:
    content = f.read()

with codecs.open("new_layout.txt", "r", "utf-8") as f:
    new_content = f.read()

pattern = re.compile(r" *with ui\.row\(\)\.classes\('w-full h-full no-wrap gap-0'\):\n.*ui\.button\(icon='send', on_click=tutor_send_message\)[^\n]*\n", re.DOTALL)

if pattern.search(content):
    patched = pattern.sub(new_content + "\n", content, count=1)
    with codecs.open("main.py", "w", "utf-8") as f:
        f.write(patched)
    print("SUCCESS: Layout injected")
else:
    print("FAILED: Regex not found")
    
    # Try finding the first line to see how many spaces it has
    for line in content.splitlines():
        if "w-full h-full no-wrap gap-0" in line:
            print(f"Found candidate start line: '{line}'")

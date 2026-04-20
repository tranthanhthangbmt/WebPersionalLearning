import codecs

with codecs.open("layout5_tail.txt", "r", "utf-8") as f:
    tail_text = f.read()

with codecs.open("main.py", "r", "utf-8") as f:
    content = f.read()

start_marker = "                         async def tutor_start_exercise():"

start_pos = content.find(start_marker)

if start_pos != -1:
    patched = content[:start_pos] + tail_text + "\n"
    with codecs.open("main.py", "w", "utf-8") as f:
        f.write(patched)
    print("SUCCESS")
else:
    print(f"FAILED: start_pos={start_pos}")

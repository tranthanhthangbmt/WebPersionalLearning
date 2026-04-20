import os
import re

path = r'I:\MY_CODE\WebPersionalLearning\ai_video_player.py'
with open(path, 'rb') as f:
    data = f.read()

# Find all occurrences of the broken line
# The traceback says: 
#    self.img.on('error', lambda: ui.notify('Lỗi t                     # --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---
# The  char might be one or more bytes.
# We'll match from self.img.on up to the start of the comment.

# Regex to match the broken part.
# We'll use a very generous match but ensure it's on a line that looks like the player dock code.
# The comment "# --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---" is very unique.

# Let's try to find the comment first.
comment = b"# --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---"
comment_idx = data.find(comment)

if comment_idx != -1:
    # Find the start of the line containing this comment
    line_start = data.rfind(b'\n', 0, comment_idx) + 1
    # Find the end of the line
    line_end = data.find(b'\n', comment_idx)
    if line_end == -1: line_end = len(data)
    
    # Check if the line contains ui.notify
    if b'ui.notify(' in data[line_start:line_end]:
        # Construct the fixed line:
        # We'll keep the same indentation by finding it.
        indent = b''
        for byte in data[line_start:line_end]:
            if byte in [32, 9]: # space or tab
                indent += bytes([byte])
            else:
                break
        
        # New fixed line:
        fixed_line = indent + b"self.img.on('error', lambda: ui.notify('L\xe1\xbb\x97i t\xe1\xba\xa3i \xe1\xba\xa3nh minh h\xe1\xbb\x8da!')) # --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---"
        
        new_data = data[:line_start] + fixed_line + data[line_end:]
        with open(path, 'wb') as f:
            f.write(new_data)
        print(f"FIXED: Line fixed at index {line_start}")
    else:
        print("COULD NOT FIND ui.notify on the line with the comment")
else:
    print("COULD NOT FIND the docking comment")

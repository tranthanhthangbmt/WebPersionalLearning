import os
import re

path = r'I:\MY_CODE\WebPersionalLearning\ai_video_player.py'
print(f"Opening file: {path}")

try:
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Clean non-UTF8 characters
    print("Cleaning non-UTF8 characters...")
    content = data.decode('utf-8', errors='ignore')
    
    # Fix the specific line 149 issue
    print("Fixing line 149...")
    # The comment is unique
    comment = "# --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---"
    
    lines = content.splitlines()
    fixed_lines = []
    found = False
    for line in lines:
        if comment in line and "ui.notify" in line:
            # Reconstruct the line correctly
            indent = "        " if line.startswith("        ") else "    "
            new_line = f"{indent}self.img.on('error', lambda: ui.notify('Lỗi tải ảnh minh họa!')) {comment}"
            fixed_lines.append(new_line)
            found = True
            print(f"Found and fixed line: {line[:50]}...")
        else:
            fixed_lines.append(line)
    
    if not found:
        print("COULD NOT FIND THE PROBLEM LINE IN THE CLEANED CONTENT.")
        # Try a more aggressive regex search just in case
        full_content = "\n".join(fixed_lines)
        if comment in full_content:
             print("Found comment in content but not in the matched line loop. Using regex.")
             full_content = re.sub(r".*ui\.notify\('L.*" + re.escape(comment), 
                                   f"        self.img.on('error', lambda: ui.notify('Lỗi tải ảnh minh họa!')) {comment}", 
                                   full_content)
    else:
        full_content = "\n".join(fixed_lines)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    print("SUCCESS: File rewritten and fixed.")

except Exception as e:
    print(f"ERROR: {str(e)}")

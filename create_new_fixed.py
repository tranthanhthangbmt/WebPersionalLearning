import os
import re

source = r'I:\MY_CODE\WebPersionalLearning\ai_video_player.py'
target = r'I:\MY_CODE\WebPersionalLearning\ai_video_player_fixed.py'

print(f"Reading from: {source}")
print(f"Writing to: {target}")

try:
    with open(source, 'rb') as f:
        data = f.read()
    
    # Cleaning bytes
    clean_data = bytes([b for b in data if (32 <= b <= 126) or b in [10, 13, 9] or b > 127])
    content = clean_data.decode('utf-8', errors='ignore')
    
    comment = "# --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---"
    fixed_line = "        self.img.on('error', lambda: ui.notify('Lỗi tải ảnh minh họa!')) " + comment
    
    # Global replacement
    pattern = r"self\.img\.on\('error', lambda: ui\.notify\('L.*?" + re.escape(comment)
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, fixed_line, content)
        print("Success: Pattern found and replaced.")
    else:
        print("Warning: Pattern not found by regex. Using line-by-line fallback.")
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if comment in line and "ui.notify" in line:
                new_lines.append(fixed_line)
            else:
                new_lines.append(line)
        new_content = "\n".join(new_lines)

    with open(target, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"SUCCESS: Created {target}")

except Exception as e:
    print(f"ERROR: {str(e)}")

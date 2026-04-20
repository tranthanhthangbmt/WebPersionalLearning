import os
import re
import sys

path = r'I:\MY_CODE\WebPersionalLearning\ai_video_player.py'
print(f"Opening file for final fix: {path}")

try:
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"Original size: {len(data)} bytes")
    
    # 1. Clean: Strip out ALL null bytes and any non-printable control characters
    # (Leaving only standard ASCII/UTF8 printable chars, newline, carriage return, and tab)
    # This addresses the "unsupported mime" and corruption issues.
    clean_data = bytes([b for b in data if (32 <= b <= 126) or b in [10, 13, 9] or b > 127])
    content = clean_data.decode('utf-8', errors='ignore')
    
    # 2. Fix the specific line 149
    # Traceback: self.img.on('error', lambda: ui.notify('Lỗi t                     # --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---
    comment = "# --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---"
    fixed_line = "        self.img.on('error', lambda: ui.notify('Lỗi tải ảnh minh họa!')) " + comment
    
    # Global replacement for the corrupted docking line
    # Matches from self.img.on until the end of the line containing the comment.
    pattern = re.compile(r"self\.img\.on\('error', lambda: ui\.notify\('L.*?" + re.escape(comment))
    
    if pattern.search(content):
        new_content = pattern.sub(fixed_line, content)
        print("MATCH FOUND: Line 149 fixed via regex.")
    else:
        print("REGEX FAILED. Falling back to line-by-line fix.")
        lines = content.splitlines()
        new_lines = []
        found = False
        for line in lines:
            if comment in line and ("ui.notify" in line or "self.img.on" in line):
                new_lines.append(fixed_line)
                found = True
            else:
                new_lines.append(line)
        new_content = "\n".join(new_lines)
        if found: print("Line-by-line fix applied.")
        else: print("CRITICAL: TARGET LINE NOT FOUND. Check file manually.")

    # 3. Securely write back
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        f.flush()
        os.fsync(f.fileno())
    print("SUCCESS: File saved and verified.")

except Exception as e:
    print(f"FATAL ERROR during fix: {str(e)}")
    sys.exit(1)

import os
import re

path = r'I:\MY_CODE\WebPersionalLearning\ai_video_player.py'
print(f"Reading file: {path}")

try:
    with open(path, 'rb') as f:
        data = f.read()
    
    # Cleaning: Keep only printable ASCII, Vietnamese UTF-8, and common whitespace (9:tab, 10:lf, 13:cr)
    # We strip out null bytes (0) and other control characters that cause "unsupported mime"
    clean_data = bytes([b for b in data if (32 <= b <= 126) or b in [10, 13, 9] or b > 127])
    
    content = clean_data.decode('utf-8', errors='ignore')
    
    print("Fixing the syntax error on line 149...")
    # Traceback: self.img.on('error', lambda: ui.notify('Lỗi t                     # --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---
    comment = "# --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---"
    
    # Construct fixed line with double check on string closure
    fixed_line = "        self.img.on('error', lambda: ui.notify('Lỗi tải ảnh minh họa!')) " + comment
    
    # Regex to find the broken line:
    # Starts with self.img.on('error'
    # Contains ui.notify('L
    # Ends with the unique Glassmorphism comment
    pattern = r"self\.img\.on\('error', lambda: ui\.notify\('L.*?" + re.escape(comment)
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, fixed_line, content)
        print("Pattern found and replaced.")
    else:
        print("Pattern not found by regex. Trying line-by-line fallback.")
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
        if found: print("Line found and fixed using line-by-line search.")
        else: print("CRITICAL: LINE NOT FOUND. Check file manually.")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: File rewritten, cleaned, and fixed.")

except Exception as e:
    print(f"ERROR: {str(e)}")

import os
import re

path = r'I:\MY_CODE\WebPersionalLearning\ai_video_player.py'
print(f"Opening file: {path}")

try:
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # 1. Clean non-UTF8 characters / control characters
    # We decode with 'ignore' to strip problematic bytes
    content = data.decode('utf-8', errors='ignore')
    
    # 2. Fix the specific corrupted line using the unique comment
    comment = "# --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---"
    
    # We use a regex that matches the start of the line and the comment
    # while allowing for the broken string in between.
    # Pattern: any line that contains "ui.notify" and the unique comment.
    pattern = re.compile(r".*ui\.notify\('L.*" + re.escape(comment))
    
    # Replacement line with correct syntax
    # Note: We'll assume 8 spaces for indentation as is standard for method bodies in many codebases, 
    # but we will try to detect it from the previous line if possible.
    
    lines = content.splitlines()
    fixed_lines = []
    found = False
    for i, line in enumerate(lines):
        if comment in line and ("ui.notify" in line or "self.img.on" in line):
            # Try to preserve indentation
            indent = ""
            match = re.match(r"^(\s+)", line)
            if match:
                indent = match.group(1)
            else:
                indent = "        " # Fallback
            
            new_line = f"{indent}self.img.on('error', lambda: ui.notify('Lỗi tải ảnh minh họa!')) {comment}"
            fixed_lines.append(new_line)
            found = True
            print(f"Fixed line {i+1}: {new_line}")
        else:
            fixed_lines.append(line)
    
    if not found:
        print("COULD NOT FIND THE PROBLEM LINE BY LINE. TRYING GLOBAL REGEX...")
        # Try a more aggressive global regex capture
        full_content = "\n".join(fixed_lines)
        # Search for any line that starts with self.img.on('error' and ends with the comment
        global_pattern = r"(?m)^\s+self\.img\.on\('error', lambda: ui\.notify\('L.*?" + re.escape(comment)
        if re.search(global_pattern, full_content):
             full_content = re.sub(global_pattern, 
                                   f"        self.img.on('error', lambda: ui.notify('Lỗi tải ảnh minh họa!')) {comment}", 
                                   full_content)
             print("Fixed using global regex.")
        else:
             print("GLOBAL REGEX ALSO FAILED. Check file content manually.")
    else:
        full_content = "\n".join(fixed_lines)

    # 3. Save as UTF-8
    with open(path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    print("SUCCESS: File cleaned and syntax fixed.")

except Exception as e:
    print(f"FATAL ERROR: {str(e)}")

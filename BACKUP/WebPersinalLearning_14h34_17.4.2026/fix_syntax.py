import os
import re

path = r'I:\MY_CODE\WebPersionalLearning\ai_video_player.py'
with open(path, 'rb') as f:
    data = f.read()

# We look for the broken line. Note the traceback shows it starting with spaces.
# The traceback says line 149.
# We'll use a regex that matches the key elements and allows for varying whitespace.
# Traceback: self.img.on('error', lambda: ui.notify('Lỗi t                     # --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---

# Match: 
# 1. 'self.img.on'
# 2. 'error'
# 3. 'lambda: ui.notify'
# 4. 'Lỗi' (UTF-8: L\xe1\xbb\x97i)
# 5. 't'
# 6. Any number of spaces
# 7. '# --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---'

pattern = rb"self\.img\.on\('error', lambda: ui\.notify\('L\xe1\xbb\x97i t\s+# --- PROFESSIONAL PLAYER DOCK \(Glassmorphism\) ---"

# We'll replace it with a properly closed line.
# We'll assume the comment should stay there.
replacement = b"        self.img.on('error', lambda: ui.notify('L\xe1\xbb\x97i t\xe1\xba\xa3i \xe1\xba\xa3nh minh h\xe1\xbb\x8da!')) # --- PROFESSIONAL PLAYER DOCK (Glassmorphism) ---"

matches = re.findall(pattern, data)
if len(matches) == 1:
    new_data = re.sub(pattern, replacement, data)
    with open(path, 'wb') as f:
        f.write(new_data)
    print('SUCCESS: Fixed line 149')
else:
    print(f'FAILURE: Found {len(matches)} matches. Expected 1.')
    # If not found, let's try a simpler pattern
    pattern2 = rb"self\.img\.on\('error', lambda: ui\.notify\('L\xe1\xbb\x97i t"
    matches2 = re.findall(pattern2, data)
    print(f'Pattern 2 (simpler) found {len(matches2)} matches')
    if len(matches2) == 1:
        # If simpler pattern found, we look for the comment following it
        # and replace everything up to the end of that comment's line
        pattern3 = rb"self\.img\.on\('error', lambda: ui\.notify\('L\xe1\xbb\x97i t.*?# --- PROFESSIONAL PLAYER DOCK \(Glassmorphism\) ---"
        matches3 = re.findall(pattern3, data, re.DOTALL)
        if len(matches3) == 1:
             new_data = re.sub(pattern3, replacement, data, flags=re.DOTALL)
             with open(path, 'wb') as f:
                 f.write(new_data)
             print('SUCCESS: Fixed line 149 with pattern 3')

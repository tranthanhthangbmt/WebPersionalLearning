"""Fix indentation in main.py lines 2346-2352.

The render_3d_graph try-body is at 21 spaces.
Lines 2346-2352 are at 22 spaces but should be at 21.
"""

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines to fix (0-indexed): 2345 through 2351
# Line 2346 (idx 2345): 22 -> 21 spaces
# Line 2347 (idx 2346): 26 -> 25 spaces
# Line 2348 (idx 2347): 30 -> 29 spaces
# Line 2349 (idx 2348): 26 -> 25 spaces
# Line 2350 (idx 2349): 30 -> 29 spaces
# Line 2351 (idx 2350): 22 -> 21 spaces
# Line 2352 (idx 2351): 22 -> 21 spaces

fix_lines = [2345, 2346, 2347, 2348, 2349, 2350, 2351]  # 0-indexed

for idx in fix_lines:
    old_line = lines[idx]
    # Remove exactly 1 leading space
    if old_line.startswith(' '):
        lines[idx] = old_line[1:]
        old_sp = len(old_line) - len(old_line.lstrip(' '))
        new_sp = len(lines[idx]) - len(lines[idx].lstrip(' '))
        print(f"L{idx+1}: {old_sp} -> {new_sp} spaces | {lines[idx].strip()[:60]}")
    else:
        print(f"L{idx+1}: SKIPPED (no leading space)")

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\nDone! Verifying...")

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx in range(2343, 2358):
    line = lines[idx]
    spaces = len(line) - len(line.lstrip(' '))
    stripped = line.strip()
    if stripped:
        print(f"L{idx+1}: sp={spaces} | {stripped[:80]}")

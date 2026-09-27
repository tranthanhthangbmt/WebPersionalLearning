import os

path = r'i:\MY_CODE\WebPersionalLearning\main.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Look for the block
start_idx = -1
for i, line in enumerate(lines):
    if 'with ui.row().classes(\'w-full items-center px-4 py-3 bg-white border-b shadow-sm\'):' in line:
        start_idx = i - 1 # Include the "# Back button" comment if it exists above
        break

if start_idx != -1:
    # Delete from start_idx to start_idx + 6 (total 6 lines)
    # 1. # Back button
    # 2. with ui.row()...
    # 3. ui.button arrow_back
    # 4. ui.label
    # 5. ui.element flex-grow
    # 6. ui.button close
    
    # Let's verify the next few lines
    if 'ui.button(icon=\'arrow_back\'' in lines[start_idx+2]:
         print(f"Deleting lines {start_idx+1} to {start_idx+6}")
         del lines[start_idx:start_idx+6]
         with open(path, 'w', encoding='utf-8') as f:
             f.writelines(lines)
         print("Success")
    else:
         print(f"Verification failed at line {start_idx+3}: {lines[start_idx+2].strip()}")
else:
    print("Pattern not found")

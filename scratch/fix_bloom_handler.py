"""Fix the Graph Studio bloom_hub handler to use pending_bloom_nav mechanism."""
import re

with open(r'I:\MY_CODE\WebPersionalLearning\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all occurrences of bloom_hub action handlers
positions = []
start = 0
while True:
    idx = content.find("if action == 'bloom_hub':", start)
    if idx == -1:
        break
    positions.append(idx)
    start = idx + 1

print(f"Found {len(positions)} bloom_hub handlers")
for pos in positions:
    line_num = content[:pos].count('\n') + 1
    snippet = content[pos:pos+200].replace('\n', '\\n')
    print(f"  Line {line_num}: {snippet[:120]}...")

# We need to replace the SECOND occurrence (Graph Studio handler, around line 2339)
# The first one (Nexus) should already be fixed
# Let's check each one

lines = content.split('\n')

# Find line numbers for each occurrence
for pos in positions:
    line_num = content[:pos].count('\n') + 1
    # Check if this is the Graph Studio handler (has "from bloom_hub_page import build_bloom_hub_ui" nearby)
    nearby = content[pos:pos+500]
    if 'from bloom_hub_page import build_bloom_hub_ui' in nearby:
        print(f"\n>>> Graph Studio handler found at line {line_num} - NEEDS FIXING")
        
        # Find the end of this block (the 'return' statement at same indentation level)
        # Get the indentation of the if statement
        line_start = content.rfind('\n', 0, pos) + 1
        indent = pos - line_start
        
        # Find 'return' at the same indentation after this block
        search_start = pos
        block_end = None
        for i in range(line_num, min(line_num + 25, len(lines))):
            line = lines[i]
            stripped = line.strip()
            if stripped == 'return' and len(line) - len(line.lstrip()) == indent + 4:
                # indentation level of code inside the if block
                block_end = i
                break
        
        if block_end is not None:
            print(f"  Block ends at line {block_end + 1}: {lines[block_end]}")
            
            # Get the indentation from the original
            base_indent = ' ' * indent
            inner_indent = ' ' * (indent + 4)
            inner2_indent = ' ' * (indent + 8)
            
            # Build replacement
            new_lines = [
                f"{base_indent}if action == 'bloom_hub':",
                f"{inner_indent}import os",
                f"{inner_indent}subject_id = os.path.basename(json_file_path).replace('.json', '')",
                f"{inner_indent}# Use pending_bloom_nav mechanism to avoid context issues",
                f"{inner_indent}app.storage.user['pending_bloom_nav'] = {{",
                f"{inner2_indent}'subject_id': subject_id,",
                f"{inner2_indent}'node_id': raw_node_id,",
                f"{inner2_indent}'node_label': node_label,",
                f"{inner2_indent}'source': 'graph_studio',",
                f"{inner2_indent}'json_file_path': json_file_path,",
                f"{inner_indent}}}",
                f'{inner_indent}print(f"[Graph Studio] Đã đặt pending_bloom_nav cho node: {{raw_node_id}}")',
                f"{inner_indent}return",
            ]
            
            # Replace lines from line_num-1 to block_end (inclusive)
            lines[line_num-1:block_end+1] = new_lines
            print(f"  Replaced lines {line_num} to {block_end+1} with {len(new_lines)} new lines")
        else:
            print("  ERROR: Could not find block end")
    elif 'pending_bloom_nav' in nearby:
        line_num_real = content[:pos].count('\n') + 1
        print(f"\n>>> Already fixed handler at line {line_num_real}")
    else:
        line_num_real = content[:pos].count('\n') + 1
        print(f"\n>>> Unknown handler at line {line_num_real}")

# Write back
new_content = '\n'.join(lines)
with open(r'I:\MY_CODE\WebPersionalLearning\main.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\n✅ File saved successfully")

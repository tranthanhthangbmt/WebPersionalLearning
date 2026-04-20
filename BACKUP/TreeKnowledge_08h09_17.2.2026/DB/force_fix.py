import os

files_to_fix = [
    'MD2-120 câu_updated.csv',
    'MD5-120 câu_updated.csv'
]
target_lines = 121  # Header + 120 questions

with open('fix_log.txt', 'w', encoding='utf-8') as log:
    for file_name in files_to_fix:
        try:
            if not os.path.exists(file_name):
                log.write(f"{file_name}: Not Found\n")
                continue

            # Read all lines
            with open(file_name, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            original_count = len(lines)
            log.write(f"{file_name} Original: {original_count}\n")

            if original_count > target_lines:
                # Truncate
                new_lines = lines[:target_lines]
                
                # Write back
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                msg = f"{file_name} Truncated to: {len(new_lines)}\n"
                log.write(msg)
                print(msg)
            else:
                msg = f"{file_name} No change needed (count <= {target_lines})\n"
                log.write(msg)
                print(msg)

        except Exception as e:
            msg = f"Error processing {file_name}: {e}\n"
            log.write(msg)
            print(msg)

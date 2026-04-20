import os

files_to_fix = [
    'MD2-120 câu_updated.csv',
    'MD5-120 câu_updated.csv'
]
target_lines = 121  # Header + 120 questions

for file_name in files_to_fix:
    file_path = file_name
    backup_path = file_name + '.bak'
    
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        # Read lines
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"Processing {file_name}...")
        print(f"Original line count: {len(lines)}")

        if len(lines) <= target_lines:
            print(f"{file_name} is already within the target line count.")
        else:
            # Backup original
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"Backup created at {backup_path}")

            # Truncate
            new_lines = lines[:target_lines]
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"{file_name} truncated to {len(new_lines)} lines.")

    except Exception as e:
        print(f"Error processing {file_name}: {e}")

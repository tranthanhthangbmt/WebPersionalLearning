import os

file_path = 'MD2-120 câu_updated.csv'
backup_path = 'MD2-120 câu_updated.csv.bak'
target_lines = 121  # Header + 120 questions

try:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        exit(1)

    # Read lines
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Original line count: {len(lines)}")

    if len(lines) <= target_lines:
        print("File is already within the target line count.")
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
        print(f"File truncated to {len(new_lines)} lines.")

except Exception as e:
    print(f"Error: {e}")

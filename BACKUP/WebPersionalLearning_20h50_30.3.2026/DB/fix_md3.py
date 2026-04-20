import csv
import os

file_path = 'MD3-120 câu_updated.csv'
backup_path = 'MD3-120 câu_updated.csv.bak'

try:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        exit(1)

    # Read lines
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Original line count: {len(lines)}")

    # Deduplicate preserving order
    seen = set()
    unique_lines = []
    for line in lines:
        if line not in seen:
            unique_lines.append(line)
            seen.add(line)

    print(f"New line count: {len(unique_lines)}")

    # Backup original
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"Backup created at {backup_path}")

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(unique_lines)
    print("File updated successfully.")

except Exception as e:
    print(f"Error: {e}")

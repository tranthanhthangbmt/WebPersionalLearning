import csv
import os
import sys

file_path = 'MD3-120 câu_updated.csv'
output_file = 'analysis_result.txt'

try:
    with open(output_file, 'w', encoding='utf-8') as out:
        if not os.path.exists(file_path):
            msg = f"File not found: {file_path}"
            print(msg)
            out.write(msg)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                msg = f"Total lines: {len(lines)}\n"
                print(msg.strip())
                out.write(msg)
                
                unique_lines = set(lines)
                msg = f"Unique lines: {len(unique_lines)}\n"
                print(msg.strip())
                out.write(msg)
                
                non_empty = [l for l in lines if l.strip()]
                msg = f"Non-empty lines: {len(non_empty)}\n"
                print(msg.strip())
                out.write(msg)
                
                f.seek(0)
                reader = csv.reader(f)
                rows = list(reader)
                msg = f"CSV Rows: {len(rows)}\n"
                print(msg.strip())
                out.write(msg)

    sys.stdout.flush()

except Exception as e:
    print(f"Error: {e}")
    sys.stdout.flush()

import csv

input_file = 'd:/MY_CODE/AIUD_Module1_6-main/DB/MD3.csv'
output_file = 'd:/MY_CODE/AIUD_Module1_6-main/DB/MD3_cleaned.csv'

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep lines that are not just commas and whitespace
cleaned_lines = []
for line in lines:
    # Check if line has meaningful content
    # splitting by comma
    parts = line.strip().split(',')
    # If all parts are empty, skip
    if any(p.strip() for p in parts):
        cleaned_lines.append(line)

with open(input_file, 'w', encoding='utf-8') as f:
    f.writelines(cleaned_lines)

print(f"Cleaned {input_file}. Kept {len(cleaned_lines)} lines.")

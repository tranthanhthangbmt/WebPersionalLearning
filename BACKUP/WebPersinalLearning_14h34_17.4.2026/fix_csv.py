import os
import re

dir_path = r"i:\MY_CODE\WebPersionalLearning\DB\TMDT_Chuong1"

for file in os.listdir(dir_path):
    if file.startswith("Chuong_4_Tiet_") and file.endswith(".csv"):
        filepath = os.path.join(dir_path, file)
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        fixed_lines = []
        for i, line in enumerate(lines):
            # Parse CSV correctly or manually fix commas
            # In Question 25: 
            # 25,Module 4...
            # We can use regex to wrap text between commas in quotes if it's purely letters
            # But the easiest way is to use csv library with a clever heuristic?
            # Let's just wrap AAnswer, BAnswer, CAnswer, DAnswer, ResultAnswer, Explanation in quotes
            # Wait, since the file is small, let's just use regex to replace `, ` with ` - `
            # A common pattern for the unquoted commas is a comma followed by a space.
            # While true column delimiter is usually comma without space?
            # In line 26: `Dữ liệu mạng, Đường truyền cáp quang`
            line = line.replace(", ", " - ")
            fixed_lines.append(line)
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)
            
        print(f"Fixed {file}")

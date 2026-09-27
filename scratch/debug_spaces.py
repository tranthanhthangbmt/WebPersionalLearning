with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx in range(2340, 2355):
    line = lines[idx]
    spaces = len(line) - len(line.lstrip(' '))
    has_tab = line.startswith('\t')
    print(f"Line {idx+1}: spaces={spaces}, starts with tab={has_tab}, content={repr(line)}")

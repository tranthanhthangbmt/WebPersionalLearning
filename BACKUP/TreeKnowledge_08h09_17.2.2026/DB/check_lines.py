import os

files = [
    'MD2-120 câu_updated.csv',
    'MD5-120 câu_updated.csv'
]

with open('line_counts_result.txt', 'w') as out:
    for f_name in files:
        try:
            if os.path.exists(f_name):
                with open(f_name, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                out.write(f"{f_name}: {len(lines)}\n")
            else:
                out.write(f"{f_name}: Not Found\n")
        except Exception as e:
            out.write(f"{f_name}: Error {e}\n")

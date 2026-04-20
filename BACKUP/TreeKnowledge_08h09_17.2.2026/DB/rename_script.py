import os
import sys

# Change content to the DB directory
base_dir = r'd:/MY_CODE/AIUD_Module1_6-main/DB'
os.chdir(base_dir)

renames = [
    ('MD1-120 câu_updated.csv', 'MD1.csv'),
    ('MD2_fixed.csv', 'MD2.csv'),
    ('MD3-120 câu_updated.csv', 'MD3.csv'),
    ('MD4-120 câu_updated.csv', 'MD4.csv'),
    ('MD5-120 câu_updated.csv', 'MD5.csv'),
    ('MD6-120 câu_updated.csv', 'MD6.csv')
]

for old, new in renames:
    if os.path.exists(old):
        try:
            if os.path.exists(new):
                os.remove(new)
            os.rename(old, new)
            print(f"Renamed {old} to {new}")
        except Exception as e:
            print(f"Error renaming {old}: {e}")
    else:
        if os.path.exists(new):
            print(f"{new} already exists, skipping.")
        else:
            print(f"File {old} not found.")

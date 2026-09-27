import sqlite3
import os

db_path = r'I:\MY_CODE\WebPersionalLearning\pkt_research.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    print("Columns in 'user' table:")
    for col in columns:
        print(col[1])
    conn.close()

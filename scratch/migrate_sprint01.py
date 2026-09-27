"""Sprint 01: Database Migration Script
Adds Google OAuth fields to the User table.
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pkt_research.db')
print(f"Database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check existing columns
cursor.execute('PRAGMA table_info(user)')
existing_cols = {row[1] for row in cursor.fetchall()}
print(f"Existing columns: {existing_cols}")

# New columns to add
new_columns = [
    ("google_id", "TEXT DEFAULT ''"),
    ("google_avatar_url", "TEXT DEFAULT ''"),
    ("google_refresh_token", "TEXT DEFAULT ''"),
    ("drive_root_folder_id", "TEXT DEFAULT ''"),
    ("drive_subjects_folder_id", "TEXT DEFAULT ''"),
]

for col_name, col_type in new_columns:
    if col_name not in existing_cols:
        sql = f"ALTER TABLE user ADD COLUMN {col_name} {col_type}"
        cursor.execute(sql)
        print(f"  + Added column: {col_name}")
    else:
        print(f"  = Already exists: {col_name}")

conn.commit()
conn.close()
print("\nMigration completed successfully!")

import sqlite3
import os

DB_NAME = "user_progress.db"

def get_db_connection():
    """Tạo và trả về một kết nối đến CSDL SQLite."""
    # Thêm check_same_thread=False để tương thích với Streamlit
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Khởi tạo CSDL và tạo bảng 'user_progress' nếu chưa tồn tại."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_progress (
        username TEXT NOT NULL,
        skill_id TEXT NOT NULL,
        correct_count INTEGER NOT NULL,
        total_count INTEGER NOT NULL,
        PRIMARY KEY (username, skill_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Kết nối CSDL '{DB_NAME}' thành công.")

def update_user_progress(username, skill_id, is_correct):
    """
    Cập nhật (UPSERT) tiến trình của người dùng cho một kỹ năng cụ thể.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    correct_delta = 1 if is_correct else 0
    
    sql = '''
    INSERT INTO user_progress (username, skill_id, correct_count, total_count)
    VALUES (?, ?, ?, 1)
    ON CONFLICT(username, skill_id) DO UPDATE SET
        correct_count = correct_count + excluded.correct_count,
        total_count = total_count + 1
    '''
    
    try:
        c.execute(sql, (username, skill_id, correct_delta))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Lỗi khi cập nhật CSDL: {e}")
    finally:
        conn.close()

def get_user_progress(username):
    """
    Lấy toàn bộ tiến trình của người dùng từ CSDL và trả về
    dưới dạng dictionary.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    sql = '''
    SELECT skill_id, correct_count, total_count
    FROM user_progress
    WHERE username = ?
    '''
    
    user_mastery = {}
    try:
        c.execute(sql, (username,))
        rows = c.fetchall()
        
        for row in rows:
            user_mastery[row['skill_id']] = {
                'correct': row['correct_count'],
                'total': row['total_count']
            }
            
    except sqlite3.Error as e:
        print(f"Lỗi khi đọc CSDL: {e}")
    finally:
        conn.close()
        
    return user_mastery

if __name__ == "__main__":
    init_db()
import sqlite3

DB_PATH = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS chat_history(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER, role TEXT, content TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS user_files(user_id INTEGER PRIMARY KEY, file_name TEXT, summary TEXT)""")
    conn.commit()
    conn.close()

def save_message(user_id,role,content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
         "INSERT INTO chat_history(user_id, role, content) VALUES(?,?,?)",
        (user_id, role, content)
    )
    conn.commit()
    conn.close()

def load_memory(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role,content FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT 20",(user_id,))
    rows  = cursor.fetchall()
    conn.close()
    rows.reverse()
    return [{"role":r[0],"content":r[1]} for r in rows]

def save_file_summary(user_id, file_name, summary):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_files(user_id, file_name, summary) values (?,?,?)",(user_id, file_name,summary))
    conn.commit()
    conn.close()

def load_file_summary(user_id):
    conn=sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT file_name, summary FROM user_files WHERE user_id = ?",(user_id,))
    row = cursor.fetchone()
    conn.close()
    return row
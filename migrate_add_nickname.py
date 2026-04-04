"""
数据库迁移脚本：添加 nickname 字段到 User 表
运行方式：python migrate_add_nickname.py
"""
import sqlite3
import os

def migrate():
    db_path = os.path.join('instance', 'users.db')
    
    if not os.path.exists(db_path):
        print("数据库文件不存在，将在启动时自动创建")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'nickname' in columns:
        print("nickname 字段已存在，无需迁移")
        conn.close()
        return
    
    print("正在添加 nickname 字段...")
    cursor.execute("ALTER TABLE user ADD COLUMN nickname VARCHAR(50)")
    conn.commit()
    print("迁移完成！")
    
    conn.close()

if __name__ == '__main__':
    migrate()

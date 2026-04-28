import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE users ADD COLUMN mood_last_reset DATETIME")
    print("Column mood_last_reset added.")
except Exception as e:
    print(f"Error adding column: {e}")
conn.commit()
conn.close()

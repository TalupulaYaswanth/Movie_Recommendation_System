
import sqlite3

def migrate():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_owner BOOLEAN DEFAULT 0')
        print("Column is_owner added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column is_owner already exists.")
        else:
            print(f"Error: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()

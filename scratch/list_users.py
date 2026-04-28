
import sqlite3

def list_users():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, uid, email, is_owner FROM users")
        users = cursor.fetchall()
        
        print(f"\nTotal users in DB: {len(users)}")
        for u in users:
            print(f"ID: {u[0]} | UID: {u[1]} | Email: {u[2]} | Owner: {u[3]}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_users()

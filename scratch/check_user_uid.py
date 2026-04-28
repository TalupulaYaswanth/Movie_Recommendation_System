
import sqlite3

def check_user():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        uid = 'google-oauth2|117534782821107919424'
        cursor.execute("SELECT * FROM users WHERE uid=?", (uid,))
        user = cursor.fetchone()
        
        if user:
            # Get column names
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            user_dict = dict(zip(columns, user))
            print("\n[USER FOUND]")
            for k, v in user_dict.items():
                print(f"{k}: {v}")
        else:
            print(f"\n[USER NOT FOUND] UID: {uid}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_user()

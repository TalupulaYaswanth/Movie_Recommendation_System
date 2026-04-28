
import sqlite3

def set_owner():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_owner = 1 WHERE email = 'talupulayaswanth13@gmail.com'")
    if cursor.rowcount > 0:
        print("Updated existing user to Owner.")
    else:
        print("User not found in DB yet, but backend is ready for them.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    set_owner()

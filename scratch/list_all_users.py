
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'database.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- ALL REGISTERED USERS ---")
cursor.execute("SELECT uid, email, display_name, is_owner FROM users")
rows = cursor.fetchall()

if not rows:
    print("Database is empty.")
else:
    for r in rows:
        print(f"UID: {r[0]} | Email: {r[1]} | Name: {r[2]} | Owner: {r[3]}")

conn.close()

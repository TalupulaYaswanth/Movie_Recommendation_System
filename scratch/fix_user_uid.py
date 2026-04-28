
import sqlite3
import os

db_path = 'database.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

new_uid = 'EHsLmsw84COl4cc38eLNVnj0LYv1'
email = 'talupulayaswanth13@gmail.com'

cursor.execute("UPDATE users SET uid = ? WHERE email = ?", (new_uid, email))
if cursor.rowcount > 0:
    print(f"Successfully updated UID for {email} to {new_uid}")
else:
    print(f"User with email {email} not found.")

conn.commit()
conn.close()

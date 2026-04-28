
import sqlite3
import os

# Connect to the real database
db_path = os.path.join(os.path.dirname(__file__), '..', 'database.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# The specific details the user wants to authorize
NEW_UID = 'google-oauth2|117534782821107919424'
NEW_EMAIL = 'talupulayaswanth13@gmail.com'
NEW_NAME = 'Yaswanth (Owner)'

print(f"--- DATABASE OWNER UPDATE ---")

# 1. Update the existing owner to the new UID format
print(f"Transferring owner privileges to UID: {NEW_UID}")
cursor.execute("UPDATE users SET uid=? WHERE email=?", (NEW_UID, NEW_EMAIL))

# If no user had that email, insert it
if cursor.rowcount == 0:
    print(f"No existing user found with email {NEW_EMAIL}. Creating new entry...")
    cursor.execute("""
        INSERT INTO users (uid, email, display_name, is_owner, blocked)
        VALUES (?, ?, ?, 1, 0)
    """, (NEW_UID, NEW_EMAIL, NEW_NAME))
else:
    print(f"Successfully migrated UID for {NEW_EMAIL}")

conn.commit()

# Verify the result
cursor.execute("SELECT uid, email, is_owner FROM users WHERE is_owner=1")
print("\n--- CURRENT OWNERS IN DATABASE ---")
for row in cursor.fetchall():
    print(f"UID: {row[0]} | Email: {row[1]} | Owner: {row[2]}")

conn.close()
print("\nDatabase updated successfully!")

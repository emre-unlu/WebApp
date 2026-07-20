import sqlite3

from config import DB_PATH


#Retrn a user row with given id
#Used in flask login loader
def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT * FROM users WHERE id = ?'
    cursor.execute(sql, (user_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row

#Return user with given username
#used in auth login to check uniqueness at registeration
def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT * FROM users WHERE username = ?'
    cursor.execute(sql, (username,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row

#Inserts new user 
def create_user(username, password_hash, role):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    new_id = None
    sql = 'INSERT INTO users(username, password_hash, role) VALUES(?, ?, ?)'
    try:
        cursor.execute(sql, (username, password_hash, role))
        conn.commit()
        new_id = cursor.lastrowid
    except Exception as e:
        print('ERROR', str(e))
        # if something goes wrong: rollback
        conn.rollback()

    cursor.close()
    conn.close()

    return new_id

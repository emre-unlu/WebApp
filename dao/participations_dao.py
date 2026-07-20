import sqlite3

from config import DB_PATH

#returns this users booking on this seesion or none
#Busineess layer deals with its a join or change (no row yet or row already exists)
def get_participation(user_id, session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT * FROM participations WHERE user_id = ? AND session_id = ?'
    cursor.execute(sql, (user_id, session_id))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row

#Every booking of one adventurer
#Powers my jobs profile page
def get_participations_for_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = '''SELECT p.*,
                    s.day, s.start_time, s.location,
                    q.code, q.title, q.job_type, q.difficulty, q.duration_min
               FROM participations p
               JOIN sessions s ON s.id = p.session_id
               JOIN quests   q ON q.id = s.quest_id
              WHERE p.user_id = ?
              ORDER BY s.day, s.start_time'''
    cursor.execute(sql, (user_id,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

#Every booking of a session
#Powers guild masters per session stats
def get_participations_for_session(session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = '''SELECT p.*, u.username
               FROM participations p
               JOIN users u ON u.id = p.user_id
              WHERE p.session_id = ?'''
    cursor.execute(sql, (session_id,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

#Total places reserved for one role on one session
#Budineess layer checks role capacity
def get_places_taken(session_id, role):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = '''SELECT COALESCE(SUM(places), 0) AS taken
               FROM participations
              WHERE session_id = ? AND role = ?'''
    cursor.execute(sql, (session_id, role))
    taken = cursor.fetchone()['taken']

    cursor.close()
    conn.close()

    return taken

#How many sessions this adventurer has joined
#Gets the requirement 3 per week
def count_sessions_for_user(user_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT COUNT(*) AS n FROM participations WHERE user_id = ?'
    cursor.execute(sql, (user_id,))
    n = cursor.fetchone()['n']

    cursor.close()
    conn.close()

    return n

#day + starttime + duration of every session this adventurer is in
#Business layer build intervals from these to reject joining a session that overlaps one they already booked
def get_user_session_times(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = '''SELECT s.id, s.day, s.start_time, q.duration_min
               FROM participations p
               JOIN sessions s ON s.id = p.session_id
               JOIN quests   q ON q.id = s.quest_id
              WHERE p.user_id = ?'''
    cursor.execute(sql, (user_id,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

#Insert booking 
#The UNIQUE(user_id,session_id) constraint avoids users already booked 
def create_participation(user_id, session_id, role, places):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    new_id = None
    sql = '''INSERT INTO participations(user_id, session_id, role, places)
             VALUES(?, ?, ?, ?)'''
    try:
        cursor.execute(sql, (user_id, session_id, role, places))
        conn.commit()
        new_id = cursor.lastrowid
    except Exception as e:
        print('ERROR', str(e))
        # if something goes wrong: rollback
        conn.rollback()

    cursor.close()
    conn.close()

    return new_id

# Change the role and places of an existing booking
#Business layer checks 8 hour rule and capacity beforehand so this is safe
def update_participation(user_id, session_id, role, places):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    success = False
    sql = '''UPDATE participations SET role = ?, places = ?
              WHERE user_id = ? AND session_id = ?'''
    try:
        cursor.execute(sql, (role, places, user_id, session_id))
        conn.commit()
        success = True
    except Exception as e:
        print('ERROR', str(e))
        # if something goes wrong: rollback
        conn.rollback()

    cursor.close()
    conn.close()

    return success

#Cancel a booking 
#Business layer check 8 hour before rule
def delete_participation(user_id, session_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    success = False
    sql = 'DELETE FROM participations WHERE user_id = ? AND session_id = ?'
    try:
        cursor.execute(sql, (user_id, session_id))
        conn.commit()
        success = True
    except Exception as e:
        print('ERROR', str(e))
        # if something goes wrong: rollback
        conn.rollback()

    cursor.close()
    conn.close()

    return success

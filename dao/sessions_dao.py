import sqlite3

from config import DB_PATH

_SESSION_OVERVIEW = '''
    SELECT s.*,
           q.code, q.title, q.job_type, q.difficulty,
           q.duration_min, q.description, q.image,
           COALESCE(SUM(CASE WHEN p.role = 'gunman' THEN p.places END), 0) AS gunman_taken,
           COALESCE(SUM(CASE WHEN p.role = 'driver' THEN p.places END), 0) AS driver_taken,
           COALESCE(SUM(CASE WHEN p.role = 'hacker' THEN p.places END), 0) AS hacker_taken
      FROM sessions s
      JOIN quests q              ON q.id = s.quest_id
      LEFT JOIN participations p ON p.session_id = s.id
'''


#Every session with quest info, reserved counts, ordered by day then start time
#Homepage and job board
def get_all_sessions_overview():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = _SESSION_OVERVIEW + ' GROUP BY s.id ORDER BY s.day, s.start_time'
    cursor.execute(sql)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


#All sessions of one quest
#Used in the session details page
def get_sessions_for_quest(quest_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = _SESSION_OVERVIEW + ' WHERE s.quest_id = ? GROUP BY s.id ORDER BY s.day, s.start_time'
    cursor.execute(sql, (quest_id,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

#One session info with given id
#Used in the session details page
def get_session_overview_by_id(session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = _SESSION_OVERVIEW + ' WHERE s.id = ? GROUP BY s.id'
    cursor.execute(sql, (session_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row


#Gets a session by given day and loaction
#Used in filter
def get_sessions_by_day_location(day, location):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = '''SELECT s.id, s.start_time, q.duration_min
               FROM sessions s
               JOIN quests q ON q.id = s.quest_id
              WHERE s.day = ? AND s.location = ?'''
    cursor.execute(sql, (day, location))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


#Created a one scheduled run 
def create_session(quest_id, day, start_time, location):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    new_id = None
    sql = '''INSERT INTO sessions(quest_id, day, start_time, location)
             VALUES(?, ?, ?, ?)'''
    try:
        cursor.execute(sql, (quest_id, day, start_time, location))
        conn.commit()
        new_id = cursor.lastrowid
    except Exception as e:
        print('ERROR', str(e))
        conn.rollback()

    cursor.close()
    conn.close()

    return new_id

#Updated a session by given id
def update_session(session_id, day, start_time, location):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    success = False
    sql = 'UPDATE sessions SET day = ?, start_time = ?, location = ? WHERE id = ?'
    try:
        cursor.execute(sql, (day, start_time, location, session_id))
        conn.commit()
        success = True
    except Exception as e:
        print('ERROR', str(e))
        # if something goes wrong: rollback
        conn.rollback()

    cursor.close()
    conn.close()

    return success

#Deletes a run
def delete_session(session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    success = False
    sql = 'DELETE FROM sessions WHERE id = ?'
    try:
        cursor.execute(sql, (session_id,))
        conn.commit()
        success = True
    except Exception as e:
        print('ERROR', str(e))
        conn.rollback()

    cursor.close()
    conn.close()

    return success

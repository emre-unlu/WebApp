# dao/quests_dao.py - all database access for the `quests` table (the heist
# "templates"). A quest is immutable once created, so there is no update here.
import sqlite3

from config import DB_PATH

#Return every quest newest id first
#Used by guild master planner
def get_all_quests():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT * FROM quests ORDER BY id DESC'
    cursor.execute(sql)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

#Return the quest by id if not None
def get_quest_by_id(quest_id):
   
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT * FROM quests WHERE id = ?'
    cursor.execute(sql, (quest_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row

#Return quest row with this code or none 
def get_quest_by_code(code):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT * FROM quests WHERE code = ?'
    cursor.execute(sql, (code,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row

#Insert new quest
def create_quest(code, title, duration_min, job_type, difficulty, description,
                 image, created_by):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    new_id = None
    sql = '''INSERT INTO quests(code, title, duration_min, job_type,
                                difficulty, description, image, created_by)
             VALUES(?, ?, ?, ?, ?, ?, ?, ?)'''
    try:
        cursor.execute(sql, (code, title, duration_min, job_type, difficulty,
                             description, image, created_by))
        conn.commit()
        new_id = cursor.lastrowid
    except Exception as e:
        print('ERROR', str(e))
        # if something goes wrong: rollback
        conn.rollback()

    cursor.close()
    conn.close()

    return new_id

#Create a quest with given session. So 2 tables are updated
#Runs is a list of day starttime location tuples
def create_quest_with_sessions(code, title, duration_min, job_type, difficulty,
                               description, image, created_by, runs):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    new_id = None
    sql_quest = '''INSERT INTO quests(code, title, duration_min, job_type,
                                      difficulty, description, image, created_by)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?)'''
    sql_session = '''INSERT INTO sessions(quest_id, day, start_time, location)
                     VALUES(?, ?, ?, ?)'''
    try:
        cursor.execute(sql_quest, (code, title, duration_min, job_type,
                                   difficulty, description, image, created_by))
        quest_id = cursor.lastrowid
        for day, start_time, location in runs:
            cursor.execute(sql_session, (quest_id, day, start_time, location))
        conn.commit()
        new_id = quest_id
    except Exception as e:
        print('ERROR', str(e))
        # if something goes wrong: rollback (quest AND sessions disappear together)
        conn.rollback()

    cursor.close()
    conn.close()

    return new_id

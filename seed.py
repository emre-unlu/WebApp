# seed.py - Fills the database with GTA-style sample data for the instructors.
# Run with:  python seed.py
# It rebuilds the schema first, so it always produces the same clean data set.
#
# Simulated NOW (config.py): Wednesday 20:00
# Booking lock rule: a participation can be changed only while the run starts
# more than 8 hours from now  ->  everything starting before Thu 04:00 is locked.

import os
import sqlite3

from werkzeug.security import generate_password_hash

from config import BASE_DIR, DB_PATH

SCHEMA_PATH = os.path.join(BASE_DIR, "db", "schema.sql")

# username, password, role
USERS = [
    ("lester",   "lester123",   "guild_master"),
    ("franklin", "franklin123", "adventurer"),
    ("michael",  "michael123",  "adventurer"),
    ("trevor",   "trevor123",   "adventurer"),
    ("lamar",    "lamar123",    "adventurer"),
]

# code, title, duration_min, job_type, difficulty, description, image, created_by
# created_by = (1, lester); images live in static/img.
# Each quest is themed to one place and is only ever scheduled there, so the
# promo image on a run always matches the location of the run.
QUESTS = [
    # Pacific Standard Bank
    ("NS-0031", "Wire Transfer", 60, "Stealth", 2,
     "After-hours visit to Pacific Standard. Open the wire desk, "
     "move the money, leave the vault untouched. Sneaky-peaky like.", "pacific_standard.jpg", 1),
    ("NS-0666", "The Pacific Standard Job", 120, "Big Score", 5,
     "The big one. The vault of the Pacific Standard Bank in the "
     "middle of downtown. Retirement money.", "pacific_standard.jpg", 1),
    # Diamond Casino
    ("NS-0172", "Loose Diamonds", 60, "Smash & Grab", 3,
     "The Diamond's display floor. Smash the cases, bag the diamonds, "
     "be gone before security picks up the phone. Loud one.", "diamond_casino.jpg", 1),
    ("NS-0308", "Silent & Sneaky", 90, "Stealth", 4,
     "Into the Diamond Casino vault through the staff door. Night "
     "vision, suppressors, and absolute silence. Nobody notices?", "diamond_casino.jpg", 1),
    # Union Depository
    ("NS-0450", "Gold Convoy", 75, "Transport", 3,
     "Gold bricks leave the Union Depository loading dock tonight. "
     "Track them with helicopter. Get the bricks and run.", "union_depository.jpg", 1),
    ("NS-0245", "The Union Depository Contract", 120, "Loud", 4,
     "Straight through the front door of the Union Depository. "
     "Expect NOISE, expect a war on the way out. Enough money to buy a mansion if Lester doesn't take 50%", "union_depository.jpg", 1),
]


SESSIONS = [
    (1, 0, "10:00", "Pacific Standard Bank"),   #   Mon - locked (past)
    (3, 0, "21:00", "Diamond Casino"),          #   Mon - locked (past)
    (6, 1, "14:00", "Union Depository"),        #   Tue - locked (past)
    (4, 1, "22:00", "Diamond Casino"),          #   Tue - locked (past)
    (1, 2, "09:00", "Pacific Standard Bank"),   #   Wed - locked (already ran today)
    (5, 2, "23:00", "Union Depository"),        #   Wed - locked (starts in 3h < 8h rule)
    (2, 3, "10:00", "Pacific Standard Bank"),   #   Thu - open, NO participants -> Guild master can move/cancel
    (6, 3, "20:00", "Union Depository"),        #   Thu - open, hacker slots FULL
    (4, 4, "15:00", "Diamond Casino"),          #   Fri - open
    (1, 4, "19:00", "Pacific Standard Bank"),   #   Fri - open
    (5, 5, "11:00", "Union Depository"),        #   Sat - open
    (2, 5, "21:00", "Pacific Standard Bank"),   #   Sat - open
    (3, 6, "12:00", "Diamond Casino"),          #   Sun - open
    (6, 6, "18:00", "Union Depository"),        #   Sun - open
]

# user_id, session_id, role, places
PARTICIPATIONS = [
    
    (3, 2, "gunman", 1),   
    (4, 4, "driver", 1),  
    (2, 6, "gunman", 2),
    
    (2, 8, "hacker", 1),  
    (5, 8, "hacker", 1),   
    (3, 8, "gunman", 1),   
    (4, 9, "driver", 1),  
    (5, 12, "gunman", 1),  
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fresh tables every run
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    for username, password, role in USERS:
        cursor.execute(
            "INSERT INTO users(username, password_hash, role) VALUES(?, ?, ?)",
            (username, generate_password_hash(password), role))

    cursor.executemany(
        '''INSERT INTO quests(code, title, duration_min, job_type,
                              difficulty, description, image, created_by)
           VALUES(?, ?, ?, ?, ?, ?, ?, ?)''', QUESTS)

    cursor.executemany(
        '''INSERT INTO sessions(quest_id, day, start_time, location)
           VALUES(?, ?, ?, ?)''', SESSIONS)

    cursor.executemany(
        '''INSERT INTO participations(user_id, session_id, role, places)
           VALUES(?, ?, ?, ?)''', PARTICIPATIONS)

    conn.commit()
    cursor.close()
    conn.close()

    print("Seeded:", len(USERS), "users,", len(QUESTS), "quests,",
          len(SESSIONS), "sessions,", len(PARTICIPATIONS), "participations.")


if __name__ == "__main__":
    seed()

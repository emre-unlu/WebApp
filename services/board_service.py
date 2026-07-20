from dao import sessions_dao
from services import rules, clock

# The five job types
JOB_TYPES = ("Stealth", "Loud", "Smash & Grab", "Transport", "Big Score")


#Return one session row from dao into dict
#The remaining places of the roles
#Total open slots
#Whether the run is locked (If 0 slots left or inside the 8-hour freeze)
def decorate_session(row):
    s = dict(row)
    s["gunman_left"] = rules.remaining_places("gunman", s["gunman_taken"])
    s["driver_left"] = rules.remaining_places("driver", s["driver_taken"])
    s["hacker_left"] = rules.remaining_places("hacker", s["hacker_taken"])
    s["open_slots"] = s["gunman_left"] + s["driver_left"] + s["hacker_left"]
    s["has_started"] = rules.has_started(s["day"], s["start_time"])
    # The freeze window also covers runs that have already started.
    s["is_locked"] = s["open_slots"] == 0 or \
        not rules.can_modify_participation(s["day"], s["start_time"])
    s["day_name"] = clock.DAY_NAMES[s["day"]]
    return s


#One session by id , none if not exits 
#Used in the session details page and guild master edit page
def get_session(session_id):
    row = sessions_dao.get_session_overview_by_id(session_id)
    if row is None:
        return None
    return decorate_session(row)


#Every run of one quest ordered by day and start time
#Used in the details page scheduled runs list
def get_quest_runs(quest_id):
    runs = []
    for row in sessions_dao.get_sessions_for_quest(quest_id):
        runs.append(decorate_session(row))
    return runs


#Gets all sessions and then filter them based on the inputs
def get_board(day=None, job_type=None, min_difficulty=None, role=None, location=None):
    board = []
    for row in sessions_dao.get_all_sessions_overview():
        s = decorate_session(row)
        if day is not None and s["day"] != day:
            continue
        if job_type is not None and s["job_type"] != job_type:
            continue
        if min_difficulty is not None and s["difficulty"] < min_difficulty:
            continue
        if role is not None and s[role + "_left"] <= 0:
            continue
        if location is not None and s["location"] != location:
            continue
        board.append(s)
    return board

#gets the stats of the board title how many scheduled this week and how many are them are open or locked
def board_stats():
    total = 0
    locked = 0
    for row in sessions_dao.get_all_sessions_overview():
        s = decorate_session(row)
        total += 1
        if s["is_locked"]:
            locked += 1
    return {"total": total, "open": total - locked, "locked": locked}

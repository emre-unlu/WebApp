# services/quest_service.py - BUSINESS layer for what the Guild Master does to
# the schedule: create quests with their runs, move or cancel a run.
# The one hard rule everywhere: each location hosts one run at a time.
import random

from dao import quests_dao, sessions_dao
from services import rules, clock

# The three locations, used consistently across the whole application.
LOCATIONS = ("Pacific Standard Bank", "Diamond Casino", "Union Depository")

#Generate a code NS-XXXX with random numbers and check if its exists
def _new_code():
    while True:
        code = "NS-%04d" % random.randint(1, 9999)
        if quests_dao.get_quest_by_code(code) is None:
            return code

#Crate a quest and schedule all its runs at once
#Runs is a list of day starttime location already format checked by app.py
#Rules enforced by business : at least one run, no run may clash with existing run at the same location, the new runs may not clash with each other
def create_quest(created_by, title, duration_min, job_type, difficulty,
                 description, image, runs):

    if len(runs) == 0:
        return None, "Schedule at least one run."

    # Each new run vs. the runs already in the database.
    for day, start_time, location in runs:
        if location_conflict(day, start_time, duration_min, location):
            return None, location + " already hosts a run at that time."

    # Each new run vs. the other new runs (the database can't see these yet).
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            day_a, time_a, loc_a = runs[i]
            day_b, time_b, loc_b = runs[j]
            if day_a == day_b and loc_a == loc_b:
                start_a = clock.to_week_minutes(day_a, time_a)
                start_b = clock.to_week_minutes(day_b, time_b)
                if rules.intervals_overlap(start_a, duration_min, start_b, duration_min):
                    return None, "Two of your new runs overlap at " + loc_a + "."

    quest_id = quests_dao.create_quest_with_sessions(
        _new_code(), title, duration_min, job_type, difficulty,
        description, image, created_by, runs)
    if quest_id is None:
        return None, "Could not save the quest, please try again."
    return quest_id, None

#True if a run would overlap existing run at SAME LOCATION AT SAME DAY
def location_conflict(day, start_time, duration_min, location, ignore_session_id=None):

    new_start = clock.to_week_minutes(day, start_time)
    for other in sessions_dao.get_sessions_by_day_location(day, location):
        if other["id"] == ignore_session_id:
            continue
        other_start = day * clock.MINUTES_PER_DAY + clock.time_to_minutes(other["start_time"])
        if rules.intervals_overlap(new_start, duration_min,
                                   other_start, other["duration_min"]):
            return True
    return False

#Move run to a new day time location
#Allowed when no adventurer has joined and the new slot must not clash with another run at that location
def update_session(session_id, day, start_time, location):
    session = sessions_dao.get_session_overview_by_id(session_id)
    if session is None:
        return False, "This run does not exist."

    reserved = session["gunman_taken"] + session["driver_taken"] + session["hacker_taken"]
    if not rules.can_edit_session(reserved):
        return False, "Adventurers already joined - this run can no longer be modified."

    if location not in LOCATIONS:
        return False, "Unknown location."

    if location_conflict(day, start_time, session["duration_min"], location,
                         ignore_session_id=session_id):
        return False, location + " already hosts a run at that time."

    if not sessions_dao.update_session(session_id, day, start_time, location):
        return False, "Could not save the changes, please try again."
    return True, None

#Cancel a run only when no adventurer has joined
def cancel_session(session_id):
    session = sessions_dao.get_session_overview_by_id(session_id)
    if session is None:
        return False, "This run does not exist."

    reserved = session["gunman_taken"] + session["driver_taken"] + session["hacker_taken"]
    if not rules.can_edit_session(reserved):
        return False, "Adventurers already joined - this run can no longer be cancelled."

    if not sessions_dao.delete_session(session_id):
        return False, "Could not cancel the run, please try again."
    return True, None

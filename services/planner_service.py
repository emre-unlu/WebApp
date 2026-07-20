from dao import quests_dao, sessions_dao
from services import board_service, rules

#The decorated how many left for the roles, total how many left, if it can be editable
def _decorate_run(row):
    """A planner run = a board session + the numbers the Guild Master needs:
    total reserved places, the most requested role, and whether the run can
    still be edited/cancelled (= nobody joined yet)."""
    run = board_service.decorate_session(row)
    run["reserved_total"] = run["gunman_taken"] + run["driver_taken"] + run["hacker_taken"]
    run["can_edit"] = rules.can_edit_session(run["reserved_total"])

    if run["reserved_total"] == 0:
        run["top_role"] = None  # no bookings yet
    else:
        # max() on a dict compares by value via key=, returning the role name.
        taken_by_role = {"Gunman": run["gunman_taken"],
                         "Driver": run["driver_taken"],
                         "Hacker": run["hacker_taken"]}
        run["top_role"] = max(taken_by_role, key=taken_by_role.get)
    return run

#Returns groups and stats.
#One group per quest with its decorated runs, plus the global number for the stat strip
def get_planner_view():
    groups = []
    stats = {"quests": 0, "runs": 0, "open": 0, "locked": 0, "reserved": 0}

    for quest in quests_dao.get_all_quests():
        runs = []
        open_count = 0
        for row in sessions_dao.get_sessions_for_quest(quest["id"]):
            run = _decorate_run(row)
            runs.append(run)
            stats["runs"] += 1
            stats["reserved"] += run["reserved_total"]
            if run["is_locked"]:
                stats["locked"] += 1
            else:
                stats["open"] += 1
                open_count += 1

        groups.append({"quest": quest, "runs": runs, "open_count": open_count})
        stats["quests"] += 1

    return groups, stats

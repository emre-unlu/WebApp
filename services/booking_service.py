from dao import sessions_dao, participations_dao
from services import rules, clock

MAX_SESSIONS_PER_WEEK = 3

#This users booking row
def get_booking(user_id, session_id):
    
    return participations_dao.get_participation(user_id, session_id)

#Every booking of on eadventurer 
#Have the can modify flag
#used in my jobs page
def get_user_bookings(user_id):
    bookings = []
    for row in participations_dao.get_participations_for_user(user_id):
        booking = dict(row)
        booking["day_name"] = clock.DAY_NAMES[booking["day"]]
        booking["can_modify"] = rules.can_modify_participation(
            booking["day"], booking["start_time"])
        bookings.append(booking)
    return bookings

#Try to reserve places in role on one session
#Return true or false and a reason
def join_session(user_id, session_id, role, places):

    session = sessions_dao.get_session_overview_by_id(session_id)
    if session is None:
        return False, "This run does not exist."

    # 1. No joining a run that has already started.
    if rules.has_started(session["day"], session["start_time"]):
        return False, "This run has already started."

    # 1.1. New bookings freeze at the same 8-hour deadline as changes.
    if not rules.can_modify_participation(session["day"], session["start_time"]):
        return False, "Too late - bookings freeze 8 hours before the run starts."

    # 2. Role and places must be valid the form limits these too, but the
    #    business layer is the one that cannot be bypassed.
    if role not in rules.ROLE_CAPACITY:
        return False, "Unknown role."
    if places not in (1, 2):
        return False, "You can reserve 1 or 2 places."

    # 3. One booking per adventurer per run .
    if participations_dao.get_participation(user_id, session_id) is not None:
        return False, "You are already on this run."

    # 4. The chosen role must still have enough free places.
    taken = participations_dao.get_places_taken(session_id, role)
    if rules.remaining_places(role, taken) < places:
        return False, "Not enough " + role + " places left on this run."

    # 5. At most 3 runs per week.
    if participations_dao.count_sessions_for_user(user_id) >= MAX_SESSIONS_PER_WEEK:
        return False, "You already joined 3 runs this week."

    # 6. No overlap in time with a run the adventurer already joined.
    new_start = clock.to_week_minutes(session["day"], session["start_time"])
    for other in participations_dao.get_user_session_times(user_id):
        other_start = clock.to_week_minutes(other["day"], other["start_time"])
        if rules.intervals_overlap(new_start, session["duration_min"],
                                   other_start, other["duration_min"]):
            return False, "This run overlaps another run you already joined."

    # All rules passed - write the booking.
    if participations_dao.create_participation(user_id, session_id, role, places) is None:
        return False, "Could not save the booking, please try again."
    return True, None


#Change the participation of existing booking
#Have the 8 hour rule
#and also other requirements such as capacity
def change_participation(user_id, session_id, role, places):
    session = sessions_dao.get_session_overview_by_id(session_id)
    if session is None:
        return False, "This run does not exist."

    booking = participations_dao.get_participation(user_id, session_id)
    if booking is None:
        return False, "You are not on this run."

    # The 8-hour freeze.
    if not rules.can_modify_participation(session["day"], session["start_time"]):
        return False, "Too late - bookings freeze 8 hours before the run starts."

    if role not in rules.ROLE_CAPACITY:
        return False, "Unknown role."
    if places not in (1, 2):
        return False, "You can reserve 1 or 2 places."

    # Capacity check for the new role. If the adventurer keeps the same role,
    # their own current places are about to be released, so they don't count.
    taken = participations_dao.get_places_taken(session_id, role)
    if role == booking["role"]:
        taken = taken - booking["places"]
    if rules.remaining_places(role, taken) < places:
        return False, "Not enough " + role + " places left on this run."

    if not participations_dao.update_participation(user_id, session_id, role, places):
        return False, "Could not update the booking, please try again."
    return True, None

#Deletes existing participation from user 
def cancel_participation(user_id, session_id):
    session = sessions_dao.get_session_overview_by_id(session_id)
    if session is None:
        return False, "This run does not exist."

    if participations_dao.get_participation(user_id, session_id) is None:
        return False, "You are not on this run."

    if not rules.can_modify_participation(session["day"], session["start_time"]):
        return False, "Too late - bookings freeze 8 hours before the run starts."

    if not participations_dao.delete_participation(user_id, session_id):
        return False, "Could not cancel the booking, please try again."
    return True, None
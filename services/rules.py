from services import clock

# How many places each role offers on a session. This is a fixed policy, so it
# lives here in code rather than as a column in the database.
ROLE_CAPACITY = {"gunman": 4, "driver": 3, "hacker": 2}

# A booking can only be changed or cancelled while the session is still more
# than this many hours away.
MODIFY_DEADLINE_HOURS = 8


# Places / capacity

def remaining_places(role, taken):
    return ROLE_CAPACITY[role] - taken


def is_role_full(role, taken):
    return remaining_places(role, taken) <= 0


def open_slots(gunman_taken, driver_taken, hacker_taken):
    return (remaining_places("gunman", gunman_taken)
            + remaining_places("driver", driver_taken)
            + remaining_places("hacker", hacker_taken))


def is_session_full(gunman_taken, driver_taken, hacker_taken):
    return open_slots(gunman_taken, driver_taken, hacker_taken) <= 0


# Time-based rules (use the simulated clock)
def has_started(day, start_time):
    return clock.hours_until(day, start_time) <= 0


#The 8 hour rule of the exam
def can_modify_participation(day, start_time):
    return clock.hours_until(day, start_time) > MODIFY_DEADLINE_HOURS

#The overlap rule 
def intervals_overlap(start_a, duration_a, start_b, duration_b):

    end_a = start_a + duration_a
    end_b = start_b + duration_b
    return start_a < end_b and start_b < end_a



#Cheks if the run can be modified
def can_edit_session(participant_count):
    """A run may be modified or cancelled only while no adventurer has joined."""
    return participant_count == 0
from config import SIMULATED_NOW_DAY, SIMULATED_NOW_TIME

MINUTES_PER_DAY = 24 * 60  # 1440

# Display names for the fictional week, indexed by day number 0..6.
DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


#Turns HH:MM into minutes
def time_to_minutes(time_str):
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)

#Turn (day, 'HH:MM') into minutes
def to_week_minutes(day, time_str):
    return day * MINUTES_PER_DAY + time_to_minutes(time_str)

#Simulated NOW
def now_week_minutes():
    return to_week_minutes(SIMULATED_NOW_DAY, SIMULATED_NOW_TIME)

#Calculates how many hours from now to the given session (Calculate 8 hours req)
def hours_until(day, time_str):
    return (to_week_minutes(day, time_str) - now_week_minutes()) / 60

#Acceptable strings are such as 9:00 or 23:00
def is_valid_time(text):
    
    if len(text) != 5 or text[2] != ":":
        return False
    hours, minutes = text[:2], text[3:]
    if not (hours.isdigit() and minutes.isdigit()):
        return False
    return int(hours) <= 23 and int(minutes) <= 59
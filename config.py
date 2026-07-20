import os

# Absolute path to the project root, so every path works
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database
DB_PATH = os.path.join(BASE_DIR, "db", "guild.db")

# Security

SECRET_KEY = "fibooking-heist-program"

# Cap the size of any POST body (general safety limit)
MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB

# Simulated current" moment in the fictional week
#Days coded as 0,1,2,3,4,5,6
#Hour HH:MM format
SIMULATED_NOW_DAY = 2          # Wednesday
SIMULATED_NOW_TIME = "20:00"   # 24-hour
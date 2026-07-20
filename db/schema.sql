

DROP TABLE IF EXISTS participations;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS quests;
DROP TABLE IF EXISTS users;

-- Registered users
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,   
    password_hash TEXT    NOT NULL,          
    role          TEXT    NOT NULL
                  CHECK (role IN ('adventurer', 'guild_master'))
);

-- A heist template
CREATE TABLE quests (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT    NOT NULL UNIQUE,               
    title        TEXT    NOT NULL,
    duration_min INTEGER NOT NULL CHECK (duration_min > 0),
    job_type     TEXT    NOT NULL,                      
    difficulty   INTEGER NOT NULL CHECK (difficulty BETWEEN 2 AND 5),
    description  TEXT    NOT NULL,
    image        TEXT,                                  -- filename in static/img; NULL => placeholder
    created_by   INTEGER NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users (id)
);

-- A scheduled run of a heist
CREATE TABLE sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    quest_id   INTEGER NOT NULL,
    day        INTEGER NOT NULL CHECK (day BETWEEN 0 AND 6),   
    start_time TEXT    NOT NULL,                               
    location   TEXT    NOT NULL
               CHECK (location IN ('Pacific Standard Bank',
                                   'Diamond Casino',
                                   'Union Depository')),
    FOREIGN KEY (quest_id) REFERENCES quests (id)
);

-- Row is booking on one session with 1 or 2 places 
--Unique userid and sessionid at most one bookinng per user per session
CREATE TABLE participations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    role       TEXT    NOT NULL
               CHECK (role IN ('gunman', 'driver', 'hacker')),
    places     INTEGER NOT NULL CHECK (places BETWEEN 1 AND 2),
    UNIQUE (user_id, session_id),
    FOREIGN KEY (user_id)    REFERENCES users (id),
    FOREIGN KEY (session_id) REFERENCES sessions (id)
);

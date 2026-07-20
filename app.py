import os

from flask import Flask, render_template, request, redirect, url_for, abort, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from models import User
from services import (board_service,clock,auth_service,rules,booking_service,quest_service,planner_service)

app = Flask(__name__)
app.config.from_object("config")  # SECRET_KEY, upload limits, simulated clock

# Flask-Login setup
# Anonymous Until login
login_manager = LoginManager(app)
login_manager.login_view = "login"  # where @login_required sends visitors

#The session cookie with users id and authservice gets the rest of the user info from the database
@login_manager.user_loader
def load_user(user_id):
    db_user = auth_service.get_user(user_id)
    if db_user is not None:
        user = User(id=db_user["id"], username=db_user["username"],
                    role=db_user["role"])
    else:
        user = None

    return user

#Main page
@app.route("/")
def job_board():

    day_arg = request.args.get("day","")
    
    if day_arg.isdigit() and int(day_arg) <= 6:
        day = int(day_arg)
    else:
        day = None

    wanted_arg = request.args.get("wanted","")
    if wanted_arg in ("2", "3", "4", "5"):
        min_difficulty = int(wanted_arg)
    else:
        min_difficulty = None

    job_type = request.args.get("type","")
    if job_type not in board_service.JOB_TYPES:
        job_type = None

    role = request.args.get("role","")
    if role not in ("gunman","driver","hacker"):
        role = None

    location = request.args.get("location","")
    if location not in quest_service.LOCATIONS:
        location = None

    sessions = board_service.get_board(day, job_type, min_difficulty, role, location)
    stats = board_service.board_stats()

    return render_template(
        "job_board.html",
        sessions=sessions,
        stats=stats,
        job_types=board_service.JOB_TYPES,
        day_names=clock.DAY_NAMES,
        locations=quest_service.LOCATIONS,
        filters={"day": day, "type": job_type, "wanted": min_difficulty,
                 "role": role, "location": location},
    )

#The login page, it has also accepts POST requests to log the user in
@app.route("/login" , methods = ["POST","GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("job_board"))
    
    error = None
    if request.method == "POST":
        username = request.form.get("username","")
        password = request.form.get("password" ,"")

        if username == "" or password == "":
            error = "Enter both username and password"
        else:
            row = auth_service.verify_login(username,password)
            if row is None:
                error = "Wrong codename or cipher please try again"
            else:
                new = User(id=row["id"], username=row["username"],
                           role=row["role"])
                login_user(new, True)
                flash("Welcome back, " + row["username"] + "!", "success")
                return redirect(url_for("job_board"))

    
    
    return render_template("login.html",error = error)

#The register page, it has also accepts POST requests to register the user
@app.route("/register",methods = ["GET","POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("job_board"))
    
    error = None
    if request.method == "POST":
        username = request.form.get("username","")
        password = request.form.get("password","")
        password2 = request.form.get("password2","")
        role = request.form.get("role", "")

        # Format checks (front-end HTML5 repeats these; server is the authority).
        if username == "" or password == "":
            error = "Enter both codename and cipher."
        elif len(username) > 20:
            error = "The codename must be 20 characters or fewer."
        elif len(password) < 8:
            error = "The cipher must be at least 8 characters."
        elif password != password2:
            error = "Ciphers don't match - re-enter to confirm."
        elif role not in ("adventurer", "guild_master"):
            error = "Pick a role: crew or mastermind."

        else:
            new_id, error = auth_service.register_user(username, password,role)
            if error is None:
                new = User(id=new_id, username=username, role=role)
                login_user(new, True)
                flash("Codename registered - welcome to FIBooking.", "success")
                return redirect(url_for("job_board"))
    
    return render_template("register.html",error = error)

#The logout page, logsout the user and redirects to the job board
@app.route("/logout")
@login_required
def logout():

    logout_user()
    return redirect(url_for("job_board"))


@app.route("/sessions/<int:session_id>")
def details(session_id):
    
    session = board_service.get_session(session_id)
    if session is None:
        abort(404)
    
    runs = board_service.get_quest_runs(session["quest_id"])

    my_booking = None
    my_can_modify = None

    if current_user.is_authenticated and current_user.role == "adventurer":
        my_booking = booking_service.get_booking(current_user.id,session_id)
        if my_booking is not None:
            my_can_modify = rules.can_modify_participation(session["day"],session["start_time"])

    return render_template("details.html", s=session, runs=runs,
                           my_booking=my_booking, my_can_modify=my_can_modify)

@app.route("/session/<int:session_id>/join", methods=["POST"])
@login_required
def join(session_id):
    
    if current_user.role != "adventurer":
        abort(403)
    role = request.form.get("role","")
    places = request.form.get("places","")

    if role not in ("gunman","driver","hacker") or places not in ("1","2"):
        flash("Choose a role and 1 or 2 places","danger")
        return redirect(url_for("details", session_id=session_id))
    
    ok,error = booking_service.join_session(current_user.id, session_id, role,int(places))
    if ok:
        flash("You are on the crew! Places reserved","success")
    else:
        app.logger.error("join refused: %s",error)
        flash(error,"danger")

    return redirect(url_for("details", session_id=session_id))


@app.route("/session/<int:session_id>/update", methods=["POST"])
@login_required
def update_booking(session_id):
    if current_user.role != "adventurer":
        abort(403)

    booking = request.form.to_dict()
    role = booking.get("role", "")
    places = booking.get("places", "")
    if role not in ("gunman", "driver", "hacker") or places not in ("1", "2"):
        flash("Choose a role and 1 or 2 places.", "danger")
        return redirect(url_for("details", session_id=session_id))

    ok, error = booking_service.change_participation(current_user.id, session_id,
                                                     role, int(places))
    if ok:
        flash("Booking updated.", "success")
    else:
        app.logger.error("update refused: %s", error)
        flash(error, "danger")
    return redirect(url_for("details", session_id=session_id))


@app.route("/session/<int:session_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(session_id):
    if current_user.role != "adventurer":
        abort(403)

    ok, error = booking_service.cancel_participation(current_user.id, session_id)
    if ok:
        flash("Booking cancelled - places released.", "success")
    else:
        app.logger.error("cancel refused: %s", error)
        flash(error, "danger")
    return redirect(url_for("details", session_id=session_id))

@app.route("/planner")
@login_required
def planner():
    """Guild Master profile: every quest with its runs and their numbers."""
    if current_user.role != "guild_master":
        return redirect(url_for("my_jobs"))  # adventurers have their own page

    groups, stats = planner_service.get_planner_view()
    return render_template("planner.html", groups=groups, stats=stats)

@app.route("/my-jobs")
@login_required
def my_jobs():

    if current_user.role != "adventurer":
        return redirect(url_for("planner"))

    bookings = booking_service.get_user_bookings(current_user.id)
    places_total = 0
    locked_count = 0
    for b in bookings:
        places_total += b["places"]
        if not b["can_modify"]:
            locked_count +=1

    return render_template("my_jobs.html", bookings=bookings,
                           places_total=places_total, locked_count=locked_count)


#Filenames of the promo images the Guild Master can pick for a new quest
def available_images():
    img_dir = os.path.join(app.static_folder, "img")
    if not os.path.isdir(img_dir):
        return []
    return sorted(f for f in os.listdir(img_dir)
                  if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))


@app.route("/new-score",methods = ["GET","POST"])
@login_required
def new_score():
    if current_user.role != "guild_master":
        abort(403)

    error = None

    runs_input = [{"day": "", "start_time": "", "location": ""}]

    if request.method == "POST":
        title = request.form.get("title","")
        duration = request.form.get("duration","")
        job_type = request.form.get("job_type","")
        difficulty = request.form.get("difficulty","")
        description = request.form.get("description","")
        image = request.form.get("image","")

        days = request.form.getlist("day")
        starts = request.form.getlist("start_time")
        locations = request.form.getlist("location")
        runs_input = []
        for i in range(len(days)):
            runs_input.append({"day": days[i],
                               "start_time": starts[i] if i < len(starts) else "",
                               "location": locations[i] if i < len(locations) else ""})
            
        if title == "" or description == "":
            error = "Title and briefing are required."
        elif not (duration.isdigit() and 0 < int(duration) <=600):
            error = "Duration must be a number of minutes (1-600)."
        elif job_type not in board_service.JOB_TYPES:
            error = "Pick a valid job type."
        elif difficulty not in ("2", "3", "4", "5"):
            error = "Wanted level must be between 2 and 5 stars."
        elif image != "" and image not in available_images():
            error = "Pick a valid promo image."
        elif len(runs_input) == 0:
            error = "Schedule at least one run."
        else:
            for r in runs_input:
                if not (r["day"].isdigit() and int(r["day"]) <= 6) \
                        or not clock.is_valid_time(r["start_time"]) \
                        or r["location"] not in quest_service.LOCATIONS:
                    error = "Every run needs a valid day, start time and location."
                    break

        #  business rules + insert
        if error is None:
            runs = [(int(r["day"]), r["start_time"], r["location"]) for r in runs_input]
            quest_id, error = quest_service.create_quest(
                current_user.id, title, int(duration), job_type,
                int(difficulty), description, image or None, runs)
            if error is None:
                flash("Score created - runs are on the board.", "success")
                return redirect(url_for("planner"))
        app.logger.error("new score refused: %s", error)

    return render_template("new_score.html", error=error, runs_input=runs_input,
                           job_types=board_service.JOB_TYPES,
                           locations=quest_service.LOCATIONS,
                           day_names=clock.DAY_NAMES,
                           images=available_images())
    
@app.route("/session/<int:session_id>/edit", methods=["GET", "POST"])
@login_required
def edit_session(session_id):
    """Move a run to another day/time/location (Guild Master only, and only
    while nobody has joined it)."""
    if current_user.role != "guild_master":
        abort(403)

    session = board_service.get_session(session_id)
    if session is None:
        abort(404)

    error = None
    if request.method == "POST":
        form = request.form.to_dict()
        day = form.get("day", "")
        start_time = form.get("start_time", "")
        location = form.get("location", "")

        if not (day.isdigit() and int(day) <= 6) or not clock.is_valid_time(start_time) \
                or location not in quest_service.LOCATIONS:
            error = "Fill in a valid day, time and location."
        else:
            ok, error = quest_service.update_session(session_id, int(day),
                                                     start_time, location)
            if ok:
                flash("Run moved.", "success")
                return redirect(url_for("planner"))
        app.logger.error("edit refused: %s", error)

    return render_template("edit_session.html", s=session, error=error,
                           day_names=clock.DAY_NAMES,
                           locations=quest_service.LOCATIONS)

@app.route("/session/<int:session_id>/cancel-run", methods=["POST"])
@login_required
def cancel_session(session_id):
    """Cancel a whole run (Guild Master only, only while nobody joined)."""
    if current_user.role != "guild_master":
        abort(403)

    ok, error = quest_service.cancel_session(session_id)
    if ok:
        flash("Run cancelled.", "success")
    else:
        app.logger.error("cancel run refused: %s", error)
        flash(error, "danger")
    return redirect(url_for("planner"))


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404,
                           message="The run or page you asked for is not on "
                                   "file. It may have been cancelled or never "
                                   "existed."), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403,
                           message="Your clearance does not cover this "
                                   "operation. Sign in with the right account "
                                   "and try again."), 403

if __name__ == "__main__":
    app.run(debug=True)
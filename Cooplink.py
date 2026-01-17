import sqlite3
from flask import Flask, render_template,request,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash, check_password_hash


cooplink = Flask(__name__)

cooplink.secret_key = "your_secret_key_here"  # required for sessions

@cooplink.route("/")
def home():
	return render_template("home.html")


@cooplink.route("/multi_signup")
def sign__up():
	return render_template('multi_signup.html')




def get_db():
    return sqlite3.connect("instance\cooplink.db")

# ----------------- SIGN UP -----------------
@cooplink.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        username = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        system = request.form['system']

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for('sign__up'))

        hashed_password = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, email, password, system)
                VALUES (?, ?, ?, ?)
            """, (username, email, hashed_password, system))
            db.commit()
            flash("Account created successfully! Please log in.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already registered")
            return redirect(url_for('sign__up'))
        finally:
            db.close()

    return render_template("multi_signup.html")
#----------------- END SIGN UP -----------------

# ----------------- LOG IN -----------------
@cooplink.route("/login", methods=["GET", "POST"])
def log_in():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        system = request.form['system']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, username, password, system FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        db.close()

        if user:
            user_id, username, hashed_password, user_system = user
            if check_password_hash(hashed_password, password) and user_system == system:
                session['user_id'] = user_id
                session['username'] = username
                session['system'] = user_system
                flash(f"Welcome {username}!")
                return redirect(url_for('dashboard'))
        flash("Invalid credentials or system")
        return redirect(url_for('login'))

    return render_template("login.html")
#---------------- END LOG IN -----------------

# ----------------- DASHBOARDS -----------------
@cooplink.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("cooplink_dashboard.html")

@cooplink.route("/dashboard-COOPLINK")
def dashboard_COOPLINK():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session['system'] == user_system:
        return render_template("cooplink.html")
#----------------- END DASHBOARDS -----------------


#--------------------- ADD USER -----------------
@cooplink.route("/add_user")
def add_user():
    return render_template("user_add.html")
#--------------------- END ADD USER -----------------

@cooplink.route("/active sessions")
def active_sessions():
	return render_template('active_sessions.html')


@cooplink.route("/login attempts")
def login_attempts():
	return render_template('log_in_attempts.html')


@cooplink.route("/server health")
def server_health():
	return render_template('server_health.html')


@cooplink.route("/active sessions")
def jobs_events():
	return render_template('jobs_events.html')




# ----------------- LOGOUT -----------------
@cooplink.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))
#----------------- END LOGOUT -----------------

@cooplink.route("/log_in")
def login():
    return render_template("multi_login.html")


@cooplink.route("/projects")
def projects():
    return render_template("multi_login.html")


@cooplink.route("/contact")
def contact():
    return render_template("multi_login.html")



@cooplink.route("/about")
def about():
    return render_template("multi_login.html")



if __name__ == "__main__":
    cooplink.run(host="0.0.0.0", port=5000,debug=True)
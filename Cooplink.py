from dotenv import load_dotenv
load_dotenv()
import sqlite3
import os
from flask import Flask, render_template,request,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta



cooplink = Flask(__name__)

#------------- SECURING SESSION -------------
cooplink.config.update(
SESSION_COOKIE_HTTPONLY = True, # Prevents JavaScript access to session cookies
SESSION_COOKIE_SAMESITE = "Lax", # Mitigates CSRF attacks
SESSION_COOKIE_SECURE = False, # Ensures cookies are only sent over HTTP
SESSION_COOKIE_NAME = "cooplink_session", #session cookie name
PERMANENT_SESSION_LIFETIME = timedelta(minutes=30) # Session lifetime
)
#------------- END SECURING SESSION -------------

#-------------- SESSION ENFORCEMENT ---------
@cooplink.before_request
def session_enforcement():
    if session.get("user_id") and not session.get("system"):
        session.clear()
        flash("Session expired. Please log in again.")
        return redirect(url_for('login'))

#-------------- END SESSION ENFORCEMENT ---------

#--------------SECURING SCERET KEY--------
cooplink.secret_key = os.environ.get("SECRET_KEY")
if not cooplink.secret_key:
    raise RuntimeError("SECRET_KEY environment variable not set")

#--------------END SECURING SCERET KEY--------


#------------- SESSION LIFETIME -------------
cooplink.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
#------------- END SESSION LIFETIME -------------


#----------------- HOME -----------------
@cooplink.route("/Cooplink")
def home():
	return render_template("home.html")

#----------------- END HOME -----------------


#----------------- MULTI SIGN UP -----------------

@cooplink.route("/multi_signup")
def sign__up():
	return render_template('multi_signup.html')

#----------------- END MULTI SIGN UP -----------------


#----------- Database connection -----------

def get_db():
    return sqlite3.connect(os.path.join(cooplink.instance_path, 'cooplink.db'))

#----------- End Database connection -----------

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
@cooplink.route("/log_in", methods=["GET", "POST"])
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
                session.clear()  # Clear any existing session data
                session.permanent = True  # Makes the session permanent
                session['user_id'] = user_id
                session['username'] = username
                session['system'] = user_system
                session.modified = True  # Ensure session is marked as modified
                flash(f"Welcome {username}!")
                return redirect(url_for('dashboard'))
        flash("Invalid credentials or system")
        return redirect(url_for('log_in'))

    return render_template("multi_login.html")
#---------------- END LOG IN -----------------

# ----------------- DASHBOARDS -----------------
@cooplink.route("/dashboard")
def dashboard():
    if not session.get('user_id'):
        flash("Please log in to access the dashboard.")
        return redirect(url_for('log_in'))
    return render_template("cooplink_dashboard.html")

@cooplink.route("/dashboard-COOPLINK")
def dashboard_COOPLINK():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('system'):
        return render_template("cooplink.html")
#----------------- END DASHBOARDS -----------------


#--------------------- ADD USER -----------------
@cooplink.route("/add_user")
def add_user():
    return render_template("user_add.html")
#--------------------- END ADD USER -----------------



# ----------------- LOGOUT -----------------
@cooplink.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('log_in'))
#----------------- END LOGOUT -----------------




if __name__ == "__main__":
    cooplink.run(host="0.0.0.0", port=5000,debug=True)
#Cooplink - Muilti-System Web Platform
#This application handles:
#-user authentication
#Session management
#Multi-system routing (cooplink,beilo)
#Dashboard rendering

#STATUS: MVP (In Development)

from dotenv import load_dotenv
load_dotenv()
import sqlite3
import os
from flask import Flask, render_template,request,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename  
from datetime import timedelta
import psycopg2
from psycopg2.extras import RealDictCursor



cooplink = Flask(__name__)


#------------- SECURING SESSION -------------
cooplink.config.update(
SESSION_COOKIE_HTTPONLY = True, # Prevents JavaScript access to session cookies
SESSION_COOKIE_SAMESITE = "Lax", # Mitigates CSRF attacks
SESSION_COOKIE_SECURE = False, # Ensures cookies are only sent over HTTP if set to True
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

#------------------ UPLOAD FOLDER -----------------

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # make sure folder exists

cooplink.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#----------------- END UPLOAD FOLDER -----------------



#----------------- HOME -----------------
@cooplink.route("/Cooplink")
def home():
	return render_template("home.html")

#----------------- END HOME -----------------


#----------------- MULTI SIGN UP -----------------

@cooplink.route("/auth/multi_signup")
def sign__up():
	return render_template('auth/multi_signup.html')

#----------------- END MULTI SIGN UP -----------------


#----------- Database connection -----------

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)

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
            return redirect(url_for('sign_up'))

        hashed_password = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, email, password, system)
                VALUES (%s, %s, %s, %s)
            """, (username, email, hashed_password, system))
            db.commit()
            flash("Account created successfully! Please log in.")
            return redirect(url_for('log_in'))
        except sqlite3.IntegrityError:
            flash("Email already registered")
            return redirect(url_for('sign_up'))
        finally:
            db.close()

    return render_template("auth/multi_signup.html")
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
        cursor.execute("SELECT id, username, password, system FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        db.close()

        if user:
            user_id = user['id']
            username = user['username']
            hashed_password = user['password']
            user_system = user['system']

            if check_password_hash(hashed_password, password) and user_system == system:
                session.clear()  # Clear any existing session data
                session.permanent = True  # Makes the session permanent
                session['user_id'] = user_id
                session['username'] = username
                session['system'] = user_system
                session.modified = True  # Ensure session is marked as modified
                if user_system == "cooplink":
                    return redirect(url_for('dashboard'))
                elif user_system == "campus suite":
                    return redirect(url_for('campus_suite_dashboard'))
                elif user_system == "Beilo":
                    return redirect(url_for('dashboard_BEILO'))
                else:
                    flash("System not recognized for dashboard access.")
                    return redirect(url_for('log_in'))
        flash("Invalid credentials or system")
        return redirect(url_for('log_in'))

    return render_template("auth/multi_login.html")
#---------------- END LOG IN -----------------

# ----------------- DASHBOARDS -----------------
@cooplink.route("/dashboard")
def dashboard():
    if not session.get('user_id'):
        flash("Please log in to access the dashboard.")
        return redirect(url_for('log_in'))
    return render_template("dashboard/cooplink_dashboard.html")

#----------------- COOPLINK DASHBOARD -----------------

@cooplink.route("/dashboard-COOPLINK")
def dashboard_COOPLINK():
    if 'user_id' not in session:
        return redirect(url_for('log_in'))
    if session.get('system'):
        return render_template("dashboard/cooplink.html")

#----------------- END COOPLINK DASHBOARD -----------------


#------------------- BEILO ---------------------------


#----------------- BEILO DASHBOARD -----------------

@cooplink.route("/dashboard-BEILO")
def dashboard_BEILO():
    if 'user_id' not in session:
        return redirect(url_for('log_in'))

    db = get_db()
    cursor=db.cursor()
    
    cursor.execute( """  SELECT 
    orders.id,
    beilo_products.name,
    orders.phone_number,
    orders.quantity,
    orders.created_at
    FROM orders
    JOIN beilo_products
    ON orders.id = beilo_products.id
    ORDER BY orders.created_at DESC

     """)

    orders = cursor.fetchall()
    #----------------- TOTAL ORDERS -----------------
    cursor.execute( """
    SELECT COUNT(*) As count
    FROM orders
    WHERE DATE(created_at) = CURRENT_DATE
    """ )
    todays_orders = cursor.fetchone()['count'] 
    #---------------- PENDING ORDERS -----------------
    cursor.execute( """
    SELECT COUNT(*) As count
    FROM orders
    WHERE status = 'pending'
    """ )
    pending_orders = cursor.fetchone()['count']

    
    #------------------ COMPLETED ORDERS -----------------
    if request.method == "POST":
        order_id = request.form.get("order_id")
        if order_id:
            cursor.execute("""
            UPDATE orders
            SET status = 'completed'
            WHERE id = %s
            """,(order_id,))
            db.commit()


    return render_template("shop/beilo/templates/beilo.html", orders=orders,todays_orders=todays_orders,pending_orders=pending_orders)


#------------------- ORDER CONTROL ----------------
@cooplink.route("/complete/<int:order_id>", methods=["POST"])
def complete_order(order_id):
    db=get_db()
    cursor = db.cursor()

    cursor.execute("""
    UPDATE orders SET status = 'completed' WHERE id = %s
    """,(order_id,))

    db.commit()
    return redirect(url_for('dashboard_BEILO'))




#----------------- END BEILO DASHBOARD -----------------


#------------------ BEILO_SITE ----------------------
@cooplink.route("/beilo_site")
def beilo_site():
    db=get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM beilo_products ORDER BY id DESC")
    products = cursor.fetchall()
    return render_template("beilo/beilo_site.html", products=products)

#------------------ END BEILO_SITE ----------------------

#----------------- BEILO PRODUCT MANAGEMENT -----------------


#----------------- IMAGE UPLOAD -----------------
#----------------- IMAGE UPLOAD / PRODUCT MANAGEMENT -----------------
@cooplink.route("/beilo_product_management", methods=["GET", "POST"])
def beilo_product_management():
    if 'user_id' not in session:
        return redirect(url_for('log_in'))
    
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        try:
            print("Received POST request for product management")
            # --- get form data ---
            name = request.form["name"]
            category = request.form["category"]
            price = request.form["price"]
            stock = request.form["stock"]
            branch = request.form["branch"]

            # --- handle image ---
            file = request.files["image"]
            image_filename = None
            #---- ensure upload folder exists ---
            UPLOAD_FOLDER = "static/uploads"
            cooplink.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(cooplink.config['UPLOAD_FOLDER'], filename))
                image_filename = filename

            # --- insert into DB ---
            cursor.execute("""
                INSERT INTO beilo_products (name, category, price, stock, branch, image)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, category, price, stock, branch, image_filename))

            db.commit()
            print("Product added successfully:")

        except Exception as e:
            print("An err occured while trying to access the Database, please try again later!:", e)
            db.rollback()

        return redirect(url_for('beilo_product_management'))

        #---------------GET REQUEST-------------------
    cursor.execute("SELECT * FROM beilo_products")
    products = cursor.fetchall()
    return render_template("shop/beilo/templates/product_management.html", products=products)


#----------------- ALLOWED IMAGE FORMATS -----------------

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#----------------- END IMAGE UPLOAD -----------------

#-----------------DELETE PRODUCT-------------------
@cooplink.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(''' DELETE FROM beilo_products WHERE id=%s ''', (id,))
    
    db.commit()

    db.close()

    return redirect(url_for('beilo_product_management'))


#------------------ END BEILO PRODUCT MANAGEMENT -----------------


#------------------ BEILO_BUY_REQUEST -----------------------

@cooplink.route("/buy/<int:id>", methods=["GET", "POST"])
def buy_product(id):
    db = get_db()
    cursor = db.cursor()

    # -------------- Get product details ---------------
    cursor.execute("SELECT * FROM beilo_products WHERE id = %s", (id,))
    product = cursor.fetchone()

    if not product:
        return "Product not found", 404

    if request.method == "POST":
        phone = request.form["phone_number"]
        quantity = int(request.form["quantity"])
        name = product
        

#------------------ SAVING ORDER --------------------
        cursor.execute("""INSERT INTO orders (product_name, phone_number, quantity) VALUES (%s, %s, %s) """, (product['name'], phone, quantity))
        

        db.commit()
        name = cursor.execute("SELECT * FROM beilo_products")
        products = cursor.fetchall()
        return "Order placed successfully!"

    return render_template("shop/beilo/templates/request_buy.html", product=product)



@cooplink.route("/successfull_order")
def successfull_order():
    return render_template("shop/beilo/order_confirm.html")

#------------------ END BEILO BUY REQUEST ---------------------




#----------------- BEILO END ------------------------



#----------------- END DASHBOARDS -----------------


#--------------------- ADD USER -----------------
@cooplink.route("/add_user")
def add_user():
    return render_template("feature/user_add.html")
#--------------------- END ADD USER -----------------



# ----------------- LOGOUT -----------------
@cooplink.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('log_in'))
#----------------- END LOGOUT -----------------




if __name__ == "__main__":
    cooplink.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))

from flask import Blueprint, request, redirect, url_for,jsonify, session, render_template
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)


# ----------------------
# LOGOUT
# ----------------------
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))




# ----------------------
# SIGNUP
# ----------------------
@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                "status": "error",
                "message": "Username and password required"
            })

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute(
            "SELECT user_id FROM users WHERE username=%s",
            (username,)
        )
        if cursor.fetchone():
            conn.close()
            return jsonify({
                "status": "error",
                "message": "Username already exists"
            })

        # Insert user
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )
        conn.commit()

        conn.close()

        return jsonify({
            "status": "success",
            "message": "Signup successful"
        })

    except Exception as e:
        print("SIGNUP ERROR:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        })

# ----------------------
# LOGIN
# ----------------------

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'GET':
        return render_template('index.html')

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id, password FROM users WHERE username=%s",
        (username,)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['user_id']
        return jsonify({"status": "success"})

    return jsonify({"status": "error"})


    return render_template

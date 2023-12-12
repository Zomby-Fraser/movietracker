from flask import Flask, render_template, request, jsonify, session
import hashlib
import mysql.connector

app = Flask(__name__)
app.secret_key = 'klahSKDbjasnio'

db_config = {
    'host': 'zombyfraser.mysql.pythonanywhere-services.com',
    'user': 'zombyfraser',
    'password': 'modMad-hibso2-nunseg',
    'database': 'zombyfraser$default'
}

@app.route('/')
def loginPage():
    return render_template('login.html')

@app.route('/home')
def homePage():
    if 'username' in session:
        return 'This is a protected route.'
    else:
        return 'You are not logged in.', 401

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Query to find the user
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, hashed_password))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['username'] = username  # Store username in session
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

if __name__ == '__main__':
    app.run(debug=True)


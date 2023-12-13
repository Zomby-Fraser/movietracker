from flask import Flask, render_template, request, jsonify, session
import hashlib
import mysql.connector
import requests
import re
from bs4 import BeautifulSoup

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
        return render_template('home.html')
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

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    return 'You have been logged out.'

@app.route('/add_movie', methods=['POST'])
def addMovie():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
        url = request.form.get('url', headers)

        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extracting the title
        title = soup.find('h1').text.strip()

        # Extracting the year of release
        year = soup.find_all('div', attrs={'class':'sc-69e49b85-0 jqlHBQ'})[0].find('a').text

        # Extracting the IMDB ID from the URL
        imdb_id = url.split('/')[4]

        return {
            'title': title,
            'imdb_id': imdb_id,
            'year_of_release': year
        }

    except requests.RequestException as e:
        print(f'Error fetching the IMDB page: {e}')
        return None
    except AttributeError:
        print('Error parsing IMDB page. The structure of the page might have changed.')
        return None

if __name__ == '__main__':
    app.run(debug=True)


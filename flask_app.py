from flask import Flask, render_template, request, jsonify, session
import hashlib
import mysql.connector
from mysql.connector.cursor import MySQLCursorDict
import requests
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'klahSKDbjasnio'

db_config = {
    'host': 'zombyfraser.mysql.pythonanywhere-services.com',
    'user': 'zombyfraser',
    'password': 'dobqod-Faxjoc-zagbi4',
    'database': 'zombyfraser$default'
}

@app.route('/')
def loginPage():
    return render_template('login.html')

@app.route('/home')
def homePage():
    if 'username' in session:
        conn = mysql.connector.connect(**db_config)
        # Example query (adjust based on your actual database schema)
        query = """
        SELECT m.movie_key, m.title, m.year_of_release, mn.download_link, GROUP_CONCAT(ms.source_name) AS sources
        FROM MoviesNeeded mn
        JOIN Movies m ON mn.movie_key = m.movie_key
        LEFT JOIN MovieSources ms ON m.movie_key = ms.movie_key
        WHERE m.movie_key NOT IN (SELECT movie_key FROM MovieCollection)
        GROUP BY m.movie_key;
        """
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute(query)
        column_names = cursor.column_names
        movies = [dict(zip(column_names, row)) for row in cursor.fetchall()]

        sources = {}

        for movie in movies:
            movie_source_list = []
            for sources in movie['sources'].split(","):
                movie_source_list.append(sources)
            sources[movie['movie_key']] = movie_source_list

        cursor.close()
        conn.close()
        
        return render_template('home.html', movies=movies, sources=sources)
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
            user_id = user[0]
            session['id'] = user_id
            session['username'] = username  # Store username in session
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(err)}), 500

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    return 'You have been logged out.'

@app.route('/add_movie', methods=['POST'])
def addMovie():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
        url = request.form.get('url')

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extracting the title
        title = soup.find('h1').text.strip()

        # Extracting the year of release
        year = soup.find_all('div', attrs={'class':'sc-69e49b85-0 jqlHBQ'})[0].find('a').text

        # Extracting the IMDB ID from the URL
        imdb_id = url.split('/')[4]

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = "INSERT INTO Movies (title, imdb_id, year_of_release) VALUES (%s, %s, %s);"
        cursor.execute(query, (title, imdb_id, year))

        new_movie_key = cursor.lastrowid

        query = "INSERT INTO MoviesNeeded (movie_key) VALUES (%s)"
        cursor.execute(query, (new_movie_key,))

        conn.commit()
        cursor.close()
        conn.close()

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


from flask import Flask, render_template, request, jsonify, session
import hashlib
import mysql.connector
from mysql.connector.cursor import MySQLCursorDict
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'klahSKDbjasnio'

db_config = {
    # 'host': 'zombyfraser.mysql.pythonanywhere-services.com',
    'host': 'localhost',
    'user': 'zombyfraser',
    'password': 'dobqod-Faxjoc-zagbi4',
    'database': 'zombyfraser$default'
}

@app.route('/')
def loginPage():
    registration_code = request.args.get('registration_code')
    if not registration_code:
        return render_template('login.html')
    else:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True) 
        query = "SELECT registration_code, registration_code_used_flag FROM RegistrationCodes WHERE registration_code = %s"
        cursor.execute(query, (registration_code,))
        registration_check = cursor.fetchall()
        registration_check = registration_check[0]

        if len(registration_check) == 0:
            return "Invalid registration code.", 401
        elif registration_check['registration_code_used_flag']:
            return "Registration code already used.", 401

        return render_template('login.html', registration_check=registration_check)

@app.route('/home')
def homePage():
    if 'username' in session:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)  # Use the dictionary cursor to get results as dictionaries

        if session['role_id'] == 1 or session['role_id'] == 4:
            source_query = "ms.source_name, ' (', ms.size_in_gb, 'GB) ', '[', tt.torrent_tracker_abbreviation, ']'"
        else:
            source_query = "ms.source_name, ' (', ms.size_in_gb, 'GB)'"

        query = f'''SELECT 
            m.movie_key, 
            m.title, 
            m.year_of_release, 
            mn.download_link, 
            mn.comment,
            GROUP_CONCAT(CONCAT({source_query})) AS sources,
            GROUP_CONCAT(ms.source_selected) AS accepted_sources,
            GROUP_CONCAT(ms.source_key) AS source_keys
        FROM MoviesNeeded mn
        JOIN Movies m ON mn.movie_key = m.movie_key
        LEFT JOIN MovieSources ms ON m.movie_key = ms.movie_key
        LEFT JOIN TorrentTrackers tt ON ms.source_torrent_tracker_key = tt.torrent_tracker_key
        WHERE m.movie_key NOT IN (SELECT movie_key FROM MovieCollection)
        GROUP BY m.movie_key, m.title, m.year_of_release, mn.download_link
        ORDER BY m.title;'''
        cursor.execute(query)
        movies = cursor.fetchall()
        movie_data = []

        for movie in movies:
            # Split the sources and accepted sources
            sources = movie['sources'].split(',') if movie['sources'] else []
            accepted_values = movie['accepted_sources'].split(b',') if movie['accepted_sources'] else []
            source_keys = movie['source_keys'].split(',') if movie['source_keys'] else []

            # Convert each byte in accepted_values to boolean
            accepted_booleans = [bool(int.from_bytes(byte, 'big')) for byte in accepted_values]

            # Prepare the list to store sources with their acceptance status
            sources_data = []
            
            for i, source in enumerate(sources):
                # Get the acceptance status for each source, defaulting to False if not available
                accepted = accepted_booleans[i] if i < len(accepted_booleans) else False
                sources_data.append({'source_name': source, 'accepted': accepted, 'source_key': source_keys[i]})

            # Update the movie dictionary
            movie['sources'] = sources_data
            movie_data.append(movie)
            del movie['accepted_sources']

        query = f'''
            SELECT 
                torrent_tracker_key AS torrent_tracker_key,
                torrent_tracker_name AS torrent_tracker_name
            FROM TorrentTrackers
        '''
        cursor.execute(query)
        trackers = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('home.html', movies=movie_data, session=session, trackers=trackers)
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
        cursor = conn.cursor(dictionary=True)

        # Query to find the user
        query = '''SELECT 
            u.id AS user_id,
            u.username AS username,
            ur.users_role_id AS role_id
        FROM Users u
        INNER JOIN UserRoles ur ON ur.users_id = u.id
        WHERE u.username = %s AND u.password = %s'''
        cursor.execute(query, (username, hashed_password))

        user = cursor.fetchall()
        cursor.close()
        conn.close()

        user = user[0]

        if user:
            session['role_id'] = user['role_id']
            session['id'] = user['user_id']
            session['username'] = user['username']
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
            'divs': 
                f'''<tr>
                    <td>{title}</td>
                    <td>{year}</td>
                    <td></td>
                    <td><div class="source-options"></div></td>
                    <td><button>Mark as Downloaded</button></td>
                    <td></td>
                    </tr>''',
            'title': title,
            'year': year
        }

    except requests.RequestException as e:
        print(f'Error fetching the IMDB page: {e}')
        return None
    except AttributeError:
        print('Error parsing IMDB page. The structure of the page might have changed.')
        return None

@app.route('/search_imdb', methods=['POST'])
def searchIMDB():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
        title = request.form.get('title')
        year = request.form.get('year')
        url = f"https://www.imdb.com/find/?q={title}({year})"

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extracting the title
        search_results = soup.find_all('li', attrs={'class':'ipc-metadata-list-summary-item ipc-metadata-list-summary-item--click find-result-item find-title-result'})

        results = []
        base_url = "https://www.imdb.com/title/"
        for result in search_results:
            if result.find('img'):
                image = result.find('img').get('src')
            else:
                image = None
            title = result.find('a', attrs={'class':'ipc-metadata-list-summary-item__t'}).text
            if result.find('span', attrs={'class':'ipc-metadata-list-summary-item__li'}):
                year = result.find('span', attrs={'class':'ipc-metadata-list-summary-item__li'}).text
            else: 
                image = "Unknown"
            imdb_url = base_url + result.find('a', attrs={'class':'ipc-metadata-list-summary-item__t'})['href'].split("/")[2]
            results.append({
                'image': image,
                'title': title,
                'year': year,
                'imdb_url': imdb_url
            })

        return jsonify({'results': results})

    except requests.RequestException as e:
        print(f'Error fetching the IMDB page: {e}')
        # Return a valid error response
        return jsonify({'error': 'Error fetching the IMDB page'}), 500

    except AttributeError:
        print('Error parsing IMDB page. The structure of the page might have changed.')
        # Return a valid error response
        return jsonify({'error': 'Error parsing IMDB page'}), 500

@app.route('/update_selected_source', methods=['POST'])
def updateSelectedSource():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        source_key = request.form.get('source_key')
        source_selection_flag = request.form.get('source_selection_flag')

        if source_selection_flag == "true":
            source_selection_flag = 1
        else:
            source_selection_flag = 0

        query = "UPDATE MovieSources SET source_selected = %s WHERE source_key = %s"
        cursor.execute(query, (source_selection_flag,source_key))

        conn.commit()
        cursor.close()
        conn.close()

        return {
            'results': 'Success!'
        }

    except Exception as e:
        return {
            'status': 500,
            'statusText': str(e)
        }


@app.route('/add_source', methods=['POST'])
def addMovieSource():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        movie_key = request.form.get('movie_key')
        source_name = request.form.get('source_name')
        source_tracker_key = request.form.get('source_tracker_key')
        source_size = request.form.get('source_size')
        print(source_tracker_key)
        query = '''
            INSERT INTO MovieSources (movie_key, source_name, size_in_gb, source_selected, source_torrent_tracker_key) VALUES(%s, %s, %s, b'0', %s);
        '''
        cursor.execute(query, (movie_key, source_name, source_size, source_tracker_key))
        conn.commit()
        cursor.close()
        conn.close()

        return {
            'status': 200,
            'statusText': 'Source Added!'
        }

    except Exception as e:
        return {
            'status': 500,
            'statusText': str(e)
        }

@app.route('/update_comment', methods=['POST'])
def updateMovieComment():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        movie_key = request.form.get('movie_key')
        movie_comment = request.form.get('movie_comment')
        query = '''
            UPDATE MoviesNeeded SET comment = %s WHERE movie_key = %s
        '''
        cursor.execute(query, (movie_comment, movie_key))
        conn.commit()
        cursor.close()
        conn.close()

        return {
            'status': 200,
            'statusText': 'Source Added!'
        }

    except Exception as e:
        return {
            'status': 500,
            'statusText': str(e)
        }
    
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Query to find the user
        query = '''INSERT INTO Users (username, password) VALUES (%s, %s)'''
        cursor.execute(query, (username, hashed_password))
        new_user_id = cursor.lastrowid

        query = '''INSERT INTO UserRoles (users_id, users_role_id) VALUES (%s, 3)'''
        cursor.execute(query, (new_user_id,))

        conn.commit()
        
        # Query to find the user
        query = '''SELECT 
            u.id AS user_id,
            u.username AS username,
            ur.users_role_id AS role_id
        FROM Users u
        INNER JOIN UserRoles ur ON ur.users_id = u.id
        WHERE u.username = %s AND u.password = %s'''
        cursor.execute(query, (username, hashed_password))

        user = cursor.fetchall()
        cursor.close()
        conn.close()

        user = user[0]

        if user:
            session['role_id'] = user['role_id']
            session['id'] = user['user_id']
            session['username'] = user['username']
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(err)}), 500

@app.route('/mark_movie_as_downloaded', methods=['POST'])
def markMovieAsDownloaded():
    movie_key = request.form.get('movie_key')
    user_id = session['id']

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = '''INSERT INTO MovieCollection (movie_key, user_id) VALUES (%s, %s)'''
        cursor.execute(query, (movie_key, user_id))

        query = '''DELETE FROM MoviesNeeded WHERE movie_key = %s'''
        cursor.execute(query, (movie_key,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Movie added to collection'}), 200

    except Exception as e:
        return {
            'status': 500,
            'statusText': str(e)
        }

if __name__ == '__main__':
    app.run(debug=True, port=5001)


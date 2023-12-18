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
    'host': 'localhost',
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
        cursor = conn.cursor(dictionary=True)  # Use the dictionary cursor to get results as dictionaries

        query = '''SELECT 
            m.movie_key, 
            m.title, 
            m.year_of_release, 
            mn.download_link, 
            GROUP_CONCAT(CONCAT(ms.source_name, ' (', ms.size_in_gb, 'GB)')) AS sources,
            GROUP_CONCAT(ms.source_selected) AS accepted_sources,
            GROUP_CONCAT(ms.source_key) AS source_keys
        FROM MoviesNeeded mn
        JOIN Movies m ON mn.movie_key = m.movie_key
        LEFT JOIN MovieSources ms ON m.movie_key = ms.movie_key
        WHERE m.movie_key NOT IN (SELECT movie_key FROM MovieCollection)
        GROUP BY m.movie_key, m.title, m.year_of_release, mn.download_link;'''
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

        cursor.close()
        conn.close()

        return render_template('home.html', movies=movie_data)
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
    # try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
        title = request.form.get('title')
        year = request.form.get('year')
        url = f"https://www.imdb.com/find/?q={title}({year})"

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extracting the title
        search_results = soup.find_all('li', attrs={'class':'ipc-metadata-list-summary-item ipc-metadata-list-summary-item--click find-result-item find-title-result'})

        # breakpoint()

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

    # except requests.RequestException as e:
    #     print(f'Error fetching the IMDB page: {e}')
    #     # Return a valid error response
    #     return jsonify({'error': 'Error fetching the IMDB page'}), 500

    # except AttributeError:
    #     print('Error parsing IMDB page. The structure of the page might have changed.')
    #     # Return a valid error response
    #     return jsonify({'error': 'Error parsing IMDB page'}), 500

@app.route('/update_selected_source', methods=['POST'])
def updateSelectedSource():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        source_key = request.form.get('source_key')
        source_selection_flag = request.form.get('source_selection_flag')
        print(source_selection_flag)
        if source_selection_flag == "true":
            source_selection_flag = 1
        else:
            source_selection_flag = 0

        query = "UPDATE MovieSources SET source_selected = %s WHERE source_key = %s"
        cursor.execute(query, (source_selection_flag,source_key))
        print(query)

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


if __name__ == '__main__':
    app.run(debug=True, port=5001)


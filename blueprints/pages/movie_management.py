from flask import Flask, render_template, request, jsonify, session
import hashlib
import mysql.connector
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import blueprints.database as database

from flask import Blueprint
movie_managament = Blueprint('movie_managament', __name__)

@movie_managament.route('/home')
def homePage():
    if 'username' in session:
        conn = database.new_conn()

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
            m.only_on_streaming_flag,
            m.no_blu_ray_release_flag,
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
        movies = database.pull(conn, query)
        movie_data = []

        for movie in movies:
            movie['title'] = database.process_title(conn, movie['title'])

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

        movie_data = sorted(movie_data, key=lambda x: x['title'].lower())

        query = f'''
            SELECT 
                torrent_tracker_key AS torrent_tracker_key,
                torrent_tracker_name AS torrent_tracker_name
            FROM TorrentTrackers
        '''
        trackers = database.pull(conn, query)
        conn.close()

        return render_template('home.html', movies=movie_data, session=session, trackers=trackers)
    else:
        return 'You are not logged in.', 401

@movie_managament.route('/add_movie', methods=['POST'])
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

        conn = database.new_conn()

        query = "INSERT INTO Movies (title, imdb_id, year_of_release) VALUES (%s, %s, %s);"
        new_movie_key = database.execute(conn, query, (title, imdb_id, year))

        query = "INSERT INTO MoviesNeeded (movie_key) VALUES (%s)"
        database.execute(conn, query, (new_movie_key,))

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

@movie_managament.route('/search_imdb', methods=['POST'])
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
    
@movie_managament.route('/update_property', methods=['POST'])
def updateMovieProperty():
    movie_key = request.form.get('movie_key')
    type = request.form.get('type')
    if type == 'bluray':
        bluray = 1
        streaming = 0
    elif type == 'streaming':
        bluray = 0
        streaming = 1
    elif type == 'none':
        bluray = 0
        streaming = 0
    else:
        return {
            'status': 422,
            'statusText': 'Invalid property type. `bluray`, `streaming`, and `none` are currently the only valid entries.'
        }

    try:
        conn = database.new_conn()

        query = 'UPDATE Movies SET no_blu_ray_release_flag = %s, only_on_streaming_flag = %s WHERE movie_key = %s'
        database.execute(conn, query, (bluray, streaming, movie_key))

        conn.close()

        return jsonify({'message': 'Movie propety updated.'}), 200

    except Exception as e:
        return {
            'status': 500,
            'statusText': str(e)
        }
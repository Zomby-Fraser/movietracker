import requests
import blueprints.database as database
from dotenv import load_dotenv

load_dotenv()

conn = database.new_conn()


# Replace these with your actual client ID and access token
client_id = '472a8c2f7988932746210823828708957e6705c59e8246c9f58ce6cc44ce2dce'
access_token = '0553081f2dce23fd9c3b68223cdc8eb5ad96cd4093739ff5a6b626f683dc4248'

# Trakt API headers
headers = {
    'Content-Type': 'application/json',
    'trakt-api-version': '2',
    'trakt-api-key': client_id,
    'Authorization': f'Bearer {access_token}'
}

# Trakt API endpoint for your movie collection
url = 'https://api.trakt.tv/sync/collection/movies'

response = requests.get(url, headers=headers)
collection = response.json()

# Print the collection with TMDB and IMDb IDs
for item in collection:
    title = item['movie']['title']
    print(title)
    year = item['movie']['year']
    tmdb_id = item['movie']['ids'].get('tmdb')
    imdb_id = item['movie']['ids'].get('imdb')
    
    sql = f"SELECT movie_key, title, imdb_id, year_of_release, only_on_streaming_flag, no_blu_ray_release_flag, tmdb_id FROM Movies WHERE imdb_id = %s;"
    records = database.pull(conn, sql, (imdb_id,))

    if not records:
        sql = f"INSERT INTO Movies (`title`, `imdb_id`, `tmdb_id`, `year_of_release`) VALUES (%s, %s, %s, %s)"
        new_movie_key = database.execute(conn, sql, (title, imdb_id, tmdb_id, year))

        sql = f"INSERT INTO MovieCollection (movie_key, subtitles_needed, user_id, web_dl_flag) VALUES(%s, 0, 7, b'0');"
        database.execute(conn, sql, (new_movie_key, ))

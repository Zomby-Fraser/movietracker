from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import blueprints.database as database
import math

from flask import Blueprint
collection_page = Blueprint('collection', __name__)

@collection_page.route('/collection')
def loginPage():
    conn = database.new_conn()
    sql = '''
        SELECT 
            m.title AS title,
            m.movie_key AS movie_key,
            m.year_of_release AS year_of_release,
            mc.subtitles_needed AS subtitles_needed
        FROM MovieCollection mc
        INNER JOIN Movies m
        ON m.movie_key = mc.movie_key
        LIMIT 0, 50
    '''
    movies = database.pull(conn, sql)

    sql = '''
        SELECT 
            COUNT(*) AS cnt
        FROM MovieCollection mc
    '''
    movie_count = math.ceil(database.pull(conn, sql)[0]['cnt']/50)

    return render_template('collection.html', movies=movies, movie_count=movie_count)

@collection_page.route('/query_collection',  methods=['POST'])
def queryCollection():
    user_id = request.form.get('user_id')
    page = request.form.get('page')
    limit = int(page)*50

    conn = database.new_conn()

    sql = f'''
        SELECT 
            m.title AS title,
            m.movie_key AS movie_key,
            m.year_of_release AS year_of_release,
            mc.subtitles_needed AS subtitles_needed
        FROM MovieCollection mc
        INNER JOIN Movies m
        ON m.movie_key = mc.movie_key
        WHERE mc.user_id = %s
        LIMIT %s, 50
    '''
    movies = database.pull(conn, sql, (user_id, limit))
    divs = movieDivMaker(movies)

    return { 'divs': divs }, 200

@collection_page.route('/update_sub_status', methods=['POST'])
def updateSubStatus():
    user_id = request.form.get('user_id')
    status = request.form.get('status')
    movie_key = int(request.form.get('movie_key'))

    conn = database.new_conn()

    status = 1
    if status == 'added':
        status = 0
        
    sql = f"UPDATE MovieCollection SET subtitles_needed = %s WHERE user_id = %s AND movie_key = %s;"
    database.execute(conn, sql, (status, user_id, movie_key))

    return { 'response': 'Movie updated!' }, 200


def movieDivMaker(movies):
    divs = ""
    for movie in movies:
        title = movie['title']
        year_of_release = movie['year_of_release']
        subtitles_needed = movie['subtitles_needed']
        movie_key = movie['movie_key']
        row_class = ''
        if subtitles_needed:
            row_class = 'style="background-color: gold;" '

        divs += f'''
            <tr id="movie{movie_key}" {row_class}>
                <td>{title} ({year_of_release})</td>
                <td>
                    <button onclick="manageMovie({movie_key})">Manage Title</button>
                </td>
            </tr>
        '''

    return divs
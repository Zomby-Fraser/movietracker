from flask import Flask, render_template, request, jsonify, session
import hashlib
import mysql.connector
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import blueprints.database as database

from flask import Blueprint
movie_requests_page = Blueprint('movie_requests', __name__)

@movie_requests_page.route('/update_selected_source', methods=['POST'])
def updateSelectedSource():
    try:
        conn = database.new_conn()

        source_key = request.form.get('source_key')
        source_selection_flag = request.form.get('source_selection_flag')

        if source_selection_flag == "true":
            source_selection_flag = 1
        else:
            source_selection_flag = 0

        query = "UPDATE MovieSources SET source_selected = %s WHERE source_key = %s"
        database.execute(conn, query, (source_selection_flag,source_key))

        conn.close()

        return {
            'results': 'Success!'
        }

    except Exception as e:
        return {
            'status': 500,
            'statusText': str(e)
        }
    

@movie_requests_page.route('/add_source', methods=['POST'])
def addMovieSource():
    try:
        conn = database.new_conn()
        cursor = conn.cursor()

        movie_key = request.form.get('movie_key')
        source_name = request.form.get('source_name')
        source_tracker_key = request.form.get('source_tracker_key')
        source_size = request.form.get('source_size')
        query = '''
            INSERT INTO MovieSources (movie_key, source_name, size_in_gb, source_selected, source_torrent_tracker_key) VALUES(%s, %s, %s, b'0', %s);
        '''
        new_source_key = database.execute(conn, query, (movie_key, source_name, source_size, source_tracker_key))
        conn.close()

        return {
            'status': 200,
            'statusText': 'Source Added!',
            'sourceKey': new_source_key,
            'sourceMovieKey': movie_key,
            'sourceName': source_name
        }

    except Exception as e:
        return {
            'status': 500,
            'statusText': str(e)
        }
    
@movie_requests_page.route('/update_comment', methods=['POST'])
def updateMovieComment():
    try:
        conn = database.new_conn()

        movie_key = request.form.get('movie_key')
        movie_comment = request.form.get('movie_comment')
        query = '''
            UPDATE MoviesNeeded SET comment = %s WHERE movie_key = %s
        '''
        database.execute(conn, query, (movie_comment, movie_key))
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

@movie_requests_page.route('/mark_movie_as_downloaded', methods=['POST'])
def markMovieAsDownloaded():
    movie_key = request.form.get('movie_key')
    user_id = session['id']

    try:
        conn = database.new_conn()

        query = '''INSERT INTO MovieCollection (movie_key, user_id) VALUES (%s, %s)'''
        database.execute(conn, query, (movie_key, user_id))

        query = '''DELETE FROM MoviesNeeded WHERE movie_key = %s'''
        database.execute(conn, query, (movie_key,))

        conn.close()

        return jsonify({'message': 'Movie added to collection'}), 200

    except Exception as e:
        return jsonify({'status': 500,'statusText': str(e)}), 500
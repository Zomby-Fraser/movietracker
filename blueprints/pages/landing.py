from flask import Flask, render_template, request, jsonify, session
import hashlib
import mysql.connector
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import blueprints.database as database

from flask import Blueprint
landing_page = Blueprint('landing', __name__)

@landing_page.route('/')
def loginPage():
    registration_code = request.args.get('registration_code')
    if not registration_code:
        return render_template('login.html')
    else:
        conn = mysql.connector.connect()
        cursor = conn.cursor(dictionary=True) 
        query = "SELECT registration_code, registration_code_used_flag FROM RegistrationCodes WHERE registration_code = %s"
        cursor.execute(conn, query, (registration_code,))
        registration_check = cursor.fetchall()
        registration_check = registration_check[0]

        if len(registration_check) == 0:
            return "Invalid registration code.", 401
        elif registration_check['registration_code_used_flag']:
            return "Registration code already used.", 401
        
    return render_template('login.html', registration_check=registration_check)

@landing_page.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    print(password)

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        conn = database.new_conn()

        query = '''SELECT 
            u.id AS user_id,
            u.username AS username,
            ur.users_role_id AS role_id
        FROM Users u
        INNER JOIN UserRoles ur ON ur.users_id = u.id
        WHERE u.username = %s AND u.password = %s'''
        user = database.pull(conn, query, (username, hashed_password))
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
    except Exception as err:
        return jsonify({'error': str(err)}), 500
    
@landing_page.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        conn = database.new_conn()

        query = '''INSERT INTO Users (username, password) VALUES (%s, %s)'''
        new_user_id = database.execute(conn, query, (username, hashed_password))

        query = '''INSERT INTO UserRoles (users_id, users_role_id) VALUES (%s, 3)'''
        database.execute(conn, query, (new_user_id,))
        
        query = '''SELECT 
            u.id AS user_id,
            u.username AS username,
            ur.users_role_id AS role_id
        FROM Users u
        INNER JOIN UserRoles ur ON ur.users_id = u.id
        WHERE u.username = %s AND u.password = %s'''
        user = database.execute(conn, query, (username, hashed_password))

        user = user[0]

        if user:
            session['role_id'] = user['role_id']
            session['id'] = user['user_id']
            session['username'] = user['username']

            query = '''UPDATE RegistrationCodes SET registration_code_date_used = CURRENT_TIMESTAMP, registration_code_used_flag = 1, registration_code_user_id = %s'''
            database.execute(conn, query, (session['id'],))

            conn.close()
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(err)}), 500
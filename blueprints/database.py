import mysql.connector
import os

def new_conn():
    db_host = os.environ.get('DB_HOST')
    print(db_host)
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')
    db = os.environ.get('DB')
    db_config = {
        'host': db_host,
        'user': db_user,
        'password': db_pass,
        'database': db
    }
    return mysql.connector.connect(**db_config)

def pull(conn, query, params = None):
    cursor = conn.cursor(dictionary=True) 
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    return results

def execute(conn, query, params = None):
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    return new_id

def process_title(conn, movie_name):
    cursor = conn.cursor(dictionary=True) 
    query = "SELECT movie_prefix FROM MoviePrefixes WHERE movie_prefix_disabled_flag = 0"
    cursor.execute(query)
    prefixes = cursor.fetchall()
    for prefix in prefixes:
        prefix = prefix['movie_prefix']
        if movie_name.startswith(prefix):
            return movie_name[len(prefix):] + ", " + prefix.strip()
    return movie_name

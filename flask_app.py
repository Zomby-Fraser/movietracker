from flask import Flask, render_template, request, jsonify, session, Blueprint
import hashlib
import mysql.connector
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import blueprints.database as database
import pkgutil
import importlib

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET')

pages_path = os.path.join(os.path.dirname(__file__), 'blueprints', 'pages')
pages_package = 'blueprints.pages'

for (_, name, _) in pkgutil.iter_modules([pages_path]):
    print(f'Loading module: {pages_package}.{name}')
    module = importlib.import_module(f'{pages_package}.{name}')
    for item in dir(module):
        obj = getattr(module, item)
        if isinstance(obj, Blueprint):
            app.register_blueprint(obj)

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    return 'You have been logged out.'

if __name__ == '__main__':
    app.run(debug=True, port=5001)


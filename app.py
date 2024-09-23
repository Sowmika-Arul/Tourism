from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import current_user
import mysql.connector
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# MySQL Database configuration
config = {
    'user': 'root',
    'password': '11-Apr-05',
    'host': 'localhost',
    'database': 'tour',
    'raise_on_warnings': True
}

# Connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(**config)

# Route to display login form
@app.route('/')
def login():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
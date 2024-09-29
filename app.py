from flask import Flask, render_template
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

# Fetch travel package data from the database
def get_travel_packages():
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT destination_name, image_url, highlights, total_days, amount FROM travel_packages"
    cursor.execute(query)
    packages = cursor.fetchall()  # Fetch all rows from travel_packages table
    cursor.close()
    connection.close()
    return packages

@app.route('/')
def index():
    return render_template('index.html')

# Route to display travel packages
@app.route('/places')
def show_travel_packages():
    travel_packages = get_travel_packages()  # Fetch data from the DB
    return render_template('places.html', packages=travel_packages)  # Pass data to the template

if __name__ == '__main__':
    app.run(debug=True)

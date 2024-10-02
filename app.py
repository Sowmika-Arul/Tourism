from flask import Flask, render_template, request, redirect, url_for, session, flash
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
    query = "SELECT destination_name, image_url, hotel, transport, amount FROM travel_packages"
    cursor.execute(query)
    packages = cursor.fetchall()  # Fetch all rows from travel_packages table
    cursor.close()
    connection.close()
    return packages

# Fetch user from the database
def get_user(username, password):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user

@app.route('/')
def index():
    return render_template('index.html')

# Route to display travel packages
@app.route('/places')
def show_travel_packages():
    travel_packages = get_travel_packages()  # Fetch data from the DB
    return render_template('places.html', packages=travel_packages)  # Pass data to the template

# Route for user login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Validate user credentials
    user = get_user(username, password)
    if user:
        session['username'] = username  # Store the username in session
        flash('Login successful!', 'success')
        return redirect(url_for('show_travel_packages'))  # Redirect to the travel packages page
    else:
        flash('Invalid username or password', 'danger')
        return redirect(url_for('index'))  # Redirect back to the index page

# Route to logout
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))  # Redirect to the index page

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import secrets
from datetime import datetime  

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
@app.route('/packages')
def show_travel_packages():
    travel_packages = get_travel_packages()  # Fetch data from the DB
    return render_template('packages.html', packages=travel_packages)  # Pass data to the template
# Route to display and book a travel package

@app.route('/book_package', methods=['GET', 'POST'])
def book_package():
    # Get the package name from the URL parameters
    package_name = request.args.get('package_name')
    print(package_name)
    # Fetch the selected package details from the database based on the package_name
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch package details from the database
    query = "SELECT * FROM travel_packages WHERE destination_name = %s"
    formatted_query = query % repr(package_name)
    print(formatted_query)
    cursor.execute(query, (package_name,))
    selected_package = cursor.fetchone()
    print(selected_package);
    
    if request.method == 'POST':
        # Handle the booking logic when the form is submitted
        booking_date = request.form['date']
        username = session.get('username')  # Assuming username is stored in the session

        # Ensure the user is logged in
        if not username:
            flash('You must be logged in to book a package.', 'danger')
            return redirect(url_for('auth'))  # Redirect to the login/signup page if not logged in
        
        # Insert the booking details into the database
        query = """
            INSERT INTO pack_bookings (username, package_name, hotel, transport, price, booking_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            username,
            selected_package['destination_name'],
            selected_package['hotel'],
            selected_package['transport'],
            selected_package['amount'],
            booking_date
        ))
        connection.commit()
        
        flash('Your booking is confirmed!', 'success')
        return redirect(url_for('book_package', package_name=selected_package['destination_name']))  # Redirect to the same page
    
    cursor.close()
    connection.close()
    
    return render_template('form_page.html', selected_package=selected_package)

@app.route('/select_package/<package_name>', methods=['POST'])
def store_selected_package(package_name):
    # Store the selected package in the session
    session['selected_package'] = package_name
    return redirect(url_for('auth'))  # Redirect to login page if not logged in

# Route to handle user signup/login
@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        if 'signup' in request.form:
            # Handle signup
            username = request.form['signup-username']
            email = request.form['email']
            password = request.form['signup-password']
            phone = request.form['phone']
            
            # Insert user details into the database
            connection = get_db_connection()
            cursor = connection.cursor()
            try:
                query = "INSERT INTO users (username, email, password, phone) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (username, email, password, phone))
                connection.commit()
                flash('Signup successful! Please log in.', 'success')
                return redirect(url_for('auth'))
            except mysql.connector.Error as err:
                flash('Signup failed. Please try again.', 'danger')
            finally:
                cursor.close()
                connection.close()
        
        elif 'login' in request.form:
            # Handle login
            username = request.form['username']
            password = request.form['password']
            
            # Validate user credentials
            connection = get_db_connection()
            cursor = connection.cursor()
            query = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
            cursor.close()
            connection.close()  
            
            if user:
                session['username'] = username
                flash('Login successful!', 'success')

                # Check if there's a selected package in the session
                if 'selected_package' in session:
                    selected_package = session['selected_package']
                    return redirect(url_for('book_package', package_name=selected_package))  # Redirect to booking page
                else:
                    return redirect(url_for('home')) 
                 # Or any default page after  # Or any default page after login
            else:
                flash('Invalid username or password', 'danger')
    
    return render_template('auth.html')  # Render the login/signup page

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth'))

if __name__ == '__main__':
    app.run(debug=True)

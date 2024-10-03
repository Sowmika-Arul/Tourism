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

# Fetch hotel details with search functionality
def get_hotel_details(search_hotel=None, search_location=None):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        SELECT hotel_name, location, amount, rating, single_rooms_available, 
               double_rooms_available, amenities, contact_info
        FROM hotel_details
    """
    conditions = []
    params = []
    
    if search_hotel:
        conditions.append("hotel_name LIKE %s")
        params.append(f"%{search_hotel}%")
        
    if search_location:
        conditions.append("location LIKE %s")
        params.append(f"%{search_location}%")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, params)
    hotels = cursor.fetchall()
    cursor.close()
    connection.close()
    return hotels

# Fetch single hotel details from the database by hotel name
def get_hotel_by_name(hotel_name):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        SELECT hotel_name, location, amount, rating, single_rooms_available, 
               double_rooms_available, amenities, contact_info, image
        FROM hotel_details WHERE hotel_name = %s
    """
    cursor.execute(query, (hotel_name,))
    hotel = cursor.fetchone()  # Fetch the single row for the selected hotel
    cursor.close()
    connection.close()
    return hotel

# Fetch tourist places from the database
def get_tourist_places():
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT place_name, location, opening_time, closing_time, rating, image_url FROM tourist_places"
    cursor.execute(query)
    places = cursor.fetchall()  # Fetch all rows from tourist_places table
    cursor.close()
    connection.close()
    return places

@app.route('/')
def index():
    return render_template('index.html')

# Route to display travel packages
@app.route('/packages')
def show_travel_packages():
    travel_packages = get_travel_packages()  # Fetch data from the DB
    return render_template('packages.html', packages=travel_packages)  # Pass data to the template

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

# Route to display hotel details with search functionality
@app.route('/hotels', methods=['GET', 'POST'])
def show_hotel_details():
    search_hotel = request.form.get('search_hotel')  # Get search term for hotel name
    search_location = request.form.get('search_location')  # Get search term for location
    
    hotel_details = get_hotel_details(search_hotel, search_location)  # Fetch filtered hotel details
    return render_template('hotel.html', hotels=hotel_details)  # Pass data to the template

# Route to handle hotel booking
@app.route('/book_hotel/<hotel_name>', methods=['GET', 'POST'])
def book_hotel(hotel_name):
    # Fetch hotel details
    hotel = get_hotel_by_name(hotel_name)
    
    if request.method == 'POST':
        # Handle booking form submission here
        customer_name = request.form['customer_name']
        email = request.form['email']
        phone = request.form['phone']
        rooms = request.form['rooms']
        check_in_date = request.form['check_in_date']
        check_out_date = request.form['check_out_date']
        
        # Perform booking logic (store booking in the database, etc.)
        # You might want to save check_in_date and check_out_date to your booking table in the database
        flash(f'Booking confirmed for {hotel_name} from {check_in_date} to {check_out_date}.', 'success')
        
        return redirect(url_for('index'))  # Redirect to the homepage after booking confirmation
    
    # If the method is GET, render the booking page with hotel details
    return render_template('book_hotel.html', hotel=hotel)

# Route to display tourist places
@app.route('/tourist_places')
def show_tourist_places():
    tourist_places = get_tourist_places()  # Fetch data from the DB
    return render_template('tourist_places.html', places=tourist_places)  # Pass data to the template

if __name__ == '__main__':
    app.run(debug=True)

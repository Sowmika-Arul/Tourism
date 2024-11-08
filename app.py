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

# Route to display hotel details with search functionality
@app.route('/hotels', methods=['GET', 'POST'])
def show_hotel_details():
    search_hotel = request.form.get('search_hotel')  # Get search term for hotel name
    search_location = request.form.get('search_location')  # Get search term for location
    
    hotel_details = get_hotel_details(search_hotel, search_location)  # Fetch filtered hotel details
    return render_template('hotel.html', hotels=hotel_details)  # Pass data to the template

@app.route('/book_hotel/<hotel_name>', methods=['GET', 'POST'])
def book_hotel(hotel_name):
    # Fetch hotel details
    hotel = get_hotel_by_name(hotel_name)
    
    if request.method == 'POST':
        # Get booking details from the form
        adults = int(request.form['adults'])
        children = int(request.form['children'])
        room_type = request.form['room_type']
        rooms = int(request.form['rooms'])
        check_in_date = request.form['check_in_date']
        check_out_date = request.form['check_out_date']
        
        # Calculate the total amount based on room type and number of rooms
        amount_per_night = hotel[2]  # Assuming hotel[2] contains the price per night
        number_of_nights = (datetime.strptime(check_out_date, '%Y-%m-%d') - datetime.strptime(check_in_date, '%Y-%m-%d')).days
        total_amount = amount_per_night * rooms * number_of_nights

        # Handle booking logic (store booking in the database, etc.)
        # Save check_in_date, check_out_date, and total_amount to your bookings table in the database
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            query = """
            INSERT INTO bookings (username, hotel_name, rooms, check_in_date, check_out_date, amount, adults, children, room_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (session['username'], hotel_name, rooms, check_in_date, check_out_date, total_amount, adults, children, room_type))
            connection.commit()
            flash(f'Booking confirmed for {hotel_name} from {check_in_date} to {check_out_date}. Total Amount: ${total_amount}', 'success')
        except mysql.connector.Error as err:
            flash('Booking failed. Please try again.', 'danger')
        finally:
            cursor.close()
            connection.close()
        
        return redirect(url_for('index'))  # Redirect to the homepage after booking confirmation
    
    # If the method is GET, render the booking page with hotel details
    return render_template('book_hotel.html', hotel=hotel)

# Route to display tourist places
@app.route('/tourist_places')
def show_tourist_places():
    tourist_places = get_tourist_places()  # Fetch data from the DB
    return render_template('tourist_places.html', places=tourist_places)  # Pass data to the template

# Fetch tourist places and hotel details by destination
def get_places_and_hotels(destination):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Query to fetch tourist places
    query_places = """
        SELECT place_name, location, opening_time, closing_time, rating, image_url 
        FROM tourist_places 
        WHERE location LIKE %s
    """
    cursor.execute(query_places, (f"%{destination}%",))
    places = cursor.fetchall()

    # Query to fetch hotel details
    query_hotels = """
        SELECT hotel_name, location, amount, rating, single_rooms_available, 
               double_rooms_available, amenities, contact_info, image
        FROM hotel_details 
        WHERE location LIKE %s
    """
    cursor.execute(query_hotels, (f"%{destination}%",))
    hotels = cursor.fetchall()

    cursor.close()
    connection.close()
    
    return places, hotels


# Route to handle destination search
@app.route('/search', methods=['POST'])
def search():
    destination = request.form['destination']  # Get the destination from the form
    places, hotels = get_places_and_hotels(destination)  # Fetch data from the DB
    return render_template('search_results.html', places=places, hotels=hotels, destination=destination)

@app.route("/contact", methods=['GET'])
def contact():
     return render_template('contact.html')

@app.route('/search_places', methods=['GET'])
def search_places():
    location = request.args.get('location', '').lower()
    all_places = get_tourist_places()  # Fetch all tourist places from the database
    filtered_places = [place for place in all_places if location in place[1].lower()]
    return render_template('tourist_places.html', places=filtered_places)

@app.route('/profile')
def profile():
    if 'username' not in session:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
    
    username = session['username']
    user_info = get_user_info(username)
    bookings = get_user_bookings(username)
    
    return render_template('profile.html', user=user_info, bookings = bookings)

# Function to fetch user info (assuming there's a 'users' table with basic user data)
def get_user_info(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT username, email, phone FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user_info = cursor.fetchone()
    cursor.close()
    connection.close()
    return user_info

# Function to fetch user bookings
def get_user_bookings(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        SELECT hotel_name, rooms, check_in_date, check_out_date, amount
        FROM bookings
        WHERE username = %s
        ORDER BY check_in_date DESC
    """
    cursor.execute(query, (username,))
    bookings = cursor.fetchall()
    cursor.close()
    connection.close()
    return bookings

# Route to display the signup/login page and handle signup/login
@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        if 'signup' in request.form:
            # Handle signup
            username = request.form['signup-username']  # Changed to match the new input name
            email = request.form['email']
            password = request.form['signup-password']  # Changed to match the new input name
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
            username = request.form['username']  # This should remain as it is
            password = request.form['password']  # This should remain as it is
            
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
                return redirect(url_for('profile'))  # Redirect to the profile page
            else:
                flash('Invalid username or password', 'danger')
    
    return render_template('auth.html')  # Render the combined login/signup page

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

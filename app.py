from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import secrets
from datetime import datetime  

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

config = {
    'user': 'root',
    'password': '11-Apr-05',
    'host': 'localhost',
    'database': 'tour',
    'raise_on_warnings': True
}

def get_db_connection():
    return mysql.connector.connect(**config)

def get_travel_packages():
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT destination_name, image_url, hotel, transport, amount FROM travel_packages"
    cursor.execute(query)
    packages = cursor.fetchall()  
    cursor.close()
    connection.close()
    return packages

def get_user(username, password):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user

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

def get_hotel_by_name(hotel_name):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        SELECT hotel_name, location, amount, rating, single_rooms_available, 
               double_rooms_available, amenities, contact_info, image
        FROM hotel_details WHERE hotel_name = %s
    """
    cursor.execute(query, (hotel_name,))
    hotel = cursor.fetchone()  
    cursor.close()
    connection.close()
    return hotel


def get_tourist_places():
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT place_name, location, opening_time, closing_time, rating, image_url FROM tourist_places"
    cursor.execute(query)
    places = cursor.fetchall()  
    cursor.close()
    connection.close()
    return places

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/packages')
def show_travel_packages():
    travel_packages = get_travel_packages()  
    return render_template('packages.html', packages=travel_packages)  


@app.route('/hotels', methods=['GET', 'POST'])
def show_hotel_details():
    search_hotel = request.form.get('search_hotel')  
    search_location = request.form.get('search_location')  
    
    hotel_details = get_hotel_details(search_hotel, search_location)  
    return render_template('hotel.html', hotels=hotel_details) 

@app.route('/book_hotel/<hotel_name>', methods=['GET', 'POST'])
def book_hotel(hotel_name):
   
    hotel = get_hotel_by_name(hotel_name)

   
    if 'username' not in session:
        return redirect(url_for('auth'))  
    
    if request.method == 'POST':
      
        adults = int(request.form['adults'])
        children = int(request.form['children'])
        room_type = request.form['room_type']
        rooms = int(request.form['rooms'])
        check_in_date = request.form['check_in_date']
        check_out_date = request.form['check_out_date']
        
      
        amount_per_night = hotel[2]  
        number_of_nights = (datetime.strptime(check_out_date, '%Y-%m-%d') - datetime.strptime(check_in_date, '%Y-%m-%d')).days
        total_amount = amount_per_night * rooms * number_of_nights

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
        
        return redirect(url_for('index'))  
    
  
    return render_template('book_hotel.html', hotel=hotel)


@app.route('/tourist_places')
def show_tourist_places():
    tourist_places = get_tourist_places()  
    return render_template('tourist_places.html', places=tourist_places)  

def get_places_and_hotels(destination):
    connection = get_db_connection()
    cursor = connection.cursor()
   
    query_places = """
        SELECT place_name, location, opening_time, closing_time, rating, image_url 
        FROM tourist_places 
        WHERE location LIKE %s
    """
    cursor.execute(query_places, (f"%{destination}%",))
    places = cursor.fetchall()
 
    query_hotels = """
        SELECT hotel_name, location, amount, rating, single_rooms_available, 
               double_rooms_available, amenities, contact_info, image
        FROM hotel_details 
        WHERE location LIKE %s
    """
    cursor.execute(query_hotels, (f"%{destination}%",))
    hotels = cursor.fetchall()

    query_transport = """
        SELECT from_place, to_place, mode_of_transport, travel_time 
        FROM transport 
        WHERE from_place LIKE %s OR to_place LIKE %s
    """
    cursor.execute(query_transport, (f"%{destination}%", f"%{destination}%"))
    transport = cursor.fetchall()

    cursor.close()
    connection.close()
    
    return places, hotels, transport


@app.route('/search', methods=['POST'])
def search():
    destination = request.form['destination']  
    places, hotels, transport = get_places_and_hotels(destination)  
    return render_template('search_results.html', places=places, hotels=hotels, transport=transport, destination=destination)

@app.route("/contact", methods=['GET'])
def contact():
     return render_template('contact.html')

@app.route('/search_places', methods=['GET'])
def search_places():
    location = request.args.get('location', '').lower()
    all_places = get_tourist_places()  
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
    package_bookings = get_user_book(username)
    
    return render_template('profile.html', user=user_info, bookings = bookings, package_bookings = package_bookings)


def get_user_info(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT username, email, phone FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user_info = cursor.fetchone()
    cursor.close()
    connection.close()
    return user_info


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

def get_user_book(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        SELECT package_name ,hotel, transport, price, booking_date
        FROM pack_bookings
        WHERE username = %s
        ORDER BY booking_date DESC
    """
    cursor.execute(query, (username,))
    package_bookings = cursor.fetchall()
    cursor.close()
    connection.close()
    return package_bookings


@app.route('/book_package', methods=['GET', 'POST'])
def book_package():
  
    package_name = request.args.get('package_name')
    print(package_name)
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    
    query = "SELECT * FROM travel_packages WHERE destination_name = %s"
    formatted_query = query % repr(package_name)
    print(formatted_query)
    cursor.execute(query, (package_name,))
    selected_package = cursor.fetchone()
    print(selected_package);
    
    if request.method == 'POST':
       
        booking_date = request.form['date']
        username = session.get('username')  

        if not username:
            flash('You must be logged in to book a package.', 'danger')
            return redirect(url_for('auth'))  
        
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
        return redirect(url_for('profile'))  
    
    cursor.close()
    connection.close()
    
    return render_template('form_page.html', selected_package=selected_package)

@app.route('/select_package/<package_name>', methods=['POST'])
def store_selected_package(package_name):
  
    if 'username' in session:
        
        return redirect(url_for('book_package', package_name=package_name))
    else:
       
        session['selected_package'] = package_name
        return redirect(url_for('auth'))

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        if 'signup' in request.form:
    
            username = request.form['signup-username']
            email = request.form['email']
            password = request.form['signup-password']
            phone = request.form['phone']
            
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

            username = request.form['username']
            password = request.form['password']
            
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

               
                if 'selected_package' in session:
                    selected_package = session['selected_package']
                    return redirect(url_for('book_package', package_name=selected_package)) 
                else:
                    return redirect(url_for('profile')) 
            else:
                flash('Invalid username or password', 'danger')
    
    return render_template('auth.html')  

@app.route('/delete_hotel_booking', methods=['POST'])
def delete_hotel_booking():
    if 'username' not in session:
        flash('You need to log in to delete a booking.', 'warning')
        return redirect(url_for('auth'))

    username = session['username']
    hotel_name = request.form['hotel_name']
    check_in_date = request.form['check_in_date']

    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        DELETE FROM bookings
        WHERE username = %s AND hotel_name = %s AND check_in_date = %s
    """
    cursor.execute(query, (username, hotel_name, check_in_date))
    connection.commit()
    cursor.close()
    connection.close()

    flash(f'Hotel booking for {hotel_name} on {check_in_date} has been deleted.', 'success')
    return redirect(url_for('profile'))

@app.route('/delete_package_booking', methods=['POST'])
def delete_package_booking():
    if 'username' not in session:
        flash('You need to log in to delete a package booking.', 'warning')
        return redirect(url_for('auth'))

    username = session['username']
    package_name = request.form['package_name']
    booking_date = request.form['booking_date']

    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        DELETE FROM pack_bookings
        WHERE username = %s AND package_name = %s AND booking_date = %s
    """
    cursor.execute(query, (username, package_name, booking_date))
    connection.commit()
    cursor.close()
    connection.close()

    flash(f'Package booking for {package_name} on {booking_date} has been deleted.', 'success')
    return redirect(url_for('profile'))

@app.route('/update_user_info', methods=['POST'])
def update_user_info():
    new_username = request.form['username']
    new_email = request.form['email']
    new_phone = request.form['phone']

    user_id = session.get('user_id')
    
  
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET username = ?, email = ?, phone = ? WHERE id = ?
    """, (new_username, new_email, new_phone, user_id))
    conn.commit()
    conn.close()

    
    return redirect(url_for('profile')) 


@app.route('/logout')
def logout():
    session.clear() 
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))  #

if __name__ == '__main__':
    app.run(debug=True)
# imports
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit
from algorithm import weatherbitAPI
from algorithm import pollenAPI

# setups and global variables
app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)
returns, outputs, cue, username, login_message, tgwm = [], [], False, "", "", []

# unpack flare_ups
def unpackflareups():
    severity_list = []
    with open('flareupdatabase.txt', 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            flare_data = line.split(',')
            print(flare_data)
            if len(flare_data) != 3:
                continue  # Skip lines with incorrect format
            severity_list.append(flare_data[-1])
            return severity_list

# socketio shine chat
@socketio.on('join')
def handle_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('user_join', {'username': username}, room=room)


@socketio.on('leave')
def handle_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('user_leave', {'username': username}, room=room)


@socketio.on('message')
def handle_message(data):
    username = data['username']
    room = data['room']
    message = data['message']
    emit('new_message', {'username': username, 'message': message}, room=room)

# app routes
@app.route('/templates/index')
def home():
    global login_message
    return render_template('index.html', login_message=login_message, official_username=username)

@app.route('/templates/environment')
def environment():
    global login_message
    global cue
    if cue:
        # weatherbit API 1
        lat = returns[0]
        lon = returns[1]
        weatherbits = weatherbitAPI(lat, lon)
        uv_index = round(weatherbits[0])
        temperature = weatherbits[1]
        humidity = weatherbits[2]
        # weatherbit API 2
        weatherbits2 = pollenAPI(lat, lon)
        treepollen = weatherbits2[0]
        grasspollen = weatherbits2[1]
        weedpollen = weatherbits2[2]
        mold = weatherbits2[3]
        mostpollen = weatherbits2[4]
        outputs.extend((uv_index, temperature, humidity, treepollen, grasspollen, weedpollen, mold, mostpollen))
        exercise_report = classify2() # just to get tgwm for now
        cue = False
    return render_template('environment.html', outputs=outputs, login_message=login_message, official_username=username, tgwm = tgwm)

@app.route('/templates/exercise')
def exercise():
    global cue
    global login_message
    if cue:
        # weatherbit API 1
        lat = returns[0]
        lon = returns[1]
        weatherbits = weatherbitAPI(lat, lon)
        uv_index = round(weatherbits[0])
        temperature = weatherbits[1]
        humidity = weatherbits[2]
        # weatherbit API 2
        weatherbits2 = pollenAPI(lat, lon)
        treepollen = weatherbits2[0]
        grasspollen = weatherbits2[1]
        weedpollen = weatherbits2[2]
        mold = weatherbits2[3]
        mostpollen = weatherbits2[4]
        outputs.extend((uv_index, temperature, humidity, treepollen, grasspollen, weedpollen, mold, mostpollen))
        cue = False
    exercise_report = classify()
    return render_template('exercise.html', outputs=outputs, login_message=login_message, official_username=username, exercise_report=exercise_report)

@app.route('/templates/flare_ups')
def flare_ups():
    global login_message
    return render_template('flare_ups.html', login_message=login_message, official_username=username)
    
@app.route('/flare_ups', methods=['POST'])
def receive_flareups():
    flareups = request.get_json()
    with open('flareupdatabase.txt', 'a') as file:
        for flareup in flareups:
            line = f"{flareup['startDate']},{flareup['endDate']},{flareup['severity']}\n"
            file.write(line)
    return 'Flare-ups received'


@app.route('/templates/connections')
def connections():
    global login_message
    global username
    logged_in = 'username' in session
    return render_template('connections.html', login_message=login_message, official_username=username, logged_in=logged_in)


@app.route('/transfer', methods=['POST'])
def transfer():
    global returns
    global cue
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    returns.extend((latitude, longitude))
    cue = True
    return f"Latitude: {latitude}\nLongitude: {longitude}"

@app.route('/templates/account', methods=['GET'])
def account():
    global login_message
    signup_message = request.args.get('signup_message')
    login_message = request.args.get('login_message')
    return render_template('account.html', signup_message=signup_message, login_message=login_message)

# Handle POST request for the login form
@app.route('/templates/account', methods=['POST'])
def login():
    global login_message
    global username
    username = request.form.get('username')
    session['username'] = username
    password = request.form.get('password')
    if check_credentials(username, password):
        login_message = 'Logged in successfully!'
        return redirect(url_for('account', login_message=login_message, official_username=username))
    else:
        login_message = 'Invalid username or password. Please try again.'
        return redirect(url_for('account', login_message=login_message))

# Handle POST request for the sign-up form
@app.route('/signup', methods=['POST'])
def signup():
    global username
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    # Store the sign-up information in the database
    store_account_info(first_name, last_name, email, username, password)
    signup_message = 'Sign up successful!'
    return render_template('account.html', signup_message=signup_message)

# Handle POST request to clear session data (logout)
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('account'))

def check_credentials(username, password):
    with open('accountdatabase.txt', 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            account_info = line.split(',')
            if len(account_info) != 5:
                continue  # Skip lines with incorrect format
            stored_password = account_info[-1]
            stored_username = account_info[-2]
            if stored_username.strip() == username and stored_password.strip() == password:
                return True
    return False

def store_account_info(first_name, last_name, email, username, password):
    account_info = f"{first_name},{last_name},{email},{username},{password}\n"
    with open('accountdatabase.txt', 'a') as file:
        file.write(account_info)

# exercise algorithm and classification
def classify():
    global outputs
    classification = 0
    classification = classification + uv_index(outputs) + temperature(outputs) + humidity(outputs) + treepollen(outputs) + grasspollen(outputs) + weedpollen(outputs) + moldlevel(outputs) + predominantpollentype(outputs) + pastflareups(outputs)
    if 80 <= classification <= 100:
        classification = "very Likely"
    elif 50 <= classification <= 79:
        classification = "likely"
    elif 20 <= classification <= 49:
        classification = "unlikely"
    else:
        classification = "very Unlikely"
    return classification

def classify2():
    global outputs
    classification = 0
    classification = classification + uv_index(outputs) + temperature(outputs) + humidity(outputs) + treepollen(outputs) + grasspollen(outputs) + weedpollen(outputs) + moldlevel(outputs) + predominantpollentype(outputs)
    if 80 <= classification <= 100:
        classification = "very Likely"
    elif 50 <= classification <= 79:
        classification = "likely"
    elif 20 <= classification <= 49:
        classification = "unlikely"
    else:
        classification = "very Unlikely"
    return classification

# uv_index
def uv_index(outputs):
    if 0 <= outputs[0] <= 2:
        return 5
    elif 3 <= outputs[0] <= 5:
        return 7
    elif 6 <= outputs[0] <= 7:
        return 10
    elif 8 <= outputs[0] <= 10:
        return 15
    else:
        return 20

# temperature
def temperature(outputs):
    if outputs[1] <= 50:
        return 3
    elif 50 <= outputs[1] <= 80:
        return 7
    else:
        return 10

# humidity
def humidity(outputs):
    if 30 <= outputs[2] <= 50:
        return 3
    elif 50 <= outputs[2] <= 80:
        return 7
    else:
        return 10

# treepollen
def treepollen(outputs):
    global tgwm
    if outputs[3]==0:
        tgwm.append('None')
        return 1
    elif outputs[3]==1:
        tgwm.append('Low')
        return 3
    elif outputs[3]==2:
        tgwm.append('Moderate')
        return 5
    elif outputs[3]==3:
        tgwm.append('High')
        return 7
    else:
        tgwm.append('Very High')
        return 10

# grasspollen
def grasspollen(outputs):
    global tgwm
    if outputs[4]==0:
        tgwm.append('None')
        return 1
    elif outputs[4]==1:
        tgwm.append('Low')
        return 3
    elif outputs[4]==2:
        tgwm.append('Moderate')
        return 5
    elif outputs[4]==3:
        tgwm.append('High')
        return 7
    else:
        tgwm.append('Very High')
        return 10

# weedpollen
def weedpollen(outputs):
    global tgwm
    if outputs[5]==0:
        tgwm.append('None')
        return 1
    elif outputs[5]==1:
        tgwm.append('Low')
        return 3
    elif outputs[5]==2:
        tgwm.append('Moderate')
        return 5
    elif outputs[5]==3:
        tgwm.append('High')
        return 7
    else:
        tgwm.append('Very High')
        return 10

# moldlevel
def moldlevel(outputs):
    global tgwm
    if outputs[6]==0:
        tgwm.append('None')
        return 1
    elif outputs[6]==1:
        tgwm.append('Low')
        return 3
    elif outputs[6]==2:
        tgwm.append('Moderate')
        return 5
    elif outputs[6]==3:
        tgwm.append('High')
        return 7
    else:
        tgwm.append('Very High')
        return 10

# predominantpollentype
def predominantpollentype(outputs):
    if outputs[7]=='Weeds':
        return 3
    elif outputs[7]=='Trees':
        return 5
    elif outputs[7]=='Molds':
        return 7
    else:
        return 10

# pastflareups
def pastflareups(outputs):
    severity_score = 0
    severity_list = unpackflareups()
    for level in severity_list:
        if level=="Low":
            severity_score += 1
        elif level=="Medium":
            severity_score += 5
        else:
            severity_score += 10
    return severity_score

# CALLING EVERYTHING TOGETHER
if __name__ == '__main__':
    socketio.run(app)

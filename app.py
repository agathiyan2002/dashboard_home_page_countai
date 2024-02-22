from flask import Flask, render_template
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

FIREBASE_URL = 'https://dashboard-api-62cdd-default-rtdb.firebaseio.com/'

@app.route('/')
def home():
    # Fetch data from Firebase
    firebase_data = fetch_firebase_data()
    online_count, offline_count = count_online_offline_mills(firebase_data)

    # Pass the data to the template
    return render_template('home.html', firebase_data=firebase_data, online_count=online_count, offline_count=offline_count)

def fetch_firebase_data():
    try:
        response = requests.get(FIREBASE_URL + '.json')
        response.raise_for_status()
        firebase_data = response.json()

        # Convert the structure to a list of dictionaries
        formatted_data = [{key: value} for key, value in firebase_data.items()]

        return formatted_data
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Request Error: {err}")
    return None

def count_online_offline_mills(firebase_data):
    online_count = 0
    offline_count = 0

    current_time = datetime.now()

    for mill_data in firebase_data:
        for key, data in mill_data.items():
            sending_time = datetime.strptime(data['sending_time'], '%Y-%m-%d %H:%M:%S')
            time_difference = current_time - sending_time

            if time_difference.total_seconds() <= 60:  # 1800 seconds = 30 minutes
                data['status'] = 'online'
                online_count += 1
            else:
                data['status'] = 'offline'
                offline_count += 1

    return online_count, offline_count

if __name__ == '__main__':
    app.run(debug=True)

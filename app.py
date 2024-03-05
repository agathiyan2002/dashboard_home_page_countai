from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

FIREBASE_URL = "https://dashboard-api-62cdd-default-rtdb.firebaseio.com/"


@app.route("/")
def home():
    firebase_data = fetch_firebase_data()
    online_count, offline_count = count_online_offline_mills(firebase_data)
    return render_template(
        "home.html",
        firebase_data=firebase_data,
        online_count=online_count,
        offline_count=offline_count,
    )


@app.route("/details/<mill_key>")
def details(mill_key):
    firebase_data = fetch_firebase_data()

    for mill_data in firebase_data:
        for key, data in mill_data.items():
            if mill_key in key:
                uptime_data = data.get("uptime", [])
                status = calculate_status(uptime_data)
                data["status"] = status

    # Filter firebase_data to get details for the selected mill_key
    mill_details = next((data for data in firebase_data if mill_key in data), None)
    mill_value = mill_details[mill_key]

    # Additional data from the query parameters
    details_screen_data = mill_details[mill_key]["details_Screen_data"]

    uptime_data = mill_details[mill_key]["uptime"]
    system_storage_data = mill_details.get(mill_key, {}).get("system_storage")

    # Calculate the status based on the last entry in the uptime data
    status = calculate_status(uptime_data)

    return render_template(
        "details_screen.html",
        mill_details=mill_value,
        firebase_data=firebase_data,
        details_screen_data=details_screen_data,
        uptime=uptime_data,
        system_storage=system_storage_data,
        status=status,
    )


def calculate_status(uptime_data):
    if uptime_data:
        # Get the last entry in the uptime list
        last_entry = uptime_data[-1]

        # Extract the timestamp from the last entry
        timestamp_str = last_entry.get("timestamp")

        if timestamp_str:
            # Convert the timestamp to a datetime object
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            # Get the current time
            current_time = datetime.now()

            # Calculate the time difference
            time_difference = current_time - timestamp

            # Check if the system is online (within the last 2 minutes, for example)
            if time_difference.total_seconds() <= 120:
                return "online"
            else:
                return "offline"
        else:
            return "Timestamp not found in the last entry"
    else:
        return "No uptime data available"


@app.route("/refresh_data")
def refresh_data():
    firebase_data = fetch_firebase_data()
    online_count, offline_count = count_online_offline_mills(firebase_data)
    return jsonify(
        {
            "online_count": online_count,
            "offline_count": offline_count,
            # Add other data you want to refresh here
        }
    )


def fetch_firebase_data():
    try:
        response = requests.get(FIREBASE_URL + ".json")
        response.raise_for_status()
        firebase_data = response.json()
        formatted_data = [{key: value} for key, value in firebase_data.items()]
        return formatted_data
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return None


def count_online_offline_mills(firebase_data):
    online_count = 0
    offline_count = 0
    current_time = datetime.now()
    for mill_data in firebase_data:
        for key, data in mill_data.items():
            uptime_data = data.get("uptime", [])

            if uptime_data:
                last_entry = uptime_data[-1]
                time_difference = current_time - datetime.strptime(
                    last_entry["timestamp"], "%Y-%m-%d %H:%M:%S"
                )

                if all(
                    value == 0
                    for value in last_entry.values()
                    if isinstance(value, (int, float))
                ):
                    data["status"] = "offline"
                    offline_count += 1
                elif time_difference.total_seconds() <= 60:
                    data["status"] = "online"
                    online_count += 1
                else:
                    data["status"] = "offline"
                    offline_count += 1
            else:
                data["status"] = "offline"
                offline_count += 1

    return online_count, offline_count


def get_details_for_mill(mill_key):
    # Placeholder function - modify this based on your actual data structure or retrieval method
    # Here, we just return a simple dictionary
    return {"mill_key": mill_key, "details": f"Details for Mill {mill_key}"}


if __name__ == "__main__":
    app.run(debug=True)

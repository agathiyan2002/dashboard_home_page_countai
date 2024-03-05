from db import Reportdb
import psycopg2
import requests
import schedule
import time
from datetime import datetime, timedelta
import sentry_sdk
from disk_info import DiskInfo
from db import Reportdb

# Replace these values with your PostgreSQL connection details
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "kpr"
DB_USER = "postgres"
DB_PASSWORD = "soft"
mill_name = "kpr-machine-225532"

# Replace this with your Firebase Realtime Database URL
FIREBASE_URL = "https://dashboard-api-62cdd-default-rtdb.firebaseio.com/"


def log():
    log_file_path = "/home/alan/knit/projects/knit-i/knitting-core/system_stats.log"
    data_entries = []

    try:
        with open(log_file_path, "r") as file:
            for line in file:
                try:
                    parts = line.split(",")
                    if len(parts) >= 6:
                        timestamp_str = parts[0]
                        cpu_utilization = float(parts[1].split(": ")[1].rstrip("%"))
                        ram_usage = int(parts[2].split(": ")[1].split(" ")[0])
                        machine_status = int(parts[3].split(": ")[1])
                        gpu_utilization = float(parts[4].split(": ")[1].rstrip("%"))
                        memory_utilization = float(parts[5].split(": ")[1].rstrip("%"))
                        temperature = int(parts[6].split(": ")[1])

                        formatted_timestamp = datetime.strptime(
                            timestamp_str, "%Y-%m-%d %H:%M:%S.%f"
                        ).strftime("%Y-%m-%d %H:%M:%S")

                        entry = {
                            "timestamp": formatted_timestamp,
                            "cpu_utilization": cpu_utilization,
                            "ram_usage": ram_usage,
                            "machine_status": machine_status,
                            "gpu_utilization": gpu_utilization,
                            "memory_utilization": memory_utilization,
                            "temperature": temperature,
                        }

                        data_entries.append(entry)
                    else:
                        print(f"Skipping line: {line}")
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    print(f"Error processing line: {line}")
    except FileNotFoundError as e:
        sentry_sdk.capture_exception(e)
        print(f"File not found: {log_file_path}")

    # Apply filtering and filling here
    filtered_data = filter_last_two_minutes(data_entries)
    filled_data = fill_missing_entries(filtered_data)

    return filled_data


def filter_last_two_minutes(data_entries):
    current_time = datetime.now()
    two_minutes_ago = current_time - timedelta(minutes=2)

    filtered_entries = [
        entry
        for entry in data_entries
        if datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S") > two_minutes_ago
    ]

    return filtered_entries


def fill_missing_entries(data_entries):
    filled_entries = []
    current_time = None

    for entry in data_entries:
        if current_time is None:
            current_time = entry["timestamp"]
            filled_entries.append(entry)
        else:
            timestamp_difference = datetime.strptime(
                entry["timestamp"], "%Y-%m-%d %H:%M:%S"
            ) - datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
            if timestamp_difference.total_seconds() > 1:
                filled_entries.extend(
                    fill_missing_data(current_time, entry["timestamp"])
                )
            # Only append the entry if it's not a duplicate and not all values are 0
            if entry not in filled_entries and any(entry.values()):
                # Remove entries with the same timestamp
                filled_entries = [
                    e for e in filled_entries if e["timestamp"] != entry["timestamp"]
                ]
                filled_entries.append(entry)
            current_time = entry["timestamp"]

    return filled_entries


def fill_missing_data(start_time, end_time):
    filled_data = []
    current_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    while current_time < end_time:
        filled_data.append(
            {
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "cpu_utilization": 0,
                "ram_usage": 0,
                "machine_status": 0,
                "gpu_utilization": 0,
                "memory_utilization": 0,
                "temperature": 0,
            }
        )
        current_time += timedelta(seconds=1)

    return filled_data


def fetch_data():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )

        cursor = conn.cursor()

        # Fetch machine_status from machine_details
        machine_query = "SELECT machine_status FROM machine_details;"
        cursor.execute(machine_query)
        machine_data = cursor.fetchall()

        # Fetch bypass and button_status from button_details
        button_query = "SELECT button_name, button_status FROM button_details WHERE button_name = 'bypass';"
        cursor.execute(button_query)
        button_data = cursor.fetchone()

        # Fetch specific columns from machine_program_details where machineprogram_sts_id = 1
        program_query = """
            SELECT fabric_type, fabric_color, count, denier, loop_length
            FROM machine_program_details
            WHERE machineprogram_sts_id::integer = 1;
        """
        cursor.execute(program_query)
        program_data = cursor.fetchone()

        # Fetch alarm_id and defect_id from combined_alarm_defect_details
        alarm_defect_query = (
            "SELECT alarm_id, defect_id FROM combined_alarm_defect_details;"
        )
        cursor.execute(alarm_defect_query)
        alarm_defect_data = cursor.fetchall()

        # Fetch defect_type_id from defect_details using defect_id from combined_alarm_defect_details
        defect_type_query = """
            SELECT defect_id, defecttyp_id
            FROM defect_details
            WHERE defect_id IN %s;
        """
        defect_ids = tuple([defect_id for _, defect_id in alarm_defect_data])
        cursor.execute(defect_type_query, (defect_ids,))
        defect_type_data = cursor.fetchall()

        # Fetch necessary columns from live_status table
        live_status_query = """
            SELECT machine_status, controller_status, software_status, camera_status,
                   image_status, ml_status, alarm_status, monitor_status, report_status
            FROM live_status;
        """
        cursor.execute(live_status_query)
        live_status_data = cursor.fetchone()

        roll_query = (
            "SELECT roll_id, revolution FROM roll_details WHERE roll_sts_id = 1;"
        )
        cursor.execute(roll_query)
        roll_data = cursor.fetchone()

        total_doff_query = """
            SELECT doff
            FROM machine_program_details
            WHERE machineprogram_sts_id = '1';
        """
        cursor.execute(total_doff_query)
        total_doff_count = cursor.fetchone()[0]

        return (
            machine_data,
            button_data,
            program_data,
            defect_type_data,
            live_status_data,
            roll_data,
            total_doff_count,
        )

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        if conn:
            conn.close()


def upload_to_firebase(data):
    try:
        # Delete the existing data with mill_name key
        # requests.delete(FIREBASE_URL + mill_name + ".json")

        # Upload the new data
        response = requests.patch(FIREBASE_URL + mill_name + ".json", json=data)
        response.raise_for_status()
        print("Data uploaded to Firebase successfully!")
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Request Error: {err}")


def job():
    print("Fetching data and uploading to Firebase...")
    (
        machine_data,
        button_data,
        program_data,
        defect_type_data,
        live_status_data,
        roll_data,
        total_doff_count,
    ) = fetch_data()

    log_data = log()

    report = Reportdb()
    dataframe = report.getDataFrame()
    graph_dataframe = report.getGraphDataframe()

    # Convert DataFrame to dictionary with formatted date
    dataframe_dict = dataframe.to_dict(orient="records")
    for entry in dataframe_dict:
        if "date" in entry:
            entry["date"] = entry["date"].strftime("%Y-%m-%d")

    # Replace 'S.NO' with 'Serial Number' in keys
    for entry in dataframe_dict:
        if "S.NO" in entry:
            entry["Serial Number"] = entry.pop("S.NO")

    # Convert 'hour' from Decimal to string
    for entry in dataframe_dict:
        if "hour" in entry:
            entry["hour"] = str(entry["hour"])

    graph_dataframe_dict = graph_dataframe.to_dict(orient="records")
    for entry in graph_dataframe_dict:
        if "date" in entry:
            entry["date"] = entry["date"].strftime("%Y-%m-%d")

    # Convert 'hour' from Decimal to string
    for entry in graph_dataframe_dict:
        if "hour" in entry:
            entry["hour"] = str(entry["hour"])

    print("DataFrame as Dictionary:")
    print(dataframe_dict)

    print("\nGraph DataFrame as Dictionary:")
    print(graph_dataframe_dict)

    if (
        machine_data is not None
        and button_data is not None
        and program_data is not None
        and defect_type_data is not None
        and live_status_data is not None
        and roll_data is not None
        and total_doff_count is not None
        and dataframe_dict is not None
        and graph_dataframe_dict is not None
    ):
        defect_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}

        for _, defect_type_id in defect_type_data:
            defect_counts[defect_type_id] += 1

        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        disk_info = DiskInfo()

        home_storage_info = None  # Initialize home_storage_info to None

        if disk_info.home_total == 0:
            root_storage_info = disk_info.get_root_storage_info()
        else:
            root_storage_info = disk_info.get_root_storage_info()
            home_storage_info = disk_info.get_home_storage_info()
        print(total_doff_count)

        status_dict = {
            mill_name: {
                "bypass": "ON" if button_data[1] == 1 else "OFF",
                "machine_status": (
                    "running" if machine_data[0][0] == 1 else "not running"
                ),
                "fabric_type": program_data[0],
                "fabric_color": program_data[1],
                "count": program_data[2],
                "denier": program_data[3],
                "loop_length": program_data[4],
                "Lycra": defect_counts.get(1, 0),
                "Hole": defect_counts.get(2, 0),
                "Shutoff": defect_counts.get(3, 0),
                "Needle": defect_counts.get(4, 0),
                "Oil": defect_counts.get(5, 0),
                "Twoply": defect_counts.get(6, 0),
                "Stopline": defect_counts.get(7, 0),
                "Countmix": defect_counts.get(8, 0),
                "sending_time": upload_time,
                "uptime": log_data,
                "system_storage": {
                    "home": home_storage_info,
                    "root": root_storage_info,
                },
                "details_Screen_data": {
                    "graph_dataframe_dict": graph_dataframe_dict,
                    "roll_id": roll_data[0],  # Fetch the roll_id from roll_data
                    "doff_currect_roll": roll_data[1],
                    "total_doff_count": total_doff_count,
                    "machine_status": "ON" if int(live_status_data[0]) == 1 else "OFF",
                    "controller_status": (
                        "ON" if int(live_status_data[1]) == 1 else "OFF"
                    ),
                    "software_status": "ON" if int(live_status_data[2]) == 1 else "OFF",
                    "camara_status": "ON" if int(live_status_data[3]) == 1 else "OFF",
                    "image_status": "ON" if int(live_status_data[4]) == 1 else "OFF",
                    "ml_status": "ON" if int(live_status_data[5]) == 1 else "OFF",
                    "alarm_status": "ON" if int(live_status_data[6]) == 1 else "OFF",
                    "monitor_status": "ON" if int(live_status_data[7]) == 1 else "OFF",
                    "report_status": "ON" if int(live_status_data[8]) == 1 else "OFF",
                },
            }
        }

        modified_status_dict = status_dict[mill_name]
        upload_to_firebase(modified_status_dict)


# Schedule the job to run every 4 seconds for testing purposes
schedule.every(4).seconds.do(job)

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(1)

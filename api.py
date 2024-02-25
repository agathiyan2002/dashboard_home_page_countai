import psycopg2
import requests
import schedule
import time
from datetime import datetime

# Replace these values with your PostgreSQL connection details
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "kpr"
DB_USER = "postgres"
DB_PASSWORD = "soft"
mill_name = "kpr55"

# Replace this with your Firebase Realtime Database URL
FIREBASE_URL = "https://dashboard-api-62cdd-default-rtdb.firebaseio.com/"


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

        return machine_data, button_data, program_data, defect_type_data

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
    machine_data, button_data, program_data, defect_type_data = fetch_data()

    if (
        machine_data is not None
        and button_data is not None
        and program_data is not None
        and defect_type_data is not None
    ):
        defect_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}

        for _, defect_type_id in defect_type_data:
            defect_counts[defect_type_id] += 1

        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("+++++++++++++++++++++")
        print(defect_counts)
        print("+++++++++++++++++++++++++")

        status_dict = {
            mill_name: {
                "bypass": "on" if button_data[1] == 1 else "off",
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
            }
        }
        modified_status_dict = status_dict[mill_name]
        upload_to_firebase(modified_status_dict)


# Schedule the job to run every 1 minute for testing purposes
# schedule.every(30).minutes.do(job)
schedule.every(4).seconds.do(job)
# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(1)

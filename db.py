import pytz
import base64
import psycopg2
import datetime
import pandas as pd
import sentry_sdk


class Execute:
    def __init__(self):
        self.keepalive_kwargs = {
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 5,
            "keepalives_count": 5,
        }
        self.conn = self.connect()

    def connect(self):
        conn = psycopg2.connect(
            database="kpr",
            user="postgres",
            password="soft",
            host="127.0.0.1",
            port="5432",
            **self.keepalive_kwargs,
        )
        conn.autocommit = True
        return conn

    def insert(self, query):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            cur.close()
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def insertReturnId(self, query):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            id = cur.fetchone()[0]
            cur.close()
            return id
        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def select(self, query):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            rows = [
                dict((cur.description[i][0], value) for i, value in enumerate(row))
                for row in cur.fetchall()
            ]
            cur.close()
            return rows

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def update(self, query):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            cur.close()
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def delete(self, query):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            cur.close()
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False


class Reportdb:
    def __init__(self):
        self.execute = Execute()

    def getTotalRotationPerHour(self, start_date, end_date):
        try:
            query = (
                "SELECT DATE(timestamp) AS date,EXTRACT(HOUR FROM timestamp) AS hour,COUNT(*) AS rotation_count FROM rotation_details WHERE timestamp >= ('"
                + start_date
                + "') AND timestamp <= ('"
                + end_date
                + "') GROUP BY date, hour ORDER BY date, hour;"
            )
            data = self.execute.select(query)
            return data

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def getTotalDefectPerHour(self, start_date, end_date):
        try:
            query = (
                "SELECT DATE(defect_details.timestamp) AS date,EXTRACT(HOUR FROM defect_details.timestamp) AS hour,COUNT(*) AS defect_count FROM public.alarm_status INNER join public.defect_details on defect_details.defect_id = alarm_status.defect_id WHERE defect_details.timestamp >= ('"
                + start_date
                + "') AND defect_details.timestamp < ('"
                + end_date
                + "') GROUP BY date, hour ORDER BY date, hour;"
            )
            data = self.execute.select(query)
            return data

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def getrollidShift(self, start_date, end_date, start_time, end_time):
        try:
            query = (
                "SELECT roll_id,revolution,roll_number FROM public.roll_details WHERE roll_end_date >= '"
                + start_date
                + "'::timestamp + '"
                + start_time
                + "'::interval AND roll_end_date < '"
                + end_date
                + "'::timestamp + '"
                + end_time
                + "'::interval  OR roll_start_date >= '"
                + start_date
                + "'::timestamp + '"
                + start_time
                + "'::interval AND roll_start_date < '"
                + end_date
                + "'::timestamp + '"
                + end_time
                + "'::interval AND roll_sts_id=1 ORDER BY roll_id ASC;"
            )
            data = self.execute.select(query)
            return data

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def getrollid(self, start_date, end_date):
        try:
            query = (
                "SELECT roll_id,revolution,roll_number FROM public.roll_details WHERE roll_end_date >= '"
                + start_date
                + "'::timestamp  AND roll_end_date < '"
                + end_date
                + "'::timestamp or roll_start_date >= '"
                + start_date
                + "'::timestamp  AND roll_start_date < '"
                + end_date
                + "'::timestamp AND roll_sts_id=1  ORDER BY roll_id ASC;"
            )
            data = self.execute.select(query)
            return data

        except Exception as e:
            print(str(e))
            sentry_sdk.capture_exception(e)
            return False

    def getRollDetails(self, roll_id):
        try:
            query = (
                "SELECT TO_CHAR(roll_start_date, 'HH24:MI') AS start_time ,TO_CHAR(roll_end_date, 'HH24:MI') AS end_time ,EXTRACT(HOUR FROM (roll_end_date-roll_start_date)) || 'h ' || EXTRACT(MINUTE FROM (roll_end_date-roll_start_date)) || 'min' AS total_hours,roll_details.revolution FROM public.roll_details WHERE roll_id = '"
                + str(roll_id)
                + "';"
            )
            data = self.execute.select(query)
            return data

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def getLycraDefectDetails(self, roll_id):
        try:
            query = (
                "SELECT defect_type.defect_name,COUNT(*) AS count FROM public.alarm_status INNER join public.defect_details on defect_details.defect_id = alarm_status.defect_id INNER JOIN public.defect_type ON defect_type.defecttyp_id = defect_details.defecttyp_id WHERE defect_details.roll_id = '"
                + str(roll_id)
                + "' and defect_type.defect_name = 'lycra' GROUP BY defect_type.defecttyp_id"
            )
            data = self.execute.select(query)
            return data

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def getNeedlnDefectDetails(self, roll_id):
        try:
            query = (
                "SELECT defect_type.defect_name,COUNT(*) AS count FROM public.alarm_status INNER join public.defect_details on defect_details.defect_id = alarm_status.defect_id INNER JOIN public.defect_type ON defect_type.defecttyp_id = defect_details.defecttyp_id WHERE defect_details.roll_id = '"
                + str(roll_id)
                + "' and defect_type.defect_name = 'needln' GROUP BY defect_type.defecttyp_id"
            )
            data = self.execute.select(query)
            return data

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def getHoleDefectDetails(self, roll_id):
        try:
            query = (
                "SELECT defect_type.defect_name,COUNT(*) AS count FROM public.alarm_status INNER join public.defect_details on defect_details.defect_id = alarm_status.defect_id INNER JOIN public.defect_type ON defect_type.defecttyp_id = defect_details.defecttyp_id WHERE defect_details.roll_id = '"
                + str(roll_id)
                + "' and defect_type.defect_name = 'hole' GROUP BY defect_type.defecttyp_id"
            )
            data = self.execute.select(query)
            return data

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def getOthersDefectDetails(self, roll_id):
        try:
            query = (
                "SELECT defect_type.defect_name,COUNT(*) AS count FROM public.alarm_status INNER join public.defect_details on defect_details.defect_id = alarm_status.defect_id INNER JOIN public.defect_type ON defect_type.defecttyp_id = defect_details.defecttyp_id WHERE defect_details.roll_id = '"
                + str(roll_id)
                + "'and defect_type.defect_name != 'lycra' and defect_type.defect_name != 'needln' and defect_type.defect_name != 'hole' GROUP BY defect_type.defecttyp_id"
            )
            data = self.execute.select(query)
            return data

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    def getDataFrame(self):
        try:
            start_date = (
                datetime.datetime.now() - datetime.timedelta(days=15)
            ).strftime("%Y-%m-%d 06:00:00")
            # Calculate end date as current date and time
            end_date = datetime.datetime.now().strftime("%Y-%m-%d 06:00:00")

            dataframe = []
            roll_id = self.getrollid(start_date, end_date)

            roll_count = 1
            for rollid in roll_id:
                if rollid["revolution"] != "0":
                    data = {}
                    data["S.NO"] = roll_count
                    data["SubLot <br>Roll Number"] = rollid["roll_number"]
                    roll_count += 1

                    for roll in self.getRollDetails(rollid["roll_id"]):
                        data["Start Time"] = roll["start_time"]
                        data["End Time"] = roll["end_time"]
                        data["Total Taken"] = roll["total_hours"]
                        data["No of Revolutions"] = roll["revolution"]
                        if roll["end_time"] is None:
                            data["Total Taken"] = "Running"
                            data["End Time"] = "Running"

                    # Create empty dict
                    data["Lycra"] = 0
                    data["Needle line"] = 0
                    data["Hole"] = 0

                    for lycra in self.getLycraDefectDetails(rollid["roll_id"]):
                        data["Lycra"] = lycra["count"]

                    for needln in self.getNeedlnDefectDetails(rollid["roll_id"]):
                        data["Needle line"] = needln["count"]

                    for hole in self.getHoleDefectDetails(rollid["roll_id"]):
                        data["Hole"] = hole["count"]

                    data["Others"] = 0
                    otherdefects = ""
                    for others in self.getOthersDefectDetails(rollid["roll_id"]):
                        otherdefects += (
                            others["defect_name"] + ": " + str(others["count"]) + ", "
                        )
                    # Remove last comma
                    otherdefects = otherdefects[:-2]
                    data["Others"] = otherdefects
                    data["Decision"] = " " * 50

                    dataframe.append(data)
            # Convert to dataframe
            dataframe = pd.DataFrame(dataframe)

            return dataframe

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    # =====================
    def getGraphDataframe(self):
        try:
            # Calculate start date as 24 hours ago from current time
            # start_date = (
            #     datetime.datetime.now() - datetime.timedelta(days=1)
            # ).strftime("%Y-%m-%d %H:%M:%S")
            start_date = (
                datetime.datetime.now() - datetime.timedelta(days=1)
            ).strftime("%Y-%m-%d 06:00:00")
            # Calculate end date as current date and time
            end_date = datetime.datetime.now().strftime("%Y-%m-%d 06:00:00")

            dataframe = []
            totalrevolution = self.getTotalRotationPerHour(start_date, end_date)
            totaldefect = self.getTotalDefectPerHour(start_date, end_date)
            for revolution in totalrevolution:
                data = {}
                data["date"] = revolution["date"]
                data["hour"] = revolution["hour"]
                data["rotation_count"] = revolution["rotation_count"]
                data["defect_count"] = 0
                for defect in totaldefect:
                    if (
                        defect["date"] == revolution["date"]
                        and defect["hour"] == revolution["hour"]
                    ):
                        data["defect_count"] = defect["defect_count"]
                dataframe.append(data)
            # Convert to dataframe
            dataframe = pd.DataFrame(dataframe)
            return dataframe

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False

    # =======================
    def getDataFrameShift(self, date, shift):
        try:

            timing = self.execute.select(
                f"SELECT start_time,end_time FROM public.shift_details WHERE shift_name='{shift.upper()}' or shift_name='{shift.lower()}'"
            )
            start_time = str(timing[0]["start_time"])
            end_time = str(timing[0]["end_time"])

            start_date = date
            # end date is next day 06:00:00
            increasing = 1 if (shift.lower()) == "c" else 0
            end_date = datetime.datetime.strptime(
                date, "%Y-%m-%d"
            ) + datetime.timedelta(days=increasing)
            end_date = end_date.strftime("%Y-%m-%d")

            dataframe = []
            roll_id = self.getrollidShift(start_date, end_date, start_time, end_time)
            roll_count = 1
            for rollid in roll_id:
                if rollid["revolution"] != "0":
                    data = {}
                    data["S.NO"] = roll_count
                    data["SubLot <br>Roll Number"] = rollid["roll_number"]
                    roll_count = roll_count + 1

                    for roll in self.getRollDetails(rollid["roll_id"]):
                        data["Start Time"] = roll["start_time"]
                        data["End Time"] = roll["end_time"]
                        data["Total Taken"] = roll["total_hours"]
                        data["No of Revolutions"] = roll["revolution"]
                        if roll["end_time"] == None:
                            data["Total Taken"] = "Running"
                            data["End Time"] = "Running"

                    # crate empty dict
                    data["Lycra"] = 0
                    data["Needle line"] = 0
                    data["Hole"] = 0

                    for lycra in self.getLycraDefectDetails(rollid["roll_id"]):
                        data["Lycra"] = lycra["count"]

                    for needln in self.getNeedlnDefectDetails(rollid["roll_id"]):
                        data["Needle line"] = needln["count"]

                    for hole in self.getHoleDefectDetails(rollid["roll_id"]):
                        data["Hole"] = hole["count"]

                    data["Others"] = 0
                    otherdefects = ""
                    for others in self.getOthersDefectDetails(rollid["roll_id"]):
                        otherdefects = (
                            otherdefects
                            + others["defect_name"]
                            + ": "
                            + str(others["count"])
                            + ", "
                        )
                    # remove last comma
                    otherdefects = otherdefects[:-2]
                    data["Others"] = otherdefects
                    data["Decision"] = " " * 50

                    dataframe.append(data)
                # convrt to dataframe
            dataframe = pd.DataFrame(dataframe)
            # save to csv
            # dataframe.to_csv("report.csv", index=False)

            return dataframe, start_time, end_time

        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False, False, False

    def getMachineName(self):
        try:
            query = "SELECT machinedtl_name FROM public.machine_details ORDER BY machinedtl_id"
            data = self.execute.select(query)
            return data[0]["machinedtl_name"]
        except Exception as e:
            sentry_sdk.capture_exception(e)
            print(str(e))
            return False


# if __name__ == "__main__":
#     report = Reportdb()
#     report.getGraphDataframe("2023-12-19")
# report.getTotalRotationPerHour("2023-12-19","2023-12-20")
# report.getTotalDefectPerHour("2023-12-19","2023-12-19")

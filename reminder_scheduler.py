import sqlite3
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client
from dotenv import load_dotenv
import os



load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

twilio_client = Client(
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN
)
print("Twilio configuration loaded:", bool(
    TWILIO_ACCOUNT_SID and
    TWILIO_AUTH_TOKEN and
    TWILIO_PHONE_NUMBER
))

def send_sms(phone_number, message):
    try:
        sms = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )

        print("SMS SENT:", sms.sid)
        return True

    except Exception as e:
        print("TWILIO ERROR:", e)
        return False



def get_db_connection():
    conn = sqlite3.connect("clockcare.db")
    conn.row_factory = sqlite3.Row
    return conn


# Keep track of reminders already sent
sent_reminders = set()


def check_reminders():

    now = datetime.now()

    current_time = now.strftime("%H:%M")

    five_minutes_before = (
        now + timedelta(minutes=5)
    ).strftime("%H:%M")

    today = now.strftime("%Y-%m-%d")

    conn = get_db_connection()

    reminders = conn.execute("""
        SELECT *
        FROM medicine_reminders
        WHERE status = 'active'
    """).fetchall()

    conn.close()

    for reminder in reminders:

        reminder_id = reminder["id"]
        reminder_time = reminder["reminder_time"]

        # --------------------------------
        # 5 MINUTES BEFORE REMINDER
        # --------------------------------

        five_minute_key = (
            today,
            reminder_id,
            "five_minutes"
        )

        if (
            reminder_time == five_minutes_before
            and five_minute_key not in sent_reminders
        ):

            message = (
                    f"Hello {reminder['patient_name']}! "
                    f"Your {reminder['medicine_name']} medicine is due in 5 minutes."
            )
            print("5 MINUTE REMINDER:", message)
            send_sms(
                reminder["phone_number"],
                message
            )
            sent_reminders.add(five_minute_key)
        # --------------------------------
        # EXACT TIME REMINDER
        # --------------------------------

        exact_time_key = (
            today,
            reminder_id,
            "exact_time"
        )

        if (
            reminder_time == current_time
            and exact_time_key not in sent_reminders
        ):

            message = (
                f"Hello {reminder['patient_name']}! "
                f"It's time to take your {reminder['medicine_name']} "
                f"({reminder['dosage']}) - {reminder['instruction']}."
            )

            print("EXACT TIME REMINDER:", message)

            if send_sms(
                reminder["phone_number"],
                message
            ):
                sent_reminders.add(exact_time_key)


def start_scheduler():

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        check_reminders,
        "interval",
        seconds=5
    )

    scheduler.start()

    print("Medicine reminder scheduler started.")


if __name__ == "__main__":

    start_scheduler()

    try:
        while True:
            pass

    except KeyboardInterrupt:
        print("Scheduler stopped.")
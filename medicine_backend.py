import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from flask import Blueprint, request, redirect, flash, session
from gemini_service import generate_lifestyle_suggestion


# Load environment variables
load_dotenv(".env.local")


# Create a Blueprint for Medicine Reminder
medicine_bp = Blueprint("medicine", __name__)


# ------------------------ DATABASE CONNECTION

def get_db_connection():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL")
    )


# ------------------ CREATE MEDICINE REMINDERS TABLE

def create_medicine_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_reminders (
            id SERIAL PRIMARY KEY,

            patient_name TEXT NOT NULL,

            phone_number TEXT NOT NULL,

            health_issue TEXT,

            medicine_name TEXT,

            dosage TEXT,

            reminder_time TEXT NOT NULL,

            duration TEXT,

            instruction TEXT,

            status TEXT DEFAULT 'active',

            lifestyle_suggestion TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


# ------------------- SAVE MEDICINE REMINDER

@medicine_bp.route("/set_reminder", methods=["POST"])
def set_reminder():

    patient_name = request.form.get("patientName", "").strip()

    phone_number = session.get("user_phone")

    if not phone_number:
        flash("Please login first to set a medicine reminder.")
        return redirect("/login")

    health_issue = request.form.get("healthIssue", "").strip()
    medicine_name = request.form.get("medicineName", "").strip()
    dosage = request.form.get("dosage", "").strip()
    reminder_time = request.form.get("reminderTime", "").strip()
    duration = request.form.get("duration", "").strip()
    instruction = request.form.get("instruction", "").strip()


    # ------------------------ VALIDATION

    if not patient_name:
        flash("Please enter the patient's name.")
        return redirect("/medicine_reminder")

    if not reminder_time:
        flash("Please select a reminder time.")
        return redirect("/medicine_reminder")

    if not medicine_name:
        flash("Please enter the medicine name.")
        return redirect("/medicine_reminder")


    # ------------------------ SAVE TO DATABASE

    conn = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO medicine_reminders
            (
                patient_name,
                phone_number,
                health_issue,
                medicine_name,
                dosage,
                reminder_time,
                duration,
                instruction,
                status
            )

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)

            RETURNING id
        """, (
            patient_name,
            phone_number,
            health_issue,
            medicine_name,
            dosage,
            reminder_time,
            duration,
            instruction,
            "active"
        ))

        reminder_id = cursor.fetchone()[0]


        # Generate lifestyle suggestions using Gemini
        lifestyle_suggestion = generate_lifestyle_suggestion(
            medicine_name,
            health_issue
        )


        # Save Gemini suggestion

        cursor.execute("""
            UPDATE medicine_reminders
            SET lifestyle_suggestion = %s
            WHERE id = %s
        """, (
            lifestyle_suggestion,
            reminder_id
        ))


        conn.commit()

        cursor.close()
        conn.close()

        flash("✅ Medicine reminder saved successfully!")


    except Exception as e:

        print("DATABASE ERROR:", e)

        if conn:
            conn.rollback()
            conn.close()

        flash("❌ Could not save the medicine reminder.")


    return redirect("/medicine_reminder")


# -------------------------- VIEW ALL MEDICINE REMINDERS

@medicine_bp.route("/reminders")
def view_reminders():

    conn = get_db_connection()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cursor.execute("""
        SELECT *
        FROM medicine_reminders
        ORDER BY reminder_time
    """)

    reminders = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "reminders": reminders
    }


# --------------------------- DELETE A MEDICINE REMINDER

@medicine_bp.route(
    "/delete_reminder/<int:reminder_id>",
    methods=["POST"]
)
def delete_reminder(reminder_id):

    conn = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM medicine_reminders
            WHERE id = %s
        """, (reminder_id,))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Medicine reminder deleted successfully.")

    except Exception as e:

        print("DATABASE ERROR:", e)

        if conn:
            conn.rollback()
            conn.close()

        flash("Could not delete the reminder.")

    return redirect("/medicine_reminder")


# ------------------------- DEACTIVATE A REMINDER

@medicine_bp.route(
    "/deactivate_reminder/<int:reminder_id>",
    methods=["POST"]
)
def deactivate_reminder(reminder_id):

    conn = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE medicine_reminders
            SET status = 'inactive'
            WHERE id = %s
        """, (reminder_id,))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Medicine reminder deactivated.")

    except Exception as e:

        print("DATABASE ERROR:", e)

        if conn:
            conn.rollback()
            conn.close()

        flash("Could not deactivate the reminder.")

    return redirect("/medicine_reminder")


# -------------------------- ACTIVATE A REMINDER

@medicine_bp.route(
    "/activate_reminder/<int:reminder_id>",
    methods=["POST"]
)
def activate_reminder(reminder_id):

    conn = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE medicine_reminders
            SET status = 'active'
            WHERE id = %s
        """, (reminder_id,))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Medicine reminder activated.")

    except Exception as e:

        print("DATABASE ERROR:", e)

        if conn:
            conn.rollback()
            conn.close()

        flash("Could not activate the reminder.")

    return redirect("/medicine_reminder")
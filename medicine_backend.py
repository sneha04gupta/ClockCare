import sqlite3
from flask import Blueprint, request, redirect, flash, session
from gemini_service import generate_lifestyle_suggestion

# Create a Blueprint for Medicine Reminder
medicine_bp = Blueprint("medicine", __name__)


# ------------------------DATABASE CONNECTION

def get_db_connection():
    conn = sqlite3.connect("clockcare.db")
    conn.row_factory = sqlite3.Row
    return conn


# ------------------CREATE MEDICINE REMINDERS TABLE


def create_medicine_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_name TEXT NOT NULL,

            phone_number TEXT NOT NULL,

            health_issue TEXT,

            medicine_name TEXT,

            dosage TEXT,

            reminder_time TEXT NOT NULL,

            duration TEXT,

            instruction TEXT,

            status TEXT DEFAULT 'active',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(medicine_reminders)")
    columns = [row[1] for row in cursor.fetchall()]

    if "lifestyle_suggestion" not in columns:
        cursor.execute("""
            ALTER TABLE medicine_reminders
            ADD COLUMN lifestyle_suggestion TEXT
        """)

    conn.commit()
    conn.close()


# -------------------SAVE MEDICINE REMINDER


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


    # ------------------------VALIDATION
    

    if not patient_name:
        flash("Please enter the patient's name.")
        return redirect("/medicine_reminder")



    if not reminder_time:
        flash("Please select a reminder time.")
        return redirect("/medicine_reminder")


    if not medicine_name:
        flash("Please enter the medicine name.")
        return redirect("/medicine_reminder")


    # ------------------------SAVE TO DATABASE
    

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

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

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

        reminder_id = cursor.lastrowid

        # Generate lifestyle suggestions using Gemini
        lifestyle_suggestion = generate_lifestyle_suggestion(
            medicine_name,
            health_issue
        )

        # Save Gemini's suggestion
        cursor.execute("""
            UPDATE medicine_reminders
            SET lifestyle_suggestion = ?
            WHERE id = ?
        """, (
            lifestyle_suggestion,
            reminder_id
        ))

        conn.commit()
        conn.close()

        flash("✅ Medicine reminder saved successfully!")

    except sqlite3.Error as e:

        print("DATABASE ERROR:", e)

        flash("❌ Could not save the medicine reminder.")


    # Return to medicine reminder page
    return redirect("/medicine_reminder")


# --------------------------VIEW ALL MEDICINE REMINDERS


@medicine_bp.route("/reminders")
def view_reminders():

    conn = get_db_connection()

    reminders = conn.execute("""
        SELECT *
        FROM medicine_reminders
        ORDER BY reminder_time
    """).fetchall()

    conn.close()

    return {
        "reminders": [dict(reminder) for reminder in reminders]
    }


# ---------------------------DELETE A MEDICINE REMINDER


@medicine_bp.route("/delete_reminder/<int:reminder_id>", methods=["POST"])
def delete_reminder(reminder_id):

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM medicine_reminders
            WHERE id = ?
        """, (reminder_id,))

        conn.commit()

        conn.close()

        flash("Medicine reminder deleted successfully.")

    except sqlite3.Error as e:

        print("DATABASE ERROR:", e)

        flash("Could not delete the reminder.")

    return redirect("/medicine_reminder")


# -------------------------DEACTIVATE A REMINDER


@medicine_bp.route("/deactivate_reminder/<int:reminder_id>",
                   methods=["POST"])
def deactivate_reminder(reminder_id):

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute("""
            UPDATE medicine_reminders

            SET status = 'inactive'

            WHERE id = ?
        """, (reminder_id,))

        conn.commit()

        conn.close()

        flash("Medicine reminder deactivated.")

    except sqlite3.Error as e:

        print("DATABASE ERROR:", e)

        flash("Could not deactivate the reminder.")

    return redirect("/medicine_reminder")


# --------------------------ACTIVATE A REMINDER


@medicine_bp.route("/activate_reminder/<int:reminder_id>",
                   methods=["POST"])
def activate_reminder(reminder_id):

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute("""
            UPDATE medicine_reminders

            SET status = 'active'

            WHERE id = ?
        """, (reminder_id,))

        conn.commit()

        conn.close()

        flash("Medicine reminder activated.")

    except sqlite3.Error as e:

        print("DATABASE ERROR:", e)

        flash("Could not activate the reminder.")

    return redirect("/medicine_reminder")
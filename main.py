import os
import sqlite3
from medicine_backend import medicine_bp, create_medicine_table
from flask import Flask, render_template, request, redirect, flash, session

from google import genai


app = Flask(__name__)
app.register_blueprint(medicine_bp)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "clockcare_secret_key"
)

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)




# Create database
def create_database():
    conn = sqlite3.connect("clockcare.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Home page
@app.route("/")
def home():
    return render_template("home.html")


# About page
@app.route("/about")
def about():
    return render_template("about.html")


# Medicine reminder page
@app.route("/medicine_reminder")
def medicine_reminder():
    return render_template("medicine_reminder.html")


# Emergency help page
@app.route("/emergency_help")
def emergency_help():
    return render_template("emergency_help.html")


# Medicine information page
@app.route("/medicine_info")
def medicine_info():
    return render_template("medicine_info.html")


# Ask medicine
@app.route("/ask_medicine", methods=["POST"])
def ask_medicine():

    data = request.get_json(silent=True) or {}
    question = data.get("question")

    if not question:
        return {
            "answer": "Please enter a medicine name or question."
        }

    try:

        prompt = f"""
You are ClockCare Assistant, a simple medicine information assistant.

The user asked:
{question}

Give a SHORT and EASY-TO-UNDERSTAND answer.

Do NOT mention dosage or how much medicine to take.

Use this exact structure:

💊 Medicine: [medicine name]

What is it?
- Explain in 1-2 very simple sentences.

What is it used for?
- Give 2-3 common uses in simple words.

✅ Benefits:
- Give 2-3 short points.

⚠️ Common side effects:
- Give 2-3 common side effects.

❌ Precautions:
- Give 2 short important precautions.

Keep the entire answer under 150 words.

Use simple language that an ordinary user can easily understand.
Do not use complicated medical terms unless you explain them simply.

If the medicine or question is unclear, politely ask the user to provide the medicine name.

Do not diagnose the user or recommend a specific medicine.

For serious symptoms or personal medical advice, suggest consulting a doctor or pharmacist.
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        print("GEMINI RESPONSE:", response.text)

        return {
            "answer": response.text
        }

    except Exception as e:

        print("GEMINI ERROR:", e)

        return {
            "answer": "Gemini error. Check the VS Code terminal."
        }


# Lifestyle page
@app.route("/lifestyle")
def lifestyle():

    latest_reminder = None

    if "user_phone" in session:

        conn = sqlite3.connect("clockcare.db")
        conn.row_factory = sqlite3.Row

        latest_reminder = conn.execute("""
            SELECT *
            FROM medicine_reminders
            WHERE phone_number = ?
              AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
        """, (session["user_phone"],)).fetchone()

        conn.close()

    return render_template(
        "lifestyle.html",
        latest_reminder=latest_reminder
    )


# Signup page
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"].strip()

        if phone.startswith("0"):
            phone = "+91" + phone[1:]
        elif not phone.startswith("+"):
            phone = "+91" + phone

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect("/signup")

        try:
            conn = sqlite3.connect("clockcare.db")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (name, email, phone, password)
                VALUES (?, ?, ?, ?)
            """, (name, email, phone, password))

            conn.commit()
            conn.close()

            flash("Account created successfully!")
            return redirect("/signup")

        except sqlite3.IntegrityError:
            try:
                conn.close()
            except:
                pass

            flash("This email is already registered!")
            return redirect("/signup")

        except Exception as e:
            print("SIGNUP ERROR:", repr(e))

            import traceback
            traceback.print_exc()

            try:
                conn.close()
            except:
                pass

            flash("Signup failed. Please try again.")
            return redirect("/signup")

    return render_template("signup.html")



# Login page
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("clockcare.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_email"] = user[2]
            session["user_phone"] = user[3]

            flash("Login successful!")
            return redirect("/medicine_reminder")
        else:
            flash("Invalid email or password!")
            return redirect("/login")
    return render_template("login.html")


# Start Flask
create_database()
create_medicine_table()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )

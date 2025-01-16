import flask
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

# Flask-Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Für Flash-Messages und Sessions

# Globale Variable für Benutzer-Daten
users = None


# Funktion zum Laden der Benutzer aus der CSV-Datei
def load_users():
    try:
        return pd.read_csv("data/users.csv")
    except FileNotFoundError:
        # Falls die Datei nicht existiert, ein leeres DataFrame zurückgeben
        return pd.DataFrame(
            columns=["id", "username", "email", "password", "weight", "height", "heart_rate", "blood_pressure", "sleep",
                     "stress", "reminder"])


# Funktion zum Speichern der Benutzer in der CSV-Datei
def save_users():
    users.to_csv("data/users.csv", index=False)


# Benutzer-Daten direkt beim Start laden
users = load_users()


# Route für die Startseite
@app.route("/")
def index():
    return render_template("inhalte.html")


# Route für die Registrierung
@app.route("/register", methods=["GET", "POST"])
def register():
    global users
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Überprüfen, ob der Benutzername oder die E-Mail-Adresse bereits existiert
        if not users[(users["username"] == username) | (users["email"] == email)].empty:
            flash("Username or email already exists!", "danger")
            return redirect(url_for("register"))

        # Neuen Benutzer hinzufügen
        new_id = users["id"].max() + 1 if not users.empty else 1
        new_user = {
            "id": new_id,
            "username": username,
            "email": email,
            "password": password,
            "weight": None,
            "height": None,
            "heart_rate": None,
            "blood_pressure": None,
            "sleep": None,
            "stress": None,
            "reminder": None
        }
        users = users.append(new_user, ignore_index=True)
        save_users()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# Route für das Login
@app.route("/login", methods=["GET", "POST"])
def login():
    global users
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Benutzer anhand der E-Mail-Adresse finden
        user = users[users["email"] == email]
        if not user.empty and user.iloc[0]["password"] == password:
            session["logged_in"] = True
            session["user_id"] = user.iloc[0]["id"]
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password!", "danger")

    return render_template("login.html")


# Route für das Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# Route für die Home-Seite
@app.route("/home")
def home():
    global users
    user_id = session.get("user_id")
    if user_id is None:
        flash("You need to log in to access the dashboard.", "danger")
        return redirect(url_for("login"))

    # Gesundheitsdaten und Erinnerungen des Benutzers abrufen
    user_data = users.loc[
        users["id"] == user_id, ["weight", "height", "heart_rate", "blood_pressure", "sleep", "stress"]].dropna()
    reminders = users.loc[users["id"] == user_id, "reminder"].dropna()

    health_data = user_data.to_dict("records")
    reminders_list = reminders.to_list()

    return render_template("home.html", health_data=health_data, reminders=reminders_list)


# Route für die Eingabe von Gesundheitsdaten
@app.route("/input_data", methods=["GET", "POST"])
def input_data():
    global users
    user_id = session.get("user_id")
    if user_id is None:
        flash("You need to log in to input health data.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        weight = request.form["weight"]
        height = request.form["height"]
        heart_rate = request.form["heart_rate"]
        blood_pressure = request.form["blood_pressure"]
        sleep = request.form["sleep"]
        stress = request.form["stress"]

        # Gesundheitsdaten des Benutzers aktualisieren
        users.loc[users["id"] == user_id, ["weight", "height", "heart_rate", "blood_pressure", "sleep", "stress"]] = [
            weight, height, heart_rate, blood_pressure, sleep, stress
        ]
        save_users()

        flash("Health data saved successfully!", "success")
        return redirect(url_for("home"))

    return render_template("input_data.html")


# Route für Erinnerungen/Notizen
@app.route("/reminders", methods=["GET", "POST"])
def reminders():
    global users
    user_id = session.get("user_id")
    if user_id is None:
        flash("You need to log in to add a reminder.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        reminder = request.form["reminder"]
        users.loc[users["id"] == user_id, "reminder"] = reminder
        save_users()

        flash("Reminder saved successfully!", "success")
        return redirect(url_for("home"))

    return render_template("reminders_notes.html")


# Route für Plots
@app.route("/plots", methods=["GET"])
def plots():
    global users
    user_id = session.get("user_id")
    if user_id is None:
        flash("You need to log in to view plots.", "danger")
        return redirect(url_for("login"))

    user_data = users.loc[
        users["id"] == user_id, ["weight", "height", "heart_rate", "blood_pressure", "sleep", "stress"]]
    if user_data.empty or user_data.isnull().values.any():
        return render_template("plots.html", plot_available=False)

    # Beispielplot erstellen
    plt.figure(figsize=(10, 6))
    plt.plot(["Weight", "Height", "Heart Rate", "Blood Pressure", "Sleep", "Stress"], user_data.values[0], marker="o")
    plt.title("Health Data Overview")
    plt.xlabel("Health Metrics")
    plt.ylabel("Values")
    plt.grid()

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template("plots.html", plot_available=True, plot_title="Health Data Trends", plot_url=plot_url,
                           page=1)


# App starten
if __name__ == "__main__":
    app.run(debug=True)

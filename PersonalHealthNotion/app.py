import flask
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import json

# Flask-Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Globale Variable für Benutzer-Daten
users = None


# Funktion zum Laden der Benutzer aus der CSV-Datei
def load_users():
    try:
        return pd.read_csv("data/users.csv")
    except FileNotFoundError:
        # Falls die Datei nicht existiert, ein leeres DataFrame zurückgeben
        return pd.DataFrame(columns=["id", "username", "email", "password", "health_data", "reminders"])


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
            "health_data": json.dumps([]),  # Leere Liste für Gesundheitsdaten
            "reminders": json.dumps([])  # Leere Liste für Erinnerungen
        }

        new_user_df = pd.DataFrame([new_user])
        users = pd.concat([users, new_user_df], ignore_index=True)
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
            session["user_id"] = int(user.iloc[0]["id"])  # ID in Standard-`int` umwandeln
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

    user = users.loc[users["id"] == user_id].iloc[0]
    username = user["username"]  # Benutzernamen abrufen
    health_data = json.loads(user["health_data"])
    reminders = json.loads(user["reminders"])

    return render_template("home.html", username=username, health_data=health_data, reminders=reminders)


# Route für die Eingabe von Gesundheitsdaten
@app.route("/input_data", methods=["GET", "POST"])
def input_data():
    global users
    user_id = session.get("user_id")
    if user_id is None:
        flash("You need to log in to input health data.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        new_data = {
            "weight": request.form["weight"],
            "height": request.form["height"],
            "heart_rate": request.form["heart_rate"],
            "blood_pressure": request.form["blood_pressure"],
            "sleep": request.form["sleep"],
            "stress": request.form["stress"]
        }

        user_index = users[users["id"] == user_id].index[0]
        health_data = json.loads(users.at[user_index, "health_data"])
        health_data.append(new_data)
        users.at[user_index, "health_data"] = json.dumps(health_data)
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
        new_reminder = request.form["reminder"]

        user_index = users[users["id"] == user_id].index[0]
        reminders = json.loads(users.at[user_index, "reminders"])
        reminders.append(new_reminder)
        users.at[user_index, "reminders"] = json.dumps(reminders)
        save_users()

        flash("Reminder saved successfully!", "success")
        return redirect(url_for("home"))

    return render_template("reminders_notes.html")


# Aktualisierte plots-Route
@app.route("/plots", methods=["GET"])
def plots():
    global users
    user_id = session.get("user_id")
    if user_id is None:
        flash("You need to log in to view plots.", "danger")
        return redirect(url_for("login"))

    # Benutzer und Gesundheitsdaten abrufen
    user = users.loc[users["id"] == user_id].iloc[0]
    health_data = json.loads(user["health_data"])

    if not health_data:
        return render_template("plots.html", plot_available=False)

    # Metriken definieren
    metrics = ["weight", "height", "heart_rate", "blood_pressure", "sleep", "stress"]
    plots = {}

    for metric in metrics:
        values = []
        # Valide Werte extrahieren
        for entry in health_data:
            if metric in entry and entry[metric].strip():
                if metric == "blood_pressure":
                    # `blood_pressure` speziell behandeln
                    if "/" in entry[metric]:
                        try:
                            systolic, diastolic = map(float, entry[metric].split("/"))
                            values.append((systolic + diastolic) / 2)  # Durchschnitt berechnen
                        except ValueError:
                            continue  # Fehlerhafte Einträge ignorieren
                else:
                    try:
                        values.append(float(entry[metric]))
                    except ValueError:
                        continue  # Fehlerhafte Einträge ignorieren

        # Nur Plot erstellen, wenn valide Werte vorhanden sind
        if values:
            plt.figure(figsize=(8, 5))
            plt.plot(
                range(1, len(values) + 1),  # x-Achse: Einerschritte
                values,
                marker="o",
                label=metric.capitalize(),
            )
            plt.title(f"{metric.capitalize()} Over Time")
            plt.xlabel("Entry Number")
            plt.ylabel(metric.capitalize())
            plt.grid()
            plt.legend()

            img = io.BytesIO()
            plt.savefig(img, format="png")
            img.seek(0)
            plots[metric] = base64.b64encode(img.getvalue()).decode()
            plt.close()

    # Pagination-Handling
    page = int(request.args.get("page", 1))  # Standardmäßig Seite 1
    if page < 1 or page > len(metrics):
        flash("Invalid page number.", "danger")
        return redirect(url_for("plots", page=1))

    # Aktuelle Metrik basierend auf der Seite
    current_metric = metrics[page - 1]
    current_plot_url = plots.get(current_metric)

    # Sicherstellen, dass die aktuelle Metrik einen Plot hat
    if current_plot_url is None:
        flash(f"No data available for {current_metric.capitalize()}.", "warning")
        return redirect(url_for("plots", page=1))

    return render_template(
        "plots.html",
        plot_available=True,
        current_plot=current_plot_url,
        current_metric=current_metric.capitalize(),
        page=page,
        total_pages=len(metrics)
    )


# App starten
if __name__ == "__main__":
    app.run(debug=True)

import flask
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd

# Flask-Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Für Flash-Messages und Sessions

# Globale Variable für Benutzerdaten
users = None

# Funktion zum Laden der Benutzer aus der CSV-Datei
def load_users():
    try:
        return pd.read_csv("data/users.csv")
    except FileNotFoundError:
        # Falls die Datei nicht existiert, ein leeres DataFrame zurückgeben
        return pd.DataFrame(columns=["id", "username", "email", "password"])

# Funktion zum Speichern eines neuen Benutzers
def save_user(username, email, password):
    global users
    new_id = users["id"].max() + 1 if not users.empty else 1  # Neue ID generieren
    new_user = {"id": new_id, "username": username, "email": email, "password": password}
    users = users.append(new_user, ignore_index=True)  # Neuen Benutzer hinzufügen
    users.to_csv("data/users.csv", index=False)  # Änderungen in der CSV speichern
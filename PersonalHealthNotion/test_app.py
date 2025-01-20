import pytest
from app import app, load_users

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """Test the index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome to Personal Health Notion" in response.data


def test_register_route(client):
    """Test the registration route."""
    global users
    users = load_users()

    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Überprüfe, ob wir erfolgreich auf die Login-Seite umgeleitet wurden
    assert b"Login" in response.data


def test_login_route(client):
    """Test the login route."""
    global users
    users = load_users()

    response = client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Hi testuser, welcome to your Dashboard!" in response.data


def test_input_data(client):
    """Test the input data route."""
    global users
    users = load_users()

    # Logge den Benutzer ein
    client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'password123'
    })

    # Sende neue Gesundheitsdaten
    response = client.post('/input_data', data={
        'weight': '70',
        'height': '180',
        'heart_rate': '72',
        'blood_pressure': '120/80',
        'sleep': '8',
        'stress': '5'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_reminders(client):
    """Test the reminders route."""
    global users
    users = load_users()

    # Logge den Benutzer ein
    client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'password123'
    })

    # Sende einen neuen Reminder
    response = client.post('/reminders', data={
        'reminder': 'Drink water every 2 hours'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_plots_route(client):
    """Test the plots route."""
    global users
    users = load_users()

    # Logge den Benutzer ein
    client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'password123'
    })

    # Abrufen der Plots-Seite
    response = client.get('/plots', follow_redirects=True)

    assert response.status_code == 200
    assert b"Health Data Plots" in response.data

"""
Integration tests for the user and calculation routes.

These send real HTTP requests to the app with TestClient and use the real
PostgreSQL database. Locally, start it first with: docker compose up -d db
"""

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.models.user import User
from app.security import verify_password
from main import app

client = TestClient(app)

USER = {"username": "alice", "email": "alice@example.com", "password": "secret123"}


@pytest.fixture(autouse=True)
def fresh_tables():
    """Give every test empty tables."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def register_alice():
    """Register the test user and return their id."""
    return client.post("/users/register", json=USER).json()["id"]


# ---------- User routes ----------

def test_register_user():
    """Registering returns 201 and the user, but never the password."""
    response = client.post("/users/register", json=USER)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "password" not in data
    assert "password_hash" not in data


def test_register_saves_hashed_password():
    """The database stores a hash, not the plain password."""
    client.post("/users/register", json=USER)
    db = SessionLocal()
    user = db.query(User).filter(User.username == "alice").first()
    db.close()
    assert user.password_hash != "secret123"
    assert verify_password("secret123", user.password_hash)


@pytest.mark.parametrize("second_user", [
    {"username": "alice", "email": "other@example.com", "password": "secret123"},
    {"username": "bob", "email": "alice@example.com", "password": "secret123"},
])
def test_register_duplicate(second_user):
    """A duplicate username or email returns 400."""
    client.post("/users/register", json=USER)
    response = client.post("/users/register", json=second_user)
    assert response.status_code == 400
    assert response.json()["error"] == "Username or email already registered"


@pytest.mark.parametrize("changes", [
    {"email": "not-an-email"},
    {"password": "short"},
    {"username": "ab"},
])
def test_register_invalid_data(changes):
    """Invalid registration data is rejected with 400."""
    response = client.post("/users/register", json={**USER, **changes})
    assert response.status_code == 400
    assert "error" in response.json()


def test_login_success():
    """The right username and password log in."""
    client.post("/users/register", json=USER)
    response = client.post("/users/login", json={"username": "alice", "password": "secret123"})
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"
    assert response.json()["user"]["username"] == "alice"


@pytest.mark.parametrize("credentials", [
    {"username": "alice", "password": "wrongpass"},
    {"username": "nobody", "password": "secret123"},
])
def test_login_failure(credentials):
    """A wrong password or unknown user returns 401."""
    client.post("/users/register", json=USER)
    response = client.post("/users/login", json=credentials)
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid username or password"


# ---------- Calculation routes (BREAD) ----------

def test_full_bread_flow():
    """Add, read, browse, edit, and delete one calculation."""
    user_id = register_alice()

    # Add
    response = client.post("/calculations", json={"a": 2, "b": 3, "type": "Add", "user_id": user_id})
    assert response.status_code == 201
    calc = response.json()
    assert calc["result"] == 5
    calc_id = calc["id"]

    # Read
    response = client.get(f"/calculations/{calc_id}")
    assert response.status_code == 200
    assert response.json()["type"] == "Add"

    # Browse
    response = client.get("/calculations")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Edit
    response = client.put(f"/calculations/{calc_id}", json={"a": 4, "b": 5, "type": "Multiply"})
    assert response.status_code == 200
    assert response.json()["result"] == 20
    assert response.json()["type"] == "Multiply"

    # Delete
    response = client.delete(f"/calculations/{calc_id}")
    assert response.status_code == 204
    assert client.get(f"/calculations/{calc_id}").status_code == 404


def test_browse_empty():
    """Browse returns an empty list when there are no calculations."""
    response = client.get("/calculations")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("calc_type, a, b, expected", [
    ("Add", 2, 3, 5),
    ("Sub", 10, 4, 6),
    ("Multiply", 4, 5, 20),
    ("Divide", 10, 4, 2.5),
])
def test_add_each_type(calc_type, a, b, expected):
    """Every calculation type is computed and saved correctly."""
    user_id = register_alice()
    response = client.post(
        "/calculations", json={"a": a, "b": b, "type": calc_type, "user_id": user_id}
    )
    assert response.status_code == 201
    assert response.json()["result"] == expected


@pytest.mark.parametrize("bad_data", [
    {"a": 1, "b": 2, "type": "Modulus"},   # not an allowed type
    {"a": 1, "b": 0, "type": "Divide"},    # dividing by zero
    {"a": "abc", "b": 2, "type": "Add"},   # not a number
    {"a": 1, "type": "Add"},               # missing b
])
def test_add_invalid_data(bad_data):
    """Invalid calculation data is rejected with 400 and nothing is saved."""
    user_id = register_alice()
    response = client.post("/calculations", json={**bad_data, "user_id": user_id})
    assert response.status_code == 400
    assert "error" in response.json()
    assert client.get("/calculations").json() == []


def test_add_for_unknown_user():
    """A calculation for a user that doesn't exist returns 404."""
    response = client.post("/calculations", json={"a": 1, "b": 2, "type": "Add", "user_id": 999})
    assert response.status_code == 404
    assert response.json()["error"] == "User not found"


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_calculation_returns_404(method):
    """Read, Edit, and Delete return 404 for an id that doesn't exist."""
    if method == "put":
        response = client.put("/calculations/999", json={"a": 1, "b": 2, "type": "Add"})
    else:
        response = getattr(client, method)("/calculations/999")
    assert response.status_code == 404
    assert response.json()["error"] == "Calculation not found"


def test_edit_with_invalid_data():
    """Editing with invalid data is rejected and the calculation is unchanged."""
    user_id = register_alice()
    calc_id = client.post(
        "/calculations", json={"a": 2, "b": 3, "type": "Add", "user_id": user_id}
    ).json()["id"]
    response = client.put(f"/calculations/{calc_id}", json={"a": 1, "b": 0, "type": "Divide"})
    assert response.status_code == 400
    assert client.get(f"/calculations/{calc_id}").json()["result"] == 5
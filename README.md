# FastAPI Calculator with Secure User Model

A FastAPI calculator app with a secure user model, built for Module 10. Users are stored in PostgreSQL with SQLAlchemy, user data is validated with Pydantic, and passwords are hashed with bcrypt before they are saved. GitHub Actions tests the code, scans the Docker image, and pushes it to Docker Hub.

## Docker Hub

Image: **https://hub.docker.com/r/atharhanjra/assignment12**

```
docker pull atharhanjra/assignment12:latest
docker run -p 8000:8000 atharhanjra/assignment12:latest
```

Then open http://localhost:8000.

## What's Included

- **User model** (`app/models/user.py`): `username`, `email`, `password_hash`, and `created_at`, with unique constraints on username and email
- **Pydantic schemas** (`app/schemas/user.py`): `UserCreate` (username, valid email, password) and `UserRead` (never includes the password or hash)
- **Password hashing** (`app/security.py`): `hash_password` and `verify_password` using bcrypt
- **User functions** (`app/user_service.py`): `create_user` saves only the hashed password; `authenticate_user` checks a login

## Calculation Model (Module 11)

- **Model** (`app/models/calculation.py`): `id`, `a`, `b`, `type`, `result`, and `user_id` (a foreign key to `users`). The result is computed once and stored.
- **Schemas** (`app/schemas/calculation.py`): `CalculationCreate` only allows Add, Sub, Multiply, or Divide, and rejects dividing by zero; `CalculationRead` returns the saved calculation.
- **Factory** (`app/calculation_factory.py`): `CalculationFactory` picks the right operation for each type.

To run only the calculation tests:

    pytest tests/unit/test_calculation_factory.py tests/unit/test_calculation_schemas.py tests/integration/test_calculation_db.py

## API Routes (Module 12)

**Users** (`app/routes/users.py`)

| Method | Route | What it does |
|---|---|---|
| POST | `/users/register` | Create a user (password is hashed). Returns 201, or 400 if the username/email is taken |
| POST | `/users/login` | Check username and password. Returns 200, or 401 if they don't match |

**Calculations** (`app/routes/calculations.py`)

| Method | Route | What it does |
|---|---|---|
| GET | `/calculations` | Browse all calculations |
| GET | `/calculations/{id}` | Read one calculation (404 if not found) |
| PUT | `/calculations/{id}` | Edit a calculation and recompute its result |
| POST | `/calculations` | Add a calculation for an existing user (201) |
| DELETE | `/calculations/{id}` | Delete a calculation (204) |

Invalid data (bad email, unknown type, dividing by zero) returns 400.

## Manual Checks with OpenAPI

1. Start the database and the app:
   docker compose up -d db
   python main.py
2. Open http://127.0.0.1:8000/docs
3. For each route, click it, then **Try it out**, enter the JSON, and click **Execute**:
   - Register: `{"username": "alice", "email": "alice@example.com", "password": "secret123"}`
   - Login: `{"username": "alice", "password": "secret123"}`
   - Add: `{"a": 10, "b": 4, "type": "Divide", "user_id": 1}`
   - Browse: no body needed
4. Check the **Server response** code and body.

To run only the route integration tests:

    pytest tests/integration/test_routes.py

## Running the Tests Locally

1. Set up the project:
   ```
   git clone https://github.com/atharhanjra/assignment12.git
   cd assignment12
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python -m playwright install --with-deps chromium
   ```
2. Start the PostgreSQL database (Docker Desktop must be running):
   ```
   docker compose up -d db
   ```
3. Run the tests:
   ```
   pytest
   ```
   Or by type:
   ```
   pytest tests/unit/
   pytest tests/integration/
   pytest tests/e2e/
   ```

- **Unit tests** check hashing and schema validation.
- **Integration tests** use the real PostgreSQL database to check user creation, duplicate usernames and emails, invalid emails, and login.
- **End-to-end tests** use Playwright to test the calculator in a browser.

## CI/CD Pipeline

The workflow in `.github/workflows/test.yml` runs on every push to `main`:

1. **test:** runs all tests with a PostgreSQL service container
2. **security:** builds the Docker image and scans it with Trivy
3. **deploy:** pushes the image to Docker Hub as `atharhanjra/assignment12`
# Candidate Management API

A simple, asynchronous REST API for managing candidates and their applications in a recruitment process, built with FastAPI, SQLAlchemy (async), PostgreSQL, and Docker.

---

## Quickstart

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and fill in your secrets / database settings:

```dotenv
# .env
DEBUG=True
JWT_SECRET=your_jwt_secret_here
JWT_ALGORITHM=HS256

# Adjust as necessary
DB_SERVER=localhost
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=backend_service
DB_PORT=5432
```

### Install & Run Locally

> **Prerequisites:** Python 3.12+, PostgreSQL running on the above DB settings

```bash
# 1) Create a virtualenv & install deps
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# 2) (Re)create your database
#    e.g. using psql:
psql -h $DB_SERVER -U $DB_USER -c "CREATE DATABASE $DB_NAME;"

# 3) Run the app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Your API will be live at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### Run with Docker & Docker Compose

> **Prerequisites:** Docker & Docker Compose

```bash
# Build & start everything
docker-compose up --build

# — or in detached mode —
docker-compose up --build -d
```

- **Postgres** at `localhost:5432`
- **API** at `http://localhost:8000`
- **Docs** at `http://localhost:8000/docs`

To tear down:

```bash
docker-compose down
```

---

## Testing

```bash
# If running locally:
pytest

# If inside Docker container:
docker-compose exec web pytest
```

---

## Project Structure

```
├── app/
│   ├── core/         # config, database, security, db client
│   ├── models/       # SQLAlchemy models (User, Candidate, Application)
│   ├── routes/       # FastAPI routers (auth, candidate, application)
│   └── schemas/      # Pydantic schemas
├── tests/            # pytest suite (stubbed DBClient, endpoint tests)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── main.py           # FastAPI entrypoint
```

---

## Environment Variables

| Variable         | Description                                  | Default           |
|------------------|----------------------------------------------|-------------------|
| `DEBUG`          | Enable FastAPI logging & SQL echo            | `False`           |
| `JWT_SECRET`     | Secret for signing JWT tokens                | _REQUIRED_        |
| `JWT_ALGORITHM`  | JWT algorithm (e.g. `HS256`)                 | _REQUIRED_        |
| `DB_SERVER`      | Postgres hostname                            | `localhost`       |
| `DB_USER`        | Postgres user                                | `postgres`        |
| `DB_PASSWORD`    | Postgres password                            | `postgres`        |
| `DB_NAME`        | Postgres database name                       | `backend_service` |
| `DB_PORT`        | Postgres port                                | `5432`            |

---

## Footer Notes
This Python project was specifically created as a test project for the backend developer role at [REDACTED].

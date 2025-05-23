# Expense Tracker API

A FastAPI-based backend application for managing shared expenses among users and groups. This application is built with modern Python practices, including asynchronous programming and comprehensive testing.

## Features

-   **User Management**: User registration, retrieval, updates, and deletion. Secure password hashing.
-   **Group Management**: Creation of groups, adding/removing members, group details retrieval, updates, and deletion.
-   **Expense Tracking**: Adding expenses (individual or group), specifying who paid and who participated. Calculation of shares (currently equal split). Retrieval, update, and deletion of expenses.
-   **Asynchronous**: Fully asynchronous API built with FastAPI and async database interactions.
-   **Database**: Uses SQLModel ORM with an async SQLite backend (via `aiosqlite`).
-   **Testing**: Comprehensive test suite using Pytest and HTTPX.

## Tech Stack

-   Python 3.10+
-   FastAPI
-   SQLModel (ORM based on Pydantic and SQLAlchemy)
-   SQLite (with `aiosqlite` for async operations)
-   Uvicorn (ASGI server)
-   Passlib (for password hashing)
-   Python-JOSE (for JWTs, if implemented later)
-   Pytest (for testing)
-   HTTPX (for async HTTP requests in tests)
-   `uv` (for environment and package management)

## Setup and Installation

This project uses `uv` for managing the Python environment and dependencies.

1.  **Prerequisites**:
    *   Ensure you have Python 3.10 or newer installed.
    *   Install `uv` by following the official instructions on [astral.sh/uv](https://astral.sh/uv) (e.g., `pip install uv`).

2.  **Clone the Repository**:
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

3.  **Create and Activate Virtual Environment**:
    Navigate to the project root directory and run:
    ```bash
    uv venv
    ```
    This creates a `.venv` directory. Activate it:
    *   macOS/Linux: `source .venv/bin/activate`
    *   Windows (PowerShell): `.venv\Scripts\Activate.ps1`
    *   Windows (CMD): `.venv\Scripts\activate.bat`

4.  **Install Dependencies**:
    With the virtual environment activated:
    ```bash
    uv sync
    ```

## Running the Application

To run the development server:
```bash
uvicorn app.main:app --reload --port 8000
```
The API will be accessible at `http://localhost:8000`.
Interactive API documentation (Swagger UI) will be available at `http://localhost:8000/docs`.
Alternative API documentation (ReDoc) will be available at `http://localhost:8000/redoc`.

## Running Tests

To run the test suite:
```bash
pytest
```
Or, using `uv`:
```bash
uv run pytest
```
This will discover and run all tests in the `app/tests` directory. Make sure the test database (`test_app_temp.db`) can be created in the root directory, or adjust its path in `app/tests/conftest.py` if needed.

## Project Structure (Overview)

```
├── app/                  # Main application code
│   ├── core/             # Core utilities (e.g., security)
│   ├── crud/             # CRUD operations for database models
│   ├── db/               # Database setup and session management
│   ├── models/           # SQLModel definitions and Pydantic schemas
│   ├── routers/          # API endpoint definitions (FastAPI routers)
│   ├── services/         # Business logic layer
│   ├── tests/            # Automated tests
│   │   ├── conftest.py   # Pytest fixtures and test configuration
│   │   └── test_*.py     # Test files
│   └── main.py           # FastAPI application entry point
├── requirements.txt      # Project dependencies
├── uv_setup_guide.md     # Detailed uv setup guide (supplements this README)
└── README.md             # This file
```

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
    cd <your-repo-name>/app
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

## Configuration

The application uses a `.env` file for configuration. An example file `.env.example` is provided in the project root (`../.env.example` relative to this `app` directory).

1.  **Create `.env` file**: Copy `.env.example` to `.env` in the project root:
    ```bash
    # From the project root directory (/Users/awalsangikar/personal/spendshare/)
    cp .env.example .env
    ```
2.  **Edit `.env`**: Modify the variables in the `.env` file as needed. Key variables include:
    *   `DATABASE_URL`: The connection string for your database.
    *   `DATABASE_ECHO`: Set to `True` to enable SQLAlchemy echo logging.
    *   `CORS_ALLOWED_ORIGINS_STRING`: A comma-separated string of allowed CORS origins.
    *   `SECRET_KEY`: A secret key for JWT token generation (important for production).
    *   `API_TITLE`, `API_DESCRIPTION`, `API_VERSION`: Metadata for the API documentation.

## Running the Application

Ensure you have created and configured your `.env` file in the project root as described in the "Configuration" section.

To run the development server (from the `app` directory, after activating the venv):
```bash
uvicorn src.main:app --reload --port 8000
```
The API will be accessible at `http://localhost:8000`.
Interactive API documentation (Swagger UI) will be available at `http://localhost:8000/docs`.

## Running Tests

To run the test suite:
```bash
pytest
```
Or, using `uv` (from the `app` directory, after activating the venv):
```bash
uv run pytest
```
This will discover and run all tests in the `app/src/tests` directory. Make sure the test database (`test_app_temp.db`) can be created in the root directory, or adjust its path in `app/src/tests/conftest.py` if needed.

## Docker Deployment

A `Dockerfile` is provided in this `app` directory to build a container image for the application.

1.  **Ensure `.env` file is present in the `app` directory**: Create or copy your `.env` file into the `/Users/awalsangikar/personal/spendshare/app/` directory. This file will be copied into the Docker image during the build process. Make sure it's configured for your deployment environment.
    Example: If your main `.env` is in the project root, you might copy it:
    ```bash
    # From the project root directory (/Users/awalsangikar/personal/spendshare/)
    cp .env app/.env 
    ```
    Or, create `app/.env` directly with the required settings.

2.  **Build the Docker Image**:
    Navigate to the `app` directory (`/Users/awalsangikar/personal/spendshare/app/`) and run:
    ```bash
    docker build -t spendshare-api .
    ```

3.  **Run the Docker Container**:
    ```bash
    docker run -d -p 8000:8000 --name spendshare-container spendshare-api
    ```
    This will run the container in detached mode and map port 8000 on your host to port 8000 in the container.
    The API will be accessible at `http://localhost:8000` (or `http://<your-docker-host-ip>:8000`).

    To run the container and provide environment variables directly (overriding those in the `.env` file copied during build):
    ```bash
    docker run -d -p 8000:8000 \
      -e DATABASE_URL="your_production_database_url" \
      -e SECRET_KEY="your_production_secret_key" \
      --name spendshare-container-prod spendshare-api
    ```

4.  **View Logs**:
    ```bash
    docker logs spendshare-container
    ```

5.  **Stop and Remove Container**:
    ```bash
    docker stop spendshare-container
    docker rm spendshare-container
    ```
